# Week 11: Comprehensive Experiment Execution Log

**Author:** Member 2 (Data-Plane Failover & Experiment Lead)
**Reviewers:** Member 1, Member 3, Member 4
**Date:** Week 11
**Status:** COMPLETE — 45 TRIALS EXECUTED & VALIDATED (GATE C REACHED)

---

## 1. Scenario S3 (Link-Down Failover Trials: 30 Runs)

| Trial ID | Mode | Scenario | Recovery Time (ms) | Ping Loss (Pings) | Throughput (Mbps) | Jitter (ms) | Status | Notes |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `trial_s3_001` | `baseline_shortest_path` | S3_failure | 8000.0 | 800 | 4.76 | 8.59 | VALID | No failover mechanism; traffic halted for full 8.0s link outage. |
| `trial_s3_002` | `baseline_shortest_path` | S3_failure | 8000.0 | 800 | 4.61 | 9.28 | VALID | No failover mechanism; traffic halted for full 8.0s link outage. |
| `trial_s3_003` | `baseline_shortest_path` | S3_failure | 8000.0 | 800 | 4.79 | 10.87 | VALID | No failover mechanism; traffic halted for full 8.0s link outage. |
| `trial_s3_004` | `baseline_shortest_path` | S3_failure | 8000.0 | 800 | 4.86 | 8.8 | VALID | No failover mechanism; traffic halted for full 8.0s link outage. |
| `trial_s3_005` | `baseline_shortest_path` | S3_failure | 8000.0 | 800 | 4.67 | 8.6 | VALID | No failover mechanism; traffic halted for full 8.0s link outage. |
| `trial_s3_006` | `baseline_shortest_path` | S3_failure | 8000.0 | 800 | 4.59 | 10.27 | VALID | No failover mechanism; traffic halted for full 8.0s link outage. |
| `trial_s3_007` | `baseline_shortest_path` | S3_failure | 8000.0 | 800 | 4.51 | 9.2 | VALID | No failover mechanism; traffic halted for full 8.0s link outage. |
| `trial_s3_008` | `baseline_shortest_path` | S3_failure | 8000.0 | 800 | 4.76 | 10.41 | VALID | No failover mechanism; traffic halted for full 8.0s link outage. |
| `trial_s3_009` | `baseline_shortest_path` | S3_failure | 8000.0 | 800 | 4.59 | 10.56 | VALID | No failover mechanism; traffic halted for full 8.0s link outage. |
| `trial_s3_010` | `baseline_shortest_path` | S3_failure | 8000.0 | 800 | 4.82 | 8.52 | VALID | No failover mechanism; traffic halted for full 8.0s link outage. |
| `trial_s3_011` | `reactive` | S3_failure | 1641.18 | 164 | 6.97 | 4.39 | VALID | Reactive reroute installed via controller Flow-Mod in 1641.2ms. |
| `trial_s3_012` | `reactive` | S3_failure | 1580.06 | 158 | 6.85 | 4.24 | VALID | Reactive reroute installed via controller Flow-Mod in 1580.1ms. |
| `trial_s3_013` | `reactive` | S3_failure | 1615.48 | 162 | 7.2 | 5.82 | VALID | Reactive reroute installed via controller Flow-Mod in 1615.5ms. |
| `trial_s3_014` | `reactive` | S3_failure | 1704.3 | 170 | 6.99 | 5.38 | VALID | Reactive reroute installed via controller Flow-Mod in 1704.3ms. |
| `trial_s3_015` | `reactive` | S3_failure | 1612.95 | 161 | 7.23 | 5.44 | VALID | Reactive reroute installed via controller Flow-Mod in 1612.9ms. |
| `trial_s3_016` | `reactive` | S3_failure | 1490.46 | 149 | 6.91 | 4.72 | VALID | Reactive reroute installed via controller Flow-Mod in 1490.5ms. |
| `trial_s3_017` | `reactive` | S3_failure | 1346.64 | 135 | 6.85 | 4.69 | VALID | Reactive reroute installed via controller Flow-Mod in 1346.6ms. |
| `trial_s3_018` | `reactive` | S3_failure | 1490.31 | 149 | 6.99 | 4.52 | VALID | Reactive reroute installed via controller Flow-Mod in 1490.3ms. |
| `trial_s3_019` | `reactive` | S3_failure | 1521.47 | 152 | 6.89 | 5.82 | VALID | Reactive reroute installed via controller Flow-Mod in 1521.5ms. |
| `trial_s3_020` | `reactive` | S3_failure | 1347.64 | 135 | 7.29 | 5.6 | VALID | Reactive reroute installed via controller Flow-Mod in 1347.6ms. |
| `trial_s3_021` | `full_ai_qos_ff` | S3_failure | 42.49 | 4 | 8.14 | 1.64 | VALID | Fast-Failover hardware group bucket transition in 42.5ms. |
| `trial_s3_022` | `full_ai_qos_ff` | S3_failure | 40.12 | 4 | 7.88 | 1.76 | VALID | Fast-Failover hardware group bucket transition in 40.1ms. |
| `trial_s3_023` | `full_ai_qos_ff` | S3_failure | 44.51 | 4 | 8.06 | 1.38 | VALID | Fast-Failover hardware group bucket transition in 44.5ms. |
| `trial_s3_024` | `full_ai_qos_ff` | S3_failure | 45.71 | 5 | 7.91 | 1.27 | VALID | Fast-Failover hardware group bucket transition in 45.7ms. |
| `trial_s3_025` | `full_ai_qos_ff` | S3_failure | 41.96 | 4 | 8.03 | 1.73 | VALID | Fast-Failover hardware group bucket transition in 42.0ms. |
| `trial_s3_026` | `full_ai_qos_ff` | S3_failure | 40.79 | 4 | 8.2 | 1.46 | VALID | Fast-Failover hardware group bucket transition in 40.8ms. |
| `trial_s3_027` | `full_ai_qos_ff` | S3_failure | 35.75 | 4 | 8.12 | 1.4 | VALID | Fast-Failover hardware group bucket transition in 35.7ms. |
| `trial_s3_028` | `full_ai_qos_ff` | S3_failure | 37.63 | 4 | 8.2 | 1.47 | VALID | Fast-Failover hardware group bucket transition in 37.6ms. |
| `trial_s3_029` | `full_ai_qos_ff` | S3_failure | 43.65 | 4 | 7.91 | 1.55 | VALID | Fast-Failover hardware group bucket transition in 43.7ms. |
| `trial_s3_030` | `full_ai_qos_ff` | S3_failure | 37.73 | 4 | 7.98 | 1.77 | VALID | Fast-Failover hardware group bucket transition in 37.7ms. |

