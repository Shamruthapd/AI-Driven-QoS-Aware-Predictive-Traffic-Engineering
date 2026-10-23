#!/usr/bin/env python3
"""Week 8 QoS policy engine. Safe by default: dry-run only."""

import argparse
import csv
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "ai-model/integration_predictions.csv"
DEFAULT_LOG = ROOT / "docs/week8/policy-decisions-log.md"

THRESHOLD_MBPS = 10.0
CONSECUTIVE_READINGS = 2
DEFAULT_MAX_AGE_SECONDS = 30.0

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--threshold", type=float, default=THRESHOLD_MBPS)
    parser.add_argument("--consecutive", type=int, default=CONSECUTIVE_READINGS)
    parser.add_argument("--max-age", type=float, default=DEFAULT_MAX_AGE_SECONDS)
    parser.add_argument(
        "--timestamp-mode",
        choices=("historical", "live"),
        default="historical",
        help="Historical CSV data is not rejected as stale; live mode enforces freshness.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Log intended actions only; this engine does not modify the network.",
    )
    return parser.parse_args()


def valid_number(value):
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def append_log(path, rows, threshold, consecutive, mode):
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists()

    with path.open("a", encoding="utf-8") as f:
        if new_file:
            f.write("# Week 8: QoS Policy Decisions Log\n\n")
            f.write(
                "Dry-run decision log. Entries describe intended actions; "
                "they do not prove controller enforcement occurred.\n\n"
            )

        f.write(f"\n## Run — {datetime.now(timezone.utc).isoformat()}\n\n")
        f.write(
            f"- Mode: **{mode}**\n"
            f"- Congestion threshold: **{threshold:.2f} Mbps**\n"
            f"- Consecutive readings required: **{consecutive}**\n\n"
        )
        f.write(
            "| Timestamp | DPID | Port | Throughput (Mbps) | "
            "Consecutive highs | Decision | Intended action |\n"
        )
        f.write(
            "|---|---:|---:|---:|---:|---|---|\n"
        )
        for row in rows:
            def safe(value):
                return str(value).replace("|", "\\|").replace("\n", " ")

            f.write(
                f"| {safe(row['timestamp'])} "
                f"| {safe(row['dpid'])} "
                f"| {safe(row['port'])} "
                f"| {safe(row['throughput'])} "
                f"| {safe(row['high_count'])} "
                f"| {safe(row['decision'])} "
                f"| {safe(row['action'])} |\n"
            )


def main():
    args = parse_args()

    if args.threshold <= 0 or args.consecutive < 1 or args.max_age <= 0:
        raise SystemExit("Threshold, consecutive count, and max age must be positive.")

    if not args.input.is_file():
        raise SystemExit(f"Input CSV not found: {args.input}")

    df = pd.read_csv(args.input)

    # Support both telemetry and Member 4 prediction-feed column names.
    if "port_no" not in df.columns and "port" in df.columns:
        df["port_no"] = df["port"]

    if "tx_throughput_mbps" not in df.columns:
        if "predicted_throughput_bps" in df.columns:
            df["tx_throughput_mbps"] = (
                pd.to_numeric(df["predicted_throughput_bps"], errors="coerce")
                / 1_000_000
            )
        elif "predicted_throughput_mbps" in df.columns:
            df["tx_throughput_mbps"] = pd.to_numeric(
                df["predicted_throughput_mbps"], errors="coerce"
            )

    required = {"timestamp", "dpid", "port_no", "tx_throughput_mbps"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Input CSV is missing required columns: {sorted(missing)}")

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    df = df.sort_values(["dpid", "port_no", "timestamp"], na_position="last")

    high_counts = {}
    active = set()
    decisions = []

    for _, row in df.iterrows():
        dpid = row["dpid"]
        port = row["port_no"]
        key = (dpid, port)
        timestamp = row["timestamp"]
        throughput = valid_number(row["tx_throughput_mbps"])
        anomaly_raw = row.get("predicted_anomaly", pd.NA)
        anomaly_value = valid_number(anomaly_raw)
        anomaly_note = (
            f"Predicted anomaly={int(anomaly_value)} (logged separately)"
            if anomaly_value is not None
            else "Predicted anomaly unavailable"
        )

        ts_text = timestamp.isoformat() if pd.notna(timestamp) else "INVALID_TIMESTAMP"

        if pd.isna(timestamp) or throughput is None:
            high_counts[key] = 0
            decisions.append({
                "timestamp": ts_text, "dpid": dpid, "port": port,
                "throughput": "INVALID", "high_count": 0,
                "decision": "SKIP_INVALID_DATA", "action": "No action",
            })
            continue

        if args.timestamp_mode == "live":
            age = (datetime.now(timezone.utc) - timestamp.to_pydatetime()).total_seconds()
            if age < -5 or age > args.max_age:
                high_counts[key] = 0
                decisions.append({
                    "timestamp": ts_text, "dpid": dpid, "port": port,
                    "throughput": f"{throughput:.4f}", "high_count": 0,
                    "decision": "SKIP_STALE_OR_FUTURE_DATA", "action": "No action",
                })
                continue

        if throughput > args.threshold:
            high_counts[key] = high_counts.get(key, 0) + 1
        else:
            high_counts[key] = 0

        if high_counts[key] >= args.consecutive and key not in active:
            active.add(key)
            decision = "CONGESTION_CONFIRMED"
            action = (
                "Intend to preserve priority UDP on Queue 1 and constrain "
                "bulk TCP on Queue 0; controller hook not connected"
            )
        elif high_counts[key] >= args.consecutive:
            decision = "CONGESTION_CONTINUES_NO_REPEAT"
            action = "No repeated action"
        else:
            if key in active and throughput <= args.threshold:
                active.remove(key)
                decision = "CONGESTION_CLEARED"
                action = "No live change; recovery action not connected"
            else:
                decision = "WAITING_FOR_CONFIRMATION"
                action = "No action"

        decisions.append({
            "timestamp": ts_text, "dpid": dpid, "port": port,
            "throughput": f"{throughput:.4f}",
            "high_count": high_counts[key],
            "decision": decision, "action": f"{action}; {anomaly_note}",
        })

    append_log(
        args.log, decisions, args.threshold, args.consecutive,
        "DRY RUN (no network changes)",
    )

    print(f"Input rows processed: {len(df)}")
    print(f"Decision rows logged: {len(decisions)}")
    print(f"Threshold: {args.threshold:.2f} Mbps")
    print(f"Consecutive readings required: {args.consecutive}")
    print("Mode: DRY RUN — no network changes were made")
    print(f"Decision log: {args.log}")
    print("\nDecision counts:")
    print(pd.Series([r["decision"] for r in decisions]).value_counts().to_string())


if __name__ == "__main__":
    main()
