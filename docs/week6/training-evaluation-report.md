# Week 6 – LSTM Training and Evaluation Report

## 1. Objective

The objective of Week 6 was to train the LSTM model using the complete Week 4 training dataset, evaluate its prediction performance on the original validation dataset, perform independent validation using Member 2's dataset, and prepare the trained model for integration with the other project modules.

The evaluation focuses on:

- Prediction error using MSE and MAE.
- Anomaly detection using MSE thresholding.
- Precision, recall, and F1-score.
- MAPE analysis and documentation of its limitations.
- Independent validation using Member 2's dataset.
- Model handoff and integration readiness.


---

## 2. Dataset Summary

| Parameter | Value |
|---|---:|
| Original processed rows | 864 |
| Removed malformed/incomplete rows | 10 |
| Clean rows | 854 |
| Training rows | 683 |
| Validation rows | 171 |
| Sequence length | 5 |
| Number of input features | 10 |

The LSTM uses the following 10 telemetry features:

1. `rx_packets_delta`
2. `tx_packets_delta`
3. `rx_bytes_delta`
4. `tx_bytes_delta`
5. `rx_dropped_delta`
6. `tx_dropped_delta`
7. `rx_errors_delta`
8. `tx_errors_delta`
9. `throughput_bps`
10. `packet_rate_pps`


---

## 3. LSTM Model Architecture

The LSTM model was implemented using PyTorch.

| Parameter | Value |
|---|---:|
| Input size | 10 |
| Hidden size | 64 |
| Number of LSTM layers | 2 |
| Output size | 10 |
| Sequence length | 5 |
| Dropout | 0.2 |
| Optimizer | Adam |
| Learning rate | 0.001 |
| Loss function | MSE Loss |
| Training epochs | 20 |
| Batch size | 32 |
| Device | CPU |
| Random seed | 42 |

The model receives a sequence of 5 telemetry observations and predicts the next 10-feature telemetry vector.


---

## 4. Week 5 Smoke Test

Before full training, a smoke test was performed to verify the complete LSTM pipeline.

The smoke test successfully verified:

- Dataset loading.
- Sliding-window sequence generation.
- PyTorch Dataset/DataLoader.
- LSTM forward pass.
- Prediction generation.
- Loss calculation.
- Short training process.

### Smoke Test Shapes

| Component | Shape |
|---|---|
| Single input sequence | `(5, 10)` |
| Single target | `(10,)` |
| Batch input | `(32, 5, 10)` |
| Batch target | `(32, 10)` |
| Batch prediction | `(32, 10)` |

The smoke-test training loss decreased approximately from **0.74 to 0.20**, confirming that the model could learn from the prepared telemetry data.

Smoke-test loss curve:

`docs/week5/smoke-test-loss-curve.png`


---

## 5. Sequence Generation

The training and validation datasets were converted into sliding-window sequences.

For a sequence length of 5:

```text
[t1, t2, t3, t4, t5] → predict t6
[t2, t3, t4, t5, t6] → predict t7
[t3, t4, t5, t6, t7] → predict t8