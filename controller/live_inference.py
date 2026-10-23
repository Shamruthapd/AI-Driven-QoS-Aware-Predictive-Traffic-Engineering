"""
Live LSTM inference for the AI-QoS SDN controller.

Week 6 responsibilities:
- Load the trained LSTM checkpoint.
- Load the fitted feature scaler.
- Convert live OpenFlow port counters into the exact 10 features
  used during model training.
- Maintain a 5-sample sequence for each (DPID, port) stream.
- Run live LSTM inference.
- Measure inference latency.
- Align predictions with the following actual observation.
"""

import importlib.util
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import torch


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODEL_SOURCE_FILE = PROJECT_ROOT / "ai-model" / "lstm_model.py"
MODEL_CHECKPOINT = PROJECT_ROOT / "ai-model" / "checkpoints" / "lstm_model.pt"
SCALER_FILE = PROJECT_ROOT / "datasets" / "processed" / "scaler.pkl"


# ---------------------------------------------------------------------------
# Exact feature order used during model training
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------

def _load_traffic_lstm():
    """
    Dynamically load TrafficLSTM from ai-model/lstm_model.py.

    The project directory is named 'ai-model', so it cannot be imported
    directly using normal Python package syntax.
    """

    if not MODEL_SOURCE_FILE.exists():
        raise FileNotFoundError(
            f"LSTM model source file not found: {MODEL_SOURCE_FILE}"
        )

    spec = importlib.util.spec_from_file_location(
        "lstm_model",
        MODEL_SOURCE_FILE,
    )

    if spec is None or spec.loader is None:
        raise ImportError(
            f"Could not load model module from: {MODEL_SOURCE_FILE}"
        )

    lstm_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lstm_module)

    return lstm_module.TrafficLSTM


TrafficLSTM = _load_traffic_lstm()


