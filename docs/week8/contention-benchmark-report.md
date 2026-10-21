# Week 8 Contention Benchmark & Telemetry Handshake Report

## Summary of Results

The contention benchmark was run with QoS OFF and QoS ON using simultaneous bulk TCP and priority UDP traffic.

| Metric | QoS OFF | QoS ON |
|---|---:|---:|
| Bulk TCP receiver throughput | 12.00 Mbps | 3.82 Mbps |
| Priority UDP receiver throughput | 7.98 Mbps | 7.98 Mbps |
| Priority UDP receiver jitter | 0.014 ms | 0.023 ms |
| Priority UDP receiver packet loss | 0.0% | 0.0% |

Bulk TCP throughput decreased by 68.17% when QoS was enabled. UDP throughput remained at 7.98 Mbps, while receiver-side jitter increased by 0.009 ms. The UDP receiver reported 0 lost datagrams out of 10,359 in both tests.

## Queue Mapping Verification

The QoS-enabled benchmark installed these OpenFlow rules:

- TCP destination port 5201: `set_queue:0`, output to `s1-eth2`.
- UDP destination port 5202: `set_queue:1`, output to `s1-eth3`.

Queue counters were captured before Mininet shutdown:

- Port 2, Queue 0: 5,233 packets, 7,876,912 bytes, 0 queue errors.
- Port 3, Queue 1: 10,360 packets, 15,434,956 bytes, 0 queue errors.

The counters confirm that both queues carried traffic and that the intended queue mappings were active during this test.

## Data Pipeline

- Benchmark JSON: `logs/h2_bulk_{off,on}.json` and `logs/h3_priority_{off,on}.json`
- Measurement CSV: `data/results/week8_qos_on_vs_off_measurements.csv`
- Analysis script: `scripts/analyze_week8_qos.py`
- Analysis CSV: `data/results/week8_qos_analysis.csv`

The parser uses the UDP server's receiver summary for throughput, jitter, and packet loss.

## Conclusion and Limitations

The test demonstrates reduced bulk TCP throughput under the configured QoS setup, while the priority UDP flow maintained its requested throughput with no receiver-reported packet loss in this run. Queue counters confirm queue assignment and traffic transmission.

These results are from a single benchmark run per state. They do not by themselves establish a general priority guarantee under different loads or repeated trials. The queue counters show traffic transmission, not a complete end-to-end QoS guarantee.
