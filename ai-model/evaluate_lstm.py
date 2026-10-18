# ai-model/evaluate_lstm.py

# Import libraries for data processing, model inference, and evaluation.
import os
import numpy as np
import pandas as pd
import torch
import joblib

# Import the trained LSTM model architecture.
from lstm_model import TrafficLSTM


# ============================================================
# Configuration
# ============================================================

# Input validation dataset containing scaled telemetry.
VAL_FILE = "datasets/processed/val_scaled.csv"

# Trained LSTM checkpoint.
MODEL_FILE = "ai-model/checkpoints/lstm_model.pt"

# Existing scaler used during dataset preparation.
SCALER_FILE = "datasets/processed/scaler.pkl"

# Existing evaluation output.
RESULT_FILE = "ai-model/evaluation_results.csv"

# New integration output for Member 3.
INTEGRATION_FILE = "ai-model/integration_predictions.csv"

# Number of previous observations used for each prediction.
SEQ_LEN = 5

# Number of telemetry features expected by the model.
INPUT_SIZE = 10

# Current anomaly threshold, which still requires calibration.
MSE_THRESHOLD = 5.0

# Small epsilon used to exclude zero and near-zero actual values from MAPE.
MAPE_EPSILON = 1e-8

# Select GPU when available; otherwise, use CPU.
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ============================================================
# Feature Configuration
# ============================================================

# IMPORTANT: Preserve this exact order during training and inference.
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
# Create Sequences and Preserve Target Metadata
# ============================================================

def create_sequences(df, seq_len):
    """
    Create sliding-window sequences separately for each switch and port.

    The target is the observation immediately following the input window.
    Metadata is retained for that exact target observation.
    """

    X = []
    y = []
    labels = []
    metadata = []

    # Prevent sequences from crossing different switches or ports.
    for (dpid, port), group in df.groupby(["dpid", "port"]):

        # Sort observations chronologically within each switch and port.
        group = group.sort_values("timestamp").reset_index(drop=True)

        # Extract the ten scaled telemetry features.
        values = group[FEATURE_COLUMNS].to_numpy(dtype=np.float32)

        # Extract labels corresponding to the observations.
        group_labels = group["is_anomalous"].to_numpy()

        # Generate one sequence for each available target observation.
        for i in range(len(group) - seq_len):

            # Use five previous observations as the model input.
            X.append(values[i:i + seq_len])

            # The following observation is the prediction target.
            target_index = i + seq_len
            y.append(values[target_index])

            # Preserve the actual anomaly label for the target.
            labels.append(group_labels[target_index])

            # Preserve identifiers and timestamp for the same target.
            metadata.append({
                "timestamp": group.loc[target_index, "timestamp"],
                "dpid": dpid,
                "port": port,
            })

    # Return arrays with matching sequence indexes.
    return (
        np.asarray(X, dtype=np.float32),
        np.asarray(y, dtype=np.float32),
        np.asarray(labels),
        pd.DataFrame(metadata),
    )


# ============================================================
# Load Validation Dataset
# ============================================================

print("=" * 70)
print("LSTM VALIDATION AND MEMBER 3 INTEGRATION EXPORT")
print("=" * 70)

print(f"Using device: {DEVICE}")

# Ensure the validation dataset exists.
if not os.path.exists(VAL_FILE):
    raise FileNotFoundError(f"Validation file not found: {VAL_FILE}")

# Load the scaled validation dataset.
df = pd.read_csv(VAL_FILE)

print(f"Validation rows before cleaning: {len(df)}")


# ============================================================
# Clean and Validate Input Data
# ============================================================

# These columns must be present to evaluate and export integration data.
required_columns = FEATURE_COLUMNS + [
    "timestamp",
    "dpid",
    "port",
    "is_anomalous",
]

# Fail clearly if the dataset schema is incorrect.
missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Validation dataset is missing required columns: {missing_columns}"
    )

# Remove rows with missing values in required fields.
df = df.dropna(subset=required_columns).copy()

# Keep only valid binary anomaly labels.
df = df[df["is_anomalous"].isin([0, 1])].copy()

