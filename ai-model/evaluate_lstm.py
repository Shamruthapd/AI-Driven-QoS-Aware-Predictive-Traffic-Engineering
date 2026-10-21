
# ai-model/evaluate_lstm.py
# LSTM validation with telemetry-gap filtering and integration export.

import os
import sys

import numpy as np
import pandas as pd
import torch
import joblib

# Allow imports from the ai-model directory.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lstm_model import TrafficLSTM


# ============================================================
# Configuration
# ============================================================

VAL_FILE = "datasets/processed/val_scaled.csv"
MODEL_FILE = "ai-model/checkpoints/lstm_model.pt"
SCALER_FILE = "datasets/processed/scaler.pkl"

RESULT_FILE = "ai-model/evaluation_results.csv"
INTEGRATION_FILE = "ai-model/integration_predictions.csv"

SEQ_LEN = 5
INPUT_SIZE = 10
MAX_GAP_SECONDS = 10

MSE_THRESHOLD = 5.0
MAPE_EPSILON = 1e-8

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


# ============================================================
# Features
# ============================================================

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


# ============================================================
# Create Sequences Without Crossing Long Gaps or Invalid Rows
# ============================================================

def create_sequences(df, seq_len):
    """
    Create sequences separately for each switch-port stream.

    Invalid rows are retained as sequence boundaries until
    gap detection is complete. A sequence is accepted only if
    every input row and its target row are valid and consecutive.

    Returns:
        X: input sequences
        y: target feature vectors
        labels: target anomaly labels
        metadata: identifiers and timestamps of target rows
        gaps_detected: number of time gaps detected
    """

    X = []
    y = []
    labels = []
    metadata = []
    gaps_detected = 0

    df = df.copy()

    # Parse timestamps without silently discarding invalid rows.
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce",
        utc=True,
    )

    # Convert model features and labels to numeric values.
    # Invalid values become NaN and break any sequence containing them.
    for column in FEATURE_COLUMNS + ["is_anomalous"]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    # Sort each switch-port stream before examining intervals.
    df = df.sort_values(
        ["dpid", "port", "timestamp"],
        na_position="last",
    ).reset_index(drop=True)

    for (dpid, port), group in df.groupby(
        ["dpid", "port"],
        sort=False,
    ):

        group = group.reset_index(drop=True)

        timestamps = group["timestamp"]

        # A row is usable only when every required value is valid.
        row_valid = (
            group[
                FEATURE_COLUMNS + ["is_anomalous"]
            ].notna().all(axis=1)
            & timestamps.notna()
        ).to_numpy()

        # Convert feature columns to numeric arrays.
        values = group[FEATURE_COLUMNS].to_numpy(
            dtype=np.float64,
        )

        # Identify gaps between original consecutive rows.
        gap_seconds = (
            timestamps.diff().dt.total_seconds().to_numpy()
        )

        # A gap or invalid row breaks continuity.
        break_after = (
            (gap_seconds > MAX_GAP_SECONDS)
            | (gap_seconds < 0)
            | ~row_valid
        )

        gaps_detected += int(
            np.sum(
                (gap_seconds > MAX_GAP_SECONDS)
                | (gap_seconds < 0)
            )
        )

        # Replace invalid feature values only for safe array handling.
        # Such rows remain excluded through row_valid.
        values = np.nan_to_num(
            values,
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
        )

        group_labels = group["is_anomalous"].to_numpy()

        for i in range(len(group) - seq_len):

            target_index = i + seq_len

            # Require every input row and target row to be valid.
            if not np.all(row_valid[i:target_index + 1]):
                continue

            # No time gap may occur inside the input-target window.
            # break_after[j] refers to the interval ending at row j.
            if np.any(break_after[i + 1:target_index + 1]):
                continue

            X.append(
                values[i:target_index].astype(np.float32)
            )

            y.append(
                values[target_index].astype(np.float32)
            )

            labels.append(
                int(group_labels[target_index])
            )

            metadata.append({
                "timestamp": group.loc[
                    target_index, "timestamp"
                ],
                "dpid": dpid,
                "port": port,
            })

    return (
        np.asarray(X, dtype=np.float32).reshape(
            -1, seq_len, len(FEATURE_COLUMNS)
        ),
        np.asarray(y, dtype=np.float32).reshape(
            -1, len(FEATURE_COLUMNS)
        ),
        np.asarray(labels, dtype=np.int64),
        pd.DataFrame(
            metadata,
            columns=["timestamp", "dpid", "port"],
        ),
        gaps_detected,
    )


