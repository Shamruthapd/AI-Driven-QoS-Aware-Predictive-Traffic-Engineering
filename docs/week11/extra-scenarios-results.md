# Week 11: Stress-Test Evaluation: Extra Network Failure Scenarios

**Author:** Member 3 (Self-Healing Design & Recovery-Evaluation Lead)  
**Collaborators:** Member 1, Member 2  
**Date:** Week 11 (Month 3)  
**Status:** EVALUATED & DOCUMENTED

---

## 1. Overview
In addition to the standard single link-down trials in Scenario S3, the project resilience design (`docs/week9/failure-scenario-catalog.md`) identified three challenging edge-case scenarios:
1. **Link Flapping:** Periodic rapid oscillations of the primary inter-switch link.
2. **Failure During Heavy Congestion:** A physical link break occurring while the network is under 170% offered load.
3. **Double Failure (Partition):** Simultaneous failure of both primary (`s1-eth3`) and backup (`s1-eth4`) links, leaving no valid path between `s1` and `s2`.

---

## 2. Test Execution & Results

### 2.1 Scenario E1: Link Flapping Test
- **Method:** `mininet/inject_failure.py --interface s1-eth3 --cycles 5 --down-duration 2.0 --up-interval 3.0`.
- **Observed Behavior:**
  - For each flap cycle, Fast-Failover instantly switched from Bucket 1 (port 3) to Bucket 2 (port 4) in $\approx 40\text{ ms}$, and reverted automatically to Bucket 1 when the watched port came back up.
  - The AI Self-Healing Module's 15-second cooldown timer engaged, preventing the controller from issuing conflicting route updates during the rapid physical fluctuations.
  - Total packets dropped across all 5 flap cycles: 22 packets (out of 10,000 sent).
  - **Verdict:** Stable; zero controller crashes or route flapping loops.

### 2.2 Scenario E2: Link Failure During Heavy Congestion (Combined S2 + S3)
- **Method:** Launched Scenario S2 traffic (3 Mbps Priority UDP + 12 Mbps Bulk TCP) and triggered link failure on `s1-eth3` at $t = 20.0\text{ s}$.
- **Observed Behavior:**
  - Prior to failure, the AI Self-Healing Module had already proactively rerouted Bulk TCP to port 4.
  - When port 3 failed, Priority UDP immediately failed over to port 4 via Fast-Failover Group 100.
  - Contention occurred on the 100 Mbps backup link (`s1-eth4`), which easily accommodated the combined 15 Mbps traffic without dropping packets.
  - Priority UDP delay remained at **8.4 ms**; packet loss remained under **0.2%**.
  - **Verdict:** Multi-layer coordination succeeded seamlessly.

### 2.3 Scenario E3: Double Link Failure (Total Partition)
- **Method:** Sequentially brought down `s1-eth3` (primary) and `s1-eth4` (backup).
- **Observed Behavior:**
  - When `s1-eth3` went down, FF selected bucket 2 (`s1-eth4`).
  - When `s1-eth4` also went down, both watched ports were DOWN. OpenFlow 1.3 FF specification dictates that packets are dropped at the switch.
  - The controller logged both port-status events without crashing or getting stuck in an infinite retry loop.
  - As soon as `s1-eth4` was restored, traffic resumed immediately without needing a controller restart or Mininet reboot.
  - **Verdict:** Graceful failure and clean self-recovery.

---

## 3. Summary of Edge-Case Resilience
The two-layer architecture (Fast-Failover in hardware + AI proactive cooldown in software) proves robust against rapid oscillations, heavy overload, and total temporary network partitions.
