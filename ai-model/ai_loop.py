#!/usr/bin/env python3
"""Member 4 Week 9: resilient LSTM inference loop.

Reads the existing processed telemetry CSV, evaluates the last five observations
from one switch/port stream, forecasts the next feature vector with the existing
LSTM, calibrates predicted throughput to link utilization, and appends one JSONL
record per cycle. The anomaly residual is computed only after the next actual
observation arrives, avoiding comparison with data already in the input window.

This CSV adapter is the offline Week 9 interface. Member 1 and Member 4 must
still agree on the final controller-to-runtime transport/payload for Week 10.
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import signal
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config" / "ai_loop.yaml"
LOG = logging.getLogger("member4.ai_loop")
_STOP = False
FEATURE_COLUMNS = [
    "rx_packets_delta", "tx_packets_delta", "rx_bytes_delta", "tx_bytes_delta",
    "rx_dropped_delta", "tx_dropped_delta", "rx_errors_delta", "tx_errors_delta",
    "throughput_bps", "packet_rate_pps",
]

DEFAULTS: dict[str, Any] = {
    "polling_interval_seconds": 5.0,
    "telemetry_csv": "datasets/processed/qos_features.csv",
    "output_jsonl": "data/results/week9_ai_runtime.jsonl",
    "link_capacity_bps": 10_000_000,
    "max_telemetry_age_seconds": 15,
    "max_gap_seconds": 10,
    "sequence_length": 5,
    "anomaly_mse_threshold": 5.0,
    "model_checkpoint": "ai-model/checkpoints/lstm_model.pt",
    "scaler_path": "datasets/processed/scaler.pkl",
    "use_model": True,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def finite_number(value: Any) -> float | None:
    """Return a finite float, or None for invalid, NaN, or infinite values."""
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return result if math.isfinite(result) else None


def parse_scalar(text: str) -> Any:
    """Parse the simple scalar subset used by config/ai_loop.yaml (no PyYAML needed)."""
    text = text.strip()
    if text.lower() in {"true", "false"}:
        return text.lower() == "true"
    if text.lower() in {"null", "none", "~"}:
        return None
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        return text[1:-1]
    return text.split(" #", 1)[0].strip()


def load_config(path: Path) -> dict[str, Any]:
    config = DEFAULTS.copy()
    if not path.exists():
        LOG.warning("Config not found at %s; using built-in defaults", path)
        return config
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            raise ValueError(f"Invalid config line {line_no}: expected key: value")
        key, value = stripped.split(":", 1)
        key = key.strip()
        if key not in config:
            LOG.warning("Ignoring unknown config key %r (line %d)", key, line_no)
            continue
        config[key] = parse_scalar(value)
    if float(config["polling_interval_seconds"]) <= 0:
        raise ValueError("polling_interval_seconds must be > 0")
    if int(config["sequence_length"]) < 1:
        raise ValueError("sequence_length must be >= 1")
    if float(config["link_capacity_bps"]) <= 0:
        raise ValueError("link_capacity_bps must be > 0")
    return config



def read_latest_window(
    csv_path: Path,
    sequence_length: int,
    max_gap_seconds: float,
    max_age_seconds: float,
    now: datetime | None = None,
) -> tuple[list[dict[str, Any]], str | None]:
    """Return the newest valid, contiguous, fresh window from one stream."""
    if not csv_path.is_file():
        return [], "telemetry_file_missing"

    try:
        import pandas as pd
        frame = pd.read_csv(csv_path)
    except Exception as exc:
        return [], f"telemetry_read_error:{type(exc).__name__}"

    required = ["timestamp", "dpid", "port", *FEATURE_COLUMNS]
    missing = [col for col in required if col not in frame.columns]
    if missing:
        return [], "missing_columns:" + ",".join(missing)

    frame["timestamp"] = pd.to_datetime(
        frame["timestamp"], errors="coerce", utc=True
    )

    for col in ["dpid", "port", *FEATURE_COLUMNS]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")

    identified = frame.dropna(
        subset=["timestamp", "dpid", "port"]
    ).copy()

    if identified.empty:
        return [], "no_rows_with_valid_stream_identity_and_timestamp"

    current_time = now or datetime.now(timezone.utc)
    candidates = []
    saw_non_finite = False
    saw_gap = False
    saw_insufficient = False
    saw_stale = False
    saw_future = False

    # Examine each stream independently. Never combine different ports.
    for (dpid, port), stream in identified.groupby(
        ["dpid", "port"], sort=False
    ):
        stream = stream.sort_values("timestamp").reset_index(drop=True)

        if len(stream) < sequence_length:
            saw_insufficient = True
            continue

        # Examine windows from newest to oldest. An invalid row or a gap
        # inside a window rejects that window; it is never silently skipped.
        for end in range(len(stream), sequence_length - 1, -1):
            window = stream.iloc[end - sequence_length:end].copy()

            numeric = window[FEATURE_COLUMNS].to_numpy(dtype=np.float64)
            if not np.isfinite(numeric).all():
                saw_non_finite = True
                continue

            timestamps = window["timestamp"].tolist()
            gaps = [
                (timestamps[i] - timestamps[i - 1]).total_seconds()
                for i in range(1, len(timestamps))
            ]

            if any(gap <= 0 or gap > max_gap_seconds for gap in gaps):
                saw_gap = True
                continue

            latest_time = timestamps[-1].to_pydatetime()
            age = (current_time - latest_time).total_seconds()

            if age < -1.0:
                saw_future = True
                continue

            if age > max_age_seconds:
                saw_stale = True
                # Older windows in this same stream will be even staler.
                break

            candidates.append(
                (latest_time, window.to_dict(orient="records"))
            )
            # This is the newest valid window in this stream.
            break

    if candidates:
        # Pick the newest valid window across all streams.
        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1], None

    # Give the most actionable reason available.
    if saw_stale:
        latest_timestamp = identified["timestamp"].max().to_pydatetime()
        age = (current_time - latest_timestamp).total_seconds()
        if age > max_age_seconds:
            return [], f"stale_telemetry_age_seconds:{age:.3f}"

    if saw_future:
        return [], "telemetry_timestamp_in_future"
    if saw_non_finite:
        return [], "non_finite_feature_in_latest_window"
    if saw_gap:
        return [], "telemetry_gap_or_nonmonotonic_timestamp"
    if saw_insufficient:
        return [], f"insufficient_window:less_than_{sequence_length}_rows"

    return [], "no_valid_fresh_window"



class ModelRunner:
    """Loads the repository's TrafficLSTM checkpoint and StandardScaler."""
    def __init__(self, config: dict[str, Any]):
        self.model = None
        self.scaler = None
        self.torch = None
        self.device = None
        if not config.get("use_model", True):
            self.error = "model_disabled_for_smoke_test"
            return
        checkpoint_path = ROOT / str(config["model_checkpoint"])
        scaler_path = ROOT / str(config["scaler_path"])
        if not checkpoint_path.is_file() or not scaler_path.is_file():
            self.error = "model_checkpoint_or_scaler_missing"
            LOG.warning("Cannot load inference: checkpoint=%s scaler=%s", checkpoint_path, scaler_path)
            return
        try:
            import joblib
            import torch
            import sys
            sys.path.insert(0, str(ROOT / "ai-model"))
            from lstm_model import TrafficLSTM
            self.torch = torch
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            checkpoint = torch.load(checkpoint_path, map_location=self.device, weights_only=False)
            model_config = checkpoint.get("model_config", {
                "input_size": 10, "hidden_size": 64, "num_layers": 2,
                "output_size": 10, "dropout": 0.2,
            })
            self.model = TrafficLSTM(
                input_size=model_config["input_size"],
                hidden_size=model_config["hidden_size"],
                num_layers=model_config["num_layers"],
                output_size=model_config["output_size"],
                dropout=model_config.get("dropout", 0.2),
            ).to(self.device)
            self.model.load_state_dict(checkpoint["model_state_dict"])
            self.model.eval()
            self.scaler = joblib.load(scaler_path)
            self.error = None
        except Exception as exc:
            LOG.exception("Model initialization failed")
            self.model = None
            self.scaler = None
            self.error = f"model_initialization_error:{type(exc).__name__}"

    def transform(self, rows: list[dict[str, Any]]) -> np.ndarray:
        matrix = np.asarray([[finite_number(row.get(col)) for col in FEATURE_COLUMNS]
                             for row in rows], dtype=np.float64)
        if matrix.ndim != 2 or matrix.shape[1] != len(FEATURE_COLUMNS) or not np.isfinite(matrix).all():
            raise ValueError("Telemetry feature window contains invalid or non-finite values")
        return self.scaler.transform(matrix)

    def forecast(self, rows: list[dict[str, Any]]) -> tuple[np.ndarray, np.ndarray, float]:
        """Return predicted original-unit vector, predicted scaled vector, latency ms."""
        if self.model is None or self.scaler is None:
            raise RuntimeError(self.error or "model_unavailable")
        scaled = self.transform(rows)
        tensor = self.torch.tensor(scaled, dtype=self.torch.float32, device=self.device).unsqueeze(0)
        started = time.perf_counter()
        with self.torch.no_grad():
            pred_scaled = self.model(tensor).detach().cpu().numpy()[0]
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        if not np.isfinite(pred_scaled).all():
            raise ValueError("model emitted non-finite prediction")
        pred_original = self.scaler.inverse_transform(pred_scaled.reshape(1, -1))[0]
        if not np.isfinite(pred_original).all():
            raise ValueError("inverse-scaled model output is non-finite")
        return pred_original, pred_scaled, elapsed_ms


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    """Write standards-compliant JSON; convert no value to NaN."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, allow_nan=False) + "\n")


def calibrated_utilization(throughput_bps: float, capacity_bps: float) -> float:
    if not math.isfinite(capacity_bps) or capacity_bps <= 0:
        raise ValueError("link capacity must be finite and > 0")
    if not math.isfinite(throughput_bps):
        raise ValueError("predicted throughput must be finite")
    return max(0.0, min(100.0, throughput_bps / capacity_bps * 100.0))


class Runtime:
    def __init__(self, config: dict[str, Any], model: ModelRunner):
        self.config = config
        self.model = model
        self.last_good: dict[str, Any] | None = None
        # Forecast state is per stream and is scored against the next actual sample.
        self.pending_forecasts: dict[tuple[int, int], dict[str, Any]] = {}
        self.last_residual: dict[tuple[int, int], float] = {}

    def run_cycle(self) -> dict[str, Any]:
        started = time.perf_counter()
        now = datetime.now(timezone.utc)
        rows, reason = read_latest_window(
            ROOT / str(self.config["telemetry_csv"]),
            int(self.config["sequence_length"]),
            float(self.config["max_gap_seconds"]),
            float(self.config["max_telemetry_age_seconds"]),
            now=now,
        )
        record: dict[str, Any] = {
            "timestamp": utc_now(), "event_type": "ai_inference", "status": "no_data",
            "reason": reason, "dpid": None, "port": None, "input_timestamp": None,
            "predicted_throughput_bps": None, "predicted_utilization_pct": None,
            "anomaly_residual_mse": None, "anomaly_alert": None,
            "inference_time_ms": None, "used_last_good": False,
        }
        if rows:
            last = rows[-1]
            dpid, port = int(last["dpid"]), int(last["port"])
            key = (dpid, port)
            ts = last["timestamp"]
            record.update({"dpid": dpid, "port": port, "input_timestamp": ts.isoformat() if hasattr(ts, "isoformat") else str(ts), "reason": None})
            try:
                # Score the forecast from the prior cycle once a newer observation arrives.
                pending = self.pending_forecasts.get(key)
                if pending is not None and ts > pending["base_timestamp"]:
                    actual_scaled = self.model.transform([last])[0]
                    residual = float(np.mean((pending["predicted_scaled"] - actual_scaled) ** 2))
                    if math.isfinite(residual):
                        self.last_residual[key] = residual
                        record["anomaly_residual_mse"] = residual
                        record["anomaly_alert"] = residual > float(self.config["anomaly_mse_threshold"])
                    self.pending_forecasts.pop(key, None)
                elif key in self.last_residual:
                    # Repeat the most recent measured residual, clearly tied to this stream.
                    record["anomaly_residual_mse"] = self.last_residual[key]
                    record["anomaly_alert"] = self.last_residual[key] > float(self.config["anomaly_mse_threshold"])

                pred_original, pred_scaled, inference_ms = self.model.forecast(rows)
                forecast_bps = finite_number(pred_original[FEATURE_COLUMNS.index("throughput_bps")])
                if forecast_bps is None:
                    raise ValueError("predicted throughput is non-finite")
                utilization = calibrated_utilization(forecast_bps, float(self.config["link_capacity_bps"]))
                record.update({
                    "status": "ok", "reason": None,
                    "predicted_throughput_bps": forecast_bps,
                    "predicted_utilization_pct": utilization,
                    "inference_time_ms": round(inference_ms, 3),
                })
                self.pending_forecasts[key] = {"base_timestamp": ts, "predicted_scaled": pred_scaled}
                self.last_good = {
                    "predicted_throughput_bps": forecast_bps,
                    "predicted_utilization_pct": utilization,
                    "anomaly_residual_mse": record["anomaly_residual_mse"],
                    "anomaly_alert": record["anomaly_alert"],
                }
            except Exception as exc:
                record["reason"] = str(exc) if isinstance(exc, RuntimeError) else f"inference_error:{type(exc).__name__}:{exc}"
                LOG.warning("Inference cycle failed for dpid=%s port=%s: %s", dpid, port, record["reason"])

        if record["status"] != "ok" and self.last_good is not None:
            record.update(self.last_good)
            record["used_last_good"] = True
        record["cycle_elapsed_ms"] = round((time.perf_counter() - started) * 1000.0, 3)
        # Defensive final check: JSON output must never contain NaN or infinity.
        for field, value in list(record.items()):
            if isinstance(value, (float, np.floating)) and not math.isfinite(float(value)):
                record[field] = None
                record["status"] = "no_data"
                record["reason"] = f"non_finite_output:{field}"
        return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--once", action="store_true", help="execute one cycle and exit")
    parser.add_argument("--interval", type=float, help="override polling interval in seconds")
    parser.add_argument("--duration", type=float, help="stop after N seconds; useful for smoke tests")
    parser.add_argument("--no-model", action="store_true", help="exercise resilience without loading PyTorch")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    config = load_config(args.config)
    if args.interval is not None:
        config["polling_interval_seconds"] = args.interval
    if args.no_model:
        config["use_model"] = False
    interval = float(config["polling_interval_seconds"])
    output_path = ROOT / str(config["output_jsonl"])
    runtime = Runtime(config, ModelRunner(config))
    start = time.monotonic()
    LOG.info("Runtime started: interval=%.2fs output=%s", interval, output_path)

    def request_stop(_signum: int, _frame: Any) -> None:
        global _STOP
        _STOP = True
    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    while not _STOP:
        cycle_start = time.monotonic()
        try:
            record = runtime.run_cycle()
            append_jsonl(output_path, record)
            LOG.info("status=%s reason=%s inference_ms=%s elapsed_ms=%s", record["status"], record.get("reason"), record.get("inference_time_ms"), record["cycle_elapsed_ms"])
        except Exception as exc:  # protect the loop from unexpected cycle-level errors
            LOG.exception("Unexpected cycle error; continuing")
            append_jsonl(output_path, {
                "timestamp": utc_now(), "event_type": "ai_inference", "status": "no_data",
                "reason": f"unexpected_cycle_error:{type(exc).__name__}", "used_last_good": runtime.last_good is not None,
                "cycle_elapsed_ms": round((time.monotonic() - cycle_start) * 1000.0, 3),
            })
        if args.once or (args.duration is not None and time.monotonic() - start >= args.duration):
            break
        time.sleep(max(0.0, interval - (time.monotonic() - cycle_start)))
    LOG.info("Runtime stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
