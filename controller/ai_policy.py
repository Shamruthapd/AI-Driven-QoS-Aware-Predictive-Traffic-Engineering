from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class AIPolicyDecision:
    dpid: int
    port: int
    mse: float
    classification: str
    queue_id: int
    inference_latency_ms: float


class AIPolicy:
    MSE_THRESHOLD = 5.0

    NORMAL_QUEUE = 0
    ANOMALOUS_QUEUE = 1

    def evaluate(
        self,
        dpid,
        port,
        prediction_scaled,
        actual_scaled,
        inference_latency_ms,
    ):
        prediction = np.asarray(
            prediction_scaled,
            dtype=np.float64,
        )

        actual = np.asarray(
            actual_scaled,
            dtype=np.float64,
        )

        if prediction.shape != actual.shape:
            raise ValueError(
                "Prediction and actual feature shapes do not match: "
                f"{prediction.shape} != {actual.shape}"
            )

        mse = float(
            np.mean(
                np.square(prediction - actual)
            )
        )

        if mse > self.MSE_THRESHOLD:
            classification = "ANOMALOUS"
            queue_id = self.ANOMALOUS_QUEUE
        else:
            classification = "NORMAL"
            queue_id = self.NORMAL_QUEUE

        return AIPolicyDecision(
            dpid=int(dpid),
            port=int(port),
            mse=mse,
            classification=classification,
            queue_id=queue_id,
            inference_latency_ms=float(
                inference_latency_ms
            ),
        )
