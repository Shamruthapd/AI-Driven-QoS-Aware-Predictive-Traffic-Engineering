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
from os_ken.lib.packet import tcp
from os_ken.lib.packet import udp

from controller.flow_classifier import classify_flow


class AIQoSSDNController(app_manager.OSKenApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    PRIORITY_METADATA = 1
    BEST_EFFORT_METADATA = 2

    PRIORITY_QUEUE = 1
    BEST_EFFORT_QUEUE = 0

    METADATA_MASK = 0xFFFFFFFFFFFFFFFF

    S1_FF_GROUP_PRIORITY = 100
    S1_FF_GROUP_BEST_EFFORT = 101
    S2_FF_GROUP_PRIORITY = 200
    S2_FF_GROUP_BEST_EFFORT = 201
    S3_FF_GROUP = 300

    # Primary egress ports that route inter-switch traffic to s3
    S1_FF_PORTS = (3,)
    S2_FF_PORTS = (3,)
    S3_FF_PORTS = (1, 2)

    FF_DESTINATIONS = {
        1: {
            "00:00:00:00:00:03": S1_FF_GROUP_PRIORITY,
            "00:00:00:00:00:04": S1_FF_GROUP_PRIORITY,
        },
        2: {
            "00:00:00:00:00:01": S2_FF_GROUP_PRIORITY,
            "00:00:00:00:00:02": S2_FF_GROUP_PRIORITY,
        },
        3: {
            "00:00:00:00:00:01": S3_FF_GROUP,
            "00:00:00:00:00:02": S3_FF_GROUP,
            "00:00:00:00:00:03": S3_FF_GROUP,
            "00:00:00:00:00:04": S3_FF_GROUP,
        },
    }

    def __init__(self, *args, **kwargs):
        super(AIQoSSDNController, self).__init__(*args, **kwargs)

        self.mac_to_port = {}
        self.datapaths = {}
        self.qos_flows = {}

        self.logger.info("====================================")
        self.logger.info(" AI-QoS SDN Controller Started ")
        self.logger.info(" Controller Version: v6 ")
        self.logger.info(" OpenFlow Version: 1.3 ")
        self.logger.info(" QoS Classification: ENABLED ")
        self.logger.info(" QoS Metadata Tags: ENABLED ")
        self.logger.info(" Queue Enforcement: ENABLED ")
        self.logger.info(" Fast-Failover Groups: ENABLED ")
        self.logger.info(" s1 FF Group: 100 ")
        self.logger.info(" s2 FF Group: 200 ")
        self.logger.info(" s3 FF Group: 300 ")
        self.logger.info("====================================")

    @set_ev_cls(
        ofp_event.EventOFPSwitchFeatures,
        CONFIG_DISPATCHER
    )
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        self.datapaths[datapath.id] = datapath

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        self.mac_to_port.setdefault(datapath.id, {})

        self.logger.info(
            "Switch connected | DPID=%s",
            datapath.id
        )

        self.add_flow(
            datapath=datapath,
            priority=0,
            match=parser.OFPMatch(),
            actions=[
                parser.OFPActionOutput(
                    ofproto.OFPP_CONTROLLER,
                    ofproto.OFPCML_NO_BUFFER
                )
            ]
        )

        # Drop IPv6 traffic at switch level to prevent triangle multicast storms
        self.add_flow(
            datapath=datapath,
            priority=50,
            match=parser.OFPMatch(eth_type=ether_types.ETH_TYPE_IPV6),
            actions=[]
        )

        self.logger.info(
            "Table-miss and IPv6 drop flows installed | DPID=%s",
            datapath.id
        )

    def add_flow(
        self,
        datapath,
        priority,
        match,
        actions,
        metadata=None
    ):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        instructions = []
        flow_actions = list(actions)

        if metadata is not None:
            instructions.append(
                parser.OFPInstructionWriteMetadata(
                    metadata,
                    self.METADATA_MASK
                )
            )

        if metadata == self.PRIORITY_METADATA:
            flow_actions.insert(
                0,
                parser.OFPActionSetQueue(self.PRIORITY_QUEUE)
            )

        elif metadata == self.BEST_EFFORT_METADATA:
            flow_actions.insert(
                0,
                parser.OFPActionSetQueue(self.BEST_EFFORT_QUEUE)
            )

        instructions.append(
            parser.OFPInstructionActions(
                ofproto.OFPIT_APPLY_ACTIONS,
                flow_actions
            )
        )

        datapath.send_msg(
            parser.OFPFlowMod(
                datapath=datapath,
                priority=priority,
                match=match,
                instructions=instructions
            )
        )

    @staticmethod
    def is_multicast_or_broadcast(mac_address):
        mac_address = mac_address.lower()

        return (
            mac_address == "ff:ff:ff:ff:ff:ff"
            or mac_address.startswith("01:00:5e:")
            or mac_address.startswith("33:33:")
        )

    def get_forwarding_actions(
        self,
        datapath,
        out_port,
        parser,
        dst=None,
        traffic_class="BEST_EFFORT"
    ):
        from controller.ai_sdn_bridge import SHARED_STATE
        dpid = datapath.id

        # Switch 3 (Core transit switch between s1 and s2)
        # Port 1 connects to s1 (hosts h1, h2); Port 2 connects to s2 (hosts h3, h4).
        if dpid == 3:
            if dst in ("00:00:00:00:00:01", "00:00:00:00:00:02"):
                self.logger.info("Core s3 transit -> s1 (port 1) | DST=%s", dst)
                return [parser.OFPActionOutput(1)]
            elif dst in ("00:00:00:00:00:03", "00:00:00:00:00:04"):
                self.logger.info("Core s3 transit -> s2 (port 2) | DST=%s", dst)
                return [parser.OFPActionOutput(2)]
            return [parser.OFPActionOutput(out_port)]

        if SHARED_STATE.get("active_mode") == "baseline_shortest_path":
            return [parser.OFPActionOutput(out_port)]

        # Switch 1 Fast-Failover: inter-switch traffic destined for s2 hosts (h3, h4)
        if dpid == 1 and dst in ("00:00:00:00:00:03", "00:00:00:00:00:04"):
            group_id = (
                self.S1_FF_GROUP_PRIORITY
                if traffic_class == "PRIORITY"
                else self.S1_FF_GROUP_BEST_EFFORT
            )
            self.logger.info(
                "Fast-Failover forwarding | DPID=1 | DST=%s | CLASS=%s | GROUP=%s",
                dst,
                traffic_class,
                group_id
            )
            return [parser.OFPActionGroup(group_id)]

        # Switch 2 Fast-Failover: inter-switch traffic destined for s1 hosts (h1, h2)
        if dpid == 2 and dst in ("00:00:00:00:00:01", "00:00:00:00:00:02"):
            group_id = (
                self.S2_FF_GROUP_PRIORITY
                if traffic_class == "PRIORITY"
                else self.S2_FF_GROUP_BEST_EFFORT
            )
            self.logger.info(
                "Fast-Failover forwarding | DPID=2 | DST=%s | CLASS=%s | GROUP=%s",
                dst,
                traffic_class,
                group_id
            )
            return [parser.OFPActionGroup(group_id)]

        return [
            parser.OFPActionOutput(out_port)
        ]

    @set_ev_cls(
        ofp_event.EventOFPPacketIn,
        MAIN_DISPATCHER
    )
    def packet_in_handler(self, ev):
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
        dpid = datapath.id

        if eth.ethertype in (ether_types.ETH_TYPE_LLDP, ether_types.ETH_TYPE_IPV6):
            return

        self.mac_to_port.setdefault(dpid, {})

        learn_source = not self.is_multicast_or_broadcast(dst)

        if learn_source:
            self.mac_to_port[dpid].setdefault(src, in_port)

        self.logger.info(
            "Packet-In | DPID=%s | SRC=%s | DST=%s | IN_PORT=%s",
            dpid,
            src,
            dst,
            in_port
        )

        classification = None
        ip_pkt = pkt.get_protocol(ipv4.ipv4)
        tcp_pkt = None
        udp_pkt = None

        src_ip = None
        dst_ip = None
        ip_proto = None
        dst_port = None
        dscp = None

        if ip_pkt is not None:
            src_ip = ip_pkt.src
            dst_ip = ip_pkt.dst
            ip_proto = ip_pkt.proto
            dscp = (ip_pkt.tos >> 2) & 0x3F

            tcp_pkt = pkt.get_protocol(tcp.tcp)
            udp_pkt = pkt.get_protocol(udp.udp)

            if tcp_pkt is not None:
                dst_port = tcp_pkt.dst_port
            elif udp_pkt is not None:
                dst_port = udp_pkt.dst_port

            classification = classify_flow(
                src_ip=src_ip,
                dst_ip=dst_ip,
                ip_proto=ip_proto,
                dst_port=dst_port,
                dscp=dscp,
            )

            if classification.traffic_class == "PRIORITY":
                qos_metadata = self.PRIORITY_METADATA
                queue_id = self.PRIORITY_QUEUE
            else:
                qos_metadata = self.BEST_EFFORT_METADATA
                queue_id = self.BEST_EFFORT_QUEUE

            self.logger.info(
                "QoS Classification | "
                "SRC_IP=%s | DST_IP=%s | PROTO=%s | "
                "DST_PORT=%s | DSCP=%s | CLASS=%s | "
                "METADATA=%s | QUEUE=%s | REASON=%s",
                src_ip,
                dst_ip,
                ip_proto,
                dst_port,
                dscp,
                classification.traffic_class,
                qos_metadata,
                queue_id,
                classification.reason
            )

        STATIC_EGRESS = {
            1: {"00:00:00:00:00:01": 1, "00:00:00:00:00:02": 2, "00:00:00:00:00:03": 3, "00:00:00:00:00:04": 3},
            2: {"00:00:00:00:00:01": 3, "00:00:00:00:00:02": 3, "00:00:00:00:00:03": 1, "00:00:00:00:00:04": 2},
            3: {"00:00:00:00:00:01": 1, "00:00:00:00:00:02": 1, "00:00:00:00:00:03": 2, "00:00:00:00:00:04": 2},
        }

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
            self.logger.info(
                "Known destination | DST=%s | OUT_PORT=%s",
                dst,
                out_port
            )
        elif dpid in STATIC_EGRESS and dst in STATIC_EGRESS[dpid]:
            out_port = STATIC_EGRESS[dpid][dst]
            self.logger.info(
                "Topology egress route | DPID=%s | DST=%s | OUT_PORT=%s",
                dpid,
                dst,
                out_port
            )
        else:
            out_port = ofproto.OFPP_FLOOD
            self.logger.info(
                "Unknown destination | DST=%s | FLOOD",
                dst
            )

        if out_port == in_port:
            self.logger.info(
                "Loop packet dropped | SRC=%s | DST=%s | IN_PORT=%s",
                src,
                dst,
                in_port
            )
            return

        traffic_class = classification.traffic_class if classification is not None else "BEST_EFFORT"
        actions = self.get_forwarding_actions(
            datapath=datapath,
            out_port=out_port,
            parser=parser,
            dst=dst,
            traffic_class=traffic_class
        )

        if out_port != ofproto.OFPP_FLOOD:
            match_fields = {
                "in_port": in_port,
                "eth_dst": dst,
            }

            if classification is not None and ip_pkt is not None:
                match_fields.update({
                    "eth_type": ether_types.ETH_TYPE_IP,
                    "ipv4_src": src_ip,
                    "ipv4_dst": dst_ip,
                    "ip_proto": ip_proto,
                })

                if ip_proto == 6 and tcp_pkt is not None:
                    match_fields["tcp_dst"] = tcp_pkt.dst_port
                elif ip_proto == 17 and udp_pkt is not None:
                    match_fields["udp_dst"] = udp_pkt.dst_port

            match = parser.OFPMatch(**match_fields)

            if classification is not None:
                if classification.traffic_class == "PRIORITY":
                    qos_metadata = self.PRIORITY_METADATA
                    queue_id = self.PRIORITY_QUEUE
                else:
                    qos_metadata = self.BEST_EFFORT_METADATA
                    queue_id = self.BEST_EFFORT_QUEUE

                self.add_flow(
                    datapath=datapath,
                    priority=100,
                    match=match,
                    actions=actions,
                    metadata=qos_metadata
                )
                self.qos_flows[(dpid, out_port)] = {
                    "datapath": datapath,
                    "match": match,
                    "priority": 100,
                    "out_port": out_port,
                    "traffic_class": classification.traffic_class,
                    "queue_id": queue_id,
                }

                self.logger.info(
                    "QoS forwarding flow installed | "
                    "DPID=%s | IN_PORT=%s | SRC_IP=%s | "
                    "DST_IP=%s | PROTO=%s | DST_PORT=%s | "
                    "OUT_PORT=%s | CLASS=%s | METADATA=%s | QUEUE=%s",
                    dpid,
                    in_port,
                    src_ip,
                    dst_ip,
                    ip_proto,
                    dst_port,
                    out_port,
                    classification.traffic_class,
                    qos_metadata,
                    queue_id
                )
            else:
                self.add_flow(
                    datapath=datapath,
                    priority=10,
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

        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=msg.data
        )

        datapath.send_msg(out)

    def apply_qos_policy(self, port_no, queue_id):
        """
        Apply a QoS queue policy to the existing classified flow
        associated with the specified output port.
        """

        matches = [
            flow
            for (dpid, out_port), flow in self.qos_flows.items()
            if out_port == port_no
        ]

        if not matches:
            self.logger.warning(
                "QoS policy not applied | OUT_PORT=%s | "
                "No registered QoS flow found",
                port_no
            )
            return False

        if len(matches) > 1:
            self.logger.warning(
                "QoS policy not applied | OUT_PORT=%s | "
                "Multiple QoS flows found; port is ambiguous",
                port_no
            )
            return False

        flow = matches[0]
        datapath = flow["datapath"]
        parser = datapath.ofproto_parser

        if queue_id not in (
            self.PRIORITY_QUEUE,
            self.BEST_EFFORT_QUEUE,
        ):
            self.logger.warning(
                "QoS policy not applied | OUT_PORT=%s | "
                "Invalid QUEUE_ID=%s",
                port_no,
                queue_id
            )
            return False

        actions = self.get_forwarding_actions(
            datapath,
            port_no,
            parser
        )

        actions.insert(
            0,
            parser.OFPActionSetQueue(queue_id)
        )

        datapath.send_msg(
            parser.OFPFlowMod(
                datapath=datapath,
                priority=flow["priority"],
                match=flow["match"],
                instructions=[
                    parser.OFPInstructionActions(
                        datapath.ofproto.OFPIT_APPLY_ACTIONS,
                        actions
                    )
                ]
            )
        )

        flow["queue_id"] = queue_id

        self.logger.info(
            "QoS policy applied | DPID=%s | OUT_PORT=%s | "
            "QUEUE=%s | CLASS=%s",
            datapath.id,
            port_no,
            queue_id,
            flow["traffic_class"]
        )

        return True
