# ============================================================
# smoke_test.py
# Purpose:
#   Check whether the sequence dataset and LSTM model work
#   correctly together before actual model training.
#
# This script checks:
#   1. Dataset loading
#   2. Sequence creation
#   3. Tensor shapes
#   4. DataLoader batching
#   5. LSTM forward pass
#   6. Loss calculation
#   7. Short smoke-test training
#   8. Training-loss curve generation
# ============================================================

import sys
from pathlib import Path

import torch
import matplotlib.pyplot as plt
from torch.utils.data import DataLoader


# ------------------------------------------------------------
# 1. Make the ai-model directory available for imports
# ------------------------------------------------------------

CURRENT_DIR = Path(__file__).resolve().parent

# Add the ai-model folder to Python's import path.
sys.path.append(str(CURRENT_DIR))

# Import the previously created dataset and model classes.
from sequence_dataset import NetworkSequenceDataset
from lstm_model import TrafficLSTM


# ------------------------------------------------------------
# 2. Define paths
# ------------------------------------------------------------

# Move from ai-model/ to the project root directory.
PROJECT_DIR = CURRENT_DIR.parent

# Path to the processed training dataset.
TRAIN_DATA_PATH = (
    PROJECT_DIR
    / "datasets"
    / "processed"
    / "train_scaled.csv"
)

# Directory where the smoke-test loss curve will be saved.
WEEK5_DOCS_DIR = PROJECT_DIR / "docs" / "week5"

# Create the directory if it does not already exist.
WEEK5_DOCS_DIR.mkdir(parents=True, exist_ok=True)

# Output path for the loss curve.
LOSS_CURVE_PATH = WEEK5_DOCS_DIR / "smoke-test-loss-curve.png"


# ------------------------------------------------------------
# 3. Set reproducibility
# ------------------------------------------------------------

# Set a random seed so that the smoke-test results are
# approximately reproducible across different executions.
torch.manual_seed(42)


# ------------------------------------------------------------
# 4. Load the sequence dataset
# ------------------------------------------------------------

print("Loading sequence dataset...")

dataset = NetworkSequenceDataset(
    csv_path=TRAIN_DATA_PATH,
    sequence_length=5,
)

print("Dataset loaded successfully.")


# ------------------------------------------------------------
# 5. Display dataset information
# ------------------------------------------------------------

print("\nDataset information:")
print("Number of generated sequences:", len(dataset))

# Stop early if the dataset does not contain any sequences.
if len(dataset) == 0:
    raise ValueError("The dataset contains no generated sequences.")

# Get the first input-target pair.
first_input, first_target = dataset[0]

print("Input shape:", first_input.shape)
print("Target shape:", first_target.shape)


# ------------------------------------------------------------
# 6. Create a DataLoader
# ------------------------------------------------------------

# The DataLoader groups individual samples into batches.
data_loader = DataLoader(
    dataset,
    batch_size=32,
    shuffle=False,
)

# Get the first batch for shape verification.
input_batch, target_batch = next(iter(data_loader))

print("\nBatch information:")
print("Input batch shape:", input_batch.shape)
print("Target batch shape:", target_batch.shape)


# ------------------------------------------------------------
# 7. Create the LSTM model
# ------------------------------------------------------------

model = TrafficLSTM(
    input_size=10,
    hidden_size=64,
    num_layers=2,
    output_size=10,
)

print("\nLSTM model created successfully.")

# Display the model architecture.
print(model)


# ------------------------------------------------------------
# 8. Perform a forward pass
# ------------------------------------------------------------

# Expected input shape:
#     (batch_size, sequence_length, number_of_features)
#
# Expected output shape:
#     (batch_size, number_of_features)

predictions = model(input_batch)

print("\nForward-pass information:")
print("Prediction shape:", predictions.shape)


# ------------------------------------------------------------
# 9. Calculate an initial sample loss
# ------------------------------------------------------------

# Mean Squared Error measures the difference between the
# predicted next telemetry values and the actual target values.

loss_function = torch.nn.MSELoss()

initial_loss = loss_function(
    predictions,
    target_batch,
)

print("Initial sample loss:", initial_loss.item())


# ------------------------------------------------------------
# 10. Run a short smoke-test training loop
# ------------------------------------------------------------

# This is not the final model training process.
# It only verifies that:
#   - gradients are calculated,
#   - model parameters are updated,
#   - the loss can decrease,
#   - the complete training pipeline works.

optimizer = torch.optim.Adam(
    model.parameters(),
    lr=0.001,
)

# Keep the smoke test short so that it runs quickly.
num_epochs = 10

# Store the average loss from every epoch for plotting.
loss_history = []

print("\nStarting smoke-test training...")

for epoch in range(num_epochs):
    # Put the model into training mode.
    model.train()

    # Reset the total loss for the current epoch.
    total_loss = 0.0

    # Process every batch in the dataset.
    for X_batch, y_batch in data_loader:
        # Clear gradients from the previous batch.
        optimizer.zero_grad()

        # Generate predictions for the current batch.
        batch_predictions = model(X_batch)

        # Calculate the prediction error.
        batch_loss = loss_function(
            batch_predictions,
            y_batch,
        )

        # Calculate gradients using backpropagation.
        batch_loss.backward()

        # Update the model parameters.
        optimizer.step()

        # Add the batch loss to the epoch's total loss.
        total_loss += batch_loss.item()

    # Calculate the average loss for the current epoch.
    average_loss = total_loss / len(data_loader)

    # Store the loss for the graph.
    loss_history.append(average_loss)

    # Print the loss so that decreasing behaviour is visible.
    print(
        f"Epoch {epoch + 1:02d}/{num_epochs}, "
        f"Loss: {average_loss:.6f}"
    )


# ------------------------------------------------------------
# 11. Generate and save the smoke-test loss curve
# ------------------------------------------------------------

# Create a figure for the training-loss curve.
plt.figure(figsize=(8, 5))

# Plot the loss value for each training epoch.
plt.plot(
    range(1, num_epochs + 1),
    loss_history,
    marker="o",
    label="Training Loss",
)

# Add meaningful chart labels.
plt.xlabel("Epoch")
plt.ylabel("MSE Loss")
plt.title("LSTM Smoke-Test Training Loss")

# Display the legend and grid.
plt.legend()
plt.grid(True)

# Save the loss curve for Week 5 documentation.
plt.savefig(
    LOSS_CURVE_PATH,
    dpi=300,
    bbox_inches="tight",
)

# Close the figure to release resources.
plt.close()


# ------------------------------------------------------------
# 12. Final verification
# ------------------------------------------------------------

print("\n========================================")
print("SMOKE TEST COMPLETED SUCCESSFULLY")
print("========================================")

print("Dataset, DataLoader, LSTM, and loss calculation work.")
print("Smoke-test training completed.")
print("Loss curve saved to:")
print(LOSS_CURVE_PATH)

# Display the first and final loss values.
print(f"Initial training loss: {loss_history[0]:.6f}")
print(f"Final training loss:   {loss_history[-1]:.6f}")

# Check whether the final loss is lower than the initial loss.
if loss_history[-1] < loss_history[0]:
    print("Verification: Training loss decreased successfully.")
else:
    print("Warning: Training loss did not decrease.")