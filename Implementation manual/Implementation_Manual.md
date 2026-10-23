# Implementation Manual: AI-Driven QoS-Aware Predictive Traffic Engineering and Self-Healing in SDN-Based Edge Networks

---

**Academic Project Manual**  
**Course:** CS23502 — Networks and Data Communication  
**Institution:** Department of Computer Technology, Madras Institute of Technology Campus, Anna University, Chennai  
**Faculty Project Mentor:** Dr. Gunasekaran Raja  
**Project Team:**
* Harshitha S. R. (Reg. No: 2024503545) — Control-Plane Integration, Operational Modes & REST Bridge
* Sanjay Anand A. (Reg. No: 2024503041) — Data-Plane Failover, Network Topology & HTB Queue Architecture
* Samyuktha S. (Reg. No: 2024503527) — Resilience Evaluation, Scenario Design & Failure Injection
* Shamrutha P. D. (Reg. No: 2024503533) — AI Telemetry Pipeline, Measurement Evaluation & Report Compilation

---

## Table of Contents
1. [Project Overview and System Architecture](#1-project-overview-and-system-architecture)
2. [Hardware Specifications and Software Requirements](#2-hardware-specifications-and-software-requirements)
3. [Dependencies and Installation Instructions](#3-dependencies-and-installation-instructions)
4. [Project Folder Structure and Key Files](#4-project-folder-structure-and-key-files)
5. [Network Topology and Connectivity](#5-network-topology-and-connectivity)
6. [Controller Implementation and Key Components](#6-controller-implementation-and-key-components)
7. [System Configuration and Parameters](#7-system-configuration-and-parameters)
8. [Step-by-Step Execution Guide](#8-step-by-step-execution-guide)
9. [Testing and Verification Procedures](#9-testing-and-verification-procedures)
10. [Logs, Datasets, and Evaluation Reports](#10-logs-datasets-and-evaluation-reports)
11. [Troubleshooting and Common Errors](#11-troubleshooting-and-common-errors)
12. [Known Limitations and Reproducibility Notes](#12-known-limitations-and-reproducibility-notes)

---

## 1. Project Overview and System Architecture

### 1.1 Problem Statement
Edge networks interconnect heterogeneous IoT devices, real-time multimedia (VoIP, video surveillance), and elastic background data transfers over constrained physical links. Conventional Software-Defined Networking (SDN) architectures suffer from two primary operational bottlenecks:
1. **Control-Plane Failover Latency:** When an inter-switch physical link fails, switches generate asynchronous `OFPT_PORT_STATUS` messages to a remote controller. The controller recomputes shortest paths and pushes new flow modifications (`OFPT_FLOW_MOD`) southbound, resulting in multi-second blackouts and high packet loss bursts.
2. **Bufferbloat & QoS Contention:** Unmanaged FIFO queuing causes high-throughput TCP bulk flows to monopolize shared switch buffers, introducing high queuing latency, jitter, and packet loss for co-located real-time UDP streams.

### 1.2 System Architecture
The framework is partitioned into three cooperating layers:

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

### 1.3 Diagram References
The visual and editable diagrams are available in the `diagrams/` subdirectory:
* **System Architecture Diagram:** [`diagrams/architecture-diagram.png`](diagrams/architecture-diagram.png) (Editable: [`diagrams/architecture-diagram.drawio`](diagrams/architecture-diagram.drawio))
* **Telemetry & Failover Workflow:** [`diagrams/flow-diagram.png`](diagrams/flow-diagram.png) (Editable: [`diagrams/flow-diagram.drawio`](diagrams/flow-diagram.drawio))
* **Topology Layout:** [`diagrams/topology-final.png`](diagrams/topology-final.png)

---

## 2. Hardware Specifications and Software Requirements

### 2.1 Hardware Requirements
* **Processor (CPU):** Minimum 4 physical cores (e.g., Intel Core i5/i7 or AMD Ryzen 5/7). Required to run Open vSwitch kernel threads, Mininet network namespaces, traffic generators (`iperf3`, `ping`), and controller processes concurrently.
* **Memory (RAM):** Minimum 8 GB (16 GB recommended).
* **Storage:** At least 10 GB free disk space.
* **Host Platform:** Native Ubuntu 22.04 LTS x86_64, or Windows 10/11 running **WSL2** (Ubuntu 22.04 / 24.04).

### 2.2 Software Environment
* **Operating System:** Linux Ubuntu 22.04 LTS (Kernel 5.15 / 6.6).
* **Privileges:** Root access (`sudo`) is strictly required for Mininet network namespace creation, virtual ethernet interfaces (`veth`), and Open vSwitch datapath configuration.
* **Python Runtime:** Python 3.10 or higher.
* **OpenFlow Protocol:** Version 1.3.
* **Open vSwitch:** Version 2.17.x or higher.
* **Mininet:** Version 2.3.0 or higher.
* **Traffic Tools:** iPerf 3.9+ and standard Linux `iputils-ping`.

---

## 3. Dependencies and Installation Instructions

Follow these exact terminal commands to set up the testing environment.

### 3.1 Install System Packages
```bash
# Update repository index
sudo apt-get update

# Install networking packages, Open vSwitch, Mininet, and compiler build tools
sudo apt-get install -y \
    mininet \
    openvswitch-switch \
    openvswitch-common \
    iperf3 \
    iproute2 \
    iputils-ping \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    git \
    curl

# Ensure Open vSwitch service is running
sudo service openvswitch-switch status || sudo service openvswitch-switch start
```

### 3.2 Clone Repository and Create Virtual Environment
```bash
# Clone the repository
git clone https://github.com/Shamruthapd/AI-Driven-QoS-Aware-Predictive-Traffic-Engineering.git
cd AI-Driven-QoS-Aware-Predictive-Traffic-Engineering

# Create a clean Python virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip, setuptools, and wheel
pip install --upgrade pip setuptools wheel
```

### 3.3 Install Python Dependencies
The dependencies in `requirements.txt` contain:
```text
os-ken==4.2.1
torch
numpy
pandas
scikit-learn
joblib
matplotlib
scapy
jupyter
```

Install them via:
```bash
pip install -r requirements.txt
```

> **Note on OS-Ken Installation:** In certain Debian/Ubuntu distributions, OS-Ken relies on eventlet/greenlet compatibility. If system-level packages need discovery, set `PYTHONPATH=/usr/lib/python3/dist-packages:.` when launching controller scripts.

---

## 4. Project Folder Structure and Key Files

```
AI-Driven-QoS-Aware-Predictive-Traffic-Engineering/
├── README.md                              <- Academic project README with audited results
├── requirements.txt                       <- Python dependencies
├── Implementation manual/                 <- This implementation manual and diagrams
│   ├── Implementation_Manual.md           <- Main implementation document
│   ├── README.md                          <- Short overview of manual
│   └── diagrams/                          <- Architecture, workflow, and topology diagrams
├── controller/
│   ├── app.py                             <- Core OpenFlow 1.3 controller with QoS & Fast-Failover
│   ├── ff_groups.py                       <- OpenFlow 1.3 Fast-Failover group installation module
│   ├── flow_classifier.py                 <- L4 protocol, port, and DSCP classification rules
│   ├── port_status_logger.py              <- Asynchronous EventOFPPortStatus transition logger
│   ├── ai_sdn_bridge.py                   <- REST API bridge (/api/mode, /health) & event logger
│   ├── modes.py                           <- Operational mode definitions (baseline, reactive, full)
│   ├── telemetry.py                       <- Periodic switch port statistics poller (OFPPortStatsRequest)
│   ├── monitor.py                         <- Switch flow and port traffic monitor
│   └── config.yaml                        <- Central configuration for controller and AI loop
├── mininet/
│   ├── topo.py                            <- 4-host, 3-switch edge mesh Mininet topology
│   ├── configure_queues.sh                <- Linux-HTB QoS queue setup on OVS switch ports
│   ├── inject_failure.py                  <- High-precision interface down/up injection script
│   └── run_scenario.py                    <- Automated benchmark launcher for S1, S2, and S3
├── scenarios/
│   ├── S1_steady.yaml                     <- Scenario S1: Baseline steady-state traffic
│   ├── S2_congestion.yaml                 <- Scenario S2: Bulk congestion load
│   └── S3_failure.yaml                    <- Scenario S3: Link failure under load
├── ai-model/
│   ├── lstm_model.py                      <- PyTorch LSTM neural network definition
│   ├── ai_loop.py                         <- Standalone inference and anomaly scoring loop
│   ├── self_healing_module.py             <- Proactive rerouting policy engine
│   └── checkpoints/
│       └── lstm_model.pt                  <- Pre-trained PyTorch LSTM weights
├── data/results/
│   ├── live_s3_baseline/                  <- Raw and evaluated artifacts for Baseline live trial
│   ├── live_s3_reactive/                  <- Raw and evaluated artifacts for Reactive live trial
│   ├── live_calib_003/                    <- Raw and evaluated artifacts for Proposed live trial
│   ├── failure_injection_log.csv          <- Master link-failure injection log
│   ├── port_status_events.csv             <- Master OpenFlow port status transition log
│   └── unified_event_log.csv              <- Synchronized controller decision log
└── scripts/
    ├── run_controller.py                  <- Python entry point for SDN controller
    ├── run_controller.sh                  <- Shell launcher for controller
    ├── verify_connectivity.py             <- Preflight socket reachability and forwarding verification
    └── evaluate.py                        <- Measurement parser and evaluation harness
```

---

## 5. Network Topology and Connectivity

### 5.1 Topology Diagram
The network is instantiated by `mininet/topo.py` using `FatTreeEdgeTopo`:

```
              +--------------------------+
              |      Core Switch s3      |
              +--------------------------+
                 /                    \
      (Port 1)  /                      \  (Port 2)
   s1-eth3 (100M)                       s2-eth3 (100M)
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

### 5.2 Physical and Logical Port Mappings

#### Edge Switch `s1` (DPID 1):
* **Port 1 (`s1-eth1`):** Host `h1` (`10.0.0.1`, MAC `00:00:00:00:00:01`) — Access link (10 Mbps)
* **Port 2 (`s1-eth2`):** Host `h2` (`10.0.0.2`, MAC `00:00:00:00:00:02`) — Access link (10 Mbps)
* **Port 3 (`s1-eth3`):** Primary backbone link to Core Switch `s3-eth1` (100 Mbps)
* **Port 4 (`s1-eth4`):** Redundant direct backup link to Edge Switch `s2-eth4` (100 Mbps)

#### Edge Switch `s2` (DPID 2):
* **Port 1 (`s2-eth1`):** Host `h3` (`10.0.0.3`, MAC `00:00:00:00:00:03`) — Access link (10 Mbps)
* **Port 2 (`s2-eth2`):** Host `h4` (`10.0.0.4`, MAC `00:00:00:00:00:04`) — Access link (10 Mbps)
* **Port 3 (`s2-eth3`):** Primary backbone link to Core Switch `s3-eth2` (100 Mbps)
* **Port 4 (`s2-eth4`):** Redundant direct backup link to Edge Switch `s1-eth4` (100 Mbps)

#### Core Transit Switch `s3` (DPID 3):
* **Port 1 (`s3-eth1`):** Link to `s1-eth3` (100 Mbps)
* **Port 2 (`s3-eth2`):** Link to `s2-eth3` (100 Mbps)

### 5.3 Routing Paths
* **Primary Path:** `s1` $\rightarrow$ `s1-eth3` (Port 3) $\rightarrow$ `s3-eth1` (Port 1) $\rightarrow$ `s3-eth2` (Port 2) $\rightarrow$ `s2-eth3` (Port 3) $\rightarrow$ `s2`.
* **Backup Path:** `s1` $\rightarrow$ `s1-eth4` (Port 4) $\rightarrow$ `s2-eth4` (Port 4) $\rightarrow$ `s2`.

---

## 6. Controller Implementation and Key Components

### 6.1 OS-Ken Controller Core (`controller/app.py`)
The controller implements OpenFlow 1.3 protocol handling (`ofproto_v1_3`):
* **Table-Miss Rule:** Installs low-priority rule (priority 0) to forward unhandled packets to the controller (`OFPActionOutput(OFPP_CONTROLLER)`).
* **IPv6 Filter:** Drops IPv6 discovery traffic (priority 50) to keep logs focused on experimental IPv4 traffic.
* **Forwarding Logic:** Intercepts ARP and IPv4 packets. When routing inter-switch traffic from `s1` destined for `h3` or `h4`, it selects:
  * In `baseline_shortest_path` mode: Standard output to port 3 (`OFPActionOutput(3)`).
  * In `reactive` and `full_ai_qos_ff` modes: Routes packets into Fast-Failover groups (`OFPActionGroup(group_id)`).

### 6.2 Fast-Failover Groups (`controller/ff_groups.py`)
Provisions OpenFlow 1.3 group tables (`OFPGT_FF`):
* **Group 100 on Switch `s1` (Priority Traffic):**
  * Bucket 0: `watch_port=3`, `actions=[set_queue(1), output(3)]`
  * Bucket 1: `watch_port=4`, `actions=[set_queue(1), output(4)]`
* **Group 101 on Switch `s1` (Best-Effort Traffic):**
  * Bucket 0: `watch_port=3`, `actions=[set_queue(0), output(3)]`
  * Bucket 1: `watch_port=4`, `actions=[set_queue(0), output(4)]`
* **Group 200 / 201 on Switch `s2`:** Symmetric group definitions watching port 3 (primary) and port 4 (backup).
* **Group 300 on Switch `s3`:** Standard transit group.

### 6.3 Flow Classification (`controller/flow_classifier.py`)
Inspects ingress IPv4 packet headers:
* Dedicated Priority rule: Matches `src_ip="10.0.0.3"`, `dst_ip="10.0.0.4"`, `proto=17` (UDP), `dst_port=5202` $\rightarrow$ assigns `traffic_class="PRIORITY"` (Metadata tag 1, Queue 1).
* Default fallback: Assigns `traffic_class="BEST_EFFORT"` (Metadata tag 2, Queue 0 / Group 101).
*(Note: In Scenario S3, traffic is generated from `10.0.0.1` $\rightarrow$ `10.0.0.3`, which routes through Group 101).*

### 6.4 Linux HTB Queue Configuration (`mininet/configure_queues.sh`)
Uses Open vSwitch QoS commands to configure Linux Hierarchical Token Bucket queues:
* **Port Max Rate:** 10,000,000 bps (10 Mbps).
* **Queue 0 (Best-Effort):** `max-rate=4000000` (4 Mbps limit).
* **Queue 1 (Priority):** `min-rate=8000000` (8 Mbps guaranteed), `max-rate=10000000` (10 Mbps ceiling).
Configured on primary egress ports (`s1-eth3`, `s2-eth3`) and backup ports (`s1-eth4`, `s2-eth4`).

### 6.5 AI Telemetry & Predictive Self-Healing
* **Telemetry Poller (`controller/telemetry.py`):** Dispatches `OFPPortStatsRequest` every 5.0 seconds to record byte and packet deltas.
* **LSTM Model (`ai-model/lstm_model.py`):** Multi-layer PyTorch LSTM model mapping historical telemetry sequences (window length = 5 to 12) to predicted link utilization.
* **Self-Healing Engine (`ai-model/self_healing_module.py`):** Implements dual-threshold hysteresis ($\tau_{\text{high}} = 0.85$, $\tau_{\text{low}} = 0.60$) and a 15.0-second cooldown timer.
*(Experimental Status: Anomaly scores during sudden link tears remained below the 0.02 threshold; all failover was executed by switch-local Fast-Failover rather than proactive controller intervention).*

---

## 7. System Configuration and Parameters

The system behavior is controlled via `controller/config.yaml`:

```yaml
controller:
  openflow_ip: "0.0.0.0"
  openflow_port: 6633
  bridge_ip: "127.0.0.1"
  bridge_port: 8080
  log_level: "INFO"

telemetry:
  polling_interval_sec: 5.0
  raw_csv_path: "datasets/raw/telemetry.csv"
  export_history_limit: 1000

ai_inference:
  checkpoint_path: "ai-model/checkpoints/lstm_model.pt"
  sequence_length: 12
  inference_interval_sec: 5.0
  anomaly_mse_threshold: 5.0
  predicted_throughput_threshold_mbps: 10.0
  graceful_degradation: true

self_healing:
  cooldown_sec: 15.0
  congestion_trigger_threshold: 0.85
  failback_recovery_threshold: 0.60
  reroute_target_class: "BEST_EFFORT"
  priority_protection: true

operation_mode:
  mode: "full_ai_qos_ff"  # Choices: baseline_shortest_path, reactive, full_ai_qos_ff

logging:
  unified_event_log: "data/results/unified_event_log.csv"
  port_status_log: "data/results/port_status_events.csv"
```

### Traffic Profiles (Scenario S3: `scenarios/S3_failure.yaml`)
* **Priority UDP Flow:** Client `h1` $\rightarrow$ Server `h3:5202` (Bandwidth: 3.0 Mbps, Packet size: 1400 B, DSCP 46, Start: $t=2\text{s}$, Duration: 40s).
* **Bulk TCP Flow:** Client `h2` $\rightarrow$ Server `h4:5201` (Bandwidth target: 5.0 Mbps, DSCP 0, Start: $t=4\text{s}$, Duration: 38s).
* **ICMP Probe Stream:** `h1` $\rightarrow$ `10.0.0.3` (`ping -i 0.010 -c 4500` running concurrently over 45s).
* **Failure Event:** Physical link `s1-eth3` downed at $t=15\text{s}$ for an 8.0-second outage, then restored at $t=23\text{s}$.

---

## 8. Step-by-Step Execution Guide

To run experiments and collect valid metrics, open separate terminal windows.

### Terminal 1: Start the SDN Controller
```bash
cd AI-Driven-QoS-Aware-Predictive-Traffic-Engineering
source venv/bin/activate

# Launch OS-Ken with REST bridge and OpenFlow handlers
PYTHONPATH=/usr/lib/python3/dist-packages:. python3 scripts/run_controller.py
```
*Expected Output:*
```
[controller] Starting OS-Ken; press Ctrl+C to stop.
AI-SDN Bridge HTTP Server running on 0.0.0.0:8080
Fast-Failover Group Module with QoS Queue Preservation Started
AI-QoS SDN Controller Started | Version: v6 | OpenFlow: 1.3
```

---

### Terminal 2: Run an Automated Experiment

Execute any of the three benchmark modes using `mininet/run_scenario.py`. The runner automatically instantiates Mininet, sets the controller mode, runs preflight verification, configures queues, starts traffic, injects link failure, and saves all logs.

#### Option A: Baseline Shortest Path Mode
```bash
cd AI-Driven-QoS-Aware-Predictive-Traffic-Engineering
source venv/bin/activate

sudo PYTHONPATH=/usr/lib/python3/dist-packages:. ./venv/bin/python mininet/run_scenario.py \
    --scenario scenarios/S3_failure.yaml \
    --mode baseline_shortest_path \
    --trial-id live_s3_baseline \
    --output-dir data/results/live_s3_baseline
```

#### Option B: Reactive Mode
```bash
cd AI-Driven-QoS-Aware-Predictive-Traffic-Engineering
source venv/bin/activate

sudo PYTHONPATH=/usr/lib/python3/dist-packages:. ./venv/bin/python mininet/run_scenario.py \
    --scenario scenarios/S3_failure.yaml \
    --mode reactive \
    --trial-id live_s3_reactive \
    --output-dir data/results/live_s3_reactive
```

#### Option C: Full Fast-Failover Mode (Proposed System)
```bash
cd AI-Driven-QoS-Aware-Predictive-Traffic-Engineering
source venv/bin/activate

sudo PYTHONPATH=/usr/lib/python3/dist-packages:. ./venv/bin/python mininet/run_scenario.py \
    --scenario scenarios/S3_failure.yaml \
    --mode full_ai_qos_ff \
    --trial-id live_calib_003 \
    --output-dir data/results/live_calib_003
```

---

### Terminal 3: Parse and Evaluate Results
```bash
cd AI-Driven-QoS-Aware-Predictive-Traffic-Engineering
source venv/bin/activate

# Run evaluation harness against trial output directory
python3 scripts/evaluate.py \
    --input-dir data/results/live_calib_003 \
    --output-dir data/results/live_calib_003/eval
```
*Generated Files:*
* `eval/parsed_measurements.csv` (Per-file raw parsed metrics)
* `eval/summary_tables.csv` (Aggregated statistics)
* `eval/figures/` (Generated comparison plots)

---

### Network Cleanup Command
If an experiment is interrupted or an interface remains bound, run:
```bash
sudo mn -c
```

---

## 9. Testing and Verification Procedures

### 9.1 Preflight Connectivity Check
Before launching formal benchmarks, verify bidirectional ARP resolution, OpenFlow group installation, and iPerf3 socket communication:
```bash
sudo PYTHONPATH=/usr/lib/python3/dist-packages:. ./venv/bin/python scripts/verify_connectivity.py
```
*Verification Checklist:*
* Ping reachability: `h1` $\leftrightarrow$ `h3` (0% packet loss)
* Ping reachability: `h2` $\leftrightarrow$ `h4` (0% packet loss)
* OpenFlow groups present: `s1` (Group 100/101), `s2` (Group 200/201), `s3` (Group 300)
* UDP reception on `h3:5202`
* TCP reception on `h4:5201`

### 9.2 Controller REST Health Check
```bash
curl -s http://127.0.0.1:8080/health | python3 -m json.tool
```
*Expected Response:*
```json
{
    "status": "healthy",
    "active_mode": "full_ai_qos_ff",
    "trial_id": "live_calib_003"
}
```

---

## 10. Logs, Datasets, and Evaluation Reports

### 10.1 Trial Artifacts Structure
Each trial directory (e.g., `data/results/live_calib_003/`) contains:
* `*_flow_priority_udp.json`: Full iPerf3 JSON metrics for the UDP stream.
* `*_flow_bulk_tcp.json`: Full iPerf3 JSON metrics for the TCP stream.
* `*_ping.log`: ICMP sequence numbers, timestamps, and RTTs.
* `*_server_h3_5202.log`: Receiver server log for UDP traffic.
* `*_server_h4_5201.log`: Receiver server log for TCP traffic.
* `*_link_failure_events.csv`: Injected physical carrier down and up timestamps.
* `*_s1_group_stats_recovered.txt`: OpenFlow group bucket counters captured after link restoration.

### 10.2 Empirical Live Results Comparison

Audited measurements across the three live trials under an 8.0-second link cut on `s1-eth3`:

| Metric Category | Metric | Baseline (`live_s3_baseline`) | Reactive (`live_s3_reactive`) | Proposed (`live_calib_003`) |
| :--- | :--- | :---: | :---: | :---: |
| **Physical Outage** | Injected Link Downtime | **8.015 s** | **8.018 s** | **8.013 s** |
| **Failover Action** | Switch Datapath Rerouting | None (Bypassed) | Switch-Local FF (Group 101) | Switch-Local FF (Group 101) |
| **Diverted Traffic** | Backup Bucket 1 Cumulative | **0 packets (0.0 MB)** | **2,732 packets (4.01 MB)** | **2,717 packets (4.00 MB)** |
| **Priority UDP** | Lost Datagrams | **2,075 datagrams** | **53 datagrams** | **53 datagrams** |
| **Priority UDP** | UDP Packet Loss Rate | **20.029%** | **0.761%** | **0.723%** |
| **UDP Continuity** | Zero-Throughput Blackout | **7.0 s continuous** | **0 s (Zero blackout)** | **0 s (Zero blackout)** |
| **Bulk TCP** | Retransmissions | **186 segments** | **93 segments** | **93 segments** |
| **Liveness Ping** | Consecutive Probes Dropped | **496 drops** | **274 drops** | **272 drops** |

---

## 11. Troubleshooting and Common Errors

### 1. `Address already in use: 0.0.0.0:8080` or `Port 6633 busy`
* **Cause:** A previous controller process is still running in the background.
* **Fix:** Kill existing controller instances:
  ```bash
  sudo fuser -k 8080/tcp
  sudo fuser -k 6633/tcp
  pkill -9 -f run_controller.py
  ```

### 2. `Cannot find veth interface` or `ovs-vsctl: no bridge named ...`
* **Cause:** Mininet stopped abruptly without cleanup.
* **Fix:** Clean up Mininet virtual interfaces and restart Open vSwitch:
  ```bash
  sudo mn -c
  sudo service openvswitch-switch restart
  ```

### 3. `iperf3: error - unable to connect to server: No route to host`
* **Cause:** ARP entries have not populated across the OpenFlow switches before iPerf3 connects.
* **Fix:** Ensure the runner executes a preflight ping warmup between `h1<->h3` and `h2<->h4` to populate switch MAC learning tables before launching iPerf3.

### 4. `ModuleNotFoundError: No module named 'os_ken'`
* **Cause:** Python virtual environment is missing OS-Ken or running without dist-packages.
* **Fix:** Run commands with `PYTHONPATH=/usr/lib/python3/dist-packages:.` and ensure `venv` is activated.

---

## 12. Known Limitations and Reproducibility Notes

1. **Sample Size:** The reported live empirical measurements reflect **one validated trial per mode**. Additional experimental runs are required for statistical confidence intervals.
2. **Switch-Local Fast-Failover vs. AI:** Fast-Failover in the switch hardware datapath (`Group 101`) achieved the sub-second recovery and loss reduction. AI-triggered proactive rerouting was not demonstrated during these trials, and AI inference did not cause the observed recovery.
3. **Reactive Mode Implementation:** In [`controller/app.py`](../controller/app.py), both `reactive` and `full_ai_qos_ff` modes install Fast-Failover groups on the switches. A controller-driven dynamic path recomputation upon port failure was not independently implemented.
4. **Queue Configuration Discrepancy:** The baseline trial was executed without HTB queue shaping (unshaped FIFO), whereas reactive and proposed modes ran with active Linux-HTB traffic shaping.
5. **Priority Queue Isolation Scope:** In Scenario S3 (`10.0.0.1` $\rightarrow$ `10.0.0.3`), traffic was categorized under Best-Effort Group 101. Independent priority queue isolation under congestion was not validated in this benchmark.
6. **Group Counter Timestamps:** OpenFlow group bucket statistics (`s1_group_stats_recovered.txt`) represent cumulative datapath counters captured after link restoration; they do not measure packets restricted exclusively to the outage window.

---

*Manual maintained by the Project Team for academic evaluation and experimental reproduction.*
