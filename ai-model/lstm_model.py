# ============================================================
# lstm_model.py
# Purpose:
#   Define the LSTM neural network used to predict the next
#   network telemetry observation.
#
# Input:
#   A sequence of previous telemetry observations
#
# Output:
#   The predicted next telemetry observation
# ============================================================


import torch
import torch.nn as nn


# ------------------------------------------------------------
# 1. Define the LSTM model class
# ------------------------------------------------------------
# nn.Module is the base class for all PyTorch neural networks.
# By inheriting from nn.Module, our model gets useful features
# such as parameter management and training support.
# ------------------------------------------------------------

class TrafficLSTM(nn.Module):

    def __init__(
        self,
        input_size=10,
        hidden_size=64,
        num_layers=2,
        output_size=10,
        dropout=0.2,
    ):
        """
        Parameters:

            input_size:
                Number of input features at each time step.
                We have 10 telemetry features.

            hidden_size:
                Number of values stored in the LSTM hidden state.
                A value of 64 gives the model enough capacity
                to learn traffic patterns.

            num_layers:
                Number of stacked LSTM layers.
                Here, we use 2 LSTM layers.

            output_size:
                Number of values predicted by the model.
                We predict all 10 telemetry features.

            dropout:
                Helps reduce overfitting between LSTM layers.
        """

        # Call the constructor of nn.Module.
        super().__init__()

        # ----------------------------------------------------
        # 2. Define the LSTM layer
        # ----------------------------------------------------
        # batch_first=True means the input shape is:
        #
        #     (batch_size, sequence_length, input_size)
        #
        # Example:
        #     (32, 5, 10)
        #
        # This means:
        #     32 sequences in one batch
        #     5 time steps per sequence
        #     10 features at every time step
        # ----------------------------------------------------

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,

            # Dropout is applied only when there are
            # multiple LSTM layers.
            dropout=dropout if num_layers > 1 else 0.0,
        )

        # ----------------------------------------------------
        # 3. Define the fully connected output layer
        # ----------------------------------------------------
        # The final LSTM output has 64 hidden values.
        # The Linear layer converts those 64 values into
        # 10 predicted telemetry values.
        # ----------------------------------------------------

        self.fc = nn.Linear(
            hidden_size,
            output_size,
        )

    # --------------------------------------------------------
    # 4. Define the forward pass
    # --------------------------------------------------------
    # The forward method describes how input data moves
    # through the network.
    # --------------------------------------------------------

    def forward(self, x):
        """
        Input:
            x shape = (batch_size, sequence_length, input_size)

        Output:
            prediction shape = (batch_size, output_size)
        """

        # ----------------------------------------------------
        # 5. Pass the input sequence through the LSTM
        # ----------------------------------------------------
        # lstm_output contains the hidden representation
        # for every time step.
        #
        # The second returned value contains the final hidden
        # and cell states, which we do not need directly here.
        # ----------------------------------------------------

        lstm_output, _ = self.lstm(x)

        # ----------------------------------------------------
        # 6. Select the output from the final time step
        # ----------------------------------------------------
        # If the sequence contains 5 time steps, we use the
        # fifth time step's representation.
        #
        # Shape changes from:
        #
        #     (batch_size, 5, 64)
        #
        # to:
        #
        #     (batch_size, 64)
        # ----------------------------------------------------

        last_output = lstm_output[:, -1, :]

        # ----------------------------------------------------
        # 7. Generate the final prediction
        # ----------------------------------------------------
        # The fully connected layer converts the 64 hidden
        # values into 10 predicted telemetry features.
        # ----------------------------------------------------

        prediction = self.fc(last_output)

        return prediction