# Final Project Report — Self-Healing & Network Resilience

**Author:** Member 3 (Self-Healing Design & Recovery-Evaluation Lead)  
**Project:** AI-Driven QoS-Aware Predictive Traffic Engineering & Self-Healing in SDN-Based Edge Networks  
**Course:** CS23502 — Networks and Data Communication  

---

## 1. Resilience Philosophy & The Two-Layer Strategy
Network failures in modern edge environments manifest in two distinct forms:
1. **Hard Failures (Physical Outages):** Fiber cuts, switch hardware faults, or link interface crashes that immediately disconnect a transmission path.
2. **Soft Failures (Degradation & Congestion):** Bursty background traffic, bufferbloat, or link quality degradation where packets still pass but latency and packet loss violate strict QoS Service Level Agreements (SLAs).

To address both without conflict, we designed and implemented a **Two-Layer Resilience Architecture**:

```
+-----------------------------------------------------------------------------------+
|                        Two-Layer Resilience Architecture                           |
|                                                                                   |
|  [ LAYER 2: Proactive AI Self-Healing ] (Software / Control Plane)                |
|  - Scope: Soft degradation, predictive congestion, and SLA protection.            |
|  - Mechanism: LSTM forecasting + Anomaly detector + 15s Cooldown Timer.          |
|  - Action: Proactively offloads bulk TCP to backup link before drops happen.      |
|                                                                                   |
|  [ LAYER 1: Hardware Fast-Failover ] (Data Plane / Switch Kernel)                 |
|  - Scope: Hard physical link breakages (loss of carrier).                         |
|  - Mechanism: OpenFlow 1.3 Group Tables with watched ports.                       |
|  - Action: Switch-local sub-second failover (< 50 ms) without controller roundtrip.|
+-----------------------------------------------------------------------------------+
```

### Avoiding Conflict Between Layers
A major architectural risk in multi-layer SDN systems is **control race conditions**: Layer 2 issuing flow updates while Layer 1 is transitioning buckets. Our design eliminates this via strict precedence:
- If a link carrier state is `DOWN`, Layer 2 **defers entirely** (`DEFER_TO_FAST_FAILOVER`) and suppresses flow modifications.
- Layer 2 operates exclusively when links are `UP` but experiencing predictive congestion.
- A 15-second cooldown timer prevents route oscillation under fluctuating loads.

---

## 2. Measurement Methodology & Recovery Definition
Recovery latency is defined rigorously following RFC 2544 and Reitmann et al. (2019):
$$\text{Recovery Latency } (T_{\text{rec}}) = t_{\text{first\_successful\_rx\_on\_backup}} - t_{\text{link\_down\_event}}$$

To measure this with millisecond fidelity:
1. High-rate pings are sent at an interval of $T = 10\text{ ms}$ ($100\text{ Hz}$) from `h1` to `h3`.
2. The number of lost pings during the failure window ($N_{\text{lost}}$) is counted.
3. Recovery latency is calculated as:
   $$T_{\text{rec}} = N_{\text{lost}} \times 10\text{ ms}$$
4. Switch group statistics (`ovs-ofctl dump-group-stats`) independently confirm packet volume migrating from Bucket 0 to Bucket 1.

---

## 3. Empirical Results & The Sub-Second Claim
Across 30 repeated trials in Scenario S3:
- **Baseline (Static Shortest Path):** Mean recovery time = **8,000.00 ms** (complete loss during outage).
- **Reactive SDN (Flow-Mod):** Mean recovery time = **1,535.00 ms** ($\sigma = 118.25\text{ ms}$).
- **Proposed System (`full_ai_qos_ff`):** Mean recovery time = **41.00 ms** ($\sigma = 3.16\text{ ms}$, $p_{95} = 50.00\text{ ms}$).

### Verdict on the "Sub-Second" Claim:
The project's original review report promised sub-second recovery (< 1,000 ms). The empirical evidence confirms a measured recovery time of **~41 ms**, which is **24x faster** than the promised target. Furthermore, queue preservation was confirmed in all trials: high-priority streams retained QoS queue isolation immediately upon reaching the backup link.

---

## 4. Edge Cases: Flapping, Overload & Double Failure
As documented in `docs/week11/extra-scenarios-results.md`:
1. **Link Flapping (5 cycles):** Fast-Failover alternated buckets smoothly while the 15s cooldown prevented controller oscillations.
2. **Failure Under Congestion:** Proactive bulk redirection occurred prior to link-down; when link-down occurred, priority traffic failed over without packet loss.
3. **Double Failure (Total Partition):** The system dropped packets gracefully without controller crashing, and restored connectivity instantly when either link reconnected.

---

## 5. Technical Limitations & Future Scope
- **Emulation Timing Constraints:** OVS in Mininet runs on general-purpose Linux kernel threads. While 41 ms is excellent, real OpenFlow/P4 ASIC hardware switches (e.g. Intel Tofino, Broadcom StrataXGS) achieve sub-10 ms failover.
- **Topology Complexity:** The current prototype uses a 3-switch edge mesh. Future extensions will incorporate Multi-Path BFD (Bidirectional Forwarding Detection) over complex spine-and-leaf fabrics.
- **Future Work:**
  1. Integrating Reinforcement Learning (PPO / DQN) for dynamic multi-path weight allocation.
  2. Deployment on physical Raspberry Pi OpenFlow hardware switches.
  3. BFD hardware offloading for microsecond-level link fault detection.
