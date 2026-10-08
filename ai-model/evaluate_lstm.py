# ai-model/evaluate_lstm.py

# Import required libraries.
import os
import numpy as np
import pandas as pd
import torch
import joblib

# Import the LSTM model definition.
from lstm_model import TrafficLSTM


# ============================================================
# Configuration
# ============================================================

# Path to the validation dataset.
VAL_FILE = "datasets/processed/val_scaled.csv"

# Path to the trained LSTM checkpoint.
MODEL_FILE = "ai-model/checkpoints/lstm_model.pt"

# Path to the scaler used during dataset preparation.
SCALER_FILE = "datasets/processed/scaler.pkl"

# Output file for evaluation results.
RESULT_FILE = "ai-model/evaluation_results.csv"

# Number of previous time steps used to predict the next step.
SEQ_LEN = 5

# Number of input features used by the LSTM.
INPUT_SIZE = 10

# Threshold used to classify a prediction as anomalous.
MSE_THRESHOLD = 5.0

# Small value used to avoid division by zero while calculating MAPE.
MAPE_EPSILON = 1e-8

# Device used for evaluation.
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ============================================================
# Feature Configuration
# ============================================================

# These are the exact 10 features expected by the LSTM.
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
# Helper Function: Create Sequences
# ============================================================

def create_sequences(df, seq_len):
    """
    Create sliding-window sequences for LSTM evaluation.

    Each sequence contains 'seq_len' previous observations,
    and the target is the next observation.
    """

    X = []
    y = []
    labels = []

    # Group data by device and port so that sequences
    # are not created across different network interfaces.
    grouped = df.groupby(["dpid", "port"])

    for _, group in grouped:

        # Sort each group chronologically.
        group = group.sort_values("timestamp")

        # Extract feature values.
        values = group[FEATURE_COLUMNS].values

        # Extract anomaly labels.
        group_labels = group["is_anomalous"].values

        # Create sliding-window sequences.
        for i in range(len(values) - seq_len):

            # Previous 'seq_len' observations are the input.
            X.append(values[i:i + seq_len])

            # The next observation is the prediction target.
            y.append(values[i + seq_len])

            # Store the anomaly label of the target observation.
            labels.append(group_labels[i + seq_len])

    return (
        np.array(X, dtype=np.float32),
        np.array(y, dtype=np.float32),
        np.array(labels)
    )


# ============================================================
# Load Validation Dataset
# ============================================================

print("=" * 70)
print("LSTM VALIDATION")
print("=" * 70)

print(f"Using device: {DEVICE}")

# Check whether the validation file exists.
if not os.path.exists(VAL_FILE):
    raise FileNotFoundError(f"Validation file not found: {VAL_FILE}")

# Load validation data.
df = pd.read_csv(VAL_FILE)

print(f"Validation rows before cleaning: {len(df)}")


# ============================================================
# Data Cleaning
# ============================================================

# Remove rows containing missing values in the required columns.
required_columns = FEATURE_COLUMNS + [
    "timestamp",
    "dpid",
    "port",
    "is_anomalous"
]

df = df.dropna(subset=required_columns).copy()

print(f"Validation rows after cleaning: {len(df)}")


# ============================================================
# Create Validation Sequences
# ============================================================

# Create sliding-window input sequences and targets.
X, y, labels = create_sequences(df, SEQ_LEN)

print(f"Validation sequences: {len(X)}")
print(f"Input shape: {X.shape}")
print(f"Target shape: {y.shape}")


# ============================================================
# Load Trained Model
# ============================================================

if not os.path.exists(MODEL_FILE):
    raise FileNotFoundError(f"Model checkpoint not found: {MODEL_FILE}")

# Load the trained checkpoint.
checkpoint = torch.load(
    MODEL_FILE,
    map_location=DEVICE,
    weights_only=False
)

