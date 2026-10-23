"""
OpenFlow 1.3 Fast-Failover (FF) Group Module.
Provisions hardware/switch-level Fast-Failover group tables with queue preservation.
Ensures sub-second failover locally at the switch without controller round-trip,
and preserves QoS queue tags (Queue 1 for Priority, Queue 0 for Best-Effort) across failover.
"""

from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import (
    CONFIG_DISPATCHER,
    MAIN_DISPATCHER,
    set_ev_cls,
)
from os_ken.ofproto import ofproto_v1_3
from datetime import datetime, timezone
import csv
from pathlib import Path


class FastFailoverGroups(app_manager.OSKenApp):
    """
    OS-Ken application to install and manage OpenFlow 1.3 Fast-Failover groups.
    """

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    # Switch Port Configuration:
    # s1: port 3 -> s3 (primary), port 4 -> s2 (backup)
    # s2: port 3 -> s3 (primary), port 4 -> s1 (backup)
    # s3: port 1 -> s1 (primary), port 2 -> s2 (backup)
    SWITCH_TOPOLOGY = {
        1: {"primary_port": 3, "backup_port": 4},
        2: {"primary_port": 3, "backup_port": 4},
        3: {"primary_port": 1, "backup_port": 2},
    }

    # Group ID mappings:
    # (Priority Group, Best-Effort Group)
    GROUP_IDS = {
        1: {"priority": 100, "best_effort": 101},
        2: {"priority": 200, "best_effort": 201},
        3: {"standard": 300},
    }

    PRIORITY_QUEUE = 1
    BEST_EFFORT_QUEUE = 0

    def __init__(self, *args, **kwargs):
        super(FastFailoverGroups, self).__init__(*args, **kwargs)
        self.logger.info("Fast-Failover Group Module with QoS Queue Preservation Started")
        self.log_path = Path("data/results/port_status_events.csv")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            with open(self.log_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp_iso", "dpid", "port_no", "reason", "link_state"])

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        dpid = datapath.id

        if dpid not in self.SWITCH_TOPOLOGY:
            return

        ports = self.SWITCH_TOPOLOGY[dpid]
        p_port = ports["primary_port"]
        b_port = ports["backup_port"]

        if dpid in (1, 2):
            # 1. Install Priority Fast-Failover Group (Queue 1 in BOTH buckets)
            p_gid = self.GROUP_IDS[dpid]["priority"]
            self._install_ff_group(
                datapath=datapath,
                group_id=p_gid,
                primary_port=p_port,
                backup_port=b_port,
                queue_id=self.PRIORITY_QUEUE,
                desc="PRIORITY"
            )

            # 2. Install Best-Effort Fast-Failover Group (Queue 0 in BOTH buckets)
            be_gid = self.GROUP_IDS[dpid]["best_effort"]
            self._install_ff_group(
                datapath=datapath,
                group_id=be_gid,
                primary_port=p_port,
                backup_port=b_port,
                queue_id=self.BEST_EFFORT_QUEUE,
                desc="BEST_EFFORT"
            )

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
        now_iso = datetime.now(timezone.utc).isoformat()

        self.logger.info(
            "PORT STATUS EVENT | DPID=%s | PORT=%s | REASON=%s | LINK=%s",
            datapath.id,
            desc.port_no,
            reason,
            link_state,
        )

        try:
            with open(self.log_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([now_iso, datapath.id, desc.port_no, reason, link_state])
        except Exception as e:
            self.logger.error("Failed to write port status event log: %s", e)

    def _install_ff_group(self, datapath, group_id, primary_port, backup_port, queue_id=None, desc=""):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Primary bucket actions: set_queue (if specified) + output to primary_port
        primary_actions = []
        if queue_id is not None:
            primary_actions.append(parser.OFPActionSetQueue(queue_id))
        primary_actions.append(parser.OFPActionOutput(primary_port))

        primary_bucket = parser.OFPBucket(
            watch_port=primary_port,
            watch_group=ofproto.OFPG_ANY,
            actions=primary_actions
        )

        # Backup bucket actions: set_queue (if specified) + output to backup_port
        # CRITICAL: Keeping set_queue in BOTH buckets ensures QoS guarantees are NOT lost on failover!
        backup_actions = []
        if queue_id is not None:
            backup_actions.append(parser.OFPActionSetQueue(queue_id))
        backup_actions.append(parser.OFPActionOutput(backup_port))

        backup_bucket = parser.OFPBucket(
            watch_port=backup_port,
            watch_group=ofproto.OFPG_ANY,
            actions=backup_actions
        )

        group_mod = parser.OFPGroupMod(
            datapath=datapath,
            command=ofproto.OFPGC_ADD,
            type_=ofproto.OFPGT_FF,
            group_id=group_id,
            buckets=[primary_bucket, backup_bucket]
        )
        datapath.send_msg(group_mod)

        self.logger.info(
            "FAST-FAILOVER GROUP INSTALLED | DPID=%s | GID=%s (%s) | "
            "P_PORT=%s (watch=%s, queue=%s) | B_PORT=%s (watch=%s, queue=%s)",
            datapath.id,
            group_id,
            desc,
            primary_port,
            primary_port,
            queue_id,
            backup_port,
            backup_port,
            queue_id
        )
