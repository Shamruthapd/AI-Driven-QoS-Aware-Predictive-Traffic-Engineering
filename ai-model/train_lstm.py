# ============================================================
# train_lstm.py
#
# Purpose:
#   Train the LSTM model using the prepared network telemetry
#   sequences, record the training loss, generate a loss curve,
#   and save the trained model checkpoint.
# ============================================================

from pathlib import Path
import sys
import random

import numpy as np
import torch
import torch.nn as nn
import matplotlib.pyplot as plt
from torch.utils.data import DataLoader


# ------------------------------------------------------------
# 1. Reproducibility
# ------------------------------------------------------------

# Set a fixed seed so the training run is reproducible.
SEED = 42

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

# Apply the seed to CUDA if a GPU is available.
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)


# ------------------------------------------------------------
# 2. Import dataset and model classes
# ------------------------------------------------------------

# Get the directory containing this script.
CURRENT_DIR = Path(__file__).resolve().parent

# Make sure Python can import files from ai-model/.
sys.path.append(str(CURRENT_DIR))

from sequence_dataset import NetworkSequenceDataset
from lstm_model import TrafficLSTM


# ------------------------------------------------------------
# 3. Define project and dataset paths
# ------------------------------------------------------------

PROJECT_DIR = CURRENT_DIR.parent

TRAIN_DATA_PATH = (
    PROJECT_DIR
    / "datasets"
    / "processed"
    / "train_scaled.csv"
)

CHECKPOINT_DIR = CURRENT_DIR / "checkpoints"

# Create the checkpoint directory if it does not exist.
CHECKPOINT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

MODEL_PATH = CHECKPOINT_DIR / "lstm_model.pt"

# Create the Week 6 documentation directory.
WEEK6_DOCS_DIR = (
    PROJECT_DIR
    / "docs"
    / "week6"
)

WEEK6_DOCS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

# Path where the full-training loss curve will be saved.
LOSS_CURVE_PATH = (
    WEEK6_DOCS_DIR
    / "full-training-loss-curve.png"
)


# ------------------------------------------------------------
# 4. Define training configuration
# ------------------------------------------------------------

SEQUENCE_LENGTH = 5
BATCH_SIZE = 32
EPOCHS = 20
LEARNING_RATE = 0.001

# Use GPU if available; otherwise use CPU.
DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("Training device:", DEVICE)
print("Random seed:", SEED)


# ------------------------------------------------------------
# 5. Load training dataset
# ------------------------------------------------------------

print("\nLoading training dataset...")

train_dataset = NetworkSequenceDataset(
    csv_path=TRAIN_DATA_PATH,
    sequence_length=SEQUENCE_LENGTH,
)

print(
    "Generated training sequences:",
    len(train_dataset),
)


# ------------------------------------------------------------
# 6. Create DataLoader
# ------------------------------------------------------------

# DataLoader divides the dataset into batches.
train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
)


# ------------------------------------------------------------
# 7. Create LSTM model
# ------------------------------------------------------------

model_config = {
    "input_size": 10,
    "hidden_size": 64,
    "num_layers": 2,
    "output_size": 10,
    "dropout": 0.2,
}

# Create the LSTM using the defined configuration.
model = TrafficLSTM(
    **model_config
)

# Move the model to CPU or GPU.
model = model.to(DEVICE)


# ------------------------------------------------------------
# 8. Define loss function and optimizer
# ------------------------------------------------------------

# MSE measures the difference between predicted and actual
# scaled telemetry values.
loss_function = nn.MSELoss()

# Adam updates the model parameters using the gradients.
optimizer = torch.optim.Adam(
    model.parameters(),
    lr=LEARNING_RATE,
)


# ------------------------------------------------------------
# 9. Start training
# ------------------------------------------------------------

print("\nStarting LSTM training...")
print("=" * 60)

# Store the average loss from every epoch.
training_losses = []

for epoch in range(EPOCHS):

    # Put the model into training mode.
    model.train()

    total_loss = 0.0

    # Process one batch at a time.
    for input_batch, target_batch in train_loader:

        # Move the batch to CPU or GPU.
        input_batch = input_batch.to(DEVICE)
        target_batch = target_batch.to(DEVICE)

        # Clear gradients from the previous batch.
        optimizer.zero_grad()

        # Forward pass.
        predictions = model(input_batch)

        # Calculate prediction error.
        loss = loss_function(
            predictions,
            target_batch,
        )

        # Backward pass.
        loss.backward()

        # Update model parameters.
        optimizer.step()

        # Add this batch loss to the epoch total.
        total_loss += loss.item()

    # Calculate average loss for this epoch.
    average_loss = (
        total_loss / len(train_loader)
    )

    # Store the loss for the loss curve.
    training_losses.append(
        average_loss
    )

    print(
        f"Epoch [{epoch + 1:02d}/{EPOCHS}] "
        f"Training Loss: {average_loss:.6f}"
    )


# ------------------------------------------------------------
# 10. Generate full-training loss curve
# ------------------------------------------------------------

plt.figure(figsize=(8, 5))

# Plot the loss recorded after every training epoch.
plt.plot(
    range(1, EPOCHS + 1),
    training_losses,
    marker="o",
)

plt.xlabel("Epoch")
plt.ylabel("Training MSE Loss")
plt.title("LSTM Full Training Loss Curve")

plt.grid(True)

# Save the curve for the Week 6 report.
plt.savefig(
    LOSS_CURVE_PATH,
    dpi=200,
    bbox_inches="tight",
)

plt.close()

print("\nFull-training loss curve saved to:")
print(LOSS_CURVE_PATH)


# ------------------------------------------------------------
# 11. Save trained model checkpoint
# ------------------------------------------------------------

# Save the trained weights, model configuration, and
# sequence length so the checkpoint can be reused later.
torch.save(
    {
        "model_state_dict": model.state_dict(),
        "model_config": model_config,
        "sequence_length": SEQUENCE_LENGTH,
        "training_config": {
            "batch_size": BATCH_SIZE,
            "epochs": EPOCHS,
            "learning_rate": LEARNING_RATE,
            "seed": SEED,
        },
        "training_losses": training_losses,
    },
    MODEL_PATH,
)


# ------------------------------------------------------------
# 12. Print completion information
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("TRAINING COMPLETED")
print("=" * 60)

print("Final training loss:")
print(f"{training_losses[-1]:.6f}")

print("\nTrained model saved at:")
print(MODEL_PATH)