class LiveInference:
    """
    Perform live LSTM inference using OpenFlow telemetry.

    Each switch-port pair maintains its own sequence buffer.

    Model input:
        (1, 5, 10)

    Model output:
        10 predicted features in the original feature scale.
    """

    # -----------------------------------------------------------------------
    # Counter columns used to calculate deltas
    # -----------------------------------------------------------------------

    COUNTER_COLUMNS = [
        "rx_packets",
        "tx_packets",
        "rx_bytes",
        "tx_bytes",
        "rx_dropped",
        "tx_dropped",
        "rx_errors",
        "tx_errors",
    ]

    # Sequence length used during training
    SEQUENCE_LENGTH = 5

    def __init__(self):

        # -------------------------------------------------------------------
        # Load scaler
        # -------------------------------------------------------------------

        if not SCALER_FILE.exists():
            raise FileNotFoundError(
                f"Scaler file not found: {SCALER_FILE}"
            )

        self.scaler = joblib.load(SCALER_FILE)

        # -------------------------------------------------------------------
        # Verify scaler feature count
        # -------------------------------------------------------------------

        scaler_feature_count = getattr(
            self.scaler,
            "n_features_in_",
            None,
        )

        if scaler_feature_count is not None:
            if scaler_feature_count != len(FEATURE_COLUMNS):
                raise ValueError(
                    "Scaler feature count does not match live feature count: "
                    f"{scaler_feature_count} != {len(FEATURE_COLUMNS)}"
                )

        # -------------------------------------------------------------------
        # Load trained LSTM checkpoint
        # -------------------------------------------------------------------

        if not MODEL_CHECKPOINT.exists():
            raise FileNotFoundError(
                f"LSTM checkpoint not found: {MODEL_CHECKPOINT}"
            )

        checkpoint = torch.load(
            MODEL_CHECKPOINT,
            map_location="cpu",
        )

        # -------------------------------------------------------------------
        # Reconstruct model using checkpoint configuration
        # -------------------------------------------------------------------

        input_size = checkpoint.get(
            "input_size",
            len(FEATURE_COLUMNS),
        )

        hidden_size = checkpoint.get(
            "hidden_size",
            64,
        )

        num_layers = checkpoint.get(
            "num_layers",
            2,
        )

        output_size = checkpoint.get(
            "output_size",
            len(FEATURE_COLUMNS),
        )

        dropout = checkpoint.get(
            "dropout",
            0.2,
        )

        self.model = TrafficLSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            output_size=output_size,
            dropout=dropout,
        )

        self.model.load_state_dict(
            checkpoint["model_state_dict"]
        )

        self.model.eval()

        # -------------------------------------------------------------------
        # Per-switch-port state
        # -------------------------------------------------------------------

        # Stores the LAST observed raw counters.
        #
        # Key:
        #     (dpid, port)
        #
        # Value:
        #     dictionary containing the previous counters.
        self.previous_counters = {}

        # Stores the timestamp corresponding to previous_counters.
        self.previous_timestamps = {}

        # Each switch-port has its own 5-sample scaled feature sequence.
        self.buffers = defaultdict(
            lambda: deque(
                maxlen=self.SEQUENCE_LENGTH
            )
        )

        # Stores predictions until the next observation arrives.
        #
        # This allows:
        #
        # prediction at time t
        #        ↓
        # actual observation at time t+1
        #
        # to be aligned in predictions.csv.
        self.pending_predictions = {}

        print("LiveInference initialized")

    # -----------------------------------------------------------------------
    # Timestamp handling
    # -----------------------------------------------------------------------

    @staticmethod
    def _parse_timestamp(timestamp_value):
        """
        Convert a timestamp into a timezone-aware datetime.
        """

        if isinstance(timestamp_value, datetime):

            if timestamp_value.tzinfo is None:
                return timestamp_value.replace(
                    tzinfo=timezone.utc
                )

            return timestamp_value

        if timestamp_value is None:
            return None

        timestamp_string = str(timestamp_value)

        try:
            parsed = datetime.fromisoformat(
                timestamp_string.replace("Z", "+00:00")
            )
        except ValueError:
            return None

        if parsed.tzinfo is None:
            parsed = parsed.replace(
                tzinfo=timezone.utc
            )

        return parsed

    # -----------------------------------------------------------------------
    # Numeric conversion
    # -----------------------------------------------------------------------

    @staticmethod
    def _to_float(value):
        """
        Safely convert telemetry values to float.
        """

        if value is None:
            return 0.0

        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    # -----------------------------------------------------------------------
    # Feature calculation
    # -----------------------------------------------------------------------

    def _calculate_features(self, row):
        """
        Calculate the exact 10 features used during training.

        Training definitions from scripts/process_telemetry.py:

            throughput_bps =
                tx_bytes_delta * 8 / interval_seconds

            packet_rate_pps =
                tx_packets_delta / interval_seconds
        """

        dpid = int(row["dpid"])
        port = int(row["port"])

        key = (dpid, port)

        current_timestamp = self._parse_timestamp(
            row["timestamp"]
        )

        if current_timestamp is None:
            return None

        # -------------------------------------------------------------------
        # Read current OpenFlow counters
        # -------------------------------------------------------------------

        current_counters = {}

        for column in self.COUNTER_COLUMNS:
            current_counters[column] = self._to_float(
                row.get(column, 0)
            )

        # -------------------------------------------------------------------
        # First observation for this switch-port
        #
        # We cannot calculate a delta yet because there is no previous
        # observation.
        # -------------------------------------------------------------------

        if key not in self.previous_counters:

            self.previous_counters[key] = current_counters.copy()

            self.previous_timestamps[key] = current_timestamp

            return None

        # -------------------------------------------------------------------
        # IMPORTANT:
        #
        # Save the OLD counters BEFORE replacing them.
        # -------------------------------------------------------------------

        previous_counters = self.previous_counters[key]

        previous_timestamp = self.previous_timestamps[key]

        # -------------------------------------------------------------------
        # Calculate elapsed time
        # -------------------------------------------------------------------

        elapsed_seconds = (
            current_timestamp - previous_timestamp
        ).total_seconds()

        # -------------------------------------------------------------------
        # Calculate counter deltas
        #
        # current - previous
        # -------------------------------------------------------------------

        deltas = {}

        for column in self.COUNTER_COLUMNS:

            delta_column = f"{column}_delta"

            delta_value = (
                current_counters[column]
                - previous_counters[column]
            )

            # Handle counter reset/wraparound.
            if delta_value < 0:
                delta_value = 0.0

            deltas[delta_column] = delta_value

        # -------------------------------------------------------------------
        # NOW update the previous state.
        #
        # This must happen AFTER delta calculation.
        # -------------------------------------------------------------------

        self.previous_counters[key] = current_counters.copy()

        self.previous_timestamps[key] = current_timestamp

        # -------------------------------------------------------------------
        # Invalid interval
        # -------------------------------------------------------------------

        if elapsed_seconds <= 0:
            return None

        # -------------------------------------------------------------------
        # Derived traffic features
        #
        # These MUST match the training pipeline.
        # -------------------------------------------------------------------

        throughput_bps = (
            deltas["tx_bytes_delta"]
            * 8.0
            / elapsed_seconds
        )

        packet_rate_pps = (
            deltas["tx_packets_delta"]
            / elapsed_seconds
        )

        # -------------------------------------------------------------------
        # Exact 10-feature vector
        # -------------------------------------------------------------------

        features = np.array(
            [
                deltas["rx_packets_delta"],
                deltas["tx_packets_delta"],
                deltas["rx_bytes_delta"],
                deltas["tx_bytes_delta"],
                deltas["rx_dropped_delta"],
                deltas["tx_dropped_delta"],
                deltas["rx_errors_delta"],
                deltas["tx_errors_delta"],
                throughput_bps,
                packet_rate_pps,
            ],
            dtype=np.float64,
        )

        return features

    # -----------------------------------------------------------------------
    # Main inference function
    # -----------------------------------------------------------------------

    def process_row(self, row):
        """
        Process one live telemetry observation.

        Returns:
            None if a sequence is not ready.

            Dictionary containing prediction information when inference
            is performed.
        """

        dpid = int(row["dpid"])
        port = int(row["port"])

        # -------------------------------------------------------------------
        # Ignore OpenFlow LOCAL port
        # -------------------------------------------------------------------

        if port == 4294967294:
            return None

        key = (dpid, port)

        # -------------------------------------------------------------------
        # Retrieve prediction made from the previous sequence.
        #
        # The current observation becomes the actual value corresponding
        # to that previous prediction.
        # -------------------------------------------------------------------

        completed_prediction = self.pending_predictions.pop(
            key,
            None,
        )

        # -------------------------------------------------------------------
        # Calculate current features
        # -------------------------------------------------------------------

        features = self._calculate_features(row)

        if features is None:
            return None

        # -------------------------------------------------------------------
        # Scale using the SAME scaler used during training
        # -------------------------------------------------------------------

        scaled_features = self.scaler.transform(
            features.reshape(1, -1)
        )[0]

        # -------------------------------------------------------------------
        # Add scaled feature vector to switch-port sequence
        # -------------------------------------------------------------------

        self.buffers[key].append(
            scaled_features
        )

        # -------------------------------------------------------------------
        # Wait until 5 observations are available
        # -------------------------------------------------------------------

        if len(self.buffers[key]) < self.SEQUENCE_LENGTH:
            return None

        # -------------------------------------------------------------------
        # Create LSTM input
        #
        # Buffer:
        #     (5, 10)
        #
        # Batch dimension:
        #     (1, 5, 10)
        # -------------------------------------------------------------------

        sequence = np.array(
            self.buffers[key],
            dtype=np.float32,
        )

        input_tensor = torch.tensor(
            sequence,
            dtype=torch.float32,
        ).unsqueeze(0)

        # -------------------------------------------------------------------
        # Run inference and measure latency
        # -------------------------------------------------------------------

        inference_start = time.perf_counter()

        with torch.no_grad():
            prediction_scaled = self.model(
                input_tensor
            )

        inference_latency_ms = (
            time.perf_counter()
            - inference_start
        ) * 1000.0

        # -------------------------------------------------------------------
        # Convert prediction back to original feature scale
        # -------------------------------------------------------------------

        prediction_scaled_numpy = (
            prediction_scaled
            .cpu()
            .numpy()
        )

        prediction = self.scaler.inverse_transform(
            prediction_scaled_numpy
        )[0]

        # -------------------------------------------------------------------
        # Current actual feature vector
        # -------------------------------------------------------------------

        actual = features.copy()

        # -------------------------------------------------------------------
        # Save current prediction for alignment with the next observation
        # -------------------------------------------------------------------

        self.pending_predictions[key] = {
            "prediction": prediction.copy(),
            "timestamp": self._parse_timestamp(
                row["timestamp"]
            ),
            "inference_latency_ms": inference_latency_ms,
        }

        # -------------------------------------------------------------------
        # Return inference result
        # -------------------------------------------------------------------

        return {
            "dpid": dpid,
            "port": port,
            "input_shape": tuple(
                input_tensor.shape
            ),
            "prediction": prediction,
            "actual": actual,
            "inference_latency_ms": inference_latency_ms,
            "completed_prediction": completed_prediction,
            "actual_timestamp": self._parse_timestamp(
                row["timestamp"]
            ),
        }
