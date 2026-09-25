# ============================================================
# sequence_dataset.py
# Purpose:
#   Convert network telemetry data into input-output sequences
#   suitable for training an LSTM model.
#
# Example:
#   Input  -> Previous 5 observations
#   Target -> The next observation
# ============================================================


import numpy as np
import pandas as pd
import torch

from torch.utils.data import Dataset


# ------------------------------------------------------------
# 1. Features used by the LSTM model
# ------------------------------------------------------------
# These are the numerical network telemetry features.
#
# We do not include:
#   - timestamp: Time information, not a direct traffic feature
#   - dpid: Switch identifier
#   - port: Port identifier
#   - is_anomalous: Used later for evaluation, not model input
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


# ------------------------------------------------------------
# 2. Dataset class
# ------------------------------------------------------------
# PyTorch's Dataset class allows us to access the data one
# sample at a time using:
#
#     dataset[index]
#
# It also works with PyTorch's DataLoader during training.
# ------------------------------------------------------------

class NetworkSequenceDataset(Dataset):

    def __init__(
        self,
        csv_path,
        sequence_length=5,
        feature_columns=FEATURE_COLUMNS,
    ):
        """
        Parameters:
            csv_path:
                Location of train_scaled.csv or val_scaled.csv

            sequence_length:
                Number of previous observations used as input.
                Here, the default is 5.

            feature_columns:
                Numerical features used by the model.
        """

        self.sequence_length = sequence_length
        self.feature_columns = feature_columns

        # ----------------------------------------------------
        # 3. Load the CSV file
        # ----------------------------------------------------
        df = pd.read_csv(csv_path)

        # Convert timestamp text into a datetime object.
        # Invalid timestamps become NaT.
        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce",
        )

        # ----------------------------------------------------
        # 4. Remove rows with missing required values
        # ----------------------------------------------------
        # A row is useful only if it has:
        #   - timestamp
        #   - dpid
        #   - port
        #   - all required telemetry features
        # ----------------------------------------------------

        required_columns = [
            "timestamp",
            "dpid",
            "port",
        ] + self.feature_columns

        df = df.dropna(subset=required_columns)

        # ----------------------------------------------------
        # 5. Sort the data
        # ----------------------------------------------------
        # We sort first by switch, then port, then timestamp.
        #
        # This ensures that observations belonging to the same
        # network stream appear in chronological order.
        # ----------------------------------------------------

        df = df.sort_values(
            by=["dpid", "port", "timestamp"]
        ).reset_index(drop=True)

        # Lists to store all generated input sequences
        # and their corresponding target values.
        self.inputs = []
        self.targets = []

        # ----------------------------------------------------
        # 6. Process each switch-port stream separately
        # ----------------------------------------------------
        # A sequence must not combine:
        #
        #   dpid 1, port 1
        #   dpid 1, port 2
        #
        # because they represent different network streams.
        # ----------------------------------------------------

        for (dpid, port), group in df.groupby(["dpid", "port"]):

            # Extract only the numerical feature columns.
            # Convert them into a NumPy array of float32 values.
            values = group[self.feature_columns].to_numpy(
                dtype=np.float32
            )

            # If a stream has 5 or fewer rows, it cannot create
            # a sequence of 5 inputs plus one target.
            if len(values) <= self.sequence_length:
                continue

            # ------------------------------------------------
            # 7. Create sliding-window sequences
            # ------------------------------------------------
            # For sequence_length = 5:
            #
            # Input 1: rows 0,1,2,3,4 -> Target: row 5
            # Input 2: rows 1,2,3,4,5 -> Target: row 6
            # Input 3: rows 2,3,4,5,6 -> Target: row 7
            #
            # This is called a sliding window.
            # ------------------------------------------------

            for index in range(
                len(values) - self.sequence_length
            ):

                # Select the previous 5 observations.
                input_sequence = values[
                    index:index + self.sequence_length
                ]

                # Select the next observation as the target.
                target = values[
                    index + self.sequence_length
                ]

                # Store the generated sequence and target.
                self.inputs.append(input_sequence)
                self.targets.append(target)

        # ----------------------------------------------------
        # 8. Convert the generated data into PyTorch tensors
        # ----------------------------------------------------
        # Input tensor shape:
        #     (number_of_sequences, sequence_length, 10)
        #
        # Target tensor shape:
        #     (number_of_sequences, 10)
        # ----------------------------------------------------

        self.inputs = torch.tensor(
            np.array(self.inputs),
            dtype=torch.float32,
        )

        self.targets = torch.tensor(
            np.array(self.targets),
            dtype=torch.float32,
        )

    # --------------------------------------------------------
    # 9. Return the total number of generated samples
    # --------------------------------------------------------

    def __len__(self):
        return len(self.inputs)

    # --------------------------------------------------------
    # 10. Return one input-target pair
    # --------------------------------------------------------
    # This is called by the DataLoader during training.
    # --------------------------------------------------------

    def __getitem__(self, index):
        return self.inputs[index], self.targets[index]