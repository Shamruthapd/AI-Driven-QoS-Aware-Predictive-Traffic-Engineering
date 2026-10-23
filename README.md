# AI-Driven QoS-Aware Predictive Traffic Engineering and Self-Healing in SDN-Based Edge Networks

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![OpenFlow 1.3](https://img.shields.io/badge/OpenFlow-1.3-orange.svg)](https://opennetworking.org/)
[![OS-Ken](https://img.shields.io/badge/SDN-OS--Ken%204.2.1-green.svg)](https://github.com/osrg/ryu)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)](https://pytorch.org/)
[![Status](https://img.shields.io/badge/Release-v1.0%20(Frozen)-brightgreen.svg)]()

## 📌 Project Overview
Traditional edge networks rely on static shortest-path routing or slow reactive controller rerouting (incurring 1.2–2.5s delays during link breaks) and unmanaged FIFO queuing (causing bufferbloat and packet loss during congestion).

This project delivers a **complete, zero-cost, emulated, closed-loop intelligent SDN framework**:
1. **Switch-Local OpenFlow 1.3 Fast-Failover (FF):** Edge switches `s1` and `s2` pre-install primary and backup bucket groups with queue preservation (`set_queue` in both buckets), achieving data-plane recovery in **41.0 ms** (37.4x faster than reactive SDN).
2. **Predictive PyTorch LSTM Traffic Forecasting:** Continuously monitors port telemetry sliding windows to predict bandwidth demand and anomaly spikes in **14.8 ms**.
3. **Two-Layer Proactive Self-Healing:** Under heavy congestion (Scenario S2), the system proactively shifts bulk TCP traffic to alternate paths before drops occur, reducing priority voice/video latency by **84%** (7.6 ms vs. 48.5 ms) and eliminating bufferbloat.

---

## 📊 Key Results at a Glance

| Scenario & Metric | Static Shortest Path | Reactive SDN | **Proposed (`full_ai_qos_ff`)** | Gain |
| :--- | :---: | :---: | :---: | :---: |
| **S3: Failover Recovery Time** | 8,000 ms (Total Outage) | 1,535 ms | **41.0 ms** | **37.4x faster** (Sub-second SLA met) |
| **S3: Packets Dropped During Failure** | 800 pings (100% loss) | 153 pings | **4 pings (0.5% loss)** | **97.4% reduction in drops** |
| **S2: Priority Latency Under Load** | 48.5 ms | 22.1 ms | **7.6 ms** | **84.3% latency reduction** |
| **S2: Priority Packet Loss** | 21.4% | 4.6% | **0.12%** | **Near-zero drop rate** |
| **S2: Effective Network Goodput** | 4.1 Mbps | 6.9 Mbps | **9.4 Mbps** | **+129% throughput gain** |

---

## 🏗️ System Architecture

```
+-----------------------------------------------------------------------------------+
|                        OS-Ken OpenFlow 1.3 Controller                             |
|  - Table-miss, Flow Classification (VoIP, Video, Bulk) & Metadata Tagging         |
|  - Fast-Failover Group Tables (100, 200, 300) with set_queue in BOTH buckets       |
|  - Central Config (controller/config.yaml) & Mode Switch (controller/modes.py)    |
|  - AI-SDN REST Bridge (controller/ai_sdn_bridge.py) & Unified Event Logger        |
+-----------------------------------------------------------------------------------+
                               | OpenFlow 1.3 (TCP 6633)
                               v
+-----------------------------------------------------------------------------------+
|                             Mininet Data Plane                                    |
|  - Switches: Edge switches s1 & s2, Core backbone switch s3                       |
|  - Primary path: s1-s3-s2 (100 Mbps)  |  Redundant path: s1-s2 (100 Mbps)          |
|  - HTB QoS Queues on both paths: Queue 0 (Bulk <= 4M), Queue 1 (Priority 8-10M)   |
|  - Hosts: h1 (10.0.0.1), h2 (10.0.0.2), h3 (10.0.0.3), h4 (10.0.0.4)             |
+-----------------------------------------------------------------------------------+
                               ^ REST / JSON Telemetry (5s interval)
                               v
+-----------------------------------------------------------------------------------+
|                          AI Predictive Self-Healing Loop                          |
|  - PyTorch LSTM Bandwidth Forecaster (W=12 steps)                                 |
|  - Anomaly Detector (MSE Residual Thresholding)                                   |
|  - Self-Healing Decision Module (ai-model/self_healing_module.py)                 |
|  - 15-second Cooldown Timer & Hysteresis (Prevents Route Oscillation)             |
+-----------------------------------------------------------------------------------+
```

---

## 🚀 Step-by-Step Runbook (Cold Start)

### 1. Prerequisites
Ubuntu 22.04 LTS or WSL2 with Python 3.10+, Mininet, Open vSwitch, and iPerf3:
```bash
sudo apt-get update
sudo apt-get install -y mininet openvswitch-switch iperf3 python3-pip python3-venv
```

Clone the repository:
```bash
git clone https://github.com/Shamruthapd/AI-Driven-QoS-Aware-Predictive-Traffic-Engineering.git
cd AI-Driven-QoS-Aware-Predictive-Traffic-Engineering
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### 2. Step 1: Start the SDN Controller
In **Terminal 1**:
```bash
# Launch unified controller with Fast-Failover, QoS classification, and AI Bridge
./scripts/run_controller.sh local
```

---

### 3. Step 2: Launch the Mininet Topology
In **Terminal 2**:
```bash
# Clean previous state and start edge fat-tree topology
sudo mn -c
sudo python3 mininet/topo.py --controller-ip 127.0.0.1 --controller-port 6633
```

---

### 4. Step 3: Configure QoS Queues on Primary and Backup Links
In **Terminal 3**:
```bash
# Attach HTB queues to primary (eth3) and backup (eth4) egress ports on s1 and s2
sudo bash mininet/configure_queues.sh
```

---

### 5. Step 4: Run Traffic Scenarios & Benchmarks
In **Terminal 3**:
```bash
# Run Scenario S1: Steady Mixed Load (Nominal Baseline)
python3 mininet/run_scenario.py --scenario scenarios/S1_steady.yaml --mode full_ai_qos_ff --trial-id trial_001

# Run Scenario S2: Heavy Congestion (Evaluates Proactive AI Rerouting)
python3 mininet/run_scenario.py --scenario scenarios/S2_congestion.yaml --mode full_ai_qos_ff --trial-id trial_002

# Run Scenario S3: Hard Link Failure Under Load (Evaluates Sub-Second Fast-Failover)
python3 mininet/run_scenario.py --scenario scenarios/S3_failure.yaml --mode full_ai_qos_ff --trial-id trial_003
```

---

### 6. Step 5: Evaluate Results & Generate Comparison Charts
In **Terminal 3**:
```bash
# Run the evaluation harness over all raw measurements
python3 scripts/evaluate.py --input-dir data/results/week11_raw --output-dir data/results

# Run recovery time statistical analysis
python3 scripts/analyze_week11_recovery.py
```

Generated metrics and charts will be stored in `data/results/` and `docs/figures/`.

---

## 📁 Repository Structure

```
AI-Driven-QoS-Aware-Predictive-Traffic-Engineering/
├── README.md                              <- Tested project runbook and overview
├── controller/
│   ├── app.py                             <- OS-Ken controller with QoS & Fast-Failover
│   ├── ff_groups.py                       <- OpenFlow 1.3 FF group tables with set_queue
│   ├── flow_classifier.py                 <- L4 port & DSCP packet classification
│   ├── port_status_logger.py              <- Structured link event logger
│   ├── ai_sdn_bridge.py                   <- REST/socket bridge & unified event logger
│   ├── modes.py                           <- Operational mode switcher (3 modes)
│   └── config.yaml                        <- Central configuration file
├── mininet/
│   ├── topo.py                            <- Frozen edge fat-tree network topology
│   ├── configure_queues.sh                <- HTB queue setup on primary & backup ports
│   ├── inject_failure.py                  <- Repeatable link carrier toggle script
│   └── run_scenario.py                    <- Automated scenario benchmark runner
├── scenarios/
│   ├── S1_steady.yaml                     <- Scenario S1: Steady mixed load
│   ├── S2_congestion.yaml                 <- Scenario S2: Heavy bulk congestion
│   └── S3_failure.yaml                    <- Scenario S3: Link failure under load
├── ai-model/
│   ├── lstm_model.py                      <- PyTorch LSTM neural network
│   ├── ai_loop.py                         <- Standalone inference loop with graceful degradation
│   ├── self_healing_module.py             <- Layer 2 proactive rerouting engine
│   └── checkpoints/lstm_model.pt          <- Trained PyTorch LSTM checkpoint
├── data/results/
│   ├── week11_raw/                        <- 45 raw iPerf3 JSON and ping trial logs
│   ├── week11_controller_timelines/       <- Per-trial controller timeline CSVs
│   ├── week11_recovery_times.csv          <- Recovery time dataset per trial
│   ├── week11_summary_tables.csv          <- Complete benchmark comparison table
│   └── unified_event_log.csv              <- Synchronized 6-event-type master log
├── docs/
│   ├── figures/                           <- Performance comparison and recovery charts
│   ├── final/
│   │   ├── Final_Report.md                <- Comprehensive Final Project Report
│   │   ├── control-plane-section.md       <- Member 1 Control-Plane Report Section
│   │   ├── data-plane-section.md          <- Member 2 Data-Plane Report Section
│   │   ├── resilience-section.md          <- Member 3 Resilience Report Section
│   │   ├── topology-final.png             <- Final network topology diagram
│   │   ├── slides.md                      <- Final presentation slide deck
│   │   ├── qa-sheet.md                    <- Master defense Q&A sheet
│   │   ├── demo-commands-controller.md    <- Controller demo runbook
│   │   └── demo-commands-dataplane.md     <- Mininet demo runbook
│   └── week9/ to week11/                  <- Weekly milestone documentation
└── scripts/
    ├── run_controller.sh                  <- Single controller launcher
    ├── evaluate.py                        <- Multi-metric evaluation harness
    ├── run_week11_trials.py               <- 45-trial batch runner
    └── analyze_week11_recovery.py         <- Recovery time statistical analyzer
```

---

## 👥 Authors & Team Contributions
- **Member 1 (Harshitha):** Control-Plane Self-Healing & Integration Lead
- **Member 2 (Sanjay):** Data-Plane Failover & Experiment Lead
- **Member 3 (Samyuktha):** Self-Healing Design & Recovery-Evaluation Lead
- **Member 4 (Shamrutha):** AI Runtime, Evaluation & Final Report Lead

---

## 📄 License
Maintained as part of **CS23502 – Networks and Data Communication Mini Project**. For academic and educational use.