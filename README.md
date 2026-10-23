# AI-Driven QoS-Aware Predictive Traffic Engineering and Self-Healing in SDN-Based Edge Networks

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![OpenFlow 1.3](https://img.shields.io/badge/OpenFlow-1.3-orange.svg)](https://opennetworking.org/)
[![OS-Ken](https://img.shields.io/badge/SDN-OS--Ken%204.2.1-green.svg)](https://github.com/osrg/ryu)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)](https://pytorch.org/)
[![Mininet](https://img.shields.io/badge/Mininet-2.3.1-blueviolet.svg)](http://mininet.org/)
[![License](https://img.shields.io/badge/License-Academic%20Use-lightgrey.svg)](LICENSE)

---

## 1. Project Overview and Objectives

Edge computing networks connect heterogeneous Internet of Things (IoT) devices, latency-sensitive multimedia services (voice, video conferencing), and high-volume background data transfers over constrained bandwidth topologies. Traditional edge network routing and resource allocation suffer from two fundamental operational bottlenecks:

1. **Slow Control-Plane Reactive Failover:** When an inter-switch physical link fails, standard OpenFlow architectures send asynchronous port-status notifications to a centralized controller. The controller recomputes shortest paths and pushes new flow rules over southbound channels, causing packet drop bursts and multi-second service interruptions.
2. **Bufferbloat and QoS Contention:** Unmanaged FIFO queuing allows aggressive TCP bulk streams to saturate shared switch buffers, introducing high queuing latency, jitter, and packet loss for co-located real-time UDP streams.

### Core Objectives

This project implements and evaluates an emulated Software-Defined Networking (SDN) framework designed to address these challenges through:
* **Switch-Local Fast-Failover:** Using OpenFlow 1.3 Fast-Failover group tables on edge switches to autonomously redirect traffic to pre-configured backup links in the data plane upon carrier signal loss without waiting for controller round-trip communication.
* **QoS-Aware Traffic Differentiation Architecture:** Enforcing traffic classification via IP protocol and ports, integrated with Linux Hierarchical Token Bucket (HTB) queues designed to prioritize real-time traffic over bulk transfers.
* **Predictive AI Telemetry Pipeline:** Periodically collecting switch port statistics (`OFPPortStatsRequest`) to feed a PyTorch Long Short-Term Memory (LSTM) autoencoder model intended for network anomaly detection.

---

## 2. System Architecture

The project architecture comprises three integrated layers:

```
+===================================================================================+
|                          1. SDN CONTROL PLANE (OS-Ken)                            |
|                                                                                   |
|  - OpenFlow 1.3 Controller Core (controller/app.py)                               |
|  - L4 Flow Classifier & Metadata Tagger (controller/flow_classifier.py)           |
|  - Fast-Failover Group Manager (controller/ff_groups.py)                          |
|  - Operational Mode Switcher (controller/modes.py)                                |
|  - AI-SDN REST Bridge & Event Logger (controller/ai_sdn_bridge.py, Port 8080)     |
|  - Switch Telemetry Collector (controller/telemetry.py)                           |
+===================================================================================+
                                  | OpenFlow 1.3 Southbound (TCP 6633)
                                  v
+===================================================================================+
|                          2. EMULATED DATA PLANE (Mininet)                         |
|                                                                                   |
|  - Switches: Edge Switches (s1, s2) and Core Transit Switch (s3)                  |
|  - Primary Route: s1-s3-s2 (via s1-eth3, s3-eth1, s3-eth2, s2-eth3)              |
|  - Backup Route:  s1-s2 direct link (via s1-eth4 <-> s2-eth4)                     |
|  - QoS Queues (mininet/configure_queues.sh):                                      |
|      * Queue 0 (Best-Effort): max-rate = 4 Mbps                                   |
|      * Queue 1 (Priority UDP): min-rate = 8 Mbps, max-rate = 10 Mbps              |
|  - Hosts: h1 (10.0.0.1), h2 (10.0.0.2), h3 (10.0.0.3), h4 (10.0.0.4)             |
+===================================================================================+
                                  ^ Periodic Telemetry Polling (5.0s window)
                                  v
+===================================================================================+
|                        3. AI PREDICTIVE TELEMETRY PIPELINE                        |
|                                                                                   |
|  - PyTorch LSTM Time-Series Autoencoder (ai-model/lstm_model.py)                  |
|  - Pre-trained Checkpoint (ai-model/checkpoints/lstm_model.pt)                    |
|  - Standalone Inference & Anomaly Scoring (ai-model/ai_loop.py)                   |
|  - Self-Healing Decision Policy Engine (ai-model/self_healing_module.py)          |
+===================================================================================+
```

---

## 3. Network Topology and Traffic Configuration

The network is defined in `mininet/topo.py` using `FatTreeEdgeTopo`:

```
              +--------------------------+
              |      Core Switch s3      |
              +--------------------------+
                 /                    \
     (Port 1)   /                      \   (Port 2)
  s1-eth3 (100M)                        s2-eth3 (100M)
               /                          \
+--------------------------+    Backup    +--------------------------+
|      Edge Switch s1      |============|      Edge Switch s2      |
+--------------------------+ s1-eth4<->   +--------------------------+
    | (Port 1)   | (Port 2)  s2-eth4 (100M)   | (Port 1)   | (Port 2)
    | (10M)      | (10M)                      | (10M)      | (10M)
+-------+    +-------+                    +-------+    +-------+
|  h1   |    |  h2   |                    |  h3   |    |  h4   |
| .0.1  |    | .0.2  |                    | .0.3  |    | .0.4  |
+-------+    +-------+                    +-------+    +-------+
```

### Switch Port Mappings
* **Edge Switch `s1`:**
  * Port 1 (`s1-eth1`): Host `h1` (`10.0.0.1`, MAC `00:00:00:00:00:01`)
  * Port 2 (`s1-eth2`): Host `h2` (`10.0.0.2`, MAC `00:00:00:00:00:02`)
  * Port 3 (`s1-eth3`): Primary link to Core Switch `s3` (100 Mbps)
  * Port 4 (`s1-eth4`): Backup direct link to Edge Switch `s2` (100 Mbps)
* **Edge Switch `s2`:**
  * Port 1 (`s2-eth1`): Host `h3` (`10.0.0.3`, MAC `00:00:00:00:00:03`)
  * Port 2 (`s2-eth2`): Host `h4` (`10.0.0.4`, MAC `00:00:00:00:00:04`)
  * Port 3 (`s2-eth3`): Primary link to Core Switch `s3` (100 Mbps)
  * Port 4 (`s2-eth4`): Backup direct link to Edge Switch `s1` (100 Mbps)
* **Core Transit Switch `s3`:**
  * Port 1 (`s3-eth1`): Primary link from `s1`
  * Port 2 (`s3-eth2`): Primary link to `s2`

### Traffic Profiles (Scenario S3: Link Failure Under Load)
Defined in `scenarios/S3_failure.yaml`:
* **Priority UDP Stream:** `h1` $\rightarrow$ `h3:5202` (Bandwidth: 3.0 Mbps, Packet size: 1400 B, DSCP 46 / Expedited Forwarding, Start: $t=2\text{s}$, Duration: 40s).
* **Bulk TCP Stream:** `h2` $\rightarrow$ `h4:5201` (Bandwidth target: 5.0 Mbps, DSCP 0 / Best Effort, Start: $t=4\text{s}$, Duration: 38s).
* **ICMP Probe Stream:** `h1` $\rightarrow$ `10.0.0.3` (`ping -i 0.010 -c 4500` running concurrently over 45s).
* **Failure Injection:** Physical link `s1-eth3` is downed at $t=15\text{s}$ for an 8.0-second window, then restored at $t=23\text{s}$.

---

## 4. Implemented Features

* **OpenFlow 1.3 Fast-Failover Groups:** Group tables installed on edge switches (`Group 100` for Priority traffic, `Group 101` for Best-Effort traffic). Bucket 0 watches port 3 (primary path via `s3`), while Bucket 1 watches port 4 (direct backup link to `s2`).
* **L4 Flow Classification:** Module `controller/flow_classifier.py` inspects packet headers to assign internal metadata tags:
  * Traffic matching designated priority profiles (Metadata tag 1 $\rightarrow$ Queue 1).
  * Standard traffic falls back to default policy (Metadata tag 2 $\rightarrow$ Queue 0 / Group 101).
  * *(Note: In Scenario S3, both streams routed through Group 101, so independent priority queue isolation was not validated during benchmark failure trials).*
* **Linux HTB QoS Configuration:** Script `mininet/configure_queues.sh` configures Hierarchical Token Bucket queues on edge switch ports (Queue 0: Best-Effort capped at 4 Mbps; Queue 1: Priority with 8 Mbps guaranteed rate).
* **REST Management Bridge:** Standalone HTTP server (`controller/ai_sdn_bridge.py`) listening on port 8080 providing operational mode control (`/api/mode`) and liveness monitoring (`/health`).
* **Automated Scenario Benchmark Runner:** Script `mininet/run_scenario.py` manages namespace command execution, preflight socket verification, failure injection timing, and log collection.

---

## 5. Software Requirements and Installation

### Prerequisites
* **Operating System:** Ubuntu 22.04 LTS native or WSL2 (Ubuntu 22.04 / 24.04).
* **Root Privileges:** Required for Mininet network namespace operations and Open vSwitch configuration.
* **Core Software Packages:**
  * Open vSwitch (`openvswitch-switch`)
  * Mininet 2.3.0+ (`mininet`)
  * iPerf 3.9+ (`iperf3`)
  * Python 3.10+ with `pip` and `venv`

### Installation Commands

```bash
# Update system package repositories
sudo apt-get update

# Install required system packages
sudo apt-get install -y mininet openvswitch-switch iperf3 python3-pip python3-venv

# Clone the repository
git clone https://github.com/Shamruthapd/AI-Driven-QoS-Aware-Predictive-Traffic-Engineering.git
cd AI-Driven-QoS-Aware-Predictive-Traffic-Engineering

# Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

---

## 6. Step-by-Step Execution Guide

To reproduce experiments, commands must be executed in separate terminal windows.

### Terminal 1: Start the SDN Controller

Start the OS-Ken controller application with the REST bridge and group modules:

```bash
cd AI-Driven-QoS-Aware-Predictive-Traffic-Engineering
source venv/bin/activate

# Set PYTHONPATH to discover controller packages and start the application
PYTHONPATH=/usr/lib/python3/dist-packages:. python3 scripts/run_controller.py
```

*Verification:* Ensure the controller logs indicate `AI-SDN Bridge HTTP Server running on 0.0.0.0:8080` and the OpenFlow handler is listening on port 6633.

---

### Terminal 2: Run an Automated Benchmark Experiment

Execute the scenario runner for any of the three evaluated operational modes. The runner automatically instantiates the topology, sets the controller mode, verifies bidirectional connectivity, launches traffic, injects link failure, and saves artifacts.

#### Option A: Run the Baseline Shortest Path Mode
```bash
cd AI-Driven-QoS-Aware-Predictive-Traffic-Engineering
source venv/bin/activate

sudo PYTHONPATH=/usr/lib/python3/dist-packages:. ./venv/bin/python mininet/run_scenario.py \
    --scenario scenarios/S3_failure.yaml \
    --mode baseline_shortest_path \
    --trial-id live_s3_baseline \
    --output-dir data/results/live_s3_baseline
```

#### Option B: Run the Reactive Mode
```bash
sudo PYTHONPATH=/usr/lib/python3/dist-packages:. ./venv/bin/python mininet/run_scenario.py \
    --scenario scenarios/S3_failure.yaml \
    --mode reactive \
    --trial-id live_s3_reactive \
    --output-dir data/results/live_s3_reactive
```

#### Option C: Run the Full Fast-Failover Mode
```bash
sudo PYTHONPATH=/usr/lib/python3/dist-packages:. ./venv/bin/python mininet/run_scenario.py \
    --scenario scenarios/S3_failure.yaml \
    --mode full_ai_qos_ff \
    --trial-id live_calib_003 \
    --output-dir data/results/live_calib_003
```

---

### Terminal 3: Parse and Evaluate Results

Process the raw iPerf3 JSON metrics, server logs, and ping traces:

```bash
cd AI-Driven-QoS-Aware-Predictive-Traffic-Engineering
source venv/bin/activate

# Evaluate raw trial results
python3 scripts/evaluate.py \
    --input-dir data/results/live_calib_003 \
    --output-dir data/results/live_calib_003/eval
```

Parsed metrics are generated in `eval/parsed_measurements.csv` and summarized in `eval/summary_tables.csv`.

---

### Network Cleanup
If a trial is terminated early or interfaces need resetting:
```bash
sudo mn -c
```

---

## 7. Measured Results and Empirical Comparison

The table below summarizes genuine, audited Mininet measurements collected from live experimental trials (`live_s3_baseline`, `live_s3_reactive`, and `live_calib_003`) under an 8.0-second injected link cut on `s1-eth3`:

| Metric Category | Metric | Baseline (`live_s3_baseline`) | Reactive (`live_s3_reactive`) | Proposed (`live_calib_003`) | Evidence Source |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Physical Outage** | Link Carrier Downtime | **8.015 s** | **8.018 s** | **8.013 s** | `link_failure_events.csv` |
| **Failover Action** | Switch Datapath Rerouting | None (Bypassed) | Switch-Local FF (Group 101) | Switch-Local FF (Group 101) | `s1_group_stats_recovered.txt` |
| **Diverted Traffic** | Backup Bucket 1 Cumulative | **0 packets (0.0 MB)** | **2,732 packets (4.01 MB)** | **2,717 packets (4.00 MB)** | `s1_group_stats_recovered.txt` |
| **Priority UDP** | Datagrams Sent / Received | 10,360 / 8,285 | 6,964 / 6,911 | 7,332 / 7,279 | Client JSON / Server Log |
| **Priority UDP** | Lost Datagrams | **2,075 datagrams** | **53 datagrams** | **53 datagrams** | Server Log final summary |
| **Priority UDP** | UDP Packet Loss Rate | **20.029%** | **0.761%** | **0.723%** | Reconciled sender/receiver |
| **UDP Continuity** | Zero-Throughput Blackout | **7.0 s continuous** | **0 s (Zero blackout)** | **0 s (Zero blackout)** | Server Log interval records |
| **Bulk TCP** | Retransmissions | **186 segments** | **93 segments** | **93 segments** | Client JSON `sum_sent` |
| **Liveness Ping** | Consecutive Probes Dropped | **496 drops** | **274 drops** | **272 drops** | Ping Log sequence gaps |

### Experimental Context and Disclosures
1. **Sample Size:** Reported metrics reflect **one valid live trial per mode** in the testbed repository.
2. **Failover Execution:** The reduction in UDP packet loss (from 20.029% to $\approx 0.7\%$) and elimination of multi-second blackout were accomplished by **switch-local OpenFlow 1.3 Fast-Failover** executing in the switch hardware datapath upon carrier loss. AI-triggered proactive rerouting was not demonstrated in these trials, and AI inference did not cause the observed recovery improvement.
3. **Queue Configuration Discrepancy:** The baseline mode was evaluated with unconfigured/cleared queues (unshaped FIFO), whereas reactive and full modes had active Linux-HTB traffic shaping. Consequently, queuing delays and throughput profiles reflect different queue setups across modes.
4. **Queue Isolation Scope:** Priority queue isolation was not independently validated because flows in Scenario S3 defaulted to Best-Effort Group 101.
5. **Group Counter Scope:** The Backup Bucket 1 counter reflects cumulative packets forwarded at the time of the post-recovery snapshot; it does not measure exclusively outage-period traffic.
6. **Datapath Equivalence:** In the current codebase (`controller/app.py`), both `reactive` and `full_ai_qos_ff` modes install Fast-Failover groups on edge switches rather than performing dynamic controller-driven path recomputation, producing equivalent datapath forwarding.

---

## 8. Repository Structure

```
AI-Driven-QoS-Aware-Predictive-Traffic-Engineering/
├── README.md                              <- Main project overview and executable runbook
├── requirements.txt                       <- Python dependencies
├── controller/
│   ├── app.py                             <- OS-Ken controller application with L4 QoS & FF
│   ├── ff_groups.py                       <- OpenFlow 1.3 Fast-Failover group installation
│   ├── flow_classifier.py                 <- L4 port and DSCP packet classification logic
│   ├── port_status_logger.py              <- OpenFlow EventOFPPortStatus logger
│   ├── ai_sdn_bridge.py                   <- REST API bridge (/api/mode, /health) & event logger
│   ├── modes.py                           <- Operational mode definitions
│   ├── telemetry.py                       <- Periodic switch port statistics poller
│   └── config.yaml                        <- Controller and network configuration parameters
├── mininet/
│   ├── topo.py                            <- 4-host, 3-switch edge fat-tree Mininet topology
│   ├── configure_queues.sh                <- Linux-HTB QoS queue setup on switch ports
│   ├── inject_failure.py                  <- High-precision interface down/up injection script
│   └── run_scenario.py                    <- Automated Mininet benchmark launcher
├── scenarios/
│   ├── S1_steady.yaml                     <- Scenario S1: Baseline steady-state traffic
│   ├── S2_congestion.yaml                 <- Scenario S2: Bulk congestion load
│   └── S3_failure.yaml                    <- Scenario S3: Link failure under load
├── ai-model/
│   ├── lstm_model.py                      <- PyTorch LSTM neural network definition
│   ├── ai_loop.py                         <- Standalone inference and anomaly scoring loop
│   ├── self_healing_module.py             <- Proactive rerouting policy engine
│   └── checkpoints/
│       └── lstm_model.pt                  <- Trained PyTorch LSTM model weights
├── data/results/
│   ├── live_s3_baseline/                  <- Raw artifacts for Baseline Shortest Path live trial
│   │   ├── eval/                          <- Evaluated summary tables and metrics
│   │   ├── live_s3_baseline_server_h3_5202.log
│   │   ├── live_s3_baseline_server_h4_5201.log
│   │   └── live_s3_baseline_link_failure_events.csv
│   ├── live_s3_reactive/                  <- Raw artifacts for Reactive Mode live trial
│   │   └── eval/                          <- Evaluated summary tables and metrics
│   ├── live_calib_003/                    <- Raw artifacts for Full Fast-Failover live trial
│   │   └── eval/                          <- Evaluated summary tables and metrics
│   ├── port_status_events.csv             <- Master OpenFlow port status transition log
│   └── unified_event_log.csv              <- Synchronized controller decision and mode log
├── docs/
│   ├── final/
│   │   ├── ieee_paper.tex                 <- IEEE conference paper LaTeX source
│   │   ├── architecture-diagram.drawio    <- Editable system architecture diagram
│   │   ├── architecture-diagram.png       <- Exported architecture diagram
│   │   ├── flow-diagram.drawio            <- Editable workflow diagram
│   │   ├── flow-diagram.png               <- Exported workflow diagram
│   │   ├── topology-final.png             <- Topology illustration
│   │   ├── Final_Report.md                <- Comprehensive project report
│   │   ├── control-plane-section.md       <- Control-plane module documentation
│   │   ├── data-plane-section.md          <- Data-plane module documentation
│   │   └── resilience-section.md          <- Resilience and failover documentation
│   └── references.md                      <- Academic citations and references
└── scripts/
    ├── run_controller.py                  <- Python entry point for SDN controller
    ├── run_controller.sh                  <- Shell launcher for the controller
    ├── verify_connectivity.py             <- Preflight socket reachability and forwarding check
    └── evaluate.py                        <- Measurement parser and evaluation harness
```

---

## 9. Relationship Between Code, Diagrams, Paper, and Results

* **LaTeX Paper (`docs/final/ieee_paper.tex`):** Contains the formal academic conference submission. The experimental section reflects the audited three-mode failure-recovery comparison.
* **Architecture Diagrams (`docs/final/architecture-diagram.drawio`, `architecture-diagram.png`):** Illustrate the control plane, data plane, and AI telemetry loop relationships as implemented in `controller/` and `ai-model/`.
* **Workflow Diagram (`docs/final/flow-diagram.drawio`, `flow-diagram.png`):** Details the lifecycle of telemetry polling, anomaly evaluation, and fast-failover bucket activation.
* **Topology Illustration (`docs/final/topology-final.png`):** Represents the port mappings and link capacities configured in `mininet/topo.py`.
* **Experimental Data (`data/results/`):** Stores the empirical raw logs, client JSON metrics, and group counter dumps generated directly by `mininet/run_scenario.py`.

---

## 10. Limitations and Reproducibility Notes

1. **Single Trial Sample Size:** The empirical results reflect a single validated live trial for each controller mode (`live_s3_baseline`, `live_s3_reactive`, and `live_calib_003`). Additional trials are required for formal statistical confidence intervals.
2. **Switch-Local Failover vs. AI Causality:** All observed failover recovery was executed by switch-local OpenFlow 1.3 Fast-Failover (`Group 101`). Anomaly scores during link cuts did not exceed the detection threshold ($0.02$ MSE), so AI-triggered proactive rerouting was not demonstrated during these trials, and AI inference did not cause the measured loss reduction.
3. **Reactive Mode Implementation:** The current controller implementation (`controller/app.py`) configures Fast-Failover groups for both `reactive` and `full_ai_qos_ff` modes. Dynamic controller-driven reactive path recomputation via `OFPFlowMod` upon port-down was not independently implemented.
4. **Queue Configuration Discrepancy:** Queue shaping was cleared for `baseline_shortest_path` to emulate unmanaged edge links, while `reactive` and `full_ai_qos_ff` utilized Linux-HTB queue rate limits. This introduces queuing latency differences under load (mean ping RTT ~0.21 ms without queues vs. ~206 ms with queues).
5. **Priority Queue Isolation Scope:** Because `flow_classifier.py` designates `10.0.0.3 -> 10.0.0.4` for priority classification, traffic in Scenario S3 (`10.0.0.1 -> 10.0.0.3`) defaulted to Best-Effort Group 101. Independent queue isolation under congestion was therefore not empirically validated.
6. **Group Statistics Counter Scope:** OpenFlow group statistics (`s1_group_stats_recovered.txt`) represent cumulative datapath counters captured after link restoration; they do not measure traffic restricted exclusively to the 8.0-second failure window.
7. **Ping Cadence Under Load:** When running at high frequency (`-i 0.010`), Linux ping socket pacing slows under concurrent traffic load. Probe drop counts should be evaluated as discrete sequence gaps rather than assuming a continuous 10 ms interval.

---

## 11. Team Members and Academic Information

* **Department:** Department of Computer Technology  
* **Institution:** Madras Institute of Technology Campus, Anna University, Chennai, Tamil Nadu, India  
* **Academic Course:** CS23502 — Networks and Data Communication  
* **Faculty Project Mentor:** Dr. Gunasekaran Raja  

### Project Team

* **Harshitha S. R.** (Reg. No: 2024503545) — Control-Plane Integration, Operational Modes & REST Bridge  
* **Sanjay Anand A.** (Reg. No: 2024503041) — Data-Plane Failover, Network Topology & HTB Queue Architecture  
* **Samyuktha S.** (Reg. No: 2024503527) — Resilience Evaluation, Scenario Design & Failure Injection  
* **Shamrutha P. D.** (Reg. No: 2024503533) — AI Telemetry Pipeline, Measurement Evaluation & Report Compilation  

---

## 12. License

This repository is maintained for academic evaluation and research purposes under the MIT License. Refer to the `LICENSE` file for terms.