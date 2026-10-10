# Week 5 – Anomaly Detection Prototype Results

## 1. Objective

The objective is to develop and evaluate an initial anomaly detector using network telemetry while the trained LSTM model is being prepared.

## 2. Dataset

- Input: `datasets/processed/qos_features.csv`
- Total input rows: 864
- Labelled anomalous rows: 34
- Labelled normal rows: 830
- Feature tested: `throughput_bps`
- Ground-truth labels: `is_anomalous`

## 3. Methods Evaluated

1. Moving-average prediction with a global residual threshold (k = 3).
2. Moving-average prediction with port-specific residual thresholds (k = 3).
3. Moving-average prediction with port-specific residual thresholds (k = 2).
4. Global throughput threshold using the 95th percentile of labelled normal samples.
5. Port-specific throughput thresholds using the 95th percentile of labelled normal samples.

## 4. Preliminary Results

| Method | TP | FN | FP | TN | Recall | False-positive rate |
|---|---:|---:|---:|---:|---:|---:|
| Global residual, k = 3 | 3 | 31 | 10 | 760 | 8.82% | 1.30% |
| Port-wise residual, k = 3 | 4 | 30 | 24 | 746 | 11.76% | 3.12% |
| Port-wise residual, k = 2 | 5 | 29 | 37 | 733 | 14.71% | 4.81% |
| Global throughput, 95th percentile | 12 | 22 | 41 | 779 | 35.29% | 5.00% |
| Port-wise throughput, 95th percentile | 8 | 26 | 46 | 774 | 23.53% | 5.61% |

## 5. Discussion

The global throughput percentile method achieved the highest recall among the tested preliminary methods. The moving-average residual methods detected fewer labelled anomalies. Port-wise thresholding did not consistently improve performance.

The results show a trade-off between detecting more anomalies and generating false positives.

## 6. Limitations

- The current prototype uses a moving-average baseline rather than the trained LSTM.
- Thresholds were evaluated on the labelled dataset used to calibrate them; independent validation is still required.
- Throughput values vary significantly across ports.
- Some throughput readings are missing and were excluded from the relevant calculations.
- Labelled anomalies represent scripted events and may not represent all real network failures.
- Results must not be interpreted as proof of successful real-time detection.

## 7. Next Steps

1. Integrate Member 4's trained LSTM predictions.
2. Obtain Member 2's independent validation telemetry and real link-failure timestamps.
3. Evaluate detection performance on those separate events.
4. Tune the threshold using validation data and document the final metrics.
