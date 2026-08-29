import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_FILE = PROJECT_ROOT / "datasets" / "raw" / "telemetry.csv"
OUTPUT_FILE = PROJECT_ROOT / "datasets" / "processed" / "qos_features.csv"

COUNTERS = [
    "rx_packets",
    "tx_packets",
    "rx_bytes",
    "tx_bytes",
    "rx_dropped",
    "tx_dropped",
    "rx_errors",
    "tx_errors",
]


def main():
    df = pd.read_csv(RAW_FILE)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

    # Exclude the OpenFlow LOCAL port from link-level QoS processing.
    df = df[df["port"] != 4294967294].copy()

    df = df.sort_values(
        ["dpid", "port", "timestamp"]
    ).reset_index(drop=True)

    grouped = df.groupby(["dpid", "port"], group_keys=False)

    # Calculate counter deltas.
    for column in COUNTERS:
        previous = grouped[column].shift(1)
        delta = df[column] - previous

        # Counter reset: use the current counter value.
        df[f"{column}_delta"] = delta.where(
            (delta >= 0) | previous.isna(),
            df[column]
        )

    # Time difference in seconds.
    df["interval_seconds"] = (
        grouped["timestamp"]
        .diff()
        .dt.total_seconds()
    )

    # Throughput based on transmitted bytes.
    df["throughput_bps"] = (
        df["tx_bytes_delta"] * 8
        / df["interval_seconds"]
    )

    # Packet rate based on transmitted packets.
    df["packet_rate_pps"] = (
        df["tx_packets_delta"]
        / df["interval_seconds"]
    )

    # Packet drops observed during each interval.
    df["rx_dropped_delta"] = df["rx_dropped_delta"].clip(lower=0)
    df["tx_dropped_delta"] = df["tx_dropped_delta"].clip(lower=0)

    # Keep only meaningful processed features.
    output_columns = [
        "timestamp",
        "dpid",
        "port",
        "interval_seconds",
        "rx_packets_delta",
        "tx_packets_delta",
        "rx_bytes_delta",
        "tx_bytes_delta",
        "rx_dropped_delta",
        "tx_dropped_delta",
        "rx_errors_delta",
        "tx_errors_delta",
        "throughput_bps",
        "packet_rate_pps",
    ]

    result = df[output_columns].copy()

    result.to_csv(OUTPUT_FILE, index=False)

    print(f"Processed rows: {len(result)}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
