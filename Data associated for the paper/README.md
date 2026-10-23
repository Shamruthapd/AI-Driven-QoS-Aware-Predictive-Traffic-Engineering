# Dataset Documentation: AI-Driven QoS-Aware Predictive Traffic Engineering and Self-Healing in SDN-Based Edge Networks

This dataset archive accompanies the research paper **"AI-Driven QoS-Aware Predictive Traffic Engineering and Self-Healing in SDN-Based Edge Networks"**. It compiles the empirical data collected from live SDN testbed experiments executed on Mininet with Open vSwitch and the OS-Ken controller.

---

## 1. Dataset Organization

The dataset is structured into raw experimental logs and processed metric tables:

```
Data associated for the paper/
├── README.md                      <- Dataset documentation and file descriptions (this file)
├── raw_data/                      <- Raw event timestamps, failure injection logs, and controller events
│   ├── live_s3_baseline_link_failure_events.csv
│   ├── live_s3_reactive_link_failure_events.csv
│   ├── live_calib_003_link_failure_events.csv
│   ├── failure_injection_log.csv
│   ├── port_status_events.csv
│   └── unified_event_log.csv
└── processed_data/                <- Parsed measurements and aggregated statistical summary tables
    ├── live_s3_baseline_parsed_measurements.csv
    ├── live_s3_baseline_summary_tables.csv
    ├── live_s3_reactive_parsed_measurements.csv
    ├── live_s3_reactive_summary_tables.csv
    ├── live_calib_003_parsed_measurements.csv
    └── live_calib_003_summary_tables.csv
```

---

## 2. Experimental Modes and Associated Trials

The dataset focuses on the three validated live testbed experiments conducted under Scenario S3 (8.0-second physical link failure on interface `s1-eth3`):

| Trial Identifier | Operational Mode | Primary Mechanism | Priority UDP Loss Rate | Continuity Blackout | Retransmissions |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `live_s3_baseline` | `baseline_shortest_path` | Static shortest path (No failover) | **20.029%** | 7.0 s continuous | 186 segments |
| `live_s3_reactive` | `reactive` | OpenFlow 1.3 Fast-Failover (Group 101) | **0.761%** | 0.0 s (Zero blackout) | 93 segments |
| `live_calib_003` | `full_ai_qos_ff` | OpenFlow 1.3 Fast-Failover + Telemetry | **0.723%** | 0.0 s (Zero blackout) | 93 segments |

---

## 3. File Inventory and Header Descriptions

### 3.1 Raw Data Files (`raw_data/`)

1. **`live_s3_baseline_link_failure_events.csv`**
   * *Source:* `data/results/live_s3_baseline/live_s3_baseline_link_failure_events.csv`
   * *Purpose:* Precise timestamps of the injected physical carrier outage for the baseline shortest-path trial.
   * *Header:* `['timestamp_iso', 'timestamp_epoch', 'interface', 'event_type', 'details']`
   * *Row count:* 3 events (`LINK_DOWN_SCHEDULED`, `LINK_DOWN`, `LINK_UP` on interface `s1-eth3`).

2. **`live_s3_reactive_link_failure_events.csv`**
   * *Source:* `data/results/live_s3_reactive/live_s3_reactive_link_failure_events.csv`
   * *Purpose:* Precise timestamps of the injected physical carrier outage for the reactive mode trial.
   * *Header:* `['timestamp_iso', 'timestamp_epoch', 'interface', 'event_type', 'details']`
   * *Row count:* 3 events.

3. **`live_calib_003_link_failure_events.csv`**
   * *Source:* `data/results/live_calib_003/live_calib_003_link_failure_events.csv`
   * *Purpose:* Precise timestamps of the injected physical carrier outage for the full Fast-Failover trial.
   * *Header:* `['timestamp_iso', 'timestamp_epoch', 'interface', 'event_type', 'details']`
   * *Row count:* 3 events.

4. **`failure_injection_log.csv`**
   * *Source:* `data/results/failure_injection_log.csv`
   * *Purpose:* Master link-failure injection log consolidating failure cycles across all live trials.
   * *Header:* `['timestamp_iso', 'timestamp_epoch', 'interface', 'event_type', 'details']`
   * *Row count:* 9 events (3 cycles corresponding to `live_calib_003`, `live_s3_baseline`, and `live_s3_reactive`).

5. **`port_status_events.csv`**
   * *Source:* `data/results/port_status_events.csv`
   * *Purpose:* Master log of OpenFlow asynchronous `OFPT_PORT_STATUS` messages emitted by switch ports to the OS-Ken controller.
   * *Header:* `['timestamp_iso', 'dpid', 'port_no', 'reason', 'link_state']`
   * *Row count:* 186 events.

6. **`unified_event_log.csv`**
   * *Source:* `data/results/unified_event_log.csv`
   * *Purpose:* Consolidated controller decision and state transition log recorded via `controller/ai_sdn_bridge.py`.
   * *Header:* `['timestamp_iso', 'timestamp_epoch', 'event_type', 'dpid', 'port', 'trial_id', 'mode', 'details']`
   * *Row count:* 255 events.

