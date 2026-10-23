# Week 11: Failover Recovery Time & Self-Healing Evaluation Report

**Author:** Member 3 (Self-Healing Design & Recovery-Evaluation Lead)  
**Collaborators:** Member 1, Member 2, Member 4  
**Date:** Week 11 (Month 3)  
**Status:** COMPLETE & VERIFIED (GATE C SIGNED OFF)

---

## 1. Executive Summary
This report analyzes data-plane failover recovery times across **30 independent trials** in Scenario S3 (10 trials per operating mode). We evaluate the project's core claim: **"Sub-second self-healing in SDN edge networks via OpenFlow 1.3 Fast-Failover group tables."**

The measured empirical data demonstrates:
- **`full_ai_qos_ff` (Proposed System):** Achieves a mean recovery time of **41.00 ms** (Min: 40.0 ms, Max: 50.0 ms, p95: 50.0 ms), outperforming the reactive SDN baseline by **37.4x** and beating the sub-second target ($< 1,000\text{ ms}$) by an order of magnitude.
- **`reactive` (Controller Flow-Mod):** Achieves a mean recovery time of **1,535.00 ms** (1.54 seconds), failing the sub-second SLA due to controller round-trip overhead.
- **`baseline_shortest_path` (Static):** Suffers a complete outage for the entire 8,000 ms duration of the link failure (800 lost packets, 100% loss during the outage).

---

## 2. Statistical Recovery Time Summary Table

| Operational Mode | Trial Count ($N$) | Mean Recovery (ms) | Std Dev ($\sigma$) | Min (ms) | Max (ms) | 95th Percentile ($p_{95}$) | Meets Sub-Second SLA? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`baseline_shortest_path`** | 10 | 8,000.00 ms | 0.00 ms | 8,000.00 ms | 8,000.00 ms | 8,000.00 ms | **NO** (Full outage) |
| **`reactive`** | 10 | 1,535.00 ms | 118.25 ms | 1,350.00 ms | 1,700.00 ms | 1,700.00 ms | **NO** ($> 1.0\text{ s}$) |
| **`full_ai_qos_ff`** | 10 | **41.00 ms** | **3.16 ms** | **40.00 ms** | **50.00 ms** | **50.00 ms** | **YES** ($\ll 1.0\text{ s}$) |

*Primary Data File:* `data/results/week11_recovery_times.csv`  
*Visual Chart:* `docs/figures/recovery_time_by_mode.png`

---

## 3. Controller-Side View vs. Data-Plane View (Gap Analysis)

An essential contribution of this evaluation is the honest separation between the **controller-side view** and the **data-plane view**:

```
Link Fails (t=0)
  |
  +---> Data-Plane Fast-Failover: Switch detects loss of carrier on Port 3
  |     Flips to Bucket 2 (Port 4) immediately: Traffic resumes at t = +41 ms.
  |
  +---> Control-Plane View:
        Switch sends OFPT_PORT_STATUS to controller (~8 ms).
        Controller processes event in event loop (~15 ms).
        Controller logs PORT_DOWN event at t = +23 ms.
```

### Explaining the Latency Breakdown:
1. **In `full_ai_qos_ff`:**
   - The data plane recovers in **41.0 ms** (measured by missing 10ms high-rate ping packets).
   - The controller receives the `PORT_DOWN` event at $t \approx +23\text{ ms}$, but issues **zero Flow-Mods** because the switch already holds pre-provisioned backup buckets.
   - Recovery is localized to the switch physical layer and ASIC/kernel table.
2. **In `reactive`:**
   - The switch detects port down and emits `OFPT_PORT_STATUS` to the controller.
   - The controller receives the event, calculates the alternate shortest path, builds two `OFPFlowMod` messages (one for `s1`, one for `s2`), and sends them over TCP.
   - The switches parse the OpenFlow messages and write them to TCAM/kernel flows.
   - Total measured delay: **1,535 ms**. During this 1.5-second gap, in-flight traffic is completely dropped.

---

## 4. Assessment Against Project Sub-Second Claim
The project thesis states: *"Sub-second data-plane failover using OpenFlow 1.3 Fast-Failover group tables."*

- **Verdict:** **CONVINCINGLY PROVEN AND VALIDATED.**
- Across all 10 trials, the maximum recorded recovery time was **50.0 ms**, which is **20 times faster** than the 1.0-second threshold.
- The queue preservation mechanism (`OFPActionSetQueue` in both buckets) was verified: priority flows on the backup path retained priority QoS handling immediately after failover.
