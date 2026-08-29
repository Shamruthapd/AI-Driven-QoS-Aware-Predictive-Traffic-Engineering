import re

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

ANOMALY_EVENT_FILE = (
    PROJECT_ROOT / "docs" / "week3" / "anomaly-event-timestamps.md"
)


def load_anomaly_windows(path=ANOMALY_EVENT_FILE):
    """
    Load (anomaly_start, anomaly_end) windows logged by Member 3's
    Scapy bursty-IoT generator (traffic/scapy_iot_traffic.py).

    The generator appends blocks of three `key: value` lines:

        - event_id: anomaly-20260809_142301
        - anomaly_start: 2026-08-09T14:23:01.000000+00:00
        - anomaly_end:   2026-08-09T14:23:11.000000+00:00

    Only entries under the "## Recorded Events" section are parsed so
    that the format examples in the document header are ignored.
    """
    if not path.exists():
        return pd.DataFrame(columns=["anomaly_start", "anomaly_end"])

    text = path.read_text(encoding="utf-8")

    marker = "## Recorded Events"
    if marker in text:
        text = text.split(marker, 1)[1]

    starts = re.findall(
        r"^-\s+anomaly_start:\s*(\S+)\s*$",
        text,
        flags=re.MULTILINE,
    )
    ends = re.findall(
        r"^-\s+anomaly_end:\s*(\S+)\s*$",
        text,
        flags=re.MULTILINE,
    )

    if not starts or not ends:
        return pd.DataFrame(columns=["anomaly_start", "anomaly_end"])

    count = min(len(starts), len(ends))
    windows = pd.DataFrame(
        {
            "anomaly_start": pd.to_datetime(starts[:count], utc=True),
            "anomaly_end": pd.to_datetime(ends[:count], utc=True),
        }
    ).dropna()

    return windows


def label_anomalous_samples(timestamps, windows):
    """
    Binary flag per telemetry sample: 1 if the sample timestamp falls
    inside (inclusive of both bounds) any Member 3 anomaly window,
    otherwise 0.
    """
    flag = pd.Series(False, index=timestamps.index)

    for _, window in windows.iterrows():
        in_window = (timestamps >= window["anomaly_start"]) & (
            timestamps <= window["anomaly_end"]
        )
        flag |= in_window

    return flag.astype("int64")


def main():
    df = pd.read_csv(RAW_FILE)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

    # Label every raw sample with the binary anomaly flag derived from
    # Member 3's Scapy IoT generator anomaly-event log.
    anomaly_windows = load_anomaly_windows()
    df["is_anomalous"] = label_anomalous_samples(
        df["timestamp"],
        anomaly_windows,
    )

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
        "is_anomalous",
    ]

    result = df[output_columns].copy()

    result.to_csv(OUTPUT_FILE, index=False)

    anomalous_rows = int(result["is_anomalous"].sum())

    print(f"Anomaly windows parsed: {len(anomaly_windows)}")
    print(f"Anomalous rows labelled: {anomalous_rows}")
    print(f"Processed rows: {len(result)}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