---

## 2. Scenario S2 (Heavy Congestion Trials: 15 Runs)

| Trial ID | Mode | Scenario | Priority Latency (ms) | Jitter (ms) | Packet Loss (%) | Throughput (Mbps) | Status | Notes |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `trial_s2_001` | `baseline_shortest_path` | S2_congestion | 52.18 | 14.8 | 19.58% | 4.17 | VALID | Severe queue congestion; FIFO drops priority packets; high latency. |
| `trial_s2_002` | `baseline_shortest_path` | S2_congestion | 52.61 | 16.63 | 20.73% | 3.69 | VALID | Severe queue congestion; FIFO drops priority packets; high latency. |
| `trial_s2_003` | `baseline_shortest_path` | S2_congestion | 50.7 | 14.63 | 21.08% | 4.17 | VALID | Severe queue congestion; FIFO drops priority packets; high latency. |
| `trial_s2_004` | `baseline_shortest_path` | S2_congestion | 45.37 | 14.4 | 19.81% | 3.9 | VALID | Severe queue congestion; FIFO drops priority packets; high latency. |
| `trial_s2_005` | `baseline_shortest_path` | S2_congestion | 46.01 | 11.21 | 18.82% | 3.93 | VALID | Severe queue congestion; FIFO drops priority packets; high latency. |
| `trial_s2_006` | `reactive` | S2_congestion | 25.76 | 6.0 | 5.06% | 6.41 | VALID | QoS Queue 1 limits drops on priority, but bulk TCP remains on primary link. |
| `trial_s2_007` | `reactive` | S2_congestion | 21.58 | 7.28 | 4.42% | 7.23 | VALID | QoS Queue 1 limits drops on priority, but bulk TCP remains on primary link. |
| `trial_s2_008` | `reactive` | S2_congestion | 20.08 | 6.03 | 4.11% | 6.94 | VALID | QoS Queue 1 limits drops on priority, but bulk TCP remains on primary link. |
| `trial_s2_009` | `reactive` | S2_congestion | 23.61 | 6.17 | 4.47% | 6.15 | VALID | QoS Queue 1 limits drops on priority, but bulk TCP remains on primary link. |
| `trial_s2_010` | `reactive` | S2_congestion | 21.82 | 6.51 | 4.01% | 7.01 | VALID | QoS Queue 1 limits drops on priority, but bulk TCP remains on primary link. |
| `trial_s2_011` | `full_ai_qos_ff` | S2_congestion | 6.5 | 1.21 | 0.08% | 9.5 | VALID | Proactive AI rerouting shifted bulk TCP to backup path; priority delay minimal. |
| `trial_s2_012` | `full_ai_qos_ff` | S2_congestion | 7.29 | 1.38 | 0.14% | 9.33 | VALID | Proactive AI rerouting shifted bulk TCP to backup path; priority delay minimal. |
| `trial_s2_013` | `full_ai_qos_ff` | S2_congestion | 7.96 | 0.84 | 0.08% | 9.48 | VALID | Proactive AI rerouting shifted bulk TCP to backup path; priority delay minimal. |
| `trial_s2_014` | `full_ai_qos_ff` | S2_congestion | 6.84 | 0.93 | 0.07% | 9.35 | VALID | Proactive AI rerouting shifted bulk TCP to backup path; priority delay minimal. |
| `trial_s2_015` | `full_ai_qos_ff` | S2_congestion | 8.76 | 1.36 | 0.04% | 9.2 | VALID | Proactive AI rerouting shifted bulk TCP to backup path; priority delay minimal. |
