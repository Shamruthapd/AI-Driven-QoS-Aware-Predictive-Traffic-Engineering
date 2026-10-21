# Week 8 – Member 4: QoS ON vs OFF Analysis

## 1. Objective

Analyze the contention benchmark measurements and quantify the effect of enabling QoS on priority UDP video traffic and bulk TCP data traffic.

## 2. Input Measurements

The benchmark compared QoS OFF and QoS ON using simultaneous traffic flows:

- Priority UDP video: client sends to host `h3` on UDP port 5202.
- Bulk TCP data: client sends to host `h2` on TCP port 5201.

UDP throughput, jitter, and packet loss below are taken from iperf3 receiver output. TCP throughput is taken from the TCP receiver summary.

## 3. QoS OFF vs QoS ON Results

| Metric | QoS OFF | QoS ON | Change |
|---|---:|---:|---:|
| Priority UDP receiver throughput | 7.98 Mbps | 7.98 Mbps | 0.00% |
| Priority UDP receiver jitter | 0.014 ms | 0.023 ms | +0.009 ms |
| Priority UDP receiver packet loss | 0.0% | 0.0% | 0.0 percentage points |
| Bulk TCP receiver throughput | 12.00 Mbps | 3.82 Mbps | -68.17% |

The QoS-enabled run substantially reduced measured TCP throughput while the UDP flow maintained approximately 7.98 Mbps. Receiver-side UDP jitter increased slightly from 0.014 ms to 0.023 ms.

## 4. Priority UDP Analysis

- QoS OFF receiver throughput: 7.98 Mbps.
- QoS ON receiver throughput: 7.98 Mbps.
- QoS OFF receiver jitter: 0.014 ms.
- QoS ON receiver jitter: 0.023 ms.
- Receiver-reported packet loss: 0 of 10,359 datagrams in each run (0%).

The QoS-enabled benchmark installed an OpenFlow rule matching UDP destination port 5202 and applying `set_queue:1` before output to `s1-eth3`.

The flow table showed 10,360 matching UDP packets. Queue statistics for port 3 showed Queue 1 transmitted 10,360 packets and 15,434,956 bytes, with zero queue errors. This confirms that Queue 1 was used during the measured run.

## 5. Bulk TCP Analysis

- QoS OFF receiver throughput: 12.00 Mbps.
- QoS ON receiver throughput: 3.82 Mbps.
- Throughput change: -68.17%.

The benchmark installed an OpenFlow rule matching TCP destination port 5201 and applying `set_queue:0` before output to `s1-eth2`.

Queue statistics for port 2 showed Queue 0 transmitted 5,233 packets and 7,876,912 bytes, with zero queue errors. The measured QoS ON TCP throughput is consistent with the configured Queue 0 maximum rate of approximately 4 Mbps.

## 6. Member 4 Data Pipeline Contribution

- Measurement parser: `scripts/parse_measurements.py`
- Input JSON files: `logs/h2_bulk_off.json`, `logs/h2_bulk_on.json`, `logs/h3_priority_off.json`, and `logs/h3_priority_on.json`
- Measurement CSV: `data/results/week8_qos_on_vs_off_measurements.csv`
- Analysis script: `scripts/analyze_week8_qos.py`
- Analysis CSV: `data/results/week8_qos_analysis.csv`

The parser reads UDP receiver summaries from iperf3 server output and writes throughput, jitter, and packet-loss measurements. The analysis script calculates throughput percentage change, jitter change, and packet-loss change between the two states.

## 7. Findings and Limitations

The measured run confirms that the intended TCP-to-Queue-0 and UDP-to-Queue-1 mappings carried traffic. The TCP throughput decreased by 68.17%, while UDP receiver throughput remained stable at 7.98 Mbps with zero reported loss.

These are single-run results, not repeated-trial statistics. They demonstrate the observed behavior under this test configuration but do not establish a universal priority guarantee under all traffic loads.

## 8. Member 4 Conclusion

The Week 8 measurement and analysis pipeline has been executed successfully. Receiver-side UDP metrics and actual OpenFlow queue counters have been captured, and the reports document the latest measurements and their limitations.
