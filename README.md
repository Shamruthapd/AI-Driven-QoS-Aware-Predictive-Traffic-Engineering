# AI-Driven QoS-Aware Predictive Traffic Engineering and Self-Healing in SDN-Based Edge Networks

## 📌 Project Overview

Traditional edge networks rely on static routing protocols that cannot efficiently adapt to dynamic traffic conditions or unexpected link failures. This often leads to increased latency, packet loss, congestion, and poor Quality of Service (QoS).

This project proposes an AI-driven Software Defined Networking (SDN) solution that predicts future traffic congestion using an LSTM-based machine learning model and proactively applies QoS policies. In the event of a network failure, the system automatically reroutes traffic using OpenFlow Fast-Failover mechanisms, ensuring continuous and reliable communication.

The entire system is developed and evaluated using software-based network emulation without requiring physical networking hardware.

---

## 🎯 Objectives

- Predict network congestion before it occurs using AI.
- Improve Quality of Service (QoS) for latency-sensitive applications.
- Dynamically allocate bandwidth based on predicted traffic.
- Automatically recover from link failures using Fast-Failover.
- Evaluate network performance under different traffic conditions.

---

## 🏗️ System Architecture

The project consists of four major components:

### 1. Data Plane
- Mininet
- Open vSwitch (OVS)
- Hosts
- Network Links

### 2. Control Plane
- Ryu SDN Controller
- OpenFlow Protocol

### 3. AI Layer
- PyTorch
- LSTM Traffic Prediction Model
- Anomaly Detection

### 4. QoS & Self-Healing Layer
- QoS Policy Engine
- Fast-Failover Mechanism
- Dynamic Traffic Engineering

---

## 🛠 Technologies Used

| Technology | Purpose |
|------------|---------|
| Python | Programming Language |
| Mininet | Network Emulation |
| Ryu Controller | SDN Controller |
| OpenFlow 1.3 | Controller-Switch Communication |
| Open vSwitch (OVS) | Virtual Switch |
| PyTorch | AI Model Development |
| Git & GitHub | Version Control |
| Ubuntu Linux | Development Environment |

---

## 📂 Repository Structure

```
AI-Driven-QoS-Aware-Predictive-Traffic-Engineering/

│── README.md
│── requirements.txt
│── .gitignore

├── controller/
├── mininet/
├── ai-model/
├── datasets/
├── results/
├── screenshots/
├── presentation/

└── docs/
    ├── references.md
    ├── week1/
    ├── week2/
    ├── week3/
    ├── week4/
    ├── week5/
    ├── week6/
    ├── week7/
    ├── week8/
    ├── week9/
    ├── week10/
    ├── week11/
    └── week12/
```

---

## 🚀 Getting Started

Clone the repository:

```bash
git clone https://github.com/Shamruthapd/AI-Driven-QoS-Aware-Predictive-Traffic-Engineering.git
```

Move into the project directory:

```bash
cd AI-Driven-QoS-Aware-Predictive-Traffic-Engineering
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 📖 Documentation

Weekly documentation is maintained inside the `docs/` directory.

- Week 1 – SDN Fundamentals
- Week 2 – Development Environment
- Week 3 – Network Topology
- Week 4 – Telemetry Collection
- Week 5 – AI Model Development
- Week 6 – Model Training
- Week 7 – QoS Flow Classification
- Week 8 – QoS Policy Enforcement
- Week 9 – Fast-Failover
- Week 10 – AI-SDN Integration
- Week 11 – Performance Evaluation
- Week 12 – Final Report & Presentation

---

## 📄 License

This repository is maintained as part of the **CS23502 – Networks and Data Communication Mini Project**.

For academic and educational purposes only.