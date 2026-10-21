
import re

import pandas as pd
from pathlib import Path


# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "raw"
    / "telemetry.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT
    / "datasets"
    / "processed"
    / "qos_features.csv"
)


# Maximum interval allowed for rate calculations.
# Longer intervals are treated as discontinuities.
MAX_INTERVAL_SECONDS = 10.0


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
    PROJECT_ROOT
    / "docs"
    / "week3"
    / "anomaly-event-timestamps.md"
)


def load_anomaly_windows(path=ANOMALY_EVENT_FILE):
    """Load anomaly start/end windows from the anomaly event log."""

    if not path.exists():
        return pd.DataFrame(
            columns=["anomaly_start", "anomaly_end"]
        )

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
        return pd.DataFrame(
            columns=["anomaly_start", "anomaly_end"]
        )

    count = min(len(starts), len(ends))

    windows = pd.DataFrame({
        "anomaly_start": pd.to_datetime(
            starts[:count],
            utc=True,
            errors="coerce",
        ),
        "anomaly_end": pd.to_datetime(
            ends[:count],
            utc=True,
            errors="coerce",
        ),
    }).dropna()

    return windows


def label_anomalous_samples(timestamps, windows):
    """Mark samples that fall inside a recorded anomaly window."""

    flag = pd.Series(False, index=timestamps.index)

    for _, window in windows.iterrows():
        in_window = (
            (timestamps >= window["anomaly_start"])
            & (timestamps <= window["anomaly_end"])
        )

        flag |= in_window

    return flag.astype("int64")


def main():

    # --------------------------------------------------------
    # 1. Load and validate raw telemetry
    # --------------------------------------------------------

    df = pd.read_csv(RAW_FILE)

    print(f"Raw rows loaded: {len(df)}")

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        utc=True,
        errors="coerce",
    )

    required_raw_columns = [
        "timestamp",
        "dpid",
        "port",
        *COUNTERS,
    ]

    for column in ["dpid", "port", *COUNTERS]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    before = len(df)

    df = df.dropna(
        subset=required_raw_columns
    ).copy()

    print(f"Malformed raw rows removed: {before - len(df)}")

    # Label anomalies using recorded event windows.
    anomaly_windows = load_anomaly_windows()

    df["is_anomalous"] = label_anomalous_samples(
        df["timestamp"],
        anomaly_windows,
    )

    # Exclude OpenFlow LOCAL port from link-level processing.
    df = df[df["port"] != 4294967294].copy()

    # Sort each switch-port stream chronologically.
    df = df.sort_values(
        ["dpid", "port", "timestamp"]
    ).reset_index(drop=True)

    grouped = df.groupby(
        ["dpid", "port"],
        sort=False,
    )

    # --------------------------------------------------------
    # 2. Calculate sampling intervals
    # --------------------------------------------------------

    df["interval_seconds"] = (
        grouped["timestamp"]
        .diff()
        .dt.total_seconds()
    )

    valid_interval = (
        df["interval_seconds"].notna()
        & (df["interval_seconds"] > 0)
        & (df["interval_seconds"] <= MAX_INTERVAL_SECONDS)
    )

    # --------------------------------------------------------
    # 3. Calculate counter deltas
    # --------------------------------------------------------

    # Counter deltas are only valid within continuous intervals.
    # A negative counter difference indicates a reset or session
    # discontinuity; do not interpret it as ordinary traffic.
    for column in COUNTERS:

        previous = grouped[column].shift(1)

        delta = df[column] - previous

        valid_counter_delta = (
            valid_interval
            & previous.notna()
            & delta.ge(0)
        )

        df[f"{column}_delta"] = delta.where(
            valid_counter_delta
        )

    # --------------------------------------------------------
    # 4. Calculate throughput and packet rate
    # --------------------------------------------------------

    # Invalid intervals and counter resets remain NaN.
    # Do not replace unknown rates with zero.
    df["throughput_bps"] = (
        df["tx_bytes_delta"] * 8
        / df["interval_seconds"].where(valid_interval)
    )

    df["packet_rate_pps"] = (
        df["tx_packets_delta"]
        / df["interval_seconds"].where(valid_interval)
    )

    # --------------------------------------------------------
    # 5. Combine anomaly labels
    # --------------------------------------------------------

    # Retain the existing traffic-based thresholds.
    traffic_anomaly = (
        (df["throughput_bps"] > 1e8)
        | (df["packet_rate_pps"] > 2.5e5)
    ).fillna(False)

    df["is_anomalous"] = (
        (df["is_anomalous"] == 1)
        | traffic_anomaly
    ).astype("int64")

    # --------------------------------------------------------
    # 6. Keep nonnegative drop/error counter deltas
    # --------------------------------------------------------

    for column in [
        "rx_dropped_delta",
        "tx_dropped_delta",
        "rx_errors_delta",
        "tx_errors_delta",
    ]:
        df[column] = df[column].clip(lower=0)

    # --------------------------------------------------------
    # 7. Save processed features
    # --------------------------------------------------------

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

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(OUTPUT_FILE, index=False)

    # --------------------------------------------------------
    # 8. Report data-quality statistics
    # --------------------------------------------------------

    invalid_intervals = (
        result["interval_seconds"].isna()
        | (result["interval_seconds"] <= 0)
        | (result["interval_seconds"] > MAX_INTERVAL_SECONDS)
    )

    invalid_rates = (
        result["throughput_bps"].isna()
        | result["packet_rate_pps"].isna()
    )

    high_throughput = (
        result["throughput_bps"] > 1e8
    ).fillna(False)

    print()
    print("========================================")
    print("TELEMETRY PROCESSING COMPLETE")
    print("========================================")
    print(f"Anomaly windows parsed: {len(anomaly_windows)}")
    print(f"Processed rows: {len(result)}")
    print(f"Invalid/discontinuous intervals: {int(invalid_intervals.sum())}")
    print(f"Rows with invalid rate features: {int(invalid_rates.sum())}")
    print(f"Throughput observations above 100 Mbps: {int(high_throughput.sum())}")
    print(f"Anomalous rows labelled: {int(result['is_anomalous'].sum())}")
    print(f"Output: {OUTPUT_FILE}")
    print("========================================")


if __name__ == "__main__":
    main()
