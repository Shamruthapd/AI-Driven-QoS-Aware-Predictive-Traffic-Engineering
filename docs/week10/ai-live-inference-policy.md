# Week 10 – Live AI Inference and Policy Interface

## Objective

Week 10 connects the trained LSTM model to live OpenFlow telemetry and
produces an AI policy decision for QoS enforcement.

## Live Inference Pipeline

The controller performs the following steps:

1. Polls OpenFlow port statistics every five seconds.
2. Calculates the ten features used during model training.
3. Maintains a five-observation sequence for each switch port.
4. Runs the trained LSTM model.
5. Measures inference latency.
6. Compares the predicted and actual scaled feature vectors.
7. Calculates mean squared error.
8. Produces a queue policy decision.

## Model Configuration

| Item | Value |
|---|---|
| Input shape | `(1, 5, 10)` |
| Feature count | 10 |
| Sequence length | 5 |
| MSE threshold | 5 |
| Model output | 10 predicted features |
| Inference device | CPU |

## Policy Mapping

| MSE condition | Classification | Queue |
|---|---|---:|
| `MSE <= 5` | `NORMAL` | 0 |
| `MSE > 5` | `ANOMALOUS` | 1 |

The MSE is calculated using scaled feature values, matching the training
and evaluation pipeline.

## Controller Integration

The live telemetry collector uses:

- `controller/live_inference.py`
- `controller/ai_policy.py`
- `controller/telemetry.py`

Each completed prediction produces:

- DPID
- port number
- MSE
- classification
- queue decision
- inference latency

The policy output is an interface for the existing QoS enforcement layer.

## Verification

Live controller logs confirmed:

- input shape `(1, 5, 10)`
- inference latency approximately 5–10 ms
- normal MSE values approximately 0.001–0.004
- normal classification
- queue 0 decision
- prediction output written to `results/week6/predictions.csv`

A synthetic policy test also confirmed both branches:

- MSE `0.0` produced `NORMAL`, queue `0`
- MSE `9.0` produced `ANOMALOUS`, queue `1`

## Scope

This Week 10 implementation validates live AI inference and exposes the
AI policy decision. Fast-Failover remains implemented independently by the
Week 9 OpenFlow group application.