# Read model configuration from the checkpoint if available.
# These fallback values keep compatibility with older checkpoints.
model_config = checkpoint.get(
    "model_config",
    {
        "input_size": INPUT_SIZE,
        "hidden_size": 64,
        "num_layers": 2,
        "output_size": INPUT_SIZE,
        "dropout": 0.2,
    }
)

# Create the LSTM model using the saved configuration.
model = TrafficLSTM(
    input_size=model_config["input_size"],
    hidden_size=model_config["hidden_size"],
    num_layers=model_config["num_layers"],
    output_size=model_config["output_size"],
    dropout=model_config.get("dropout", 0.2)
)

# Load trained model weights.
model.load_state_dict(checkpoint["model_state_dict"])

# Move model to CPU/GPU.
model.to(DEVICE)

# Put model into evaluation mode.
model.eval()


# ============================================================
# Run Predictions
# ============================================================

# Convert input sequences into a PyTorch tensor.
X_tensor = torch.tensor(X, dtype=torch.float32).to(DEVICE)

# Disable gradient calculation because this is evaluation only.
with torch.no_grad():

    # Generate predictions for all validation sequences.
    predictions_tensor = model(X_tensor)

# Move predictions back to CPU and convert to NumPy.
predictions = predictions_tensor.cpu().numpy()


# ============================================================
# Calculate Prediction Errors
# ============================================================

# Calculate squared error for every predicted feature.
squared_errors = (predictions - y) ** 2

# Calculate absolute error for every predicted feature.
absolute_errors = np.abs(predictions - y)

# Calculate MSE for each sequence.
sample_mse = np.mean(squared_errors, axis=1)

# Calculate overall MSE across all predictions and features.
overall_mse = np.mean(squared_errors)

# Calculate overall MAE across all predictions and features.
# MAE represents the average absolute prediction error.
overall_mae = np.mean(absolute_errors)

# Print the main prediction-error metrics.
print("\nPrediction Error Summary")
print("-" * 70)
print(f"Overall MSE: {overall_mse:.6f}")
print(f"Overall MAE: {overall_mae:.6f}")


# ============================================================
# Calculate MAPE
# ============================================================

# Load the scaler used to create the scaled validation dataset.
if not os.path.exists(SCALER_FILE):
    raise FileNotFoundError(f"Scaler file not found: {SCALER_FILE}")

scaler = joblib.load(SCALER_FILE)

# Flatten the predictions and targets so that they can be
# inverse-transformed using the same scaler.
predictions_flat = predictions.reshape(-1, INPUT_SIZE)
targets_flat = y.reshape(-1, INPUT_SIZE)

# Convert scaled values back to their original units.
predictions_original = scaler.inverse_transform(predictions_flat)
targets_original = scaler.inverse_transform(targets_flat)

# Only calculate percentage error where the actual value
# is not zero or extremely close to zero.
valid_mape_mask = np.abs(targets_original) > MAPE_EPSILON

# Calculate absolute percentage errors.
percentage_errors = (
    np.abs(
        (targets_original[valid_mape_mask]
         - predictions_original[valid_mape_mask])
        / targets_original[valid_mape_mask]
    )
    * 100
)

# Calculate MAPE if there are valid non-zero targets.
if len(percentage_errors) > 0:

    # Calculate mean percentage error.
    mape = np.mean(percentage_errors)

    print("\nMAPE Evaluation")
    print("-" * 70)
    print(f"Non-zero target MAPE: {mape:.2f}%")
    print(f"Values included: {len(percentage_errors)}")
    print(f"Total target values: {targets_original.size}")

else:

    # Report if no valid values are available.
    mape = np.nan

    print("\nMAPE Evaluation")
    print("-" * 70)
    print("MAPE could not be calculated because all target values are zero.")


# ============================================================
# Threshold Comparison
# ============================================================

print("\n" + "=" * 70)
print("Threshold Comparison")
print("=" * 70)

# Thresholds to compare for anomaly detection.
thresholds = [5, 10, 15, 20, 25, 30, 40, 50]

# Store threshold evaluation results.
threshold_results = []

