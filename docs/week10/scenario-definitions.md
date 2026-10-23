# Week 10: Standardized Scenario Definitions & Parameters

**Author:** Member 2 (Data-Plane Failover & Experiment Lead)  
**Collaborators:** Member 1, Member 3, Member 4  
**Date:** Week 10 (Month 3 Freeze)  
**Status:** FROZEN & STANDARDIZED

---

## 1. Overview
To ensure fair and repeatable benchmarking across all three operational modes (`baseline_shortest_path`, `reactive`, and `full_ai_qos_ff`), three canonical traffic scenarios are defined with fixed parameters, flow profiles, and failure timelines.

---

## 2. Scenario Specifications

### Scenario S1: Steady Mixed Load (Nominal Baseline)
- **Configuration File:** `scenarios/S1_steady.yaml`
- **Goal:** Benchmark performance under normal, non-congested operating conditions.
- **Duration:** 30 seconds.
- **Traffic Composition:**
  - Priority Stream: 2.0 Mbps UDP (port 5202, DSCP 46 EF) from `h1` to `h3`.
  - Bulk Background Stream: 4.0 Mbps TCP (port 5201) from `h2` to `h4`.
  - IoT Telemetry: 100 packets/sec (128-byte payload) from `h2` to `h3`.
- **Bottleneck Capacity:** 10 Mbps (Combined offered load ~6.5 Mbps, 65% capacity).
- **Failure Events:** None.

### Scenario S2: Heavy Congestion (Bulk-Dominant)
- **Configuration File:** `scenarios/S2_congestion.yaml`
- **Goal:** Evaluate proactive AI self-healing and QoS queue differentiation under link saturation without physical link loss.
- **Duration:** 45 seconds.
- **Traffic Composition:**
  - Priority Stream: 3.0 Mbps UDP (port 5202, DSCP 46 EF) from `h1` to `h3`.
  - Aggressive Bulk TCP: 12.0 Mbps TCP (port 5201) from `h2` to `h4`.
  - Bursty IoT Telemetry: 250 packets/sec (256-byte payload) from `h2` to `h3`.
- **Bottleneck Capacity:** 10 Mbps (Combined offered load ~17.0 Mbps, 170% capacity).
- **Failure Events:** None.
- **Expected Outcome:** In `baseline`, priority traffic experiences severe packet loss (>20%) and jitter (>40 ms). In `full_ai_qos_ff`, Priority Queue 1 guarantees priority bandwidth, and the AI Self-Healing Module proactively redirects bulk TCP to backup link `s1-eth4`.

### Scenario S3: Link Failure Under Load
- **Configuration File:** `scenarios/S3_failure.yaml`
- **Goal:** Measure data-plane failover latency, recovery times, and packet drop counts under hard link failure.
- **Duration:** 45 seconds.
- **Traffic Composition:**
  - Priority Stream: 3.0 Mbps UDP (port 5202) from `h1` to `h3`.
  - Bulk TCP: 5.0 Mbps TCP (port 5201) from `h2` to `h4`.
- **Failure Event Timeline:**
  - $t = 0\text{s}$ to $15\text{s}$: Normal operation on primary path (`s1-eth3` <-> `s3-eth1`).
  - $t = 15.0\text{s}$: Physical link `s1-eth3` brought down via `mininet/inject_failure.py`.
  - $t = 15.0\text{s}$ to $23.0\text{s}$: Link remains down for 8.0 seconds.
  - $t = 23.0\text{s}$: Link restored (failback phase).
- **Expected Outcome:**
  - `baseline_shortest_path`: Flow stalls completely during failure (100% loss until timeout).
  - `reactive`: Controller detects port-down, computes new path, installs new flow-mods (recovery time ~1.2s to 2.5s).
  - `full_ai_qos_ff`: Switch detects port down locally and flips to backup bucket immediately (recovery time < 50 ms).

---

## 3. Emulation Constraints & Validation Notes
1. **WSL CPU Cap:** CPU utilization must be monitored; trials showing CPU saturation (>90%) or switch disconnects are documented and marked invalid.
2. **Deterministic Output:** All flow commands output standard JSON (`-J` for iPerf3) and timestamped ping logs for automated parsing by `scripts/evaluate.py`.