---

### 3.2 Processed Data Files (`processed_data/`)

Processed measurement tables were produced by the standardized evaluation script `scripts/evaluate.py`:

1. **`live_s3_baseline_parsed_measurements.csv`**
   * *Source:* `data/results/live_s3_baseline/eval/parsed_measurements.csv`
   * *Purpose:* Extracted per-stream performance metrics (throughput, packet loss, latency, jitter) for `live_s3_baseline`.
   * *Header:* `['source_file', 'mode', 'scenario', 'trial_id', 'flow_type', 'valid', 'invalid_reason', 'throughput_mbps', 'duration_seconds', 'jitter_ms', 'packet_loss_pct', 'latency_ms_mean', 'latency_ms_p95', 'ping_rtt_variation_ms', 'ping_samples', ...]`

2. **`live_s3_baseline_summary_tables.csv`**
   * *Source:* `data/results/live_s3_baseline/eval/summary_tables.csv`
   * *Purpose:* Aggregated statistical metrics for `live_s3_baseline` (confirming 20.029% priority UDP loss).
   * *Header:* `['mode', 'scenario', 'flow_type', 'metric', 'n', 'mean', 'stddev', 'min', 'max', 'p95']`

3. **`live_s3_reactive_parsed_measurements.csv`**
   * *Source:* `data/results/live_s3_reactive/eval/parsed_measurements.csv`
   * *Purpose:* Extracted per-stream performance metrics for `live_s3_reactive`.
   * *Header:* Same schema as baseline parsed measurements.

4. **`live_s3_reactive_summary_tables.csv`**
   * *Source:* `data/results/live_s3_reactive/eval/summary_tables.csv`
   * *Purpose:* Aggregated statistical metrics for `live_s3_reactive` (confirming 0.761% priority UDP loss).
   * *Header:* Same schema as baseline summary table.

5. **`live_calib_003_parsed_measurements.csv`**
   * *Source:* `data/results/live_calib_003/eval/parsed_measurements.csv`
   * *Purpose:* Extracted per-stream performance metrics for `live_calib_003` (Full AI/QoS/FF mode).
   * *Header:* Same schema as baseline parsed measurements.

6. **`live_calib_003_summary_tables.csv`**
   * *Source:* `data/results/live_calib_003/eval/summary_tables.csv`
   * *Purpose:* Aggregated statistical metrics for `live_calib_003` (confirming 0.723% priority UDP loss).
   * *Header:* Same schema as baseline summary table.

---

## 4. Distinction from Historical / Earlier Datasets

The repository root `data/results/` contains earlier milestone files that are **not** part of the three live Mininet failure-recovery experiments:

* **Week 11 Synthetic Batch Data (`week11_recovery_times.csv`, `week11_summary_tables.csv`, `week11_controller_timelines/*.csv`):**
  Generated during earlier synthetic multi-trial simulation campaigns (Trials 1–30). Used for preliminary milestone reporting; not derived from the live testbed runs.
* **Week 8 Contention QoS Files (`week8_qos_on_vs_off_measurements.csv`, `week8_qos_analysis.csv`, `week8_full_system_comparison.csv`):**
  Synthetic static contention benchmarks evaluating QoS queues ON versus OFF.
* **Week 7 Prototype Calibration Files (`week7_calibrated_utilization.csv`, `week7_failure_event_evaluation.csv`, `week7_predicted_throughput.csv`):**
  Offline neural network calibration datasets used during initial model prototyping.
* **Calibration Trials 001 and 002 (`live_raw/`, `live_calib_002/`, `live_eval/`):**
  Pre-flight test runs (`live_calib_001` encountered initial ARP warmup failures; `live_calib_002` identified a transit routing loop on core switch `s3` that was subsequently corrected).

---

## 5. Known Limitations and Scientific Transparency

1. **Sample Size:** The live experimental dataset reflects **one validated run per mode** (`live_s3_baseline`, `live_s3_reactive`, and `live_calib_003`).
2. **Switch-Local Fast-Failover vs. AI:** Recovery under link outage was executed autonomously in the switch hardware datapath via OpenFlow 1.3 Fast-Failover (`Group 101`). AI-triggered proactive rerouting was not demonstrated during these trials, and AI inference did not cause the observed recovery.
3. **Queue Shaping Discrepancy:** The baseline run operated without queue rate limiting (unshaped FIFO), whereas reactive and full modes ran with active Linux-HTB traffic shaping.
4. **Queue Isolation Scope:** In Scenario S3 (`h1 -> h3`), traffic defaulted to Best-Effort Group 101; thus, independent priority queue isolation under congestion was not validated.
5. **Group Counter Timestamps:** OpenFlow group bucket counters represent cumulative statistics recorded at the post-recovery snapshot and do not exclusively isolate outage-window bytes.
