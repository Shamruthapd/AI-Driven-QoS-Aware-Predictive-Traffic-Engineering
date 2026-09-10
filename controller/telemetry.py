import csv
from datetime import datetime, timezone
from pathlib import Path

from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import MAIN_DISPATCHER
from os_ken.controller.handler import set_ev_cls
from os_ken.ofproto import ofproto_v1_3


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = PROJECT_ROOT / "datasets" / "raw"
DATASET_FILE = DATASET_DIR / "telemetry.csv"


class TelemetryCollector(app_manager.OSKenApp):
    """
    Collect raw OpenFlow port statistics.

    Raw telemetry is stored without derived calculations so that
    later processing remains reproducible.
    """

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(TelemetryCollector, self).__init__(*args, **kwargs)

        DATASET_DIR.mkdir(parents=True, exist_ok=True)

        self.logger.info(
            "Telemetry collector initialized | output=%s",
            DATASET_FILE
        )

    @set_ev_cls(
        ofp_event.EventOFPPortStatsReply,
        MAIN_DISPATCHER
    )
    def port_stats_reply_handler(self, ev):
        """
        Receive and persist OpenFlow port statistics.
        """

        datapath = ev.msg.datapath
        timestamp = datetime.now(timezone.utc).isoformat()

        rows = []

        for stat in ev.msg.body:

            row = {
                "timestamp": timestamp,
                "dpid": datapath.id,
                "port": stat.port_no,
                "rx_packets": stat.rx_packets,
                "tx_packets": stat.tx_packets,
                "rx_bytes": stat.rx_bytes,
                "tx_bytes": stat.tx_bytes,
                "rx_dropped": stat.rx_dropped,
                "tx_dropped": stat.tx_dropped,
                "rx_errors": stat.rx_errors,
                "tx_errors": stat.tx_errors,
            }

            rows.append(row)

        self._write_rows(rows)

    def _write_rows(self, rows):
        """
        Append telemetry rows to the raw CSV dataset.
        """

        if not rows:
            return

        file_exists = DATASET_FILE.exists()
        fieldnames = list(rows[0].keys())

        with DATASET_FILE.open(
            "a",
            newline="",
            encoding="utf-8"
        ) as csv_file:

            writer = csv.DictWriter(
                csv_file,
                fieldnames=fieldnames
            )

            if not file_exists or DATASET_FILE.stat().st_size == 0:
                writer.writeheader()

            writer.writerows(rows)

        self.logger.info(
            "Telemetry recorded | DPID=%s | ports=%s",
            rows[0]["dpid"],
            len(rows)
        )
