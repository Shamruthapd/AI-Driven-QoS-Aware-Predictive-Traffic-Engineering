# Final Defense Master Q&A Sheet

**Course:** CS23502 — Networks and Data Communication  
**Date:** Week 12 Final Evaluation  
**Compilation Lead:** Member 4 (Shamrutha)  
**Contributors:** Member 1 (Harshitha), Member 2 (Sanjay), Member 3 (Samyuktha)  

---

### Q1: Why did you choose OS-Ken instead of Ryu?
**A (Member 1):**  
Ryu was officially abandoned and frozen on Python 2.7 / early Python 3, making it incompatible with modern Linux distributions (Ubuntu 22.04+) and newer OpenSSL / eventlet versions. OS-Ken is the active, community-maintained OpenStack fork that brings full Python 3.10–3.12 compatibility while maintaining complete OpenFlow 1.3 protocol compliance.

---

### Q2: Why did you use an LSTM model rather than ARIMA or standard linear regression?
**A (Member 4):**  
Network traffic exhibits non-linear burstiness, diurnal patterns, and multi-scale temporal dependencies. ARIMA models assume linear time-series stationarity and perform poorly during sudden congestion onset. Our LSTM model ingests a 12-step sliding window of 10 statistical features (packet deltas, byte deltas, packet rates, dropped counts), capturing non-linear transitions and forecasting bandwidth utilization with high accuracy (low MAPE) in just **14.8 ms** inference time.

---

### Q3: How do you justify the "sub-second self-healing" claim with real empirical numbers?
**A (Member 3 & Member 2):**  
Rather than claiming an arbitrary theoretical number, we measured recovery across 10 repeated link-down trials using high-rate (100 Hz / 10 ms interval) pings:
- The mean data-plane recovery time was **41.00 ms** (Min: 40 ms, Max: 50 ms, p95: 50 ms).
- This is **24x faster** than the 1,000 ms SLA ceiling.
- We also measured traditional reactive controller rerouting under identical conditions: it averaged **1,535.00 ms**, demonstrating that our switch-local group table approach is **37.4x faster**.

---

### Q4: Why doesn't the backup link cause a Layer-2 switching loop during normal operation?
**A (Member 1 & Member 2):**  
In traditional Ethernet, redundant links cause broadcast loops unless Spanning Tree Protocol (STP) blocks them. However, STP can take 30 to 50 seconds to re-converge.  
In our OpenFlow 1.3 design:
1. Normal MAC learning flows send traffic exclusively to OpenFlow Fast-Failover Group 100/200.
2. The Fast-Failover group has Bucket 0 (port 3) active and Bucket 1 (port 4) in standby.
3. Because Bucket 1 is inactive while port 3 is UP, packets never egress port 4 simultaneously, completely eliminating Layer-2 forwarding loops without STP convergence delays.

---

### Q5: How do you prevent route oscillation / flapping when the AI loop triggers a reroute?
**A (Member 3):**  
We implemented two classical control-theory stability mechanisms in `ai-model/self_healing_module.py`:
1. **15-Second Cooldown Timer:** After taking a rerouting action, the system ignores further triggers for 15 seconds, allowing the network queue state to settle.
2. **Hysteresis Thresholds:** The trigger threshold to reroute traffic away from the primary link is set to **0.85 (85% utilization)**, whereas the threshold to restore traffic back to the primary link is set significantly lower to **0.60 (60% utilization)**. This gap prevents boundary chatter.

---

### Q6: What are the main limitations of running this in an emulated environment?
**A (Member 2 & Member 4):**  
1. **Emulated vs. ASIC Switching:** Open vSwitch runs in Linux kernel software space. While it achieves 41 ms recovery, real enterprise SDN hardware (such as Barefoot Tofino or Juniper switches) performs bucket switching in hardware registers (< 10 ms).
2. **Virtual CPU Sharing:** On WSL2, intense parallel workloads (iPerf3 + Scapy + controller + PyTorch) share CPU cores with the host OS, occasionally causing 2-3 ms of scheduler jitter.
3. **Topology Scale:** Our validation focuses on a 3-switch edge network; production carrier networks feature thousands of nodes requiring distributed controller clustering.

---

### Q7: If a link fails, does traffic keep its QoS class or drop back to default?
**A (Member 1):**  
In many naive implementations, rerouted traffic loses its queue tag. In our design, **both the primary bucket and the backup bucket contain explicit `OFPActionSetQueue` instructions** (`set_queue:1` for Priority, `set_queue:0` for Best-Effort), and Member 2 provisioned HTB queues on backup ports (`s1-eth4`, `s2-eth4`). Contention benchmarks during failover confirmed priority UDP maintained < 1.5 ms jitter and near-zero loss after failover.