# ============================================================
# Load Validation Data
# ============================================================

print("=" * 70)
print("LSTM GAP-FILTERED VALIDATION AND INTEGRATION EXPORT")
print("=" * 70)
print(f"Device: {DEVICE}")
print(f"Maximum allowed gap: {MAX_GAP_SECONDS} seconds")

if not os.path.exists(VAL_FILE):
    raise FileNotFoundError(f"Validation file not found: {VAL_FILE}")

df = pd.read_csv(VAL_FILE)

required_columns = FEATURE_COLUMNS + [
    "timestamp",
    "dpid",
    "port",
    "is_anomalous",
]

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Validation dataset is missing columns: {missing_columns}"
    )

print(f"Validation rows before cleaning: {len(df)}")

df = df.dropna(subset=required_columns).copy()

df["is_anomalous"] = pd.to_numeric(
    df["is_anomalous"],
    errors="coerce",
)

df = df[df["is_anomalous"].isin([0, 1])].copy()

print(f"Validation rows after cleaning: {len(df)}")


# ============================================================
# Generate Filtered Sequences
# ============================================================

X, y, labels, metadata, gaps_detected = create_sequences(
    df,
    SEQ_LEN,
)

print(f"Long gaps detected: {gaps_detected}")
print(f"Valid validation sequences: {len(X)}")

if len(X) == 0:
    raise ValueError("No validation sequences remain after gap filtering.")

print(f"Input shape: {X.shape}")
print(f"Target shape: {y.shape}")


# ============================================================
# Load Scaler
# ============================================================

if not os.path.exists(SCALER_FILE):
    raise FileNotFoundError(f"Scaler file not found: {SCALER_FILE}")

scaler = joblib.load(SCALER_FILE)


# ============================================================
# Load Trained Model
# ============================================================

if not os.path.exists(MODEL_FILE):
    raise FileNotFoundError(f"Model checkpoint not found: {MODEL_FILE}")

checkpoint = torch.load(
    MODEL_FILE,
    map_location=DEVICE,
    weights_only=False,
)

model_config = checkpoint.get(
    "model_config",
    {
        "input_size": INPUT_SIZE,
        "hidden_size": 64,
        "num_layers": 2,
        "output_size": INPUT_SIZE,
        "dropout": 0.2,
    },
)

model = TrafficLSTM(
    input_size=model_config["input_size"],
    hidden_size=model_config["hidden_size"],
    num_layers=model_config["num_layers"],
    output_size=model_config["output_size"],
    dropout=model_config.get("dropout", 0.2),
)

model.load_state_dict(checkpoint["model_state_dict"])
model.to(DEVICE)
model.eval()


# ============================================================
# Generate Predictions
# ============================================================

X_tensor = torch.tensor(
    X,
    dtype=torch.float32,
).to(DEVICE)

with torch.no_grad():
    predictions = model(X_tensor).cpu().numpy()


# ============================================================
# Prediction Error Metrics
# ============================================================

squared_errors = (predictions - y) ** 2
absolute_errors = np.abs(predictions - y)

sample_mse = np.mean(squared_errors, axis=1)

overall_mse = np.mean(squared_errors)
overall_mae = np.mean(absolute_errors)

print("\nPrediction Error Summary")
print("-" * 70)
print(f"Overall MSE: {overall_mse:.6f}")
print(f"Overall MAE: {overall_mae:.6f}")


# ============================================================
# Convert Predictions to Original Units
# ============================================================

predictions_original = scaler.inverse_transform(predictions)
targets_original = scaler.inverse_transform(y)

valid_mape_mask = (
    np.abs(targets_original) > MAPE_EPSILON
)

percentage_errors = (
    np.abs(
        targets_original[valid_mape_mask]
        - predictions_original[valid_mape_mask]
    )
    / np.abs(targets_original[valid_mape_mask])
) * 100

print("\nMAPE Evaluation")
print("-" * 70)

if len(percentage_errors) > 0:
    mape = np.mean(percentage_errors)
    print(f"Non-zero target MAPE: {mape:.2f}%")
    print(f"Values included: {len(percentage_errors)}")
    print(f"Total target values: {targets_original.size}")
