
# ============================================================
# sequence_dataset.py
# Purpose:
#   Convert network telemetry data into input-output sequences
#   suitable for training an LSTM model.
#
# Improvements:
#   1. Prevent sequences from crossing long telemetry gaps.
#   2. Preserve invalid rows as sequence boundaries.
#   3. Reject sequences containing missing or infinite features.
#   4. Process each switch-port stream independently.
#   5. Preserve the existing LSTM input and target dimensions.
# ============================================================

import numpy as np
import pandas as pd
import torch

from torch.utils.data import Dataset


# ------------------------------------------------------------
# 1. Features used by the LSTM model
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

class NetworkSequenceDataset(Dataset):

    # Maximum allowed interval between consecutive observations.
    MAX_GAP_SECONDS = 10

    def __init__(
        self,
        csv_path,
        sequence_length=5,
        feature_columns=FEATURE_COLUMNS,
    ):
        """
        Parameters:
            csv_path:
                Location of train_scaled.csv or val_scaled.csv.

            sequence_length:
                Number of previous observations used as input.

            feature_columns:
                Numerical features used by the model.

        Input shape:
            (sequence_length, number_of_features)

        Target shape:
            (number_of_features,)
        """

        self.sequence_length = sequence_length
        self.feature_columns = feature_columns

        if self.sequence_length < 1:
            raise ValueError(
                "sequence_length must be at least 1."
            )

        # ----------------------------------------------------
        # 3. Load the CSV file
        # ----------------------------------------------------

        df = pd.read_csv(csv_path)

        # Check that the CSV contains all required columns.
        required_columns = [
            "timestamp",
            "dpid",
            "port",
        ] + self.feature_columns

        missing_columns = [
            column
            for column in required_columns
            if column not in df.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Missing required columns in {csv_path}: "
                f"{missing_columns}"
            )

        # Parse timestamps as UTC.
        # Invalid timestamps become NaT and break sequences.
        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce",
            utc=True,
        )

        # Convert feature columns to numeric values.
        # Invalid strings become NaN rather than being silently used.
        for column in self.feature_columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

        # ----------------------------------------------------
        # 4. Preserve invalid rows as sequence boundaries
        # ----------------------------------------------------

        # Do NOT drop rows with missing features here.
        # Removing them could make observations on either side
        # appear consecutive when they were not.
        df = df.copy()

        # A row is valid only if its timestamp, switch ID, port,
        # and all model features are usable.
        row_valid = (
            df["timestamp"].notna()
            & df["dpid"].notna()
            & df["port"].notna()
        )

        feature_values = df[
            self.feature_columns
        ].to_numpy(dtype=np.float64)

        row_valid = (
            row_valid.to_numpy()
            & np.isfinite(feature_values).all(axis=1)
        )

        df["_row_valid"] = row_valid

        # Sort observations chronologically within each stream.
        # Rows with invalid timestamps are placed at the end.
        df = df.sort_values(
            by=["dpid", "port", "timestamp"],
            na_position="last",
        ).reset_index(drop=True)

        # ----------------------------------------------------
        # 5. Initialize sequence storage and diagnostics
        # ----------------------------------------------------

        self.inputs = []
        self.targets = []

        self.streams_processed = 0
        self.gaps_detected = 0
        self.invalid_rows = int((~df["_row_valid"]).sum())
        self.sequences_created = 0

        # ----------------------------------------------------
        # 6. Process each switch-port stream separately
        # ----------------------------------------------------

        # Different ports must never be combined into one sequence.
        for (dpid, port), group in df.groupby(
            ["dpid", "port"],
            sort=False,
            dropna=True,
        ):

            self.streams_processed += 1

            group = group.reset_index(drop=True)

            # Extract feature values.
            values = group[
                self.feature_columns
            ].to_numpy(dtype=np.float64)

            # Preserve the original row-validity information.
            values_valid = (
                group["_row_valid"]
                .to_numpy(dtype=bool)
                & np.isfinite(values).all(axis=1)
            )

            # Extract timestamps for checking time gaps.
            timestamps = group[
                "timestamp"
            ]

            # Calculate time differences between consecutive rows.
            gaps = (
                timestamps.diff()
                .dt.total_seconds()
                .to_numpy()
            )

            # A sequence must stop at a long gap, a negative gap,
            # or an invalid timestamp.
            #
            # break_after[i] represents a break at row i,
            # between row i-1 and row i.
            break_after = (
                (gaps > self.MAX_GAP_SECONDS)
                | (gaps < 0)
                | timestamps.isna().to_numpy()
            )

            self.gaps_detected += int(
                np.sum(
                    (gaps > self.MAX_GAP_SECONDS)
                    | (gaps < 0)
                )
            )

            # ------------------------------------------------
            # 7. Generate valid input-target sequences
            # ------------------------------------------------

            # Five input rows require a sixth row for the target
            # when sequence_length=5.
            for start in range(
                len(values) - self.sequence_length
            ):

                end = start + self.sequence_length

                # Input rows are [start, end).
                # The target is row end.
                #
                # Check all input rows AND the target row.
                if not np.all(values_valid[start:end + 1]):
                    continue

                # Reject any window crossing a long time gap.
                # Include the interval immediately before the target.
                if np.any(break_after[start + 1:end + 1]):
                    continue

                # Extract the input sequence and next-row target.
                input_sequence = values[start:end]
                target = values[end]

                self.inputs.append(
                    input_sequence.astype(np.float32)
                )

                self.targets.append(
                    target.astype(np.float32)
                )

                self.sequences_created += 1

        # ----------------------------------------------------
        # 8. Convert lists into PyTorch tensors
        # ----------------------------------------------------

        number_of_features = len(self.feature_columns)

        if self.inputs:
            self.inputs = torch.tensor(
                np.asarray(self.inputs, dtype=np.float32),
                dtype=torch.float32,
            )

            self.targets = torch.tensor(
                np.asarray(self.targets, dtype=np.float32),
                dtype=torch.float32,
            )

        else:
            # Preserve correct dimensions even if no valid windows
            # remain after filtering.
            self.inputs = torch.empty(
                (
                    0,
                    self.sequence_length,
                    number_of_features,
                ),
                dtype=torch.float32,
            )

            self.targets = torch.empty(
                (0, number_of_features),
                dtype=torch.float32,
            )

        # ----------------------------------------------------
        # 9. Print dataset diagnostics
        # ----------------------------------------------------

        print(f"\nDataset: {csv_path}")
        print(f"Switch-port streams: {self.streams_processed}")
        print(f"Invalid rows: {self.invalid_rows}")
        print(f"Long gaps detected: {self.gaps_detected}")
        print(f"Valid sequences: {self.sequences_created}")
        print(f"Input tensor shape: {tuple(self.inputs.shape)}")
        print(f"Target tensor shape: {tuple(self.targets.shape)}")

    # --------------------------------------------------------
    # 10. Return the number of valid sequences
    # --------------------------------------------------------

    def __len__(self):
        return len(self.inputs)

    # --------------------------------------------------------
    # 11. Return one input-target pair
    # --------------------------------------------------------

    def __getitem__(self, index):
        return self.inputs[index], self.targets[index]
