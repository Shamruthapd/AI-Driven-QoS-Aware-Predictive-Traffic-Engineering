# Final Defense Q&A Sheet — Resilience & Self-Healing

**Lead:** Member 3 (Self-Healing Design Lead)  

---

### Q1: Why does OpenFlow Fast-Failover outperform reactive controller rerouting?
**A:** In reactive SDN, when a link fails:
1. The switch detects the failure and packages an OpenFlow `OFPT_PORT_STATUS` packet.
2. The packet travels over the control network to the controller.
3. The controller processes the event, runs Dijkstra's algorithm for an alternate path, and generates `OFPT_FLOW_MOD` messages.
4. The messages are transmitted back and installed in the switch's flow table.
This entire round trip introduces **1.2 to 2.5 seconds** of latency.  
With OpenFlow Fast-Failover, the controller pre-provisions both primary and backup paths in advance. The switch ASIC/kernel monitors port carrier liveness directly. When the signal drops, the switch points to the backup bucket in **~40 ms** without waiting for the controller.

---

### Q2: What happens to QoS priorities when traffic is rerouted to the backup link?
**A:** In naive implementations, rerouted traffic enters the default queue and loses all QoS differentiation. We solved this by placing explicit `OFPActionSetQueue(1)` inside the backup bucket of Group 100 on both `s1` and `s2`, and configuring corresponding HTB queues on backup egress ports (`s1-eth4`, `s2-eth4`). Priority traffic retains guaranteed 8 Mbps bandwidth even after failover.

---

### Q3: How do you prevent the AI loop and the Fast-Failover group from fighting each other?
**A:** Through our strict two-layer precedence rule:
- Fast-Failover has sole authority over **physical link down** events. The AI loop explicitly checks link status: if a link is `DOWN`, the AI engine outputs `DEFER_TO_FAST_FAILOVER` and issues zero flow modifications.
- The AI loop has sole authority over **predictive congestion and soft degradation** while links are `UP`.
- A 15-second cooldown timer guarantees that no flapping occurs.

---

### Q4: Why is your measured recovery 41 ms and not 10 ms or 1.2 s?
**A:** The 41 ms measurement was empirically obtained using 10 ms high-rate pings across 10 repeated trials on Linux Open vSwitch. The ~40 ms represents the Linux kernel `netlink` carrier loss detection and bucket transition time. In hardware ASIC switches (e.g. Barefoot Tofino), hardware loss-of-signal takes < 10 ms. In contrast, 1.2 s is what happens in reactive SDN when the control plane is involved.

---

### Q5: What happens if both the primary and backup links fail simultaneously?
**A:** As demonstrated in our double failure stress-test (`docs/week11/extra-scenarios-results.md`), if both watched ports are down, OpenFlow 1.3 drops packets at the switch. The controller logs the outages gracefully without crashing. When either link recovers, traffic resumes immediately without requiring controller or Mininet restarts.
