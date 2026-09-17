# Week 6: LSTM Training and Evaluation Report

## 1. Objective

The objective of Week 6 was to train the LSTM model using the processed network telemetry dataset and evaluate its ability to predict the next telemetry values.

The model was also evaluated for its ability to identify anomalous network behaviour using the Mean Squared Error (MSE) between the predicted and actual telemetry values.

---

## 2. Dataset Used

The dataset was prepared during Week 4 using the telemetry-processing pipeline.

| Dataset detail                    | Value |
| --------------------------------- | ----: |
| Original rows                     |   864 |
| Removed malformed/incomplete rows |    10 |
| Clean rows                        |   854 |
| Training rows                     |   683 |
| Validation rows                   |   171 |
| Sequence length                   |     5 |
| Number of input features          |    10 |

The model uses five consecutive telemetry records as input and predicts the telemetry values of the next record.

---

## 3. Input Features

The following ten features were used as model inputs:

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

The features were scaled before being provided to the LSTM model.

---

## 4. Model Architecture

The implemented model is a PyTorch-based Long Short-Term Memory (LSTM) network.

| Parameter             |              Value |
| --------------------- | -----------------: |
| Input size            |                 10 |
| Hidden size           |                 64 |
| Number of LSTM layers |                  2 |
| Output size           |                 10 |
| Sequence length       |                  5 |
| Optimizer             |               Adam |
| Learning rate         |              0.001 |
| Loss function         | Mean Squared Error |
| Training device       |                CPU |

The LSTM receives a sequence with the shape:

```text
(batch_size, 5, 10)
```

The model produces an output with the shape:

```text
(batch_size, 10)
```

The output represents the predicted values of the ten telemetry features for the next time step.

---

## 5. Training Process

The training pipeline was implemented using:

* PyTorch
* `NetworkSequenceDataset`
* `DataLoader`
* `TrafficLSTM`
* Adam optimizer
* Mean Squared Error loss

During training, the model parameters were updated using backpropagation. The training loss was recorded after every epoch to observe whether the model was learning.

The model checkpoint was saved at:

```text
ai-model/checkpoints/lstm_model.pt
```

---

## 6. Smoke-Test Result

Before full model training, a short smoke test was performed to verify the complete pipeline.

The smoke test verified:

* Dataset loading
* Sequence generation
* DataLoader batching
* Input and target tensor shapes
* LSTM forward pass
* Loss calculation
* Backpropagation
* Parameter updates
* Loss-curve generation

The smoke-test training loss decreased approximately from **0.74 to 0.20** over ten epochs.

The loss curve was saved at:

```text
docs/week5/smoke-test-loss-curve.png
```

This confirms that the dataset, LSTM model, and training pipeline work together correctly.

---

## 7. Full Training Result

The model was trained using the prepared training dataset.

The training loss decreased during the training process, indicating that the model was learning patterns from the telemetry sequences.

The final trained model was saved as:

```text
ai-model/checkpoints/lstm_model.pt
```

The checkpoint can be loaded later for evaluation or integration into the network-control pipeline.

---

## 8. Validation Evaluation

The trained model was evaluated using the available validation dataset.

The evaluation generated 121 validation sequences.

| Metric                         |     Result |
| ------------------------------ | ---------: |
| Number of validation sequences |        121 |
| Overall MSE                    |  37.632519 |
| Normal samples                 |         86 |
| Anomalous samples              |         35 |
| Normal-sample MSE              |   6.959243 |
| Anomalous-sample MSE           | 113.001137 |

The anomalous samples produced a considerably higher prediction error than the normal samples. This indicates that prediction error can be used as a possible signal for detecting unusual network behaviour.

---

## 9. Anomaly Detection Using MSE

For anomaly detection, the MSE of each prediction was compared against a threshold.

If the MSE was greater than the selected threshold, the sample was classified as anomalous.

The following thresholds were tested:

