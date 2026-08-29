from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import (
    MAIN_DISPATCHER,
    DEAD_DISPATCHER,
    set_ev_cls,
)
from os_ken.lib import hub
from os_ken.ofproto import ofproto_v1_3


class TelemetryMonitor(app_manager.OSKenApp):
    """
    Periodically requests OpenFlow port statistics
    from connected SDN switches.
    """

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    POLLING_INTERVAL = 5

    def __init__(self, *args, **kwargs):
        super(TelemetryMonitor, self).__init__(*args, **kwargs)

        self.datapaths = {}

        # Start the monitoring loop.
        self.monitor_thread = hub.spawn(self._monitor)

        self.logger.info(
            "Telemetry monitor started | interval=%ss",
            self.POLLING_INTERVAL
        )

    @set_ev_cls(
        ofp_event.EventOFPStateChange,
        [MAIN_DISPATCHER, DEAD_DISPATCHER]
    )
    def state_change_handler(self, ev):
        """
        Track switches as they connect and disconnect.
        """

        datapath = ev.datapath

        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.datapaths[datapath.id] = datapath

                self.logger.info(
                    "Telemetry registered switch | DPID=%s",
                    datapath.id
                )

        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                del self.datapaths[datapath.id]

                self.logger.info(
                    "Telemetry removed switch | DPID=%s",
                    datapath.id
                )

    def _monitor(self):
        """
        Periodically request port statistics.
        """

        while True:

            for datapath in list(self.datapaths.values()):
                self._request_port_stats(datapath)

            hub.sleep(self.POLLING_INTERVAL)

    def _request_port_stats(self, datapath):
        """
        Send an OpenFlow PortStatsRequest to a switch.
        """

        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        request = parser.OFPPortStatsRequest(
            datapath,
            0,
            ofproto.OFPP_ANY
        )

        datapath.send_msg(request)

        self.logger.debug(
            "Port statistics requested | DPID=%s",
            datapath.id
        )
