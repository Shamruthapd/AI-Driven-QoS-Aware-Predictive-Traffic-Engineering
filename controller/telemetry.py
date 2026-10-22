import csv
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from controller.ai_policy import AIPolicy
from controller.live_inference import (
    FEATURE_COLUMNS,
    LiveInference,
)

from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import MAIN_DISPATCHER
from os_ken.controller.handler import set_ev_cls
from os_ken.ofproto import ofproto_v1_3


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATASET_DIR = PROJECT_ROOT / "datasets" / "raw"
DATASET_FILE = DATASET_DIR / "telemetry.csv"

WEEK6_DIR = PROJECT_ROOT / "results" / "week6"
PREDICTION_FILE = WEEK6_DIR / "predictions.csv"


class TelemetryCollector(app_manager.OSKenApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(TelemetryCollector, self).__init__(*args, **kwargs)

        self.live_inference = LiveInference()
        self.ai_policy = AIPolicy()

        DATASET_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        WEEK6_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.logger.info(
            "Telemetry collector initialized | output=%s",
            DATASET_FILE,
        )

        self.logger.info(
            "Live AI policy initialized | MSE_THRESHOLD=%.3f",
            self.ai_policy.MSE_THRESHOLD,
        )

    @set_ev_cls(
        ofp_event.EventOFPPortStatsReply,
        MAIN_DISPATCHER,
    )
    def port_stats_reply_handler(self, ev):
        datapath = ev.msg.datapath

        timestamp = datetime.now(
            timezone.utc
        ).isoformat()

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

        for row in rows:
            result = self.live_inference.process_row(row)

            if result is None:
                continue

            self.logger.info(
                "LIVE INFERENCE READY | "
                "DPID=%s | PORT=%s | INPUT_SHAPE=%s | "
                "LATENCY_MS=%.3f",
                result["dpid"],
                result["port"],
                result["input_shape"],
                result["inference_latency_ms"],
            )

            completed_prediction = result.get(
                "completed_prediction"
            )

            if completed_prediction is None:
                continue

            prediction_original = np.asarray(
                completed_prediction["prediction"],
                dtype=np.float64,
            )

            actual_original = np.asarray(
                result["actual"],
                dtype=np.float64,
            )

            prediction_scaled = self.live_inference.scaler.transform(
                prediction_original.reshape(1, -1)
            )[0]

            actual_scaled = self.live_inference.scaler.transform(
                actual_original.reshape(1, -1)
            )[0]

            decision = self.ai_policy.evaluate(
                dpid=result["dpid"],
                port=result["port"],
                prediction_scaled=prediction_scaled,
                actual_scaled=actual_scaled,
                inference_latency_ms=completed_prediction[
                    "inference_latency_ms"
                ],
            )

            self.logger.info(
                "AI POLICY DECISION | "
                "DPID=%s | PORT=%s | MSE=%.6f | "
                "CLASS=%s | QUEUE=%s | LATENCY_MS=%.3f",
                decision.dpid,
                decision.port,
                decision.mse,
                decision.classification,
                decision.queue_id,
                decision.inference_latency_ms,
            )

            print(
                "AI POLICY DECISION | "
                f"DPID={decision.dpid} | "
                f"PORT={decision.port} | "
                f"MSE={decision.mse:.6f} | "
                f"CLASS={decision.classification} | "
                f"QUEUE={decision.queue_id} | "
                f"LATENCY_MS="
                f"{decision.inference_latency_ms:.3f}",
                flush=True,
            )

            self._write_prediction(
                result=result,
                completed_prediction=completed_prediction,
                decision=decision,
            )

    def _write_prediction(
        self,
        result,
        completed_prediction,
        decision,
    ):
        prediction = completed_prediction["prediction"]
        actual = result["actual"]

        prediction_timestamp = completed_prediction[
            "timestamp"
        ].isoformat()

        actual_timestamp = result[
            "actual_timestamp"
        ].isoformat()

        inference_latency_ms = completed_prediction.get(
            "inference_latency_ms"
        )

        row = {
            "prediction_timestamp": prediction_timestamp,
            "actual_timestamp": actual_timestamp,
            "dpid": result["dpid"],
            "port": result["port"],
            "inference_latency_ms": float(
                inference_latency_ms
            ),
            "ai_mse": decision.mse,
            "ai_classification": decision.classification,
            "ai_queue_id": decision.queue_id,
        }

        for index, feature in enumerate(FEATURE_COLUMNS):
            row[f"actual_{feature}"] = float(
                actual[index]
            )

            row[f"predicted_{feature}"] = float(
                prediction[index]
            )

        file_exists = PREDICTION_FILE.exists()
        fieldnames = list(row.keys())

        with PREDICTION_FILE.open(
            "a",
            newline="",
            encoding="utf-8",
        ) as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=fieldnames,
            )

            if (
                not file_exists
                or PREDICTION_FILE.stat().st_size == 0
            ):
                writer.writeheader()

            writer.writerow(row)

    def _write_rows(self, rows):
        if not rows:
            return

        file_exists = DATASET_FILE.exists()
        fieldnames = list(rows[0].keys())

        with DATASET_FILE.open(
            "a",
            newline="",
            encoding="utf-8",
        ) as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=fieldnames,
            )

            if (
                not file_exists
                or DATASET_FILE.stat().st_size == 0
            ):
                writer.writeheader()

            writer.writerows(rows)

        self.logger.info(
            "Telemetry recorded | DPID=%s | ports=%s",
            rows[0]["dpid"],
            len(rows),
        )