| MSE threshold | Precision | Recall | F1-score |
| ------------: | --------: | -----: | -------: |
|             5 |    0.4600 | 0.6571 |   0.5412 |
|            10 |    0.4667 | 0.6000 |   0.5250 |
|            15 |    0.4667 | 0.6000 |   0.5250 |
|            20 |    0.4815 | 0.3714 |   0.4194 |
|            25 |    0.5455 | 0.3429 |   0.4211 |
|            30 |    0.5294 | 0.2571 |   0.3462 |
|            40 |    1.0000 | 0.2000 |   0.3333 |
|            50 |    1.0000 | 0.1429 |   0.2500 |

A threshold of **5** was selected for the current evaluation because it produced the highest recall and F1-score among the tested threshold values.

---

## 10. Final Classification Result

Using an MSE threshold of 5, the model produced the following results:

| Metric    | Result |
| --------- | -----: |
| Accuracy  | 0.6777 |
| Precision | 0.4600 |
| Recall    | 0.6571 |
| F1-score  | 0.5412 |

The confusion matrix was:

```text
[[59, 27],
 [12, 23]]
```

This indicates that the model detected a significant portion of the anomalous samples, but it also generated some false-positive predictions.

---

## 11. MAPE Consideration

Mean Absolute Percentage Error (MAPE) was considered as an additional evaluation metric.

However, several telemetry features may contain zero or very small values. MAPE can become unstable or produce very large values when the actual value is zero or close to zero.

Therefore, MSE and MAE are more suitable primary metrics for the current telemetry prediction task.

If MAPE is calculated, zero-valued actual values should be handled using a small epsilon value or excluded with proper documentation. The MAPE result should be interpreted carefully because it may not accurately represent the prediction quality for near-zero telemetry values.

---

## 12. Limitations

The current implementation has the following limitations:

1. The model was trained and evaluated using the available project dataset only.
2. Independent evaluation using Member 2’s validation dataset is pending because that CSV was not available.
3. The current model uses a fixed sequence length of five records.
4. The model predicts the next telemetry vector but does not yet directly change routing or bandwidth allocation.
5. The anomaly threshold was selected using the available validation results and may require further tuning.
6. The dataset contains a limited number of anomalous samples.
7. The model was trained on CPU, so training time may increase for larger datasets.
8. MAPE may be unreliable for telemetry values that are zero or close to zero.

---

## 13. Files Created or Updated

The following files were created or used during Week 5 and Week 6:

```text
ai-model/lstm_model.py
ai-model/sequence_dataset.py
ai-model/smoke_test.py
ai-model/train_lstm.py
ai-model/evaluate_lstm.py
ai-model/checkpoints/lstm_model.pt
ai-model/evaluation_results.csv
docs/week5/model-input-spec.md
docs/week5/smoke-test-loss-curve.png
docs/week6/training-evaluation-report.md
```

---

## 14. Handoff Information

The trained checkpoint and input specification can be provided to the other project members.

### Member 1

Member 1 can use:

```text
ai-model/checkpoints/lstm_model.pt
docs/week5/model-input-spec.md
```

The input data must contain the same ten features, use the same feature order, and apply the same scaling procedure used during training.

### Member 3

Member 3 can use the model predictions and prediction errors from:

```text
ai-model/evaluation_results.csv
```

The prediction error can be used as an input signal for further anomaly analysis, traffic engineering, or self-healing decisions.

---

## 15. Current Completion Status

The following Week 5 and Week 6 tasks have been completed:

* LSTM architecture implemented.
* Sequence dataset and DataLoader implemented.
* Smoke-test training completed.
* Smoke-test loss curve generated.
* Full training pipeline executed.
* Model checkpoint saved.
* Validation evaluation completed.
* MSE threshold comparison performed.
* Anomaly classification metrics calculated.
* Evaluation results saved.
* Training and evaluation limitations documented.

The following task remains pending:

* Independent evaluation using Member 2’s validation dataset.
* Confirmation from Member 1 that the checkpoint can be loaded in the integration pipeline.
* Confirmation from Member 3 that the prediction-error outputs can be used in their module.
