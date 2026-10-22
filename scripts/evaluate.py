#!/usr/bin/env python3
"""Member 4 evaluation harness for iPerf3 JSON, ping logs, timelines and Week 8 CSV.

Examples (from repository root):
  python scripts/evaluate.py --input-dir data/results/week11_raw
  python scripts/evaluate.py --files logs/h2_bulk_off.json logs/h3_priority_on.json
  python scripts/evaluate.py --week8-summary data/results/week8_qos_on_vs_off_measurements.csv

Raw files are not modified. Missing metrics remain blank, not fabricated zeroes.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "data" / "results" / "week11_raw"
DEFAULT_OUTPUT = ROOT / "data" / "results" / "week9_harness"


def finite(value: Any) -> float | None:
    try:
        n = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return n if pd.notna(n) else None


def infer_tags(path: Path) -> dict[str, str]:
    text = path.as_posix().lower()
    modes = [
        ("baseline_shortest_path", "baseline_shortest_path"),
        ("static_shortest_path", "baseline_shortest_path"),
        ("full_ai_qos_ff", "full_ai_qos_ff"),
        ("ai_qos_ff", "full_ai_qos_ff"),
        ("full_system_ai_driven", "full_ai_qos_ff"),
        ("full_system_baseline", "baseline_shortest_path"),
        ("reactive", "reactive"),
    ]
    mode = next((value for token, value in modes if token in text), "unknown")
    scenario = next((s.upper() for s in ("s1", "s2", "s3") if re.search(rf"(^|[/_-]){s}([/_.-]|$)", text)), "unknown")
    trial_match = re.search(r"trial[_-]?(\d+)", path.stem.lower())
    trial_id = trial_match.group(0).replace("-", "_") if trial_match else path.stem
    flow = "unknown"
    if any(token in text for token in ("priority", "udp", "video")):
        flow = "priority_udp"
    elif any(token in text for token in ("bulk", "tcp", "data")):
        flow = "bulk_tcp"
    return {"mode": mode, "scenario": scenario, "trial_id": trial_id, "flow_type": flow}


def parse_iperf(path: Path, data: dict[str, Any]) -> dict[str, float | None]:
    end = data.get("end", {}) if isinstance(data, dict) else {}
    summary = end.get("sum_received") or end.get("sum") or {}
    if not summary and end.get("streams"):
        stream_summaries = []
        for item in end["streams"]:
            stream_summaries.append(item.get("udp", {}) or item.get("receiver", {}) or item.get("sender", {}))
        summary = next((item for item in stream_summaries if item), {})
    # Some iperf3 captures use server_output_text rather than native JSON fields.
    if not summary and isinstance(data, dict):
        text = data.get("server_output_text", "")
        receiver_lines = [line for line in text.splitlines() if "receiver" in line and "Mbits/sec" in line]
        if receiver_lines:
            match = re.search(r"([0-9.]+)\s+Mbits/sec\s+([0-9.]+)\s+ms\s+(\d+)/(\d+)\s+\(([0-9.]+)%\).*receiver", receiver_lines[-1])
            if match:
                return {
                    "throughput_mbps": float(match.group(1)), "jitter_ms": float(match.group(2)),
                    "packet_loss_pct": float(match.group(5)), "duration_seconds": None,
                }
    bps = finite(summary.get("bits_per_second")) if isinstance(summary, dict) else None
    seconds = finite(summary.get("seconds")) if isinstance(summary, dict) else None
    jitter = finite(summary.get("jitter_ms")) if isinstance(summary, dict) else None
    lost = finite(summary.get("lost_packets")) if isinstance(summary, dict) else None
    packets = finite(summary.get("packets")) if isinstance(summary, dict) else None
    loss = finite(summary.get(" lost_percent", summary.get("lost_percent"))) if isinstance(summary, dict) else None
    if loss is None and lost is not None and packets and packets > 0:
        loss = 100.0 * lost / packets
    return {
        "throughput_mbps": bps / 1e6 if bps is not None else None,
        "jitter_ms": jitter,
        "packet_loss_pct": loss,
        "duration_seconds": seconds,
    }


def parse_ping(path: Path) -> dict[str, float | None]:
    text = path.read_text(encoding="utf-8", errors="replace")
    rtts = [float(v) for v in re.findall(r"time[=<]([0-9.]+)\s*ms", text)]
    result: dict[str, float | None] = {}
    if rtts:
        result["latency_ms_mean"] = statistics.mean(rtts)
        result["latency_ms_p95"] = float(pd.Series(rtts).quantile(0.95))
        # Standard deviation of successive RTT differences is a simple jitter estimate;
        # keep it labelled as estimated, not equivalent to iperf3 UDP jitter.
        diffs = [abs(rtts[i] - rtts[i - 1]) for i in range(1, len(rtts))]
        result["ping_rtt_variation_ms"] = statistics.mean(diffs) if diffs else None
        result["ping_samples"] = float(len(rtts))
    sent = re.search(r"(\d+)\s+packets transmitted", text)
    received = re.search(r"(\d+)\s+(?:packets )?received", text)
    loss = re.search(r"([0-9.]+)%\s*packet loss", text)
    if loss:
        result["packet_loss_pct"] = float(loss.group(1))
    elif sent and received and int(sent.group(1)) > 0:
        result["packet_loss_pct"] = 100.0 * (int(sent.group(1)) - int(received.group(1))) / int(sent.group(1))
    return result


def parse_timeline(path: Path) -> dict[str, float | None]:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        frame = pd.DataFrame(records)
    elif suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        frame = pd.DataFrame(payload if isinstance(payload, list) else payload.get("events", []))
    else:
        frame = pd.read_csv(path)
    if frame.empty:
        return {}
    metrics: dict[str, float | None] = {}
    # Accept direct measured metric columns when a trial manifest already contains them.
    aliases = {
        "latency_ms": "latency_ms_mean", "mean_latency_ms": "latency_ms_mean",
        "latency_ms_mean": "latency_ms_mean", "latency_ms_p95": "latency_ms_p95",
        "jitter_ms": "jitter_ms", "throughput_mbps": "throughput_mbps",
        "packet_loss_pct": "packet_loss_pct", "recovery_time_ms": "recovery_time_ms",
        "e2e_delay_ms": "e2e_delay_ms", "end_to_end_delay_ms": "e2e_delay_ms",
        "telemetry_to_enforcement_ms": "telemetry_to_enforcement_ms",
    }
    for source, target in aliases.items():
        if source in frame.columns:
            values = pd.to_numeric(frame[source], errors="coerce").dropna()
            if not values.empty:
                metrics[target] = float(values.mean())
    if "event_type" in frame.columns:
        types = frame["event_type"].astype(str).str.lower()
        metrics["event_count"] = float(len(frame))
        for event_name in ("telemetry", "prediction", "decision", "enforcement", "port_down", "ff_used"):
            metrics[f"events_{event_name}"] = float(types.str.contains(event_name, regex=False).sum())
        # Only compute a delay if explicit event rows and a shared request/trial key make pairing possible.
        ts_col = next((c for c in ("timestamp", "event_timestamp", "time") if c in frame.columns), None)
        key_col = next((c for c in ("event_id", "request_id", "correlation_id") if c in frame.columns), None)
        if ts_col and key_col:
            frame["_ts"] = pd.to_datetime(frame[ts_col], errors="coerce", utc=True)
            delays = []
            for _, grp in frame.dropna(subset=[key_col, "_ts"]).groupby(key_col):
                low = grp[types.loc[grp.index].str.contains("telemetry|prediction", regex=True, na=False)]["_ts"]
                high = grp[types.loc[grp.index].str.contains("enforcement", regex=False, na=False)]["_ts"]
                if not low.empty and not high.empty:
                    delta = (high.min() - low.min()).total_seconds() * 1000
                    if delta >= 0:
                        delays.append(delta)
            if delays:
                metrics["telemetry_to_enforcement_ms"] = statistics.mean(delays)
    return metrics


def parse_one(path: Path) -> dict[str, Any]:
    tags = infer_tags(path)
    row: dict[str, Any] = {"source_file": str(path), **tags, "valid": True, "invalid_reason": ""}
    try:
        suffix = path.suffix.lower()
        if suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            metrics = parse_iperf(path, payload)
            if not any(value is not None for value in metrics.values()):
                metrics = parse_timeline(path)
        elif suffix in {".log", ".txt"} and "ping" in path.name.lower():
            metrics = parse_ping(path)
        elif suffix in {".csv", ".jsonl"}:
            metrics = parse_timeline(path)
        else:
            metrics = {}
        metrics = {key: value for key, value in metrics.items() if value is not None}
        if not metrics:
            row.update({"valid": False, "invalid_reason": "no supported metrics parsed"})
        row.update(metrics)
    except Exception as exc:
        row.update({"valid": False, "invalid_reason": f"{type(exc).__name__}: {exc}"})
    return row


def grouped_summary(df: pd.DataFrame) -> pd.DataFrame:
    metric_names = [
        "latency_ms_mean", "latency_ms_p95", "jitter_ms", "ping_rtt_variation_ms",
        "throughput_mbps", "packet_loss_pct", "recovery_time_ms", "e2e_delay_ms",
        "telemetry_to_enforcement_ms",
    ]
    valid = df[df["valid"] == True].copy()  # noqa: E712
    group_cols = ["mode", "scenario", "flow_type"]
    output = []
    for keys, group in valid.groupby(group_cols, dropna=False):
        for metric in metric_names:
            if metric not in group.columns:
                continue
            vals = pd.to_numeric(group[metric], errors="coerce").dropna().astype(float).tolist()
            if not vals:
                continue
            output.append({
                "mode": keys[0], "scenario": keys[1], "flow_type": keys[2],
                "metric": metric, "n": len(vals), "mean": statistics.mean(vals),
                "stddev": statistics.stdev(vals) if len(vals) > 1 else 0.0,
                "min": min(vals), "max": max(vals), "p95": float(pd.Series(vals).quantile(0.95)),
            })
    return pd.DataFrame(output, columns=["mode", "scenario", "flow_type", "metric", "n", "mean", "stddev", "min", "max", "p95"])


def reproduce_week8(path: Path, output_dir: Path) -> Path:
    """Regenerate the existing Week 8 QoS ON/OFF comparison from the committed CSV summary."""
    data = pd.read_csv(path)
    required = {"qos_state", "flow_type", "throughput_mbps", "jitter_ms", "packet_loss_pct"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"Week 8 summary missing columns: {sorted(missing)}")
    data["qos_state"] = data["qos_state"].astype(str).str.upper()
    rows = []
    for flow in data["flow_type"].dropna().unique():
        off_rows = data[(data["flow_type"] == flow) & (data["qos_state"] == "OFF")]
        on_rows = data[(data["flow_type"] == flow) & (data["qos_state"] == "ON")]
        if off_rows.empty or on_rows.empty:
            rows.append({"flow_type": flow, "evidence_status": "incomplete", "note": "Requires both OFF and ON observations"})
            continue
        off = off_rows.iloc[0]
        on = on_rows.iloc[0]
        off_t, on_t = finite(off["throughput_mbps"]), finite(on["throughput_mbps"])
        off_j, on_j = finite(off["jitter_ms"]), finite(on["jitter_ms"])
        off_l, on_l = finite(off["packet_loss_pct"]), finite(on["packet_loss_pct"])
        rows.append({
            "flow_type": flow, "off_throughput_mbps": off_t, "on_throughput_mbps": on_t,
            "throughput_change_pct": ((on_t - off_t) / off_t * 100.0) if off_t not in (None, 0) and on_t is not None else None,
            "off_jitter_ms": off_j, "on_jitter_ms": on_j,
            "jitter_change_ms": on_j - off_j if on_j is not None and off_j is not None else None,
            "off_packet_loss_pct": off_l, "on_packet_loss_pct": on_l,
            "loss_change_pct_points": on_l - off_l if on_l is not None and off_l is not None else None,
            "evidence_status": "recomputed_from_summary_csv",
            "note": "Derived from the committed summary CSV, not original iperf3 JSON. Not a raw-file reproduction.",
        })
    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / "week8_reproduced_comparison.csv"
    result = pd.DataFrame(rows)
    result.to_csv(out, index=False)
    chart_dir = output_dir / "figures"
    chart_dir.mkdir(parents=True, exist_ok=True)
    chart_rows = result.dropna(subset=["off_throughput_mbps", "on_throughput_mbps"]) if not result.empty else result
    if not chart_rows.empty:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        ax = chart_rows.set_index("flow_type")[["off_throughput_mbps", "on_throughput_mbps"]].plot(kind="bar")
        ax.set_title("Week 8 QoS ON/OFF throughput comparison")
        ax.set_xlabel("Flow type")
        ax.set_ylabel("Receiver throughput (Mbps)")
        ax.legend(["QoS OFF", "QoS ON"])
        plt.tight_layout()
        figure_path = chart_dir / "week8_throughput_comparison.png"
        plt.savefig(figure_path, dpi=160)
        plt.close()
        print(f"Week 8 chart written: {figure_path}")
    print(f"Week 8 comparison written: {out}")
    print("Note: this recomputes from the committed summary CSV; the raw JSON logs were not found in the repository tree.")
    return out



def create_charts(summary: pd.DataFrame, output_dir: Path) -> list[Path]:
    """Create bar charts for available grouped metrics with error bars when spread exists."""
    if summary.empty:
        return []
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    figures = output_dir / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for metric in summary["metric"].dropna().unique():
        part = summary[summary["metric"] == metric].copy()
        part = part[part["mean"].notna()]
        if part.empty:
            continue
        labels = [f"{row.mode}\n{row.scenario}\n{row.flow_type}" for row in part.itertuples()]
        means = pd.to_numeric(part["mean"], errors="coerce").to_numpy()
        stddev = pd.to_numeric(part["stddev"], errors="coerce").fillna(0).to_numpy()
        fig, ax = plt.subplots(figsize=(max(7, len(labels) * 1.1), 4.5))
        ax.bar(range(len(labels)), means, yerr=stddev, capsize=3)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=0, fontsize=8)
        ax.set_title(f"{metric.replace('_', ' ').title()} by mode and scenario")
        ax.set_ylabel(metric.replace("_", " "))
        ax.grid(axis="y", alpha=0.25)
        fig.tight_layout()
        safe_name = re.sub(r"[^a-z0-9_-]+", "_", str(metric).lower())
        out = figures / f"{safe_name}_by_mode_scenario.png"
        fig.savefig(out, dpi=160)
        plt.close(fig)
        written.append(out)
    return written

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--files", nargs="*", type=Path, help="explicit files to parse")
    parser.add_argument("--week8-summary", type=Path, help="rebuild Week 8 comparison from its committed CSV summary")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.week8_summary:
        reproduce_week8(args.week8_summary, args.output_dir)
        return 0
    files = args.files if args.files else (sorted(args.input_dir.rglob("*")) if args.input_dir.exists() else [])
    files = [path for path in files if path.is_file() and path.suffix.lower() in {".json", ".jsonl", ".csv", ".log", ".txt"}]
    if not files:
        parser.error(f"No supported measurement files found. Provide --files, --week8-summary, or populate {args.input_dir}.")
    df = pd.DataFrame([parse_one(path) for path in files])
    raw_path = args.output_dir / "parsed_measurements.csv"
    summary_path = args.output_dir / "summary_tables.csv"
    df.to_csv(raw_path, index=False)
    summary = grouped_summary(df)
    summary.to_csv(summary_path, index=False)
    charts = create_charts(summary, args.output_dir)
    print(f"Files parsed: {len(files)} | valid: {int((df['valid'] == True).sum())} | invalid: {int((df['valid'] == False).sum())}")  # noqa: E712
    print(f"Per-file metrics: {raw_path}")
    print(f"Grouped statistics: {summary_path}")
    print(f"Charts created: {len(charts)}")
    for chart in charts:
        print(f"  - {chart}")
    if (df["valid"] == False).any():  # noqa: E712
        print("WARNING: inspect invalid_reason in parsed_measurements.csv; raw inputs were not changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
