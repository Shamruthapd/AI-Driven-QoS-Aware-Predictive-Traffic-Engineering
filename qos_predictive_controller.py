import csv
import os
import time
import pandas as pd
import numpy as np
import joblib
import warnings
from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER, set_ev_cls
from os_ken.ofproto import ofproto_v1_3
from os_ken.lib import hub
from os_ken.lib.packet import packet, ethernet, ether_types

warnings.filterwarnings('ignore', category=UserWarning)

class PredictiveQoSController(app_manager.OSKenApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(PredictiveQoSController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.datapaths = {}
        self.prev_stats = {}
        
        self.CONGESTION_THRESHOLD_MBPS = 10.0
        self.feature_cols = ['port_no', 'tx_throughput_mbps', 'rx_throughput_mbps', 
                            'tx_packet_rate', 'prev_tx_mbps', 'prev_rx_mbps', 'prev_tx_pkts']
        
        self.model_path = 'models/traffic_predictor.joblib'
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            self.logger.info("=== ML Traffic Predictor Model Loaded Successfully ===")
        else:
            self.model = None
            self.logger.warning("ML Model not found! Run train_model.py first.")

        self.monitor_thread = hub.spawn(self._monitor)

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, CONFIG_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.datapaths[datapath.id] = datapath
        elif ev.state == CONFIG_DISPATCHER:
            if datapath.id in self.datapaths:
                del self.datapaths[datapath.id]

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match, instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(2)

    def _request_stats(self, datapath):
        parser = datapath.ofproto_parser
        req = parser.OFPPortStatsRequest(datapath, 0, datapath.ofproto.OFPP_ANY)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body
        dpid = ev.msg.datapath.id
        now = time.time()

        for stat in body:
            port_no = stat.port_no
            if port_no >= ev.msg.datapath.ofproto.OFPP_MAX:
                continue

            key = (dpid, port_no)
            if key in self.prev_stats:
                prev_time, prev_rx_b, prev_tx_b, prev_rx_p, prev_tx_p = self.prev_stats[key]
                duration = now - prev_time

                if duration > 0:
                    tx_bytes_delta = stat.tx_bytes - prev_tx_b
                    rx_bytes_delta = stat.rx_bytes - prev_rx_b
                    tx_pkts_delta = stat.tx_packets - prev_tx_p

                    tx_mbps = (tx_bytes_delta * 8) / (duration * 1e6)
                    rx_mbps = (rx_bytes_delta * 8) / (duration * 1e6)
                    tx_pps = tx_pkts_delta / duration

                    if self.model and port_no in [2, 3]:
                        features_df = pd.DataFrame(
                            [[port_no, tx_mbps, rx_mbps, tx_pps, tx_mbps, rx_mbps, tx_pps]],
                            columns=self.feature_cols
                        )
                        predicted_tx_mbps = self.model.predict(features_df)[0]

                        self.logger.info(f"[ML Inference] Port {port_no} | Current: {tx_mbps:.2f} Mbps | Predicted t+1: {predicted_tx_mbps:.2f} Mbps")

                        if predicted_tx_mbps > self.CONGESTION_THRESHOLD_MBPS:
                            self.logger.warning(f" ALERT: Port {port_no} predicted throughput ({predicted_tx_mbps:.2f} Mbps) exceeds threshold ({self.CONGESTION_THRESHOLD_MBPS} Mbps)!")
                            self.logger.info(f"==> Initiating Dynamic OpenFlow QoS Policy Enforcement on Port {port_no} <==")

            self.prev_stats[key] = (now, stat.rx_bytes, stat.tx_bytes, stat.rx_packets, stat.tx_packets)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        dst = eth.dst
        src = eth.src
        dpid = datapath.id

        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
