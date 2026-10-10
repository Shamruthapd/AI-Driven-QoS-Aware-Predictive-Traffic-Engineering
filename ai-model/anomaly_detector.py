"""Week 6 LSTM-based anomaly detector for network telemetry."""

import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch

from lstm_model import TrafficLSTM


ROOT = Path(__file__).resolve().parents[1]

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


def parse_args():
    parser = argparse.ArgumentParser(
        description="Detect telemetry anomalies using the trained LSTM."
    )
    parser.add_argument(
        "--input",
        default=str(ROOT / "datasets/processed/qos_features.csv"),
    )
    parser.add_argument(
        "--output",
        default=str(
            ROOT / "datasets/processed/week6_lstm_anomaly_results.csv"
        ),
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=5.0,
        help="MSE threshold in scaled feature space (default: 5.0).",
    )
    return parser.parse_args()


def load_model(device):
    checkpoint_path = ROOT / "ai-model/checkpoints/lstm_model.pt"
    scaler_path = ROOT / "datasets/processed/scaler.pkl"

    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
    if not scaler_path.exists():
        raise FileNotFoundError(f"Scaler not found: {scaler_path}")

    # The checkpoint contains the trained state and model configuration.
    checkpoint = torch.load(
        checkpoint_path,
        map_location=device,
        weights_only=False,
    )

    config = checkpoint.get(
        "model_config",
        {
            "input_size": 10,
            "hidden_size": 64,
            "num_layers": 2,
            "output_size": 10,
            "dropout": 0.2,
        },
    )

    if config["input_size"] != len(FEATURE_COLUMNS):
        raise ValueError("Checkpoint input size does not match 10 features.")
    if config["output_size"] != len(FEATURE_COLUMNS):
        raise ValueError("Checkpoint output size does not match 10 features.")

    sequence_length = int(checkpoint.get("sequence_length", 5))
    if sequence_length < 1:
        raise ValueError("Invalid sequence length in checkpoint.")

    model = TrafficLSTM(
        input_size=config["input_size"],
        hidden_size=config["hidden_size"],
        num_layers=config["num_layers"],
        output_size=config["output_size"],
        dropout=config.get("dropout", 0.2),
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()

    scaler = joblib.load(scaler_path)
    if getattr(scaler, "n_features_in_", len(FEATURE_COLUMNS)) != len(
        FEATURE_COLUMNS
    ):
        raise ValueError("Scaler does not expect the required 10 features.")

    return model, scaler, sequence_length


def prepare_data(input_path):
    df = pd.read_csv(input_path)

    required = [
        "timestamp",
        "dpid",
        "port",
        "is_anomalous",
        *FEATURE_COLUMNS,
    ]
    missing = sorted(set(required) - set(df.columns))
    if missing:
        raise ValueError(f"Input is missing required columns: {missing}")

    df["timestamp"] = pd.to_datetime(
        df["timestamp"], utc=True, errors="coerce"
    )
    for column in FEATURE_COLUMNS + ["is_anomalous"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=required).copy()
    df = df.sort_values(
        ["dpid", "port", "timestamp"]
    ).reset_index(drop=True)

    if df.empty:
        raise ValueError("No usable telemetry rows remain after cleaning.")

    df["is_anomalous"] = df["is_anomalous"].astype(int)
    return df


def create_predictions(df, model, scaler, sequence_length, threshold, device):
    # Scale using the scaler fitted during model-data preparation.
    scaled = scaler.transform(df[FEATURE_COLUMNS].to_numpy(dtype=np.float64))
    results = []

    # Never construct a sequence across different switches or ports.
    for (dpid, port), indices in df.groupby(
        ["dpid", "port"], sort=False
    ).groups.items():
        group_indices = list(indices)
        values = scaled[group_indices]

        if len(values) <= sequence_length:
            continue

        sequences = []
        targets = []
        target_positions = []

        for i in range(len(values) - sequence_length):
            sequences.append(values[i : i + sequence_length])
            targets.append(values[i + sequence_length])
            target_positions.append(group_indices[i + sequence_length])

        x = torch.tensor(np.asarray(sequences), dtype=torch.float32).to(device)
        y = np.asarray(targets, dtype=np.float32)

        with torch.no_grad():
            predicted = model(x).cpu().numpy()

        # Mean squared prediction error across the 10 scaled features.
        mse = np.mean(np.square(predicted - y), axis=1)

        for position, score in zip(target_positions, mse):
            row = df.iloc[position]
            results.append(
                {
                    "timestamp": row["timestamp"],
                    "dpid": dpid,
                    "port": port,
                    "mse": float(score),
                    "mse_threshold": threshold,
                    "actual_anomaly": int(row["is_anomalous"]),
                    "predicted_anomaly": int(score > threshold),
                }
            )

    if not results:
        raise ValueError(
            "No sequences could be predicted. Check input data and sequence length."
        )

    return pd.DataFrame(results).sort_values(
        ["timestamp", "dpid", "port"]
    ).reset_index(drop=True)


def print_metrics(results):
    actual = results["actual_anomaly"].to_numpy(dtype=int)
    predicted = results["predicted_anomaly"].to_numpy(dtype=int)

    tp = int(((actual == 1) & (predicted == 1)).sum())
    fn = int(((actual == 1) & (predicted == 0)).sum())
    fp = int(((actual == 0) & (predicted == 1)).sum())
    tn = int(((actual == 0) & (predicted == 0)).sum())

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    fpr = fp / (fp + tn) if fp + tn else 0.0
    accuracy = (tp + tn) / len(results)

    print("\nWEEK 6 LSTM ANOMALY DETECTOR")
    print("--------------------------------")
    print("Evaluated samples:", len(results))
    print("Threshold:", results["mse_threshold"].iloc[0])
    print(f"TP={tp}, FN={fn}, FP={fp}, TN={tn}")
    print(f"Accuracy:           {accuracy:.4f}")
    print(f"Precision:          {precision:.4f}")
    print(f"Recall:             {recall:.4f}")
    print(f"F1-score:           {f1:.4f}")
    print(f"False-positive rate:{fpr:.4f}")
    print(
        "\nNote: these metrics use the labels in the input dataset. "
        "They do not by themselves prove detection of a separate physical link failure."
    )


def main():
    args = parse_args()
    if not np.isfinite(args.threshold) or args.threshold < 0:
        raise ValueError("Threshold must be a finite, non-negative number.")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Device:", device)

    df = prepare_data(args.input)
    model, scaler, sequence_length = load_model(device)
    print("Input rows after cleaning:", len(df))
    print("LSTM sequence length:", sequence_length)
    print("Input features:", len(FEATURE_COLUMNS))

    results = create_predictions(
        df,
        model,
        scaler,
        sequence_length,
        args.threshold,
        device,
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output, index=False)

    print_metrics(results)
    print("Timestamped results saved to:", output)


if __name__ == "__main__":
    main()
