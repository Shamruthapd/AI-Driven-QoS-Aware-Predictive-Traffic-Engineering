# Week 5 – Anomaly Detection Design

## 1. Objective

Design a detector that identifies abnormal network traffic by comparing
actual telemetry against a prediction baseline. The Week 5 baseline is
a moving average; Week 6 will replace it with Member 4's trained LSTM.

## 2. Chosen Method: Residual-Based Detection

For each switch and port, the detector sorts observations by timestamp
and predicts throughput using the mean of the previous five readings.

Residual:
residual = actual throughput - predicted throughput

The detector estimates the mean and standard deviation of residuals
from samples labelled normal during offline calibration.

Anomaly score:
score = absolute(residual - normal residual mean)

Decision rule:
flag an anomaly when score > k * normal residual standard deviation

Week 5 uses k = 3.0. This is a starting threshold, not a claim that
the detector is optimal.

## 3. Why This Method?

- It compares observed traffic with an expected baseline instead of
  relying only on a fixed raw-throughput threshold.
- Grouping by switch and port prevents the moving average from mixing
  unrelated interfaces.
- A five-reading history is simple to implement while the LSTM is being
  integrated.
- The k-sigma rule provides an interpretable starting threshold.

## 4. Week 5 Placeholder

The prototype is implemented in `anomaly_detector_prototype.py`.
It uses the previous five readings per switch and port as the
moving-average prediction.

For this offline experiment, normal-labelled residuals are used to
estimate the threshold. Since this calibration uses labels from the
evaluated dataset, the result is preliminary and is not an independent
test of generalisation.

## 5. Scripted Week 3 Event Test

The test uses the two event windows recorded in
`docs/week3/anomaly-event-timestamps.md`.

Latest recorded run:
- First event: 6 of 22 telemetry rows were flagged.
- Second event: 2 of 12 telemetry rows were flagged.

At least one row was flagged in each event window, so both events were
detected at event level. However, several anomalous rows were missed.
This does not demonstrate detection of every anomalous sample.

## 6. Week 6 Changes

Replace the moving-average baseline with predictions from the trained
LSTM checkpoint. Ensure input features are scaled using the scaler
fitted during training, use the required feature order and sequence
length, and compare predicted and actual feature vectors.

Calibrate the final threshold on a designated normal calibration set,
then evaluate it on separate labelled data. Do not tune and evaluate
the threshold on the same test events.

Validate against:
- The scripted Week 3 anomaly windows.
- Member 2's documented real link-failure event.
- Normal-condition data to measure false positives.

Record true positives, false negatives, false positives, true negatives,
precision, recall, F1-score, false-positive rate, and the final threshold.
