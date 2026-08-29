# Week 4 — Telemetry Processing and QoS Feature Extraction

## 1. Objective

Week 4 focuses on processing the raw OpenFlow telemetry collected from the SDN controller and converting cumulative switch counters into interval-based QoS features.

The raw telemetry dataset is preserved unchanged.

## 2. Raw Telemetry Validation

The raw dataset contains:

- 2,511 telemetry rows
- 11 columns
- DPID 1
- Data ports 1 and 2
- OpenFlow LOCAL port 4294967294
- 0 duplicate rows
- 0 missing values

The timestamp range is:

2026-08-08T16:44:54.241108+00:00
to
2026-08-09T08:53:20.019353+00:00
## 3. Counter Reset Detection

Cumulative OpenFlow counters were checked for decreases between consecutive samples belonging to the same DPID and port.

Detected resets:

Counter	Resets
rx_packets	10
tx_packets	10
rx_bytes	10
tx_bytes	10
rx_dropped	0
tx_dropped	0
rx_errors	0
tx_errors	0

This confirms that counter-reset handling is required before calculating interval-based features.

Evidence:

screenshots/week4-counter-reset-validation.jpg
## 4. Telemetry Processing

The processing script is:

scripts/process_telemetry.py

The script:

1.Loads the raw telemetry.
2.Converts timestamps to UTC datetime values.
3.Excludes the OpenFlow LOCAL port.
4.Sorts samples by DPID, port, and timestamp.
5.Calculates counter deltas.
6.Detects counter decreases.
7.Uses the current counter value after a reset.
8.Calculates the sampling interval.
9.Calculates throughput.
10.Calculates packet rate.
11.Writes the processed dataset.

The raw dataset is not modified.

## 5. Processed Dataset

The generated dataset is:

datasets/processed/qos_features.csv

It contains:

1,668 rows

The processed dataset contains only the two data ports:

Port 1
Port 2

The extracted features include:

- interval duration
- received packet delta
- transmitted packet delta
- received byte delta
- transmitted byte delta
- dropped packet deltas
- error deltas
- throughput
- packet rate
## 6. Processing Validation

Validation produced:

Check	Result
Processed rows	1,668
Negative deltas	0
Missing throughput values	2
Data ports	1, 2

The two missing throughput values correspond to the first sample of each data port, where no previous counter sample exists to calculate a delta.

## 7. QoS Measurements

The observed throughput range is:

0 to 64.43 Gbit/s

The observed packet-rate range is approximately:

0 to 183,318 packets/s

These values are measurements calculated from the collected OpenFlow counters.

## 8. Throughput Visualization

The visualization script is:

scripts/plot_qos_results.py

It generates:

results/week4/throughput_over_time.png

The graph shows measured throughput over time for the two switch data ports.

## 9. Week 4 Deliverables

The completed Week 4 deliverables are:

- Raw telemetry validation
- Counter-reset detection
- Counter-reset-aware processing
- QoS feature extraction
- Processed QoS dataset
- Throughput visualization
- Validation evidence screenshot
- Processing scripts
Week 4 technical report
## 10. Week 4 Outcome

Week 4 successfully converts the raw OpenFlow telemetry into a validated, interval-based QoS feature dataset.

The raw telemetry remains preserved, while the processed dataset provides a reproducible foundation for subsequent predictive traffic-engineering and self-healing experiments.
