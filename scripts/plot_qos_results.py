import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "datasets" / "processed" / "qos_features.csv"
OUTPUT = ROOT / "results" / "week4" / "throughput_over_time.png"

df = pd.read_csv(INPUT)
df = df.dropna(subset=["throughput_bps"]).copy()

df["timestamp"] = pd.to_datetime(df["timestamp"])
df["throughput_mbps"] = df["throughput_bps"] / 1_000_000

plt.figure(figsize=(10, 5))

for port, group in df.groupby("port"):
    plt.plot(
        group["timestamp"],
        group["throughput_mbps"],
        label=f"Port {port}"
    )

plt.xlabel("Time")
plt.ylabel("Throughput (Mbps)")
plt.title("Measured Throughput Over Time")
plt.legend()
plt.xticks(rotation=30)
plt.tight_layout()

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
plt.savefig(OUTPUT, dpi=200)
plt.close()

print(f"Graph saved: {OUTPUT}")
