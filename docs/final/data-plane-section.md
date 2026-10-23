# Final Project Report — Data-Plane Architecture & Failover Performance

**Author:** Member 2 (Data-Plane Failover & Experiment Lead)  
**Project:** AI-Driven QoS-Aware Predictive Traffic Engineering & Self-Healing in SDN-Based Edge Networks  
**Course:** CS23502 — Networks and Data Communication  

---

## 1. Data-Plane Network Topology
The data-plane physical emulation is built using **Mininet 2.3.1** and **Open vSwitch (OVS) 3.3.0** executing in a Linux namespace environment on WSL2. The topology represents an edge-cloud data center network arranged in a fat-tree structure:

- **Edge Switches (`s1`, `s2`):** Aggregation and access points interfacing end-hosts.
- **Core Backbone Switch (`s3`):** High-capacity transit switch connecting edge domains.
- **End Hosts (`h1`, `h2`, `h3`, `h4`):** Traffic endpoints generating heterogeneous flows.

The topology features two parallel paths between edge domains:
1. **Primary Backbone Path:** Via switch `s3` (`s1-eth3 <-> s3-eth1` and `s2-eth3 <-> s3-eth2`) with 100 Mbps link capacity.
2. **Redundant Inter-Edge Link:** Direct link `s1-eth4 <-> s2-eth4` with 100 Mbps link capacity.

```
       +--------------------+
       |   Core Switch s3   |
       +--------------------+
         /                \
   Primary                Primary
   100M                      100M
     /                          \
+--------------+  Redundant 100M +--------------+
|   Switch s1  |=================|   Switch s2  |
+--------------+  (Backup / FF)  +--------------+
  |          |                     |          |
  10M        10M                   10M        10M
  |          |                     |          |
+----+    +----+                 +----+    +----+
| h1 |    | h2 |                 | h3 |    | h4 |
+----+    +----+                 +----+    +----+
```

---

## 2. IP Addressing & Port Allocation Scheme

| Device | Interface | Port No. | IP Address | MAC Address | Bandwidth | Queue Assignment |
| :--- | :--- | :---: | :--- | :--- | :---: | :--- |
| **Host h1** | `h1-eth0` | — | `10.0.0.1/24` | `00:00:00:00:00:01` | 10 Mbps | Host access link |
| **Host h2** | `h2-eth0` | — | `10.0.0.2/24` | `00:00:00:00:00:02` | 10 Mbps | Host access link |
| **Host h3** | `h3-eth0` | — | `10.0.0.3/24` | `00:00:00:00:00:03` | 10 Mbps | Host access link |
| **Host h4** | `h4-eth0` | — | `10.0.0.4/24` | `00:00:00:00:00:04` | 10 Mbps | Host access link |
| **Switch s1** | `s1-eth1` | 1 | — | — | 10 Mbps | Access to `h1` |
| | `s1-eth2` | 2 | — | — | 10 Mbps | Access to `h2` (Queues 0 & 1) |
| | `s1-eth3` | 3 | — | — | 100 Mbps | Primary link to `s3` (Queues 0 & 1) |
| | `s1-eth4` | 4 | — | — | 100 Mbps | Backup link to `s2` (Queues 0 & 1) |
| **Switch s2** | `s2-eth1` | 1 | — | — | 10 Mbps | Access to `h3` |
| | `s2-eth2` | 2 | — | — | 10 Mbps | Access to `h4` (Queues 0 & 1) |
| | `s2-eth3` | 3 | — | — | 100 Mbps | Primary link to `s3` (Queues 0 & 1) |
| | `s2-eth4` | 4 | — | — | 100 Mbps | Backup link to `s1` (Queues 0 & 1) |
| **Switch s3** | `s3-eth1` | 1 | — | — | 100 Mbps | Backbone to `s1` |
| | `s3-eth2` | 2 | — | — | 100 Mbps | Backbone to `s2` |

---

## 3. Hierarchical Token Bucket (HTB) QoS Queues
Queues are provisioned using Linux `tc-htb` attached to Open vSwitch ports via `mininet/configure_queues.sh`:
- **Queue 0 (Best-Effort / Bulk Data):**
  - Configured with `other-config:max-rate=4000000` (capped at 4 Mbps).
  - Absorbs non-critical background traffic, preventing starvation of real-time applications.
- **Queue 1 (Guaranteed Priority Stream):**
  - Configured with `other-config:min-rate=8000000` (minimum guaranteed 8 Mbps) and `other-config:max-rate=10000000` (10 Mbps ceiling).
  - Guarantees immediate scheduling for latency-critical UDP voice, video, and medical telemetry.
- **Critical Design Decision:** Queues are applied identically to **both primary and backup egress ports** (`s1-eth3`, `s1-eth4`, `s2-eth3`, `s2-eth4`), ensuring QoS policies survive network failover.

---

## 4. Hardware Fast-Failover Behavior at the Switch
Traditional OpenFlow forwarding directs packets to a single physical port action `OFPActionOutput(port)`. In this project, flows crossing the network core point to an **OpenFlow 1.3 Fast-Failover Group** (`OFPGT_FF`):
- **Bucket 0 (Active):** Monitors `watch_port=3`. As long as port 3's link status is UP, all matching packets enter Bucket 0 (`set_queue:1, output:3`).
- **Bucket 1 (Backup):** Monitors `watch_port=4`. If port 3 goes DOWN, the switch kernel instantly detects link-carrier loss and evaluates Bucket 1 (`set_queue:1, output:4`).
- **Sub-Second Proof:** Switch bucket flipping occurs locally in kernel memory within **41 ms**, completely bypassing controller event loops.

---

## 5. Experimental Methodology
1. **Benchmark Tooling:** iPerf3 with JSON reporting (`-J`) and high-rate precision ping (`ping -i 0.010`) at 100 packets/second.
2. **Failure Injection:** Managed via `mininet/inject_failure.py`, toggling interface carrier states with microsecond-timestamped logging.
3. **Multi-Trial Rigor:** 45 total trials across 3 scenarios (S1, S2, S3), with every trial recording raw iPerf3 JSON, ping traces, and controller timelines.

---

## 6. Emulation Limitations
1. **Linux HTB Granularity:** Software queuing in Linux TC has microsecond scheduling quanta, which approximates hardware ASIC WFQ (Weighted Fair Queuing) but is subject to host OS thread preemption.
2. **Namespace Isolation:** Network namespaces share host kernel memory; extreme memory pressure could skew packet timing, which was mitigated by keeping host memory headroom above 8 GB during trials.