print(f"Validation rows after cleaning: {len(df)}")


# ============================================================
# Create Validation Sequences
# ============================================================

# Generate input windows, targets, labels, and target metadata.
X, y, labels, metadata = create_sequences(df, SEQ_LEN)

# Stop if no complete sequences could be generated.
if len(X) == 0:
    raise ValueError("No validation sequences were generated.")

print(f"Validation sequences: {len(X)}")
print(f"Input shape: {X.shape}")
print(f"Target shape: {y.shape}")


# ============================================================
# Load the Existing Scaler
# ============================================================

# Ensure the original scaler exists.
if not os.path.exists(SCALER_FILE):
    raise FileNotFoundError(f"Scaler file not found: {SCALER_FILE}")

# Load the scaler used during original dataset preparation.
# Do not fit a new scaler during evaluation.
scaler = joblib.load(SCALER_FILE)


# ============================================================
# Load the Trained LSTM Checkpoint
# ============================================================

# Ensure the trained model exists.
if not os.path.exists(MODEL_FILE):
    raise FileNotFoundError(f"Model checkpoint not found: {MODEL_FILE}")

# Load the checkpoint on the selected device.
checkpoint = torch.load(
    MODEL_FILE,
    map_location=DEVICE,
    weights_only=False,
)

# Read saved architecture settings or use compatible defaults.
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

# Construct the LSTM with the saved architecture.
model = TrafficLSTM(
    input_size=model_config["input_size"],
    hidden_size=model_config["hidden_size"],
    num_layers=model_config["num_layers"],
    output_size=model_config["output_size"],
    dropout=model_config.get("dropout", 0.2),
)

# Load trained weights.
model.load_state_dict(checkpoint["model_state_dict"])

# Move the model to the selected device and enable evaluation mode.
model.to(DEVICE)
model.eval()


# ============================================================
# Generate Predictions
# ============================================================

# Convert input sequences into a PyTorch tensor.
X_tensor = torch.tensor(X, dtype=torch.float32).to(DEVICE)

# Generate predictions without calculating gradients.
with torch.no_grad():
    predictions_tensor = model(X_tensor)

# Convert predictions back to NumPy arrays.
predictions = predictions_tensor.cpu().numpy()


# ============================================================
# Calculate Prediction Errors
# ============================================================

# Calculate squared and absolute errors in scaled feature space.
squared_errors = (predictions - y) ** 2
absolute_errors = np.abs(predictions - y)

# Calculate one MSE value for each target observation.
sample_mse = np.mean(squared_errors, axis=1)

# Calculate overall prediction-error metrics.
overall_mse = np.mean(squared_errors)
overall_mae = np.mean(absolute_errors)

print("\nPrediction Error Summary")
print("-" * 70)
print(f"Overall MSE: {overall_mse:.6f}")
print(f"Overall MAE: {overall_mae:.6f}")


# ============================================================
# Calculate MAPE
# ============================================================

# Flatten predictions and targets for inverse scaling.
predictions_flat = predictions.reshape(-1, INPUT_SIZE)
targets_flat = y.reshape(-1, INPUT_SIZE)

# Convert scaled predictions and targets to original feature units.
predictions_original = scaler.inverse_transform(predictions_flat)
targets_original = scaler.inverse_transform(targets_flat)

# Exclude zero and near-zero actual values from MAPE.
valid_mape_mask = np.abs(targets_original) > MAPE_EPSILON

# Calculate percentage errors only for valid values.
percentage_errors = (
    np.abs(
        (
            targets_original[valid_mape_mask]
            - predictions_original[valid_mape_mask]
        )
        / targets_original[valid_mape_mask]
    )
    * 100
)

print("\nMAPE Evaluation")
print("-" * 70)

# Print MAPE when valid actual values are available.
if len(percentage_errors) > 0:
    mape = np.mean(percentage_errors)
    print(f"Non-zero target MAPE: {mape:.2f}%")
    print(f"Values included: {len(percentage_errors)}")
    print(f"Total target values: {targets_original.size}")
else:
    mape = np.nan
    print("MAPE could not be calculated: no valid non-zero targets.")


