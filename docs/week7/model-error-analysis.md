# Week 7 – Member 4: LSTM Error Analysis

## 1. Objective

Analyze the existing LSTM validation performance and determine whether its predicted throughput can be directly used as a 0–100% network utilization signal for QoS-aware traffic engineering.

## 2. Existing LSTM Baseline

Validation evaluation produced:

- Validation sequences: 121
- Overall MSE: 37.632519
- Normal-sample MSE: 6.959243
- Anomalous-sample MSE: 113.001137
- Precision: 0.4600
- Recall: 0.6571
- F1-score: 0.5412
- Current MSE threshold: 5

At threshold 5, the confusion matrix was:

- True Negative: 59
- False Positive: 27
- False Negative: 12
- True Positive: 23

## 3. Threshold Analysis

| MSE Threshold | Precision | Recall | F1-score |
|---:|---:|---:|---:|
| 5 | 0.4600 | 0.6571 | 0.5412 |
| 10 | 0.4667 | 0.6000 | 0.5250 |
| 15 | 0.4667 | 0.6000 | 0.5250 |
| 20 | 0.4815 | 0.3714 | 0.4194 |
| 25 | 0.5455 | 0.3429 | 0.4211 |
| 30 | 0.5294 | 0.2571 | 0.3462 |
| 40 | 1.0000 | 0.2000 | 0.3333 |
| 50 | 1.0000 | 0.1429 | 0.2500 |

Threshold 5 provides the highest F1-score among the tested thresholds, although false positives remain significant.

## 4. Training and Validation Distribution

The training dataset contains:

- Normal samples: 679
- Anomalous samples: 4
- Total samples: 683

The validation dataset contains:

- Normal samples: 110
- Anomalous samples: 61
- Total samples: 171

Therefore, the LSTM was trained predominantly on normal traffic.

The four anomalous training samples had throughput values between approximately 100 Mbps and 161 Mbps.

## 5. Throughput Distribution

### Training

- Mean throughput: 1.451 Mbps
- Maximum throughput: 160.794 Mbps

### Validation

- Mean throughput: 55.824 Mbps
- Maximum throughput: 745.942 Mbps

For validation normal traffic:

- Mean: 7.945 Mbps
- Maximum: 70.667 Mbps

For validation anomalous traffic:

- Mean: 142.162 Mbps
- Maximum: 745.942 Mbps

The validation anomalies therefore contain traffic levels substantially outside the training distribution.

## 6. Predicted Throughput Analysis

The LSTM predicts all 10 telemetry features. The predicted throughput was inverse-transformed using the training StandardScaler before analysis.

Across 121 validation sequences:

- Actual mean throughput: 54.162 Mbps
- Predicted mean throughput: 33.267 Mbps
- Throughput MAE: 45.058 Mbps
- Throughput RMSE: 124.170 Mbps
- Maximum absolute error: 649.655 Mbps

Predicted throughput by validation class:

| Class | Mean Predicted Throughput |
|---|---:|
| Normal | 22.450 Mbps |
| Anomalous | 59.844 Mbps |

The model therefore shows separation between normal and anomalous predicted throughput, but the prediction error is too large for the raw predicted throughput to be treated as a reliable utilization percentage.

## 7. QoS Capacity Reference

The Week 7 OVS QoS configuration defines:

- Link capacity: 10 Mbps
- Queue 0 maximum rate: 4 Mbps
- Queue 1 minimum rate: 8 Mbps
- Queue 1 maximum rate: 10 Mbps

The QoS configuration provides the appropriate engineering reference for future utilization calibration.

However, the current LSTM predicted-throughput signal should not yet be directly mapped to 0–100% utilization because its validation error is high and the validation traffic contains values far outside the training distribution.

## 8. Member 4 Conclusion

The current LSTM is useful as a predictive/anomaly-detection baseline, but its raw predicted throughput is not yet sufficiently accurate to serve as the final utilization-control signal.

The Week 7 findings indicate:

1. The model is trained with very few anomalous samples.
2. Validation contains substantially higher traffic levels than the training data.
3. Severe out-of-distribution traffic produces large prediction errors.
4. MSE threshold 5 remains the best tested anomaly-detection threshold by F1-score.
5. Direct conversion of raw LSTM throughput predictions into a 0–100% utilization signal is not recommended at this stage.
6. The configured 10 Mbps QoS link capacity should be used as the engineering reference for future calibration.
7. Further validation/retraining with representative congestion samples should be considered before deploying the predicted utilization signal for automatic QoS decisions.