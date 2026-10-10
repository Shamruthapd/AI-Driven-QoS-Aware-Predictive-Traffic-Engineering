# Week 6 – Anomaly Detection Evaluation

## 1. Objective

Integrate the trained LSTM into the anomaly detector, evaluate detection
performance, and document the results and remaining validation work.

## 2. Implementation

The detector is implemented in `ai-model/anomaly_detector.py`.

It loads the trained checkpoint from
`ai-model/checkpoints/lstm_model.pt` and the saved scaler from
`datasets/processed/scaler.pkl`.

It uses the required 10 telemetry features, a sequence length of five,
and separate sequences for each switch and port. It calculates mean
squared error (MSE) between the predicted and actual next telemetry
vector in scaled feature space. Samples exceeding the configured MSE
threshold are flagged as anomalous.

## 3. Dataset and Configuration

- Input: `datasets/processed/qos_features.csv`
- Input rows: 864
- Rows retained after cleaning: 854
- Evaluated samples: 804
- Anomalous labels among evaluated samples: 65
- Normal labels among evaluated samples: 739
- Threshold used in this run: 5.0
- Output: `datasets/processed/week6_lstm_anomaly_results.csv`

Threshold 5.0 is the threshold used for this run, not a final independently
validated threshold.

## 4. Aggregate Detection Results

| Metric | Result |
|---|---:|
| True positives (TP) | 34 |
| False negatives (FN) | 31 |
| False positives (FP) | 29 |
| True negatives (TN) | 710 |
| Accuracy | 92.54% |
| Precision | 53.97% |
| Recall | 52.31% |
| F1-score | 53.12% |
| False-positive rate | 3.92% |

The detector identifies some labelled anomalous samples, but misses 31
of 65 anomalous samples. Accuracy alone does not fully describe its
performance because normal samples are the majority class.

## 5. Scripted Week 3 Event Validation

The timestamped output was checked against the two event windows in
`docs/week3/anomaly-event-timestamps.md`.

| Scripted event | Labelled anomalous rows | Detected anomalous rows | Event-sample recall |
|---|---:|---:|---:|
| anomaly-20260829_220930 | 22 | 7 | 31.82% |
| anomaly-20260829_221755 | 12 | 8 | 66.67% |

At least one anomalous sample was flagged in each scripted event window.
Both events were therefore detected at event level, although several
anomalous samples were missed.

## 6. Member 2 Real Link-Failure Validation

**Status: not yet verified against the specific real link-failure event.**

The repository contains `ai-model/evaluation_member2_results.csv` with
280 aggregate evaluation rows, including anomaly labels and MSE scores.
That CSV does not contain timestamps, switch/port identifiers, or the
failure event window needed to confirm detection of a specific physical
link failure.

A repository search did not find a separate timestamped real
link-failure event file. Obtain Member 2's source telemetry or event log,
including failure start/end timestamps and the affected link or port.
Then run the detector on the relevant data and record whether it flags
the event and how often it flags normal traffic.

## 7. Limitations and Reproducibility

- These aggregate results use labels in the existing processed dataset.
  They do not prove successful real-time operation or detection of a
  separate physical link failure.
- The threshold must be calibrated on designated calibration data and
  evaluated on separate data before it is called final.
- The detector records the timestamp of the target telemetry sample.
- Loading the saved scaler emitted a scikit-learn version warning:
  it was saved with version 1.7.2 and is being loaded with version 1.9.0.
  The script completed, but the software environment should be
  standardized and the results rerun before claiming reproducibility.
- Predictions begin only after five earlier observations exist within
  each switch/port group.

## 8. Week 6 Completion Checklist

- [x] LSTM checkpoint loaded by the detector.
- [x] LSTM-based detector implemented.
- [x] Aggregate metrics and false-positive rate measured.
- [x] Both scripted Week 3 event windows evaluated.
- [ ] Member 2's specific real link-failure event verified from timestamped
      source evidence.
- [ ] Final threshold justified using calibration data and tested on
      separate validation data.
- [ ] Results reproduced in a consistent software environment.

The implementation and preliminary evaluation are available. The
unchecked items must be completed before claiming every Week 6 success
criterion is satisfied.

## 9. Held-Out Validation Split

The detector was also run against `datasets/processed/val_raw.csv` with
the threshold held fixed at 5.0. The run retained 171 rows and produced
121 predictions after accounting for the five-observation history
required within each switch/port group.

| Metric | Result |
|---|---:|
| Evaluated samples | 121 |
| True positives (TP) | 23 |
| False negatives (FN) | 12 |
| False positives (FP) | 27 |
| True negatives (TN) | 59 |
| Accuracy | 67.77% |
| Precision | 46.00% |
| Recall | 65.71% |
| F1-score | 54.12% |
| False-positive rate | 31.40% |

The validation split contains 35 anomalous and 86 normal evaluated
samples. At threshold 5.0, recall is higher than in the full-dataset
run, but the false-positive rate is also substantially higher. The
threshold therefore requires further calibration on designated
calibration data, followed by evaluation on data not used for tuning.

This validation split tests labelled telemetry, not Member 2's specific
physical link-failure event. Real-event validation remains outstanding.
