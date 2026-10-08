# Week 8 – Member 4: QoS ON vs OFF Analysis

## 1. Objective

Analyze the Week 8 contention benchmark measurements and quantify the effect of QoS enforcement on the priority UDP and bulk TCP flows.

## 2. Input Measurements

The benchmark measurements were collected for two network states:

- QoS OFF
- QoS ON

Two traffic flows were evaluated:

- Priority UDP video flow
- Bulk TCP data flow

The measurements include throughput, jitter, and packet loss.

## 3. QoS OFF vs QoS ON Results

| Flow | QoS OFF Throughput | QoS ON Throughput | Throughput Change |
|---|---:|---:|---:|
| Priority UDP Video | 8.00 Mbps | 3.95 Mbps | -50.62% |
| Bulk TCP Data | 12.02 Mbps | 3.76 Mbps | -68.72% |

The QoS ON state reduced the measured throughput of both flows.

## 4. Priority UDP Analysis

For the priority UDP video flow:

- QoS OFF throughput: 8.00 Mbps
- QoS ON throughput: 3.95 Mbps
- Throughput change: -50.62%
- QoS OFF jitter: 0.041 ms
- QoS ON jitter: 3.432 ms
- Jitter increase: 3.391 ms
- Packet loss remained 0%

The priority UDP flow therefore experienced a significant throughput reduction and increased jitter when QoS was enabled.

The current benchmark report indicates that the priority UDP flow was assigned to Queue 0 instead of the intended Queue 1. Therefore, these measurements do not yet demonstrate the final priority-QoS behavior.

## 5. Bulk TCP Analysis

For the bulk TCP data flow:

- QoS OFF throughput: 12.02 Mbps
- QoS ON throughput: 3.76 Mbps
- Throughput change: -68.72%
- Jitter remained 0 ms
- Packet loss remained 0%

The reduction is consistent with the Queue 0 HTB maximum rate of approximately 4 Mbps.

## 6. Member 4 Data Pipeline Contribution

Member 4 processed the contention benchmark measurements into a structured CSV:

`data/results/week8_qos_on_vs_off_measurements.csv`

The analysis script:

`scripts/analyze_week8_qos.py`

produces:

`data/results/week8_qos_analysis.csv`

The analysis calculates:

- QoS OFF throughput
- QoS ON throughput
- Percentage throughput change
- QoS OFF jitter
- QoS ON jitter
- Jitter change
- QoS OFF packet loss
- QoS ON packet loss
- Packet loss change

## 7. Current Finding

The Week 8 benchmark confirms that the QoS configuration is actively affecting traffic.

However, the current results should not be interpreted as the final priority-QoS result because the priority UDP flow is currently using Queue 0.

The Week 8 benchmark report identifies the required controller-side change:

`actions=set_queue:1`

for the priority UDP flow targeting destination UDP port 5202 / host `10.0.0.3`.

After the controller-side queue binding is corrected, the contention benchmark should be repeated and the resulting measurements should be analyzed again.

## 8. Member 4 Conclusion

Member 4 has completed the data-analysis portion of the Week 8 contention benchmark.

The current results demonstrate measurable QoS impact and provide a reproducible quantitative comparison between QoS OFF and QoS ON states.

The next validation should be performed after the priority UDP flow is correctly mapped to Queue 1. This will allow the final QoS-aware traffic engineering behavior to be evaluated using the same measurement and analysis pipeline.