# ============================================================
# Compare Anomaly Detection Thresholds
# ============================================================

print("\n" + "=" * 70)
print("Threshold Comparison")
print("=" * 70)

# Evaluate the same thresholds used in the existing evaluation.
thresholds = [5, 10, 15, 20, 25, 30, 40, 50]

# Keep actual labels in Boolean form for metric calculations.
actual_anomalies = labels.astype(bool)

for threshold in thresholds:

    # Flag samples whose scaled-space MSE exceeds the threshold.
    predicted = sample_mse > threshold

    # Calculate true/false positives and negatives.
    tp = np.sum(predicted & actual_anomalies)
    fp = np.sum(predicted & ~actual_anomalies)
    fn = np.sum(~predicted & actual_anomalies)

    # Calculate precision, recall, and F1 safely.
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )

    # Print the metrics for the current threshold.
    print(
        f"Threshold: {threshold:>2} | "
        f"Precision: {precision:.4f} | "
        f"Recall: {recall:.4f} | "
        f"F1-score: {f1:.4f}"
    )


# ============================================================
# Final Classification at Threshold 5.0
# ============================================================

# Apply the currently configured threshold.
predicted_anomalies = sample_mse > MSE_THRESHOLD

# Calculate confusion-matrix components.
tp = np.sum(predicted_anomalies & actual_anomalies)
tn = np.sum(~predicted_anomalies & ~actual_anomalies)
fp = np.sum(predicted_anomalies & ~actual_anomalies)
fn = np.sum(~predicted_anomalies & actual_anomalies)

# Calculate final classification metrics.
accuracy = (tp + tn) / len(actual_anomalies)
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

# Separate samples by their actual anomaly labels.
normal_mask = labels == 0
anomalous_mask = labels == 1

# Calculate class-specific MSE values.
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
# Save the Existing Evaluation Results
# ============================================================

# Preserve the existing evaluation CSV's purpose and columns.
results_df = pd.DataFrame({
    "sample_index": np.arange(len(sample_mse)),
    "mse": sample_mse,
    "actual_anomaly": labels,
    "predicted_anomaly": predicted_anomalies.astype(int),
})

# Record the threshold used for the predictions.
results_df["mse_threshold"] = MSE_THRESHOLD

# Save the existing evaluation output.
results_df.to_csv(RESULT_FILE, index=False)

print(f"\nEvaluation results saved to: {RESULT_FILE}")


# ============================================================
# Export Member 3 Integration CSV
# ============================================================

# Begin with target metadata for the exact rows being predicted.
integration_df = metadata.copy()

# Include the actual anomaly label and calculated prediction error.
integration_df["actual_anomaly"] = labels.astype(int)
integration_df["mse"] = sample_mse

# Include the anomaly decision and threshold used.
integration_df["predicted_anomaly"] = predicted_anomalies.astype(int)
integration_df["mse_threshold"] = MSE_THRESHOLD

# Add actual and predicted values in scaled space.
# These values are used for MSE and reproduce the existing decisions.
for index, feature in enumerate(FEATURE_COLUMNS):
    integration_df[f"actual_scaled_{feature}"] = y[:, index]
    integration_df[f"predicted_scaled_{feature}"] = predictions[:, index]

# Add actual and predicted values in original feature units.
# These are easier for Member 3 to interpret and inspect.
for index, feature in enumerate(FEATURE_COLUMNS):
    integration_df[f"actual_{feature}"] = targets_original.reshape(
        len(y), INPUT_SIZE
    )[:, index]

    integration_df[f"predicted_{feature}"] = predictions_original.reshape(
        len(predictions), INPUT_SIZE
    )[:, index]

# Save the integration CSV separately from the existing evaluation CSV.
integration_df.to_csv(INTEGRATION_FILE, index=False)

print(f"Member 3 integration CSV saved to: {INTEGRATION_FILE}")
print(f"Integration rows exported: {len(integration_df)}")
print("MSE uses scaled feature values and the configured feature order.")
print(f"Anomaly threshold: {MSE_THRESHOLD}")
print("=" * 70)