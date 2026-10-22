# Week 10 — End-to-End Runbook

## Purpose
Run and verify the integrated system in a repeatable order. Use separate terminals for long-running processes. Run commands from the repository root unless stated otherwise.

## 1. Pre-flight checks

```powershell
git status --short
git log -1 --oneline
python -m py_compile ai-model/ai_loop.py scripts/evaluate.py scripts/run_controller.py scripts/run_telemetry_processor.py
```

Use the project Python environment with OS-Ken and required dependencies installed. Mininet and Open vSwitch must be available in the Linux/WSL environment where the topology is intended to run.

## 2. Start Mininet

Inspect `mininet/topo.py` and confirm the topology entry point, class name, and required privileges before starting it. The filename alone does not establish the correct launch command.

Start the topology using the confirmed project command. Verify the expected switches and links and save the output.

## 3. Start OS-Ken controller

In a separate terminal, from the repository root:

```bash
python scripts/run_controller.py
```

The script launches OS-Ken with `controller.app`, `controller.telemetry`, `controller.monitor`, and the OpenFlow handler. Controller logs are written to `logs/controller.log`.

Verify the expected switches connect. Save the relevant logs.

## 4. Start telemetry processor

In a separate terminal:

```bash
python scripts/run_telemetry_processor.py
```

This repeatedly runs `scripts/process_telemetry.py` at an approximately five-second interval. Confirm that `datasets/processed/qos_features.csv` contains recent, valid observations.

## 5. Start AI runtime

In a separate terminal:

```bash
python ai-model/ai_loop.py --help
```

Check the supported options, then start the model-backed runtime using the confirmed invocation. Check `config/ai_loop.yaml`, telemetry freshness, model checkpoint, scaler, and output path.

Inspect `data/results/week9_ai_runtime.jsonl` for successful inference records.

Important: reading processed CSV telemetry does not by itself prove a live controller-to-AI interface.

## 6. Run integration scenarios

Coordinate with Members 1, 2, and 3. Use the team's confirmed launcher and scenario definitions.

- S1: steady mixed traffic
- S2: heavy congestion
- S3: link failure under load

For each run, preserve scenario configuration, traffic measurements, controller logs, AI logs, decision/enforcement events, and recovery evidence. Do not claim a scenario passed if its required component or interface is unavailable.

## 7. Measure end-to-end delay

Use timestamps from the same correlated event/request and a common clock.

- Telemetry to prediction = prediction timestamp minus telemetry timestamp.
- Prediction to decision = decision timestamp minus prediction timestamp.
- Decision to enforcement = enforcement timestamp minus decision timestamp.
- End-to-end delay = enforcement timestamp minus telemetry timestamp.

Record sample count, mean, median, and p95 when enough samples exist. Document timestamp units and correlation method. Do not infer data-plane recovery from a port-down timestamp alone.

## 8. Finish the run

Stop components cleanly. Record whether the session was uninterrupted, update the acceptance checklist, log defects and owners, and summarize observed results in `integration-report.md`.

Gate B remains pending until the complete chain passes in one uninterrupted session with retained evidence.
