# Week 8: Member 4 Anomaly Prediction Summary

> Historical anomaly results only. This report does not trigger QoS actions.
> The prediction timestamps do not match the September telemetry file,
> so these results are not joined to throughput decisions.

## Summary

- Input: `ai-model/integration_predictions.csv`
- Total rows: 121
- Valid rows: 121
- Invalid rows skipped: 0
- Predicted anomalies: 50
- Predicted normal rows: 71

## Results by switch and port

| DPID | Port | Valid rows | Predicted anomalies |
|---:|---:|---:|---:|
| 1 | 1 | 15 | 0 |
| 1 | 2 | 16 | 0 |
| 1 | 3 | 16 | 10 |
| 1 | 4 | 16 | 11 |
| 2 | 1 | 7 | 0 |
| 2 | 2 | 7 | 0 |
| 2 | 3 | 7 | 4 |
| 2 | 4 | 7 | 5 |
| 3 | 1 | 15 | 10 |
| 3 | 2 | 15 | 10 |

## Safety note

An anomaly flag is supporting evidence only. Congestion decisions remain based on valid throughput readings and the configured consecutive-reading rule. No controller or switch changes were made.
