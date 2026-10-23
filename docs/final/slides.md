# Presentation Slide Deck — AI-Driven QoS-Aware Predictive Traffic Engineering & Self-Healing in SDN Edge Networks

**Course:** CS23502 — Networks and Data Communication  
**Date:** Week 12 (Final Review & Defense)  
**Team Members:**
- Member 1: Harshitha (Control-Plane Lead)
- Member 2: Sanjay (Data-Plane Lead)
- Member 3: Samyuktha (Self-Healing Design Lead)
- Member 4: Shamrutha (AI Runtime & Evaluation Lead)

---

## Slide 1: Title & Overview
- **Project Title:** AI-Driven QoS-Aware Predictive Traffic Engineering and Self-Healing in SDN-Based Edge Networks
- **Core Problem:** 
  - Reactive SDN failure recovery is slow (1.5s+ latency, dropped packets).
  - Best-Effort FIFO queuing causes bufferbloat and starves real-time traffic under congestion.
- **Our Solution:** A closed-loop zero-cost architecture combining OpenFlow 1.3 switch-local Fast-Failover with proactive PyTorch LSTM traffic forecasting and two-layer self-healing.
- **Speaker:** Member 4 (Shamrutha)

---

## Slide 2: Problem Statement & Motivation
- **Edge Network Constraints:**
  - Limited bandwidth and shared multi-tenant links.
  - Mission-critical traffic (telesurgery, VoIP, IoT telemetry) co-exists with aggressive bulk data transfers.
- **Why Traditional SDN Fails:**
  - Control-plane round trips (`OFPT_PORT_STATUS` -> Controller -> `OFPT_FLOW_MOD`) take 1.2s to 2.5s.
  - In a 100 Mbps link, a 1.5s delay drops **over 18 MB of in-flight data**.
- **The Research Question:** Can we achieve **sub-second self-healing (< 50 ms)** while guaranteeing QoS queue isolation before and after failover?
- **Speaker:** Member 4 (Shamrutha)

---

## Slide 3: System Architecture & The Two-Layer Strategy
- **Layer 1: Hardware Fast-Failover (Data Plane)**
  - Pre-provisions primary and backup buckets on edge switches `s1` and `s2`.
  - Switch hardware detects link loss directly in datapath; fails over locally in **41 ms**.
- **Layer 2: AI Proactive Self-Healing (Control Plane)**
  - LSTM model forecasts bandwidth demand 15-30s in advance.
  - If congestion is predicted ($> 85\%$ capacity), proactively shifts bulk TCP traffic to alternate path before packet drops occur.
- **Speaker:** Member 3 (Samyuktha)

---

## Slide 4: Data-Plane Design, Topology & QoS Queuing
- **Topology:** 3 OpenFlow 1.3 switches (`s1`, `s2`, `s3`) and 4 hosts (`h1`-`h4`).
  - Primary path: `s1-eth3 <-> s3 <-> s2-eth3` (100 Mbps).
  - Redundant direct link: `s1-eth4 <-> s2-eth4` (100 Mbps).
- **HTB QoS Queues:**
  - **Queue 0 (Bulk / Best-Effort):** Rate-limited ceiling at 4 Mbps.
  - **Queue 1 (Priority / VoIP):** Guaranteed minimum 8 Mbps, max 10 Mbps.
  - **Key Innovation:** Queues provisioned on **both primary and backup ports**, preventing QoS loss on failover.
- **Speaker:** Member 2 (Sanjay)

---

## Slide 5: Control Plane, Group Tables & REST Bridge
- **OS-Ken OpenFlow 1.3 Controller:**
  - `controller/flow_classifier.py`: Automatically tags DSCP 46 / port 5202 with `metadata=0x1`.
  - `controller/ff_groups.py`: Injects `OFPActionSetQueue` into **both** buckets of Group 100/200.
  - `controller/ai_sdn_bridge.py`: Lightweight REST bridge decoupling PyTorch CPU/GPU inference from the OpenFlow event loop.
- **Zero Flow-Mod Proof:** The controller receives port-down alerts for telemetry, but issues **zero new flow-mods** during failover.
- **Speaker:** Member 1 (Harshitha)

---

## Slide 6: Live System Demonstration
- **Segment 1: Normal Operation (Scenario S1)**
  - Verify group table configuration (`ovs-ofctl dump-groups s1`).
  - Show steady traffic flowing over primary path via `s3`.
- **Segment 2: Live Link Failure (Scenario S3)**
  - Cut primary link `s1-eth3`.
  - Ping stream drops only 4 packets (**40 ms** gap) before instant recovery.
  - Controller log confirms zero flow-mod overhead.
- **Segment 3: Congestion Mitigation (Scenario S2)**
  - AI engine detects predictive overload and offloads bulk traffic.
- **Speakers:** Member 3 (Narration), Member 2 (Mininet), Member 1 (Controller)

---

## Slide 7: Empirical Results & Performance Comparison
- **Recovery Time (Scenario S3):**
  - Static Baseline: 8,000.0 ms (Full outage).
  - Reactive SDN: 1,535.0 ms (Fails sub-second SLA).
  - **Proposed System: 41.0 ms (37.4x faster; passes sub-second claim).**
- **Priority QoS Under Heavy Congestion (Scenario S2):**
  - Priority Latency: reduced from **48.5 ms to 7.6 ms** (84% reduction).
  - Priority Packet Loss: reduced from **21.4% to 0.12%**.
  - Priority Jitter: reduced from **14.8 ms to 1.2 ms**.
  - Effective Network Goodput: increased from **4.1 Mbps to 9.4 Mbps** (+129%).
- **Speaker:** Member 4 (Shamrutha)

---

## Slide 8: Technical Limitations & Future Scope
- **Honest Limitations:**
  - Emulation on Mininet/WSL2 kernel threads introduces minor scheduling jitter.
  - Prototype evaluated on edge fat-tree mesh (3 switches).
- **Future Directions:**
  - Deploying on physical Raspberry Pi OpenFlow hardware testbeds.
  - Reinforcement Learning (PPO / DQN) for dynamic multi-path load balancing.
  - Hardware BFD (Bidirectional Forwarding Detection) for sub-10 ms detection.
- **Speaker:** Member 4 (Shamrutha)

---

## Slide 9: Conclusion & Defense Q&A
- **Summary:**
  - Zero-cost emulated SDN system: Delivered and verified.
  - Sub-second self-healing claim: Verified at **41 ms**.
  - Proactive QoS SLA protection: Verified with 84% latency reduction.
  - All Team Milestone Gates A through E achieved.
- **The Team is Ready for Questions.**
- **Speakers:** All 4 Members
