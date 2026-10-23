from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import (
    CONFIG_DISPATCHER,
    MAIN_DISPATCHER,
    set_ev_cls,
)
from os_ken.ofproto import ofproto_v1_3


class FastFailoverGroups(app_manager.OSKenApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    GROUPS = {
        1: (100, 3, 4),
        2: (200, 4, 3),
        3: (300, 1, 2),
    }

    def __init__(self, *args, **kwargs):
        super(FastFailoverGroups, self).__init__(*args, **kwargs)
        self.logger.info("Fast-Failover Group Module Started")

    @set_ev_cls(
        ofp_event.EventOFPSwitchFeatures,
        CONFIG_DISPATCHER
    )
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        group_config = self.GROUPS.get(datapath.id)

        if group_config is None:
            return

        group_id, primary_port, backup_port = group_config

        self._install_fast_failover_group(
            datapath=datapath,
            group_id=group_id,
            primary_port=primary_port,
            backup_port=backup_port,
        )

    @set_ev_cls(
        ofp_event.EventOFPPortStatus,
        MAIN_DISPATCHER
    )
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

        link_state = (
            "DOWN"
            if desc.state & ofproto.OFPPS_LINK_DOWN
            else "UP"
        )

        self.logger.info(
            "PORT STATUS | DPID=%s | PORT=%s | REASON=%s | LINK=%s",
            datapath.id,
            desc.port_no,
            reason,
            link_state,
        )

    def _install_fast_failover_group(
        self,
        datapath,
        group_id,
        primary_port,
        backup_port,
    ):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        primary_bucket = parser.OFPBucket(
            watch_port=primary_port,
            watch_group=ofproto.OFPG_ANY,
            actions=[
                parser.OFPActionOutput(primary_port)
            ],
        )

        backup_bucket = parser.OFPBucket(
            watch_port=backup_port,
            watch_group=ofproto.OFPG_ANY,
            actions=[
                parser.OFPActionOutput(backup_port)
            ],
        )

        group_mod = parser.OFPGroupMod(
            datapath=datapath,
            command=ofproto.OFPGC_ADD,
            type_=ofproto.OFPGT_FF,
            group_id=group_id,
            buckets=[
                primary_bucket,
                backup_bucket,
            ],
        )

        datapath.send_msg(group_mod)

        self.logger.info(
            "FAST-FAILOVER GROUP INSTALLED | "
            "DPID=%s | GROUP=%s | PRIMARY=PORT%s | BACKUP=PORT%s",
            datapath.id,
            group_id,
            primary_port,
            backup_port,
        )
