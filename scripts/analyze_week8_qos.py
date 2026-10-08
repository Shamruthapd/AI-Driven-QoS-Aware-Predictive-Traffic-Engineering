import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "data" / "results" / "week8_qos_on_vs_off_measurements.csv"
OUTPUT = ROOT / "data" / "results" / "week8_qos_analysis.csv"

df = pd.read_csv(INPUT)

# Separate QoS OFF and ON measurements
off = df[df["qos_state"] == "OFF"].copy()
on = df[df["qos_state"] == "ON"].copy()

results = []

for flow in df["flow_type"].unique():
    off_row = off[off["flow_type"] == flow].iloc[0]
    on_row = on[on["flow_type"] == flow].iloc[0]

    throughput_change_pct = (
        (on_row["throughput_mbps"] - off_row["throughput_mbps"])
        / off_row["throughput_mbps"]
    ) * 100

    jitter_change_ms = on_row["jitter_ms"] - off_row["jitter_ms"]
    loss_change_pct = on_row["packet_loss_pct"] - off_row["packet_loss_pct"]

    results.append({
        "flow_type": flow,
        "off_throughput_mbps": off_row["throughput_mbps"],
        "on_throughput_mbps": on_row["throughput_mbps"],
        "throughput_change_pct": round(throughput_change_pct, 2),
        "off_jitter_ms": off_row["jitter_ms"],
        "on_jitter_ms": on_row["jitter_ms"],
        "jitter_change_ms": round(jitter_change_ms, 3),
        "off_packet_loss_pct": off_row["packet_loss_pct"],
        "on_packet_loss_pct": on_row["packet_loss_pct"],
        "loss_change_pct": round(loss_change_pct, 2)
    })

analysis = pd.DataFrame(results)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
analysis.to_csv(OUTPUT, index=False)

print("\n=== Week 8 QoS ON vs OFF Analysis ===")
print(analysis.to_string(index=False))
print(f"\nAnalysis saved to: {OUTPUT}")