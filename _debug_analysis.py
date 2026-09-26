"""Temporary debug analysis script (delete after use)."""
import re
from pathlib import Path

import pandas as pd

root = Path(r"c:/Users/zenit/AI-Driven-QoS-Aware-Predictive-Traffic-Engineering")


def show(title, df):
    print("=" * 70)
    print(title)
    print("rows:", len(df), "| cols:", list(df.columns))


tel = pd.read_csv(root / "datasets/raw/telemetry.csv")
show("RAW telemetry.csv", tel)
print("dpid values:", tel.dpid.unique())
print("ports:", sorted(tel.port.unique()))
print("missing per col:")
print(tel.isna().sum().to_string())
print("duplicates:", tel.duplicated().sum())
tel["ts"] = pd.to_datetime(tel.timestamp, utc=True)
print("ts min:", tel.ts.min(), "| ts max:", tel.ts.max())
tel["dt"] = tel.groupby(["dpid", "port"]).ts.diff().dt.total_seconds()
print("interval seconds: min=%.3f max=%.3f median=%.3f" % (tel.dt.min(), tel.dt.max(), tel.dt.median()))
print("count dt==0 (same-ts rows):", (tel.dt == 0).sum())

text = (root / "docs/week3/anomaly-event-timestamps.md").read_text(encoding="utf-8")
starts = re.findall(r"^-\s+anomaly_start:\s*(\S+)\s*$", text, re.M)
ends = re.findall(r"^-\s+anomaly_end:\s*(\S+)\s*$", text, re.M)
print("\nanomaly windows parsed:", len(starts))
wins = pd.DataFrame({"s": pd.to_datetime(starts, utc=True), "e": pd.to_datetime(ends, utc=True)})
print(wins.to_string())
if len(wins):
    mn, mx = tel.ts.min(), tel.ts.max()
    inter = ((wins.s <= mx) & (wins.e >= mn)).sum()
    print("windows overlapping telemetry range:", inter, "of", len(wins))
    for i, w in wins.iterrows():
        cnt = ((tel.ts >= w.s) & (tel.ts <= w.e)).sum()
        print("  win %s -> %s: raw samples inside = %d" % (w.s, w.e, cnt))

q = pd.read_csv(root / "datasets/processed/qos_features.csv")
show("PROCESSED qos_features.csv", q)
q["ts"] = pd.to_datetime(q.timestamp, utc=True)
print("ts min:", q.ts.min(), "| ts max:", q.ts.max())
print("is_anomalous counts:")
print(q.is_anomalous.value_counts().to_string())
num = [
    "rx_packets_delta", "tx_packets_delta", "rx_bytes_delta", "tx_bytes_delta",
    "rx_dropped_delta", "tx_dropped_delta", "rx_errors_delta", "tx_errors_delta",
    "throughput_bps", "packet_rate_pps",
]
print("negative values:")
for c in num:
    n = (pd.to_numeric(q[c], errors="coerce") < 0).sum()
    if n:
        print("  ", c, n)
print("NA counts:")
print(q.isna().sum().to_string())
print("ports present:", sorted(q.port.unique()))

for f in ["clean_dataset.csv", "train_raw.csv", "val_raw.csv", "train_scaled.csv", "val_scaled.csv"]:
    p = root / "datasets/processed" / f
    if p.exists():
        d = pd.read_csv(p)
        print("%s: rows=%d cols=%d" % (f, len(d), len(d.columns)))

sc = pd.read_pickle(root / "datasets/processed/scaler.pkl")
print("scaler mean len:", len(sc.mean_), "| scale sample:", sc.scale_[:3])

baseline = root / "datasets/raw/baseline_ping_20260808.csv"
if baseline.exists():
    b = pd.read_csv(baseline)
    print("baseline ping rows:", len(b), "| cols:", list(b.columns))
    print(b.head(5).to_string())