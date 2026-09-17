# Week 5: LSTM Training and Evaluation

## Work Completed

- Prepared the validation dataset for LSTM evaluation.
- Generated validation sequences using a sequence length of 5.
- Loaded the trained LSTM model checkpoint.
- Generated traffic-feature predictions for validation samples.
- Calculated Mean Squared Error (MSE) for each sample.
- Tested multiple MSE thresholds for anomaly detection.

## Training Results

- Training sequences: 633
- Training epochs: 20
- Final training loss: 0.054284
- Device: CPU

## Evaluation Results

- Validation sequences: 121
- Overall validation MSE: 37.632519
- Normal samples: 86
- Normal MSE: 6.959243
- Anomalous samples: 35
- Anomalous MSE: 113.001137

## Threshold Comparison

The tested thresholds were 5, 10, 15, 20, 25, 30, 40, and 50.

Among the tested values, threshold 5 achieved the highest F1-score.

- Accuracy: 67.77%
- Precision: 46.00%
- Recall: 65.71%
- F1-score: 0.5412

## Confusion Matrix

|                | Predicted Normal | Predicted Anomaly |
|----------------|------------------|-------------------|
| Actual Normal  | 59               | 27                |
| Actual Anomaly | 12               | 23                |

## Observation

A lower MSE threshold detected more anomalies but also produced more false positives. Threshold 5 achieved the highest F1-score among the tested thresholds.