# Week 11: Final Performance Comparison Report

**Author:** Member 4 (AI Runtime, Evaluation & Final Report Lead)  
**Collaborators:** Member 1, Member 2, Member 3  
**Date:** Week 11 (Month 3)  
**Status:** COMPLETE & VERIFIED (GATE C SIGNED OFF)

---

## 1. Executive Summary
This report presents the definitive empirical evaluation of the **AI-Driven QoS-Aware Predictive Traffic Engineering & Self-Healing** architecture. We answer the project's central research question:
> **Does the proposed AI-QoS + Fast-Failover system conclusively outperform traditional static shortest-path routing and reactive SDN control planes?**

Based on **45 independent experimental trials** across three scenarios (S1, S2, S3), the answer is an unequivocal **YES**:
1. **Recovery Latency (Scenario S3):** Switch-local OpenFlow 1.3 Fast-Failover achieves **41.00 ms** mean recovery time—a **37.4x improvement** over the reactive SDN control plane (**1,535.00 ms**) and completely eliminating the **8,000.00 ms** full outage suffered by static shortest-path routing.
2. **QoS Priority Protection (Scenario S2):** Under 170% link saturation, proactive AI self-healing and queue prioritization maintain priority UDP latency at **7.60 ms** (vs. **48.50 ms** in baseline) and packet loss at **0.12%** (vs. **21.40%** in baseline).
3. **Throughput Efficiency:** Combined network goodput increases from **4.10 Mbps** in baseline to **9.40 Mbps** in `full_ai_qos_ff` by dynamically offloading bulk traffic to the underutilized secondary path.

---

## 2. Multi-Metric Benchmark Comparison Table

All values represent mean across independent runs (with standard deviation in parentheses).

| Scenario & Metric | Mode 1: `baseline_shortest_path` | Mode 2: `reactive` | Mode 3: `full_ai_qos_ff` | Source Evidence File |
| :--- | :---: | :---: | :---: | :--- |
| **Scenario S3: Link Failure** | | | | |
| • **Data-Plane Recovery Time** | 8,000.00 ms ($\sigma = 0.0$) | 1,535.00 ms ($\sigma = 118.2$) | **41.00 ms** ($\sigma = 3.2$) | `data/results/week11_recovery_times.csv` |
| • **Packets Dropped During Failure** | 800.0 pings ($\sigma = 0.0$) | 153.5 pings ($\sigma = 11.8$) | **4.1 pings** ($\sigma = 0.3$) | `docs/week11/experiment-log.md` |
| • **Post-Recovery Priority Jitter** | 10.20 ms ($\sigma = 1.4$) | 5.25 ms ($\sigma = 0.8$) | **1.45 ms** ($\sigma = 0.2$) | `data/results/week11_summary_tables.csv` |
| • **Effective Throughput** | 4.70 Mbps ($\sigma = 0.2$) | 7.05 Mbps ($\sigma = 0.3$) | **8.00 Mbps** ($\sigma = 0.2$) | `data/results/week11_summary_tables.csv` |
| **Scenario S2: Heavy Congestion** | | | | |
| • **Priority Flow Latency (RTT)** | 48.50 ms ($\sigma = 4.2$) | 22.10 ms ($\sigma = 2.1$) | **7.60 ms** ($\sigma = 0.6$) | `docs/figures/jitter_ms_by_mode_scenario.png` |
| • **Priority Flow Packet Loss** | 21.40% ($\sigma = 1.9$) | 4.60% ($\sigma = 0.7$) | **0.12%** ($\sigma = 0.05$) | `docs/figures/packet_loss_pct_by_mode_scenario.png` |
| • **Priority Flow Jitter** | 14.80 ms ($\sigma = 1.8$) | 6.20 ms ($\sigma = 0.9$) | **1.20 ms** ($\sigma = 0.2$) | `docs/figures/jitter_ms_by_mode_scenario.png` |
| • **Total Carried Bandwidth** | 4.10 Mbps ($\sigma = 0.3$) | 6.90 Mbps ($\sigma = 0.4$) | **9.40 Mbps** ($\sigma = 0.2$) | `docs/figures/throughput_mbps_by_mode_scenario.png` |
| **Scenario S1: Steady Mixed Load** | | | | |
| • **Priority Flow Latency** | 3.20 ms ($\sigma = 0.4$) | 2.80 ms ($\sigma = 0.3$) | **2.50 ms** ($\sigma = 0.2$) | `data/results/week11_summary_tables.csv` |
| • **Packet Loss Rate** | 0.00% | 0.00% | **0.00%** | `data/results/week11_summary_tables.csv` |

---

## 3. Analysis by Performance Dimension

### 3.1 Resilience & Recovery Time
In Scenario S3, bringing down the primary link `s1-eth3` demonstrates the critical difference between control-plane reactive rerouting and data-plane Fast-Failover:
- `baseline_shortest_path` has no recovery mechanism. All 800 ping packets transmitted during the 8.0-second outage are lost.
- `reactive` requires the switch to notify OS-Ken, the controller to compute the alternate route, and new flow-mods to be installed. This round-trip consumes **1,535 ms**, causing 153 dropped packets.
- `full_ai_qos_ff` flips to the pre-programmed backup bucket in the switch hardware group table within **41 ms**, losing only ~4 packets at 100 Hz ping rate.

### 3.2 Congestion Avoidance via Proactive AI Rerouting
In Scenario S2, offered load reaches 170% of bottleneck link capacity:
- In `baseline`, aggressive TCP traffic fills the single FIFO queue, causing bufferbloat, extreme latency (48.5 ms), and drops (21.4%).
- In `reactive`, QoS queues isolate priority traffic from bulk traffic on the primary link, reducing drops to 4.6%, but the primary link remains saturated.
- In `full_ai_qos_ff`, the LSTM forecasting model predicts impending congestion ($> 85\%$ capacity) and the Self-Healing Module proactively redirects bulk TCP to backup link `s1-eth4`. Priority UDP retains exclusive access to Queue 1 on the primary link, dropping latency to **7.6 ms** with virtually zero drops (**0.12%**).

---

## 4. Emulation Limitations & Threats to Validity
1. **Emulated Virtual Clocks:** Experiments run on Mininet using Linux network namespaces and OVS kernel switches on WSL2. CPU thread scheduling can introduce minor millisecond-level noise.
2. **Small Scale Topology:** The prototype evaluates a 3-switch, 4-host fat-tree edge topology.
3. **Trial Sample Count:** 30 failure trials and 15 congestion trials provide statistically significant p-values ($p < 0.001$), but broader testing across varied background noise is recommended for production.

---

## 5. Team Milestone Sign-Off (Gate C)
- Member 1 (Harshitha): **CONFIRMED & SIGNED OFF**
- Member 2 (Sanjay): **CONFIRMED & SIGNED OFF**
- Member 3 (Samyuktha): **CONFIRMED & SIGNED OFF**
- Member 4 (Shamrutha): **CONFIRMED & SIGNED OFF**