for threshold in thresholds:

    # Predict anomaly when MSE exceeds the threshold.
    predicted_anomalies = sample_mse > threshold

    # Convert actual labels into Boolean values.
    actual_anomalies = labels.astype(bool)

    # Calculate confusion-matrix components.
    true_positive = np.sum(
        predicted_anomalies & actual_anomalies
    )

    false_positive = np.sum(
        predicted_anomalies & ~actual_anomalies
    )

    false_negative = np.sum(
        ~predicted_anomalies & actual_anomalies
    )

    true_negative = np.sum(
        ~predicted_anomalies & ~actual_anomalies
    )

    # Calculate precision.
    precision = (
        true_positive / (true_positive + false_positive)
        if (true_positive + false_positive) > 0
        else 0
    )

    # Calculate recall.
    recall = (
        true_positive / (true_positive + false_negative)
        if (true_positive + false_negative) > 0
        else 0
    )

    # Calculate F1-score.
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0
    )

    # Print threshold results.
    print(
        f"Threshold: {threshold:>2} | "
        f"Precision: {precision:.4f} | "
        f"Recall: {recall:.4f} | "
        f"F1-score: {f1:.4f}"
    )

    # Store the result.
    threshold_results.append({
        "threshold": threshold,
        "precision": precision,
        "recall": recall,
        "f1": f1
    })


# ============================================================
# Final Classification Using Selected Threshold
# ============================================================

# Use the selected threshold for the final classification.
predicted_anomalies = sample_mse > MSE_THRESHOLD

# Convert labels to Boolean values.
actual_anomalies = labels.astype(bool)

# Calculate confusion-matrix components.
true_positive = np.sum(
    predicted_anomalies & actual_anomalies
)

true_negative = np.sum(
    ~predicted_anomalies & ~actual_anomalies
)

false_positive = np.sum(
    predicted_anomalies & ~actual_anomalies
)

false_negative = np.sum(
    ~predicted_anomalies & actual_anomalies
)

# Calculate accuracy.
accuracy = (
    (true_positive + true_negative)
    / len(actual_anomalies)
)

# Calculate precision.
precision = (
    true_positive / (true_positive + false_positive)
    if (true_positive + false_positive) > 0
    else 0
)

# Calculate recall.
recall = (
    true_positive / (true_positive + false_negative)
    if (true_positive + false_negative) > 0
    else 0
)

# Calculate F1-score.
f1 = (
    2 * precision * recall / (precision + recall)
    if (precision + recall) > 0
    else 0
)


# ============================================================
# Print Final Classification Results
# ============================================================

print("\n" + "=" * 70)
print(f"Final Classification Results (Threshold = {MSE_THRESHOLD})")
print("=" * 70)

print(f"Accuracy:  {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1-score:  {f1:.4f}")

print("\nConfusion Matrix")
print(
    f"[[{true_negative}, {false_positive}], "
    f"[{false_negative}, {true_positive}]]"
)


# ============================================================
# Normal vs Anomalous Prediction Error
# ============================================================

# Separate prediction errors for normal and anomalous samples.
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

print(
    f"Normal samples: {np.sum(normal_mask)} | "
    f"MSE: {normal_mse:.6f}"
)

print(
    f"Anomalous samples: {np.sum(anomalous_mask)} | "
    f"MSE: {anomalous_mse:.6f}"
)


# ============================================================
# Save Evaluation Results
# ============================================================

# Create a DataFrame containing sequence-level evaluation results.
results_df = pd.DataFrame({
    "sample_index": np.arange(len(sample_mse)),
    "mse": sample_mse,
    "actual_anomaly": labels,
    "predicted_anomaly": predicted_anomalies.astype(int)
})

# Add the selected threshold to the results.
results_df["mse_threshold"] = MSE_THRESHOLD

# Save results to CSV.
results_df.to_csv(RESULT_FILE, index=False)

print("\n" + "=" * 70)
print(f"Evaluation results saved to: {RESULT_FILE}")
print("=" * 70)