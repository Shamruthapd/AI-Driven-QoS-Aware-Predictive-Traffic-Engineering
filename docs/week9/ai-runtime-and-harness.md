# Week 9 — Member 4 AI Runtime and Evaluation Harness

## Purpose and scope

This deliverable turns the existing LSTM into a periodic inference runtime and adds a repeatable evaluation harness. It is designed to fail safely when telemetry is missing, stale, discontinuous, malformed, or non-finite. It does not replace the OS-Ken controller and does not claim end-to-end integration before Member 1's interface is agreed and tested.

## Files

- `ai-model/ai_loop.py` — telemetry-window validation, existing checkpoint/scaler inference, predicted throughput-to-utilization calibration, prediction residual scoring, inference timing, last-good value retention, JSONL event output.
- `config/ai_loop.yaml` — runtime interval and path/threshold configuration.
- `scripts/evaluate.py` — parser for iPerf3 JSON, ping logs, and CSV/JSONL measurement/timeline files; grouped mean, sample standard deviation, min, max and p95.

## Runtime input contract

The offline adapter reads `datasets/processed/qos_features.csv`, which is produced by the repository's telemetry processing pipeline. Required fields: `timestamp`, `dpid`, `port`, the eight counter-delta features, `throughput_bps`, and `packet_rate_pps`. Each inference window contains five observations from exactly one switch/port stream. A window is rejected when it is incomplete, non-finite, too old, non-monotonic, or has an interval gap over the configured limit.

**Week 10 integration remains a team dependency:** Member 1 and Member 4 need to agree on the live transport (REST/socket or another agreed interface), payload schema, request/response IDs, timestamps, and timeouts. The CSV is an offline adapter—not evidence that this controller contract has already been implemented.

## Inference and anomaly residual

The existing model consumes five standardized rows and predicts the next standardized feature vector. Predicted throughput is inverse-transformed, then calibrated as:

`utilization_percent = clamp(predicted_throughput_bps / link_capacity_bps × 100, 0, 100)`.

The anomaly residual is calculated when a later actual observation arrives, by comparing it with the preceding cycle's forecast in standardized feature space. This avoids comparing a prediction against a row already included in its input window. The threshold currently comes from configuration and must be validated against the current labelled dataset before any real enforcement decision relies on it.

## Output and graceful degradation

One JSON object is appended per cycle to `data/results/week9_ai_runtime.jsonl`. Key fields include timestamp, status, reason, dpid, port, predicted throughput, utilization, anomaly residual/alert, inference latency, cycle latency and `used_last_good`. Missing values are `null`; the writer rejects NaN and infinity. On missing/stale telemetry or inference failure the cycle records `status=no_data`, preserves the last successful output when available and continues. Downstream code must treat a retained value as stale, not as a fresh measurement.

## Commands

Run from the repository root:

```bash
python -m py_compile ai-model/ai_loop.py scripts/evaluate.py
python ai-model/ai_loop.py --once
python ai-model/ai_loop.py --no-model --interval 1 --duration 5
python scripts/evaluate.py --week8-summary data/results/week8_qos_on_vs_off_measurements.csv
python scripts/evaluate.py --input-dir data/results/week11_raw
```

The no-model command verifies that the loop records no-data conditions and continues; it does not test inference accuracy or prove a model-backed 30-minute run. The Week 8 command recomputes the QoS ON/OFF summary from the committed summary CSV. The original iPerf3 JSON logs were not found in the inspected repository tree, so this is **not** the raw-file reproduction gate described in the plan. Add the original files before claiming that gate passed.

## Evaluation harness behavior

The harness leaves raw source files untouched and emits `parsed_measurements.csv` and `summary_tables.csv`. Missing metrics are left blank instead of being silently replaced with zero. Trial filenames should encode the mode, scenario (`S1`, `S2`, `S3`) and trial ID—for example `full_ai_qos_ff_S2_trial_01.json` or `reactive_S3_trial_03_ping.log`. Do not combine modes under one label. Timeline delay calculations require explicit measurements or matching event/request IDs; do not infer data-plane recovery from a controller port-down timestamp alone.

## Week 9 acceptance evidence to collect

- [ ] `py_compile` passes.
- [x] Unit tests pass locally (9 tests, including telemetry-gap handling and Week 8 summary consistency).
- [ ] With valid, fresh telemetry and the checkpoint/scaler available, inference time is recorded every successful cycle.
- [ ] Missing file, stale data, missing columns, invalid values and telemetry gaps produce a `no_data` record rather than a crash or NaN.
- [ ] Run the model-backed loop for 30 minutes and retain the log; duration is not proven by a short smoke test.
- [ ] Recover the raw Week 8 iPerf3 JSON files and reproduce the old comparison from them; until then mark raw-reproduction evidence pending.
- [ ] Agree the live telemetry/AI message schema with Member 1 before Week 10 integration.

## Current limitations

The offline runtime assumes the processed telemetry CSV is updated by the data pipeline and that its final observation is sufficiently fresh. Runtime predictions and anomaly thresholds require calibration checks against current telemetry. The 30-minute stability test and true controller integration must be performed in the project environment; source code by itself is not proof those tests passed.
