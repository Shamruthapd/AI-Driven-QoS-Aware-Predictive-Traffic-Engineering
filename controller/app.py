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
from os_ken.lib.packet import ipv4
from os_ken.lib.packet import udp


class AIQoSSDNController(app_manager.OSKenApp):
    """
    AI-driven QoS-aware SDN Controller.

    Controller v2:
    - OpenFlow 1.3
    - Table-miss flow
    - MAC learning
    - Packet-In handling
    - Dynamic flow installation
    - Same-port forwarding protection
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

        # Create MAC table for this switch if necessary.
        self.mac_to_port.setdefault(dpid, {})

        # Learn source MAC address.
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

        # ---------------------------------------------------------------
        # Same-port forwarding protection.
        #
        # Never forward a packet back through the same port
        # on which it arrived.
        # ---------------------------------------------------------------
        if out_port == in_port:

            self.logger.info(
                "Loop packet dropped | SRC=%s | DST=%s | IN_PORT=%s",
                src,
                dst,
                in_port
            )

            return

        # Identify priority UDP traffic for the contention-test receiver.
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        udp_pkt = pkt.get_protocol(udp.udp)

        is_priority_udp = (
            ip_pkt is not None
            and udp_pkt is not None
            and ip_pkt.dst == "10.0.0.3"
            and udp_pkt.dst_port == 5202
            and dpid == 1
            and out_port == 3
        )

        # Select Queue 1 only for known-destination priority UDP traffic.
        actions = []

        if out_port != ofproto.OFPP_FLOOD and is_priority_udp:
            actions.append(parser.OFPActionSetQueue(1))

        actions.append(parser.OFPActionOutput(out_port))

        # Install a specific higher-priority flow for priority UDP.
        # Other traffic retains the existing generic forwarding rule.
        if out_port != ofproto.OFPP_FLOOD:

            if is_priority_udp:
                match = parser.OFPMatch(
                    in_port=in_port,
                    eth_dst=dst,
                    eth_type=ether_types.ETH_TYPE_IP,
                    ip_proto=17,
                    ipv4_dst="10.0.0.3",
                    udp_dst=5202
                )
                flow_priority = 20
            else:
                match = parser.OFPMatch(
                    in_port=in_port,
                    eth_dst=dst
                )
                flow_priority = 10

            self.add_flow(
                datapath=datapath,
                priority=flow_priority,
                match=match,
                actions=actions
            )

            self.logger.info(
                "Forwarding flow installed | "
                "DPID=%s | IN_PORT=%s | DST=%s | OUT_PORT=%s",
                dpid,
                in_port,
                dst,
                out_port
            )

        # Send the current packet immediately.
        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=msg.data
        )

        datapath.send_msg(out)

        self.logger.info(
            "Packet-Out sent | "
            "DPID=%s | SRC=%s | DST=%s | OUT_PORT=%s",
            dpid,
            src,
            dst,
            out_port
        )
