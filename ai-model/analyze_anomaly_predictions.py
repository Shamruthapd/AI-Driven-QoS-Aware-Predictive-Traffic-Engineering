#!/usr/bin/env python3
"""Summarize Member 4 anomaly predictions without triggering QoS actions."""

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "ai-model/integration_predictions.csv"
DEFAULT_OUTPUT = ROOT / "docs/week8/anomaly-prediction-summary.md"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if not args.input.is_file():
        raise SystemExit(f"Prediction CSV not found: {args.input}")

    df = pd.read_csv(args.input)
    required = {
        "timestamp", "dpid", "port",
        "predicted_anomaly", "mse", "mse_threshold"
    }
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Prediction CSV missing columns: {sorted(missing)}")

    df["timestamp"] = pd.to_datetime(
        df["timestamp"], utc=True, errors="coerce"
    )
    for column in ("predicted_anomaly", "mse", "mse_threshold"):
        df[column] = pd.to_numeric(df[column], errors="coerce")

    valid = df.dropna(
        subset=["timestamp", "dpid", "port",
                "predicted_anomaly", "mse", "mse_threshold"]
    ).copy()

    invalid_count = len(df) - len(valid)
    valid["predicted_anomaly"] = valid["predicted_anomaly"].astype(int)
    anomaly_count = int((valid["predicted_anomaly"] == 1).sum())
    normal_count = int((valid["predicted_anomaly"] == 0).sum())

    lines = [
        "# Week 8: Member 4 Anomaly Prediction Summary",
        "",
        "> Historical anomaly results only. This report does not trigger QoS actions.",
        "> The prediction timestamps do not match the September telemetry file,",
        "> so these results are not joined to throughput decisions.",
        "",
        "## Summary",
        "",
        f"- Input: `{args.input.relative_to(ROOT) if args.input.is_relative_to(ROOT) else args.input}`",
        f"- Total rows: {len(df)}",
        f"- Valid rows: {len(valid)}",
        f"- Invalid rows skipped: {invalid_count}",
        f"- Predicted anomalies: {anomaly_count}",
        f"- Predicted normal rows: {normal_count}",
        "",
        "## Results by switch and port",
        "",
        "| DPID | Port | Valid rows | Predicted anomalies |",
        "|---:|---:|---:|---:|",
    ]

    if not valid.empty:
        grouped = valid.groupby(["dpid", "port"])["predicted_anomaly"]
        for (dpid, port), values in grouped:
            lines.append(
                f"| {dpid} | {port} | {len(values)} | "
                f"{int((values == 1).sum())} |"
            )
    else:
        lines.append("| — | — | 0 | 0 |")

    lines.extend([
        "",
        "## Safety note",
        "",
        "An anomaly flag is supporting evidence only. Congestion decisions "
        "remain based on valid throughput readings and the configured "
        "consecutive-reading rule. No controller or switch changes were made.",
        "",
    ])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Prediction rows: {len(df)}")
    print(f"Valid rows: {len(valid)}")
    print(f"Predicted anomalies: {anomaly_count}")
    print(f"Predicted normal rows: {normal_count}")
    print(f"Invalid rows skipped: {invalid_count}")
    print(f"Report written to: {args.output}")


if __name__ == "__main__":
    main()
