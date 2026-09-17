# ============================================================
# train_lstm.py
# Purpose:
#   Train the LSTM model using the prepared network telemetry
#   sequences and save the trained model checkpoint.
# ============================================================


from pathlib import Path
import sys

import torch
import torch.nn as nn
from torch.utils.data import DataLoader


# ------------------------------------------------------------
# 1. Import our dataset and model classes
# ------------------------------------------------------------

# Get the directory containing this script.
CURRENT_DIR = Path(__file__).resolve().parent

# Make sure Python can import files from ai-model/.
sys.path.append(str(CURRENT_DIR))

from sequence_dataset import NetworkSequenceDataset
from lstm_model import TrafficLSTM


# ------------------------------------------------------------
# 2. Define project and dataset paths
# ------------------------------------------------------------

PROJECT_DIR = CURRENT_DIR.parent

TRAIN_DATA_PATH = (
    PROJECT_DIR
    / "datasets"
    / "processed"
    / "train_scaled.csv"
)

CHECKPOINT_DIR = CURRENT_DIR / "checkpoints"

# Create the checkpoints directory if it does not exist.
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = CHECKPOINT_DIR / "lstm_model.pt"


# ------------------------------------------------------------
# 3. Define training configuration
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


# ------------------------------------------------------------
# 4. Load the training dataset
# ------------------------------------------------------------

print("\nLoading training dataset...")

train_dataset = NetworkSequenceDataset(
    csv_path=TRAIN_DATA_PATH,
    sequence_length=SEQUENCE_LENGTH,
)

print("Generated training sequences:", len(train_dataset))


# ------------------------------------------------------------
# 5. Create the DataLoader
# ------------------------------------------------------------

# DataLoader divides the dataset into smaller batches.
# Each batch contains 32 sequences.
#
# shuffle=True allows the model to see training samples
# in a different order during each epoch.
# The samples themselves still preserve the time order
# inside each individual sequence.
# ------------------------------------------------------------

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
)


# ------------------------------------------------------------
# 6. Create the LSTM model
# ------------------------------------------------------------

model = TrafficLSTM(
    input_size=10,
    hidden_size=64,
    num_layers=2,
    output_size=10,
    dropout=0.2,
)

# Move the model to the selected device.
model = model.to(DEVICE)


# ------------------------------------------------------------
# 7. Define loss function and optimizer
# ------------------------------------------------------------

# MSELoss measures the difference between the predicted
# telemetry values and the actual next telemetry values.
loss_function = nn.MSELoss()

# Adam updates the model's internal weights based on
# the calculated gradients.
optimizer = torch.optim.Adam(
    model.parameters(),
    lr=LEARNING_RATE,
)


# ------------------------------------------------------------
# 8. Start the training loop
# ------------------------------------------------------------

print("\nStarting LSTM training...")
print("=" * 50)

for epoch in range(EPOCHS):

    # Put the model into training mode.
    model.train()

    total_loss = 0.0

    # Process one batch at a time.
    for input_batch, target_batch in train_loader:

        # Move data to CPU or GPU.
        input_batch = input_batch.to(DEVICE)
        target_batch = target_batch.to(DEVICE)

        # Clear gradients from the previous batch.
        optimizer.zero_grad()

        # Forward pass:
        # Generate predictions for the next observation.
        predictions = model(input_batch)

        # Calculate prediction error.
        loss = loss_function(
            predictions,
            target_batch,
        )

        # Backward pass:
        # Calculate gradients for the model parameters.
        loss.backward()

        # Update model parameters.
        optimizer.step()

        # Add this batch's loss to the total epoch loss.
        total_loss += loss.item()

    # Calculate the average loss for this epoch.
    average_loss = total_loss / len(train_loader)

    print(
        f"Epoch [{epoch + 1:02d}/{EPOCHS}] "
        f"Training Loss: {average_loss:.6f}"
    )


# ------------------------------------------------------------
# 9. Save the trained model
# ------------------------------------------------------------

# Save the model's learned weights and configuration.
torch.save(
    {
        "model_state_dict": model.state_dict(),
        "input_size": 10,
        "hidden_size": 64,
        "num_layers": 2,
        "output_size": 10,
        "dropout": 0.2,
        "sequence_length": SEQUENCE_LENGTH,
    },
    MODEL_PATH,
)

print("\n" + "=" * 50)
print("TRAINING COMPLETED")
print("=" * 50)
print("Trained model saved at:")
print(MODEL_PATH)