else:
    mape = np.nan
    print("MAPE could not be calculated: no valid non-zero targets.")


# ============================================================
# Anomaly Threshold Comparison
# ============================================================

print("\n" + "=" * 70)
print("Threshold Comparison")
print("=" * 70)

thresholds = [5, 10, 15, 20, 25, 30, 40, 50]
actual_anomalies = labels.astype(bool)

for threshold in thresholds:

    predicted = sample_mse > threshold

    tp = np.sum(predicted & actual_anomalies)
    fp = np.sum(predicted & ~actual_anomalies)
    fn = np.sum(~predicted & actual_anomalies)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0

    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )

    print(
        f"Threshold: {threshold:>2} | "
        f"Precision: {precision:.4f} | "
        f"Recall: {recall:.4f} | "
        f"F1-score: {f1:.4f}"
    )


# ============================================================
# Final Classification at Threshold 5.0
# ============================================================

predicted_anomalies = sample_mse > MSE_THRESHOLD

tp = np.sum(predicted_anomalies & actual_anomalies)
tn = np.sum(~predicted_anomalies & ~actual_anomalies)
fp = np.sum(predicted_anomalies & ~actual_anomalies)
fn = np.sum(~predicted_anomalies & actual_anomalies)

accuracy = (
    (tp + tn) / len(actual_anomalies)
    if len(actual_anomalies)
    else 0.0
)

precision = tp / (tp + fp) if (tp + fp) else 0.0
recall = tp / (tp + fn) if (tp + fn) else 0.0

f1 = (
    2 * precision * recall / (precision + recall)
    if (precision + recall)
    else 0.0
)

print("\n" + "=" * 70)
print(f"Final Classification Results (Threshold = {MSE_THRESHOLD})")
print("=" * 70)
print(f"Accuracy:  {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1-score:  {f1:.4f}")
print(f"Confusion Matrix: [[{tn}, {fp}], [{fn}, {tp}]]")


# ============================================================
# Prediction Error by Class
# ============================================================

normal_mask = labels == 0
anomalous_mask = labels == 1

normal_mse = (
    np.mean(sample_mse[normal_mask])
    if np.any(normal_mask)
    else np.nan
)

anomalous_mse = (
    np.mean(sample_mse[anomalous_mask])
    if np.any(anomalous_mask)
    else np.nan
)

print("\nPrediction Error by Class")
print("-" * 70)
print(f"Normal samples: {np.sum(normal_mask)} | MSE: {normal_mse:.6f}")
print(
    f"Anomalous samples: {np.sum(anomalous_mask)} | "
    f"MSE: {anomalous_mse:.6f}"
)


# ============================================================
# Save Evaluation Results
# ============================================================

results_df = pd.DataFrame({
    "sample_index": np.arange(len(sample_mse)),
    "mse": sample_mse,
    "actual_anomaly": labels.astype(int),
    "predicted_anomaly": predicted_anomalies.astype(int),
})

results_df["mse_threshold"] = MSE_THRESHOLD

results_df.to_csv(RESULT_FILE, index=False)

print(f"\nEvaluation results saved to: {RESULT_FILE}")


# ============================================================
# Export Member 3 Integration CSV
# ============================================================

integration_df = metadata.copy()

integration_df["actual_anomaly"] = labels.astype(int)
integration_df["mse"] = sample_mse
integration_df["predicted_anomaly"] = predicted_anomalies.astype(int)
integration_df["mse_threshold"] = MSE_THRESHOLD

for index, feature in enumerate(FEATURE_COLUMNS):
    integration_df[f"actual_scaled_{feature}"] = y[:, index]
    integration_df[f"predicted_scaled_{feature}"] = predictions[:, index]
    integration_df[f"actual_{feature}"] = targets_original[:, index]
    integration_df[f"predicted_{feature}"] = predictions_original[:, index]

integration_df.to_csv(INTEGRATION_FILE, index=False)

print(f"Member 3 integration CSV saved to: {INTEGRATION_FILE}")
print(f"Integration rows exported: {len(integration_df)}")
print(f"Anomaly threshold: {MSE_THRESHOLD}")
print("Evaluation uses gap-filtered validation sequences.")
print("=" * 70)