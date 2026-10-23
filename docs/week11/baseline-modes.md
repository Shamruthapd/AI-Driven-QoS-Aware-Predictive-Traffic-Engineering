# Week 11: Architectural Specification of Baseline & Comparative Modes

**Author:** Member 1 (Control-Plane Self-Healing & Integration Lead)  
**Collaborators:** Member 2, Member 3, Member 4  
**Date:** Week 11 (Month 3)  
**Status:** FROZEN & STANDARDIZED

---

## 1. Overview & Fair Testing Framework
To rigorously evaluate the proposed AI-Driven QoS-Aware Predictive Traffic Engineering & Self-Healing architecture, three standardized operating modes are executed against identical traffic loads, physical topologies, and failure schedules.

All three modes run from the **exact same controller codebase**, switched exclusively via `controller/config.yaml` or `controller/modes.py`.

---

## 2. Comparative Matrix

| Feature / Capability | Mode 1: `baseline_shortest_path` | Mode 2: `reactive` | Mode 3: `full_ai_qos_ff` (Proposed) |
| :--- | :---: | :---: | :---: |
| **Path Selection** | Static shortest path (`s1-s3-s2`) | Static shortest path with reactive fallback | Proactive AI dynamic routing + Fast-Failover |
| **QoS Queues & DSCP** | **Disabled** (All flows in Default FIFO) | **Enabled** (Queue 1: Priority, Queue 0: Bulk) | **Enabled** (Queue 1: Priority, Queue 0: Bulk) |
| **Telemetry Polling** | Disabled or passive | Active (5s interval) | Active (5s interval) |
| **LSTM Predictive Engine** | **Disabled** | **Disabled** | **Enabled** (Bandwidth forecasting, MSE anomaly detection) |
| **Proactive Congestion Reroute** | **None** (Drops occur on link saturation) | **None** (Reacts only to link down) | **Enabled** (Moves bulk traffic prior to packet drop) |
| **Failure Recovery Mechanism** | **None** (Packets dropped indefinitely) | **Controller-Initiated Reactive Flow-Mod** | **Switch-Local OpenFlow 1.3 Fast-Failover** |
| **Recovery Plane** | Control Plane (External) | Control Plane (Controller Round-Trip) | **Data Plane (Switch Hardware Local)** |
| **Expected Recovery Latency** | $\infty$ (Manual intervention) | $\approx 1.2\text{ s} - 2.5\text{ s}$ | **$< 50\text{ ms}$ (Sub-second)** |

---

## 3. Detailed Mode Specifications

### 3.1 Mode 1: `baseline_shortest_path`
- **What it does:**
  - Installs static OpenFlow forwarding rules directing all traffic along the primary backbone route `s1-eth3 <-> s3 <-> s2-eth3`.
  - Uses default FIFO switch queues with no queue shaping or bandwidth reservation.
- **What it DOES NOT do:**
  - Does not use Fast-Failover group tables.
  - Does not distinguish between high-priority VoIP and aggressive bulk TCP.
  - Does not react to link failure events (packets dropped until link is restored).

### 3.2 Mode 2: `reactive`
- **What it does:**
  - Configures QoS queues on switches to protect priority traffic under steady load.
  - Monitors link state via OpenFlow `EventOFPPortStatus`.
  - Upon receiving a `LINK_DOWN` event, the controller computes an alternate route (direct link `s1-eth4 <-> s2-eth4`) and dispatches new `OFPFlowMod` messages to reroute ongoing flows.
- **What it DOES NOT do:**
  - Does not proactively predict congestion or move traffic before packet loss occurs.
  - Does not provide sub-second failover: recovery latency is constrained by the controller-to-switch communication latency, event loop scheduling, and flow table reprogramming (1.2s - 2.5s).

### 3.3 Mode 3: `full_ai_qos_ff` (Proposed System)
- **What it does:**
  - **Layer 1 (Fast-Failover):** Edge switches `s1` and `s2` pre-install Fast-Failover groups with primary bucket (port 3) and backup bucket (port 4), embedding `OFPActionSetQueue` in both buckets. When a link drops, switch hardware fails over in $< 50\text{ ms}$ with zero controller roundtrip.
  - **Layer 2 (AI Self-Healing):** Real-time telemetry sliding windows feed the LSTM forecasting model. If severe congestion ($> 85\%$ link capacity) or degradation anomalies are predicted, the Self-Healing Module proactively shifts bulk TCP traffic to the alternate path while keeping priority UDP traffic intact on the primary path.
  - Implements a 15-second cooldown timer and hysteresis to ensure zero route flapping.

---

## 4. Per-Trial Timeline Export Protocol
For every benchmark trial executed by Member 2, `controller/modes.py` exports a synchronized timeline file to `data/results/week11_controller_timelines/{trial_id}_{mode}_timeline.csv`, containing exact controller-side timestamps for correlation with data-plane packet captures and ping logs.
