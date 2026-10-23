"""
Port Status Event Logger for OS-Ken.
Listens for OpenFlow EventOFPPortStatus messages and records port state transitions
(UP / DOWN / MODIFY / ADD / DELETE) with sub-millisecond timestamps.
Provides the 'controller-side view' of link failures for comparison with the data-plane recovery view.
"""

from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import MAIN_DISPATCHER, set_ev_cls
from os_ken.ofproto import ofproto_v1_3
import csv
import time
from datetime import datetime, timezone
from pathlib import Path


class PortStatusLogger(app_manager.OSKenApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(PortStatusLogger, self).__init__(*args, **kwargs)
        self.logger.info("Port Status Event Logger Initialized")
        self.log_path = Path("data/results/port_status_events.csv")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            with open(self.log_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp_iso", "timestamp_epoch", "dpid", "port_no", "reason", "link_state"])

    @set_ev_cls(ofp_event.EventOFPPortStatus, MAIN_DISPATCHER)
    def port_status_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        desc = msg.desc
        ofproto = datapath.ofproto

        reasons = {
            ofproto.OFPPR_ADD: "ADD",
            ofproto.OFPPR_MODIFY: "MODIFY",
            ofproto.OFPPR_DELETE: "DELETE",
        }
        reason = reasons.get(msg.reason, str(msg.reason))
        link_state = "DOWN" if (desc.state & ofproto.OFPPS_LINK_DOWN) else "UP"
        
        now = datetime.now(timezone.utc)
        epoch_ts = time.time()
        now_iso = now.isoformat()

        self.logger.info(
            "PORT_STATUS_EVENT: DPID=%s | PORT=%s | STATE=%s | REASON=%s | TIMESTAMP=%s",
            datapath.id,
            desc.port_no,
            link_state,
            reason,
            now_iso
        )

        try:
            with open(self.log_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([now_iso, f"{epoch_ts:.6f}", datapath.id, desc.port_no, reason, link_state])
        except Exception as e:
            self.logger.error("Error writing port status log: %s", e)
