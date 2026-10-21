# Week 7: Real Link-Failure Anomaly Detection Validation

## 1. Objective

Evaluate whether the trained LSTM-based anomaly detector identifies a
network link failure and distinguishes the failure period from restoration
and subsequent normal traffic.

## 2. Test Setup

- Model: Trained LSTM traffic prediction model
- Model checkpoint: `ai-model/checkpoints/lstm_model.pt`
- Feature scaler: `datasets/processed/scaler.pkl`
- Anomaly detection threshold: 5.0
- Input telemetry: `telemetry_real_failure_event.csv`
- Feature history length: 5 observations
- Usable telemetry rows: 12
- Predictions evaluated: 7

The telemetry represents a link failure between switches s1 and s2,
followed by link restoration and recovery traffic.

## 3. Results

| Metric | Result |
|---|---:|
| True positives (TP) | 3 |
| False negatives (FN) | 0 |
| False positives (FP) | 0 |
| True negatives (TN) | 4 |
| Correct predictions | 7/7 |
| Accuracy on this test | 100% |
| Precision on this test | 100% |
| Recall on this test | 100% |
| F1 score on this test | 100% |

These metrics describe only the seven evaluated observations in this
specific event-based test.

## 4. Event-Level Observations

| Event | Actual label | Prediction |
|---|---:|---:|
| Link failure begins | 1 | 1 |
| Link-down outage observation 1 | 1 | 1 |
| Link-down outage observation 2 | 1 | 1 |
| Link restored | 0 | 0 |
| Post-recovery normal traffic 1 | 0 | 0 |
| Post-recovery normal traffic 2 | 0 | 0 |
| Post-recovery normal traffic 3 | 0 | 0 |

Label 1 represents an anomaly; label 0 represents normal traffic.

The model flagged all three failure-period observations. The four
restoration/recovery observations remained below the configured MSE
threshold of 5.0 and were classified as normal.

The largest observed MSE during the failure period was approximately
126479.46. The observed recovery-period MSE values ranged from
approximately 0.0883 to 2.2243.

## 5. Interpretation

The test provides preliminary evidence that the trained model can detect
the supplied link-failure event and distinguish the included recovery
observations at the current threshold.

It does not establish general performance across different failures,
network conditions, switches, or traffic patterns.

## 6. Limitations

1. Only seven predictions were evaluated.
2. The threshold of 5.0 was used as-is and has not been calibrated through
   a systematic threshold-selection procedure.
3. The scaler was saved with scikit-learn 1.7.2 and loaded with version
   1.9.0, producing an InconsistentVersionWarning.
4. The test used manually derived telemetry features. The feature
   engineering and scaling must be checked against the training pipeline
   before treating this as definitive validation.
5. Further tests using independent failure events and normal traffic are
   required before making broader performance claims.

## 7. Output Artifact

The per-observation predictions are recorded in
`real_failure_predictions.csv`.

## 8. Conclusion

In this seven-observation test, the anomaly detector identified all three
labelled failure observations and correctly classified all four labelled
normal restoration/recovery observations. The result is encouraging but
preliminary; threshold calibration, preprocessing consistency, and
validation on additional events remain necessary.
