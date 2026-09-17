# Week 5 – LSTM Model Input Specification

## 1. Objective

The objective of this stage is to prepare network telemetry data as
sequential input for an LSTM model.

The LSTM model will use previous network observations to predict the
next telemetry observation for traffic forecasting.

---

## 2. Dataset Source

The input dataset is generated during the earlier data-processing stage.

The prepared files are:

- `datasets/processed/train_scaled.csv`
- `datasets/processed/val_scaled.csv`

The data preparation process removes malformed or incomplete rows and
applies feature scaling using the training data.

---

## 3. Input Features

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

These features represent packet activity, byte activity, packet drops,
errors, throughput, and packet rate in the network.

---

## 4. Excluded Columns

The following columns are not directly provided as model input:

| Column | Purpose |
|---|---|
| `timestamp` | Used to order observations chronologically |
| `dpid` | Identifies the network switch |
| `port` | Identifies the switch port |
| `is_anomalous` | Used later for validation and anomaly analysis |

The `is_anomalous` column is retained as an evaluation label and is not
used as an input feature.

---

## 5. Sequence Generation

A sequence length of 5 is used.

This means that the model receives five previous observations and
predicts the next observation.

Example:

```text
Input:
Observation 1
Observation 2
Observation 3
Observation 4
Observation 5

Target:
Observation 6