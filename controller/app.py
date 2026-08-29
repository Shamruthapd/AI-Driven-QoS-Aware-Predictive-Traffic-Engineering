from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import (
    CONFIG_DISPATCHER,
    MAIN_DISPATCHER,
    set_ev_cls,
)
from os_ken.ofproto import ofproto_v1_3
from os_ken.lib.packet import ethernet
from os_ken.lib.packet import ether_types
from os_ken.lib.packet import packet


class AIQoSSDNController(app_manager.OSKenApp):
    """
    AI-driven QoS-aware SDN Controller.

    Controller v2:
    - OpenFlow 1.3
    - Table-miss flow
    - MAC learning
    - Packet-In handling
    - Dynamic flow installation
    """

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(AIQoSSDNController, self).__init__(*args, **kwargs)

        # MAC learning table:
        # {datapath_id: {mac_address: switch_port}}
        self.mac_to_port = {}

        self.logger.info("====================================")
        self.logger.info(" AI-QoS SDN Controller Started ")
        self.logger.info(" Controller Version: v2 ")
        self.logger.info(" OpenFlow Version: 1.3 ")
        self.logger.info("====================================")

    @set_ev_cls(
        ofp_event.EventOFPSwitchFeatures,
        CONFIG_DISPATCHER
    )
    def switch_features_handler(self, ev):
        """
        Handle a newly connected OpenFlow switch.
        """

        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        self.mac_to_port.setdefault(datapath.id, {})

        self.logger.info(
            "Switch connected | DPID=%s",
            datapath.id
        )

        # Table-miss rule:
        # Send unmatched packets to the controller.
        match = parser.OFPMatch()

        actions = [
            parser.OFPActionOutput(
                ofproto.OFPP_CONTROLLER,
                ofproto.OFPCML_NO_BUFFER
            )
        ]

        self.add_flow(
            datapath=datapath,
            priority=0,
            match=match,
            actions=actions
        )

        self.logger.info(
            "Table-miss flow installed | DPID=%s",
            datapath.id
        )

    def add_flow(self, datapath, priority, match, actions):
        """
        Install a flow entry on the switch.
        """

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        instructions = [
            parser.OFPInstructionActions(
                ofproto.OFPIT_APPLY_ACTIONS,
                actions
            )
        ]

        flow_mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=instructions
        )

        datapath.send_msg(flow_mod)

    @set_ev_cls(
        ofp_event.EventOFPPacketIn,
        MAIN_DISPATCHER
    )
    def packet_in_handler(self, ev):
        """
        Handle packets sent from the switch to the controller.
        """

        msg = ev.msg
        datapath = msg.datapath

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        in_port = msg.match["in_port"]

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth is None:
            return

        src = eth.src
        dst = eth.dst

        # Ignore LLDP packets.
        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        dpid = datapath.id

        # Learn source MAC address.
        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port

        self.logger.info(
            "Packet-In | DPID=%s | SRC=%s | DST=%s | IN_PORT=%s",
            dpid,
            src,
            dst,
            in_port
        )

        # Determine output port.
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]

            self.logger.info(
                "Known destination | DST=%s | OUT_PORT=%s",
                dst,
                out_port
            )

        else:
            out_port = ofproto.OFPP_FLOOD

            self.logger.info(
                "Unknown destination | DST=%s | FLOOD",
                dst
            )

        actions = [
            parser.OFPActionOutput(out_port)
        ]

        # Once destination is known, install a flow.
        if out_port != ofproto.OFPP_FLOOD:

            match = parser.OFPMatch(
                in_port=in_port,
                eth_dst=dst
            )

            self.add_flow(
                datapath=datapath,
                priority=10,
                match=match,
                actions=actions
            )

            self.logger.info(
                "Forwarding flow installed | "
                "SRC=%s | DST=%s | OUT_PORT=%s",
                src,
                dst,
                out_port
            )

        # Send the current packet immediately.
        data = None

        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=data
        )

        datapath.send_msg(out)
