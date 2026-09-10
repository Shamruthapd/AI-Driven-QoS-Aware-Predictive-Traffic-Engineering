# Anomaly Event Timestamps

> Machine-readable anomaly windows for the telemetry dataset.

> These windows are appended automatically by
> `traffic/scapy_iot_traffic.py` (Member 3) and consumed by
> `scripts/process_telemetry.py` to add the binary `is_anomalous`
> label column to the processed QoS dataset (`datasets/processed/qos_features.csv`).

## Format

Each anomaly event is logged as a block of three `key: value` lines:

```
- event_id: anomaly-20260809_142301
- anomaly_start: 2026-08-09T14:23:01.000000+00:00
- anomaly_end: 2026-08-09T14:23:11.000000+00:00
```

- `anomaly_start` / `anomaly_end` are UTC ISO-8601 timestamps.
- A telemetry sample is labelled `is_anomalous = 1` when its timestamp
  is inside an anomaly window (bounds inclusive).
- Anomaly windows SHOULD be wider than the telemetry polling interval
  (`monitoring.polling_interval = 5 s` in `config/settings.yaml`) so that
  at least one raw telemetry sample falls inside the window and the spike
  is observable in the dataset.

Only entries under the section below are parsed by the processing script.

## Recorded Events

<!-- Events appended below by traffic/scapy_iot_traffic.py -->- event_id: anomaly-20260829_220930
- anomaly_start: 2026-08-29T22:09:47.700475+00:00
- anomaly_end: 2026-08-29T22:09:57.700475+00:00

- event_id: anomaly-20260829_221755
- anomaly_start: 2026-08-29T22:18:13.092432+00:00
- anomaly_end: 2026-08-29T22:18:23.092432+00:00

