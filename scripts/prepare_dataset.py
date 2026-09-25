import pandas as pd
from pathlib import Path
from sklearn.preprocessing import StandardScaler
import joblib


# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_ROOT / "datasets" / "processed" / "qos_features.csv"
CLEAN_FILE = PROJECT_ROOT / "datasets" / "processed" / "clean_dataset.csv"

TRAIN_RAW_FILE = PROJECT_ROOT / "datasets" / "processed" / "train_raw.csv"
VAL_RAW_FILE = PROJECT_ROOT / "datasets" / "processed" / "val_raw.csv"

TRAIN_SCALED_FILE = PROJECT_ROOT / "datasets" / "processed" / "train_scaled.csv"
VAL_SCALED_FILE = PROJECT_ROOT / "datasets" / "processed" / "val_scaled.csv"

SCALER_FILE = PROJECT_ROOT / "datasets" / "processed" / "scaler.pkl"


# ------------------------------------------------------------
# Columns used for ML scaling
# ------------------------------------------------------------

FEATURE_COLUMNS = [
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


def main():

    print("Loading dataset...")

    df = pd.read_csv(INPUT_FILE)

    print(f"Original rows: {len(df)}")

    # --------------------------------------------------------
    # 1. Convert timestamp
    # --------------------------------------------------------

    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        utc=True,
        errors="coerce"
    )

    # --------------------------------------------------------
    # 2. Convert numeric columns
    # --------------------------------------------------------

    numeric_columns = [
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

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

    # --------------------------------------------------------
    # 3. Remove malformed rows
    # --------------------------------------------------------

    required_columns = [
        "timestamp",
        "dpid",
        "port",
        "interval_seconds",
        *FEATURE_COLUMNS,
        "is_anomalous",
    ]

    before = len(df)

    df = df.dropna(
        subset=required_columns
    ).copy()

    removed = before - len(df)

    print(f"Removed malformed/incomplete rows: {removed}")

    # --------------------------------------------------------
    # 4. Sort chronologically
    # --------------------------------------------------------

    df = df.sort_values(
        ["timestamp", "dpid", "port"]
    ).reset_index(drop=True)

    # --------------------------------------------------------
    # 5. Save clean dataset
    # --------------------------------------------------------

    df.to_csv(
        CLEAN_FILE,
        index=False
    )

    print(f"Clean dataset saved: {CLEAN_FILE}")
    print(f"Clean rows: {len(df)}")

    # --------------------------------------------------------
    # 6. Chronological 80/20 split
    # --------------------------------------------------------

    split_index = int(len(df) * 0.80)

    train = df.iloc[:split_index].copy()
    val = df.iloc[split_index:].copy()

    print(f"Training rows: {len(train)}")
    print(f"Validation rows: {len(val)}")

    # --------------------------------------------------------
    # 7. Save RAW train/validation datasets
    # --------------------------------------------------------

    train.to_csv(
        TRAIN_RAW_FILE,
        index=False
    )

    val.to_csv(
        VAL_RAW_FILE,
        index=False
    )

    # --------------------------------------------------------
    # 8. Scale ML features
    #
    # IMPORTANT:
    # Fit scaler ONLY on training data.
    # --------------------------------------------------------

    scaler = StandardScaler()

    train_scaled = train.copy()
    val_scaled = val.copy()

    train_scaled[FEATURE_COLUMNS] = scaler.fit_transform(
        train[FEATURE_COLUMNS]
    )

    val_scaled[FEATURE_COLUMNS] = scaler.transform(
        val[FEATURE_COLUMNS]
    )

    # Save scaler for future LSTM use
    joblib.dump(
        scaler,
        SCALER_FILE
    )

    # --------------------------------------------------------
    # 9. Save scaled datasets
    # --------------------------------------------------------

    train_scaled.to_csv(
        TRAIN_SCALED_FILE,
        index=False
    )

    val_scaled.to_csv(
        VAL_SCALED_FILE,
        index=False
    )

    # --------------------------------------------------------
    # 10. Final summary
    # --------------------------------------------------------

    print()
    print("========================================")
    print("DATASET PREPARATION COMPLETE")
    print("========================================")
    print(f"Original rows : {before}")
    print(f"Clean rows    : {len(df)}")
    print(f"Train rows    : {len(train)}")
    print(f"Validation    : {len(val)}")
    print()
    print("Files created:")
    print(" - clean_dataset.csv")
    print(" - train_raw.csv")
    print(" - val_raw.csv")
    print(" - train_scaled.csv")
    print(" - val_scaled.csv")
    print(" - scaler.pkl")
    print("========================================")


if __name__ == "__main__":
    main()