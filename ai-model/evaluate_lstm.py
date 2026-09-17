from pathlib import Path

import numpy as np
import pandas as pd
import torch

from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from torch.utils.data import DataLoader, TensorDataset

from lstm_model import TrafficLSTM


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

# Identify the project root directory.
BASE_DIR = Path(__file__).resolve().parent.parent

# Define dataset, model, and output paths.
VALIDATION_FILE = BASE_DIR / "datasets" / "processed" / "val_scaled.csv"
MODEL_FILE = BASE_DIR / "ai-model" / "checkpoints" / "lstm_model.pt"
OUTPUT_FILE = BASE_DIR / "ai-model" / "evaluation_results.csv"

# Number of previous time steps used as input.
SEQUENCE_LENGTH = 5

# Features used by the LSTM model.
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

# Select GPU if available; otherwise, use CPU.
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Main threshold used for the final anomaly prediction.
MSE_THRESHOLD = 5

# Thresholds tested for comparison.
THRESHOLDS_TO_TEST = [5, 10, 15, 20, 25, 30, 40, 50]


# ---------------------------------------------------------
# Load validation data
# ---------------------------------------------------------

# Read the scaled validation dataset.
df = pd.read_csv(VALIDATION_FILE)

# Convert timestamps into datetime values.
df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="coerce",
)

# Identify columns required for evaluation.
required_columns = FEATURE_COLUMNS + [
    "timestamp",
    "dpid",
    "port",
    "is_anomalous",
]

# Remove rows with missing required values.
df = df.dropna(subset=required_columns)

# Sort telemetry data chronologically for each switch and port.
df = df.sort_values(
    by=["dpid", "port", "timestamp"]
).reset_index(drop=True)


# ---------------------------------------------------------
# Create validation sequences
# ---------------------------------------------------------

# Store input sequences, target values, and sample metadata.
sequences = []
targets = []
metadata = []

# Group data by datapath ID and port.
grouped = df.groupby(["dpid", "port"])

for (dpid, port), group in grouped:

    # Sort each group by timestamp.
    group = group.sort_values("timestamp").reset_index(drop=True)

    # Extract the model features.
    feature_values = group[FEATURE_COLUMNS].to_numpy(
        dtype=np.float32
    )

    # Create sliding-window sequences.
    for i in range(len(group) - SEQUENCE_LENGTH):

        # Use the previous five rows as the input sequence.
        input_sequence = feature_values[
            i:i + SEQUENCE_LENGTH
        ]

        # Use the next row as the prediction target.
        target_value = feature_values[
            i + SEQUENCE_LENGTH
        ]

        # Retrieve metadata for the target row.
        target_row = group.iloc[i + SEQUENCE_LENGTH]

        # Store the input sequence and target.
        sequences.append(input_sequence)
        targets.append(target_value)

        # Store metadata for later anomaly evaluation.
        metadata.append({
            "timestamp": target_row["timestamp"],
            "dpid": dpid,
            "port": port,
            "is_anomalous": int(target_row["is_anomalous"]),
        })


# Stop if no sequences were created.
if len(sequences) == 0:
    raise RuntimeError("No validation sequences were generated.")


# Convert the sequences and targets into PyTorch tensors.
X_val = torch.tensor(
    np.array(sequences),
    dtype=torch.float32,
)

y_val = torch.tensor(
    np.array(targets),
    dtype=torch.float32,
)

# Create the validation dataset and data loader.
validation_dataset = TensorDataset(X_val, y_val)

validation_loader = DataLoader(
    validation_dataset,
    batch_size=32,
    shuffle=False,
)


# ---------------------------------------------------------
# Load trained LSTM model
# ---------------------------------------------------------

# Load the saved model checkpoint.
checkpoint = torch.load(
    MODEL_FILE,
    map_location=DEVICE,
)

# Read the model configuration from the checkpoint.
model_config = checkpoint.get(
    "model_config",
    {
        "input_size": 10,
        "hidden_size": 64,
        "num_layers": 2,
        "output_size": 10,
        "dropout": 0.2,
    },
)

# Create the LSTM model.
model = TrafficLSTM(**model_config).to(DEVICE)

# Load the trained weights.
model.load_state_dict(
    checkpoint["model_state_dict"]
)

# Set the model to evaluation mode.
model.eval()


# ---------------------------------------------------------
# Generate predictions
# ---------------------------------------------------------

# Store predictions and actual target values from all batches.
all_predictions = []
all_targets = []

# Disable gradients during evaluation.
with torch.no_grad():

    # Process the validation dataset batch by batch.
    for inputs, targets_batch in validation_loader:

        # Move data to the selected device.
        inputs = inputs.to(DEVICE)
        targets_batch = targets_batch.to(DEVICE)

        # Generate predictions using the LSTM model.
        predictions = model(inputs)

        # Store predictions and targets on the CPU.
        all_predictions.append(
            predictions.cpu().numpy()
        )

        all_targets.append(
            targets_batch.cpu().numpy()
        )


# Combine all batches into NumPy arrays.
predictions_array = np.concatenate(
    all_predictions,
    axis=0,
)

targets_array = np.concatenate(
    all_targets,
    axis=0,
)


# ---------------------------------------------------------
# Calculate prediction errors
# ---------------------------------------------------------

# Calculate the MSE for every validation sample.
sample_mse = np.mean(
    (predictions_array - targets_array) ** 2,
    axis=1,
)

# Create a results DataFrame using the stored metadata.
results = pd.DataFrame(metadata)

# Add the MSE values to the results.
results["mse"] = sample_mse


# ---------------------------------------------------------
# Compare multiple MSE thresholds
# ---------------------------------------------------------

print("\nThreshold Comparison")
print("=" * 75)

# Test each possible threshold.
for threshold in THRESHOLDS_TO_TEST:

    # Predict anomalies when MSE exceeds the current threshold.
    predicted_labels = (
        results["mse"] > threshold
    ).astype(int)

    # Calculate precision for the current threshold.
    threshold_precision = precision_score(
        results["is_anomalous"],
        predicted_labels,
        zero_division=0,
    )

    # Calculate recall for the current threshold.
    threshold_recall = recall_score(
        results["is_anomalous"],
        predicted_labels,
        zero_division=0,
    )

    # Calculate F1-score for the current threshold.
    threshold_f1 = f1_score(
        results["is_anomalous"],
        predicted_labels,
        zero_division=0,
    )

    # Print the metrics for comparison.
    print(
        f"Threshold: {threshold:>2} | "
        f"Precision: {threshold_precision:.4f} | "
        f"Recall: {threshold_recall:.4f} | "
        f"F1-score: {threshold_f1:.4f}"
    )


# ---------------------------------------------------------
# Generate final anomaly predictions
# ---------------------------------------------------------

# Classify samples using the selected main threshold.
results["predicted_anomaly"] = (
    results["mse"] > MSE_THRESHOLD
).astype(int)


# ---------------------------------------------------------
# Calculate MSE statistics
# ---------------------------------------------------------

# Calculate the overall average MSE.
overall_mse = results["mse"].mean()

# Separate normal and anomalous samples using actual labels.
normal_results = results[
    results["is_anomalous"] == 0
]

anomalous_results = results[
    results["is_anomalous"] == 1
]

# Calculate the average MSE for normal samples.
normal_mse = (
    normal_results["mse"].mean()
    if len(normal_results) > 0
    else float("nan")
)

# Calculate the average MSE for anomalous samples.
anomalous_mse = (
    anomalous_results["mse"].mean()
    if len(anomalous_results) > 0
    else float("nan")
)


# ---------------------------------------------------------
# Calculate final anomaly-detection metrics
# ---------------------------------------------------------

# Actual anomaly labels.
y_true = results["is_anomalous"]

# Predicted anomaly labels.
y_pred = results["predicted_anomaly"]

# Calculate accuracy.
accuracy = accuracy_score(
    y_true,
    y_pred,
)

# Calculate precision.
precision = precision_score(
    y_true,
    y_pred,
    zero_division=0,
)

# Calculate recall.
recall = recall_score(
    y_true,
    y_pred,
    zero_division=0,
)

# Calculate F1-score.
f1 = f1_score(
    y_true,
    y_pred,
    zero_division=0,
)

# Calculate the confusion matrix.
# Format:
# [[True Negative, False Positive],
#  [False Negative, True Positive]]
confusion = confusion_matrix(
    y_true,
    y_pred,
    labels=[0, 1],
)


# ---------------------------------------------------------
# Save evaluation results
# ---------------------------------------------------------

# Save actual labels, predicted labels, MSE, and metadata.
results.to_csv(
    OUTPUT_FILE,
    index=False,
)


# ---------------------------------------------------------
# Print final evaluation summary
# ---------------------------------------------------------

print("\nPrediction Error Summary")
print("=" * 40)
print(f"Device: {DEVICE}")
print(f"Validation sequences: {len(results)}")
print(f"Overall validation MSE: {overall_mse:.6f}")
print(f"Normal samples: {len(normal_results)}")
print(f"Normal MSE: {normal_mse:.6f}")
print(f"Anomalous samples: {len(anomalous_results)}")
print(f"Anomalous MSE: {anomalous_mse:.6f}")

print("\nFinal Anomaly Detection Results")
print("=" * 40)
print(f"MSE Threshold: {MSE_THRESHOLD}")
print(f"Accuracy      : {accuracy:.4f}")
print(f"Precision     : {precision:.4f}")
print(f"Recall        : {recall:.4f}")
print(f"F1-score      : {f1:.4f}")

print("\nConfusion Matrix")
print("=" * 40)
print(confusion)

print(f"\nEvaluation results saved to: {OUTPUT_FILE}")