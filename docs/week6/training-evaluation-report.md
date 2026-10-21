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

---

## 10. Updated Gap-Filtered Evaluation

The evaluation pipeline was updated to prevent forecast sequences from crossing long telemetry gaps or invalid observations.

### Evaluation Configuration

| Parameter | Value |
|---|---|
| Maximum allowed time gap | 10 seconds |
| Input sequence length | 5 observations |
| Number of input features | 10 |
| Anomaly MSE threshold | 5.0 |
| Validation rows before cleaning | 171 |
| Valid forecast sequences after filtering | 28 |
| Long gaps detected | 40 |

### Results

| Metric | Result |
|---|---:|
| Overall MSE | 11.749613 |
| Overall MAE | 1.634814 |
| Accuracy | 57.14% |
| Precision | 66.67% |
| Recall | 58.82% |
| F1-score | 0.6250 |

At the provisional MSE threshold of 5.0, the confusion matrix was:

```text
[[6, 5],
 [7, 10]]
```

The evaluation correctly identified 10 anomalous samples, missed 7 anomalous samples, and incorrectly classified 5 normal samples as anomalous.

### Interpretation and Limitations

This evaluation used 28 valid forecast sequences after gap filtering, compared with 121 samples in the earlier evaluation. The results must therefore be reported separately; the two evaluations use different sample sets.

The reported MAPE is extremely high because the telemetry targets include zero or near-zero values and features with different numerical scales. MAPE is not a reliable headline metric for this dataset without an explicitly justified treatment of zero-valued targets.

The MSE threshold of 5.0 remains provisional. Further threshold validation and evaluation on correctly aligned failure-event telemetry are needed before claiming reliable real-world anomaly detection.

The updated evaluation does not establish successful detection of a genuine physical link failure. That validation remains pending until usable, time-aligned observations and a compatible prediction-to-residual integration test are available.
