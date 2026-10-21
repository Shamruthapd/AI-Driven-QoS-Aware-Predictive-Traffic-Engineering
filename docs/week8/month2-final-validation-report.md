# Month 2 Final Validation Report — Member 4

## 1. Objective

Validate the Week 7 telemetry and LSTM prediction pipeline and the Week 8 QoS contention benchmark. Document the measured results, current limitations, and evidence still required for full-system validation.

## 2. Week 7 — Telemetry and LSTM Validation

### 2.1 Telemetry processing

The telemetry pipeline processes switch-port counters and derives traffic features for model evaluation. The processing script excludes port `4294967294` from link-level processing.

The raw telemetry dataset contains 10,721 rows, 11 columns, no missing values, and no duplicate rows. The captured data spans 8 August 2026 to 21 October 2026.

### 2.2 LSTM error analysis

The existing validation report records 121 validation sequences and the following results:

- Overall MSE: 37.632519
- Normal-sample MSE: 6.959243
- Anomalous-sample MSE: 113.001137
- Precision at MSE threshold 5: 0.4600
- Recall at MSE threshold 5: 0.6571
- F1-score at MSE threshold 5: 0.5412

The validation distribution differs substantially from the training distribution. The prediction errors are too large to treat raw predicted throughput as a reliable utilization-control signal without further calibration and validation.

### 2.3 Utilization calibration

The calibration script converts predicted throughput to a percentage using the configured 10 Mbps capacity:

`predicted_utilization_pct = predicted_throughput_bps / 10,000,000 × 100`

The result is clipped to the 0–100% range. This provides a normalized engineering signal, but clipping alone does not establish prediction accuracy or suitability for autonomous control.

## 3. Week 8 — QoS Contention Benchmark

Two simultaneous flows were tested with QoS disabled and enabled:

- Bulk TCP traffic to host h2, destination port 5201, offered at 12 Mbps.
- Priority UDP traffic to host h3, destination port 5202, offered at 8 Mbps.

### 3.1 Measured results

| Metric | QoS OFF | QoS ON |
|---|---:|---:|
| Bulk TCP receiver throughput | 12.00 Mbps | 3.82 Mbps |
| Priority UDP receiver throughput | 7.98 Mbps | 7.98 Mbps |
| Priority UDP receiver jitter | 0.014 ms | 0.023 ms |
| Priority UDP receiver packet loss | 0.0% | 0.0% |

Bulk TCP receiver throughput decreased by 68.17%. Priority UDP receiver throughput remained approximately 7.98 Mbps, while jitter increased by 0.009 ms. The UDP receiver reported 0 lost datagrams out of 10,359 in each test.

### 3.2 Queue mapping verification

The QoS-enabled benchmark installed these rules:

- TCP destination port 5201: Queue 0, output to `s1-eth2`.
- UDP destination port 5202: Queue 1, output to `s1-eth3`.

Queue statistics confirmed traffic on Queue 0 at port 2 and Queue 1 at port 3. The UDP rule recorded 10,360 packets and 15,434,956 bytes, and Queue 1 at port 3 recorded the same traffic counters.

This verifies that the benchmark traffic was mapped to the intended queues during the QoS-enabled run.

## 4. Current Findings

The available evidence supports the following conclusions:

1. The telemetry-processing pipeline excludes the special port from link-level processing.
2. The LSTM prediction error remains a limitation for direct utilization-based autonomous control.
3. The QoS contention benchmark limits bulk TCP receiver throughput to approximately 3.82 Mbps.
4. The priority UDP flow maintains approximately 7.98 Mbps receiver throughput with zero reported packet loss in both test states.
5. OpenFlow flow and queue counters confirm that the tested TCP and UDP traffic used the intended queues.

These findings validate individual telemetry and QoS components. They do not, by themselves, prove that the complete AI-driven traffic-engineering system outperforms a static or reactive baseline.

## 5. Evidence Still Required for Full-System Validation

The following evidence is required before claiming full-system success:

- Member 1's enforcement log showing the actions applied by the controller.
- Member 3's decision log showing the AI-driven traffic-engineering decisions.
- Member 2's measurements for the corresponding traffic scenarios.
- Matched baseline and AI-driven runs using equivalent traffic conditions.
- A full-system comparison CSV containing the actual throughput, latency/jitter, and packet-loss measurements for those runs.

The full-system comparison should be generated from these recorded measurements. Missing values must not be invented or inferred from the isolated contention benchmark.

## 6. Conclusion

Member 4 has implemented and measured the Week 7 telemetry/calibration workflow and the Week 8 QoS contention benchmark. The measured results demonstrate effective queue mapping and a substantial reduction in bulk TCP receiver throughput while maintaining the tested UDP throughput and packet delivery.

The final AI-driven-versus-baseline comparison remains pending until the corresponding controller, decision, and traffic-measurement evidence is available.
