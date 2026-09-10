# SDN Architecture Foundations

**Project:** AI-driven QoS-Aware Predictive Traffic Engineering and Self-Healing in SDN-Based Edge Networks
**Course:** CS23502 – Networks and Data Communication
**Week:** 1
**Member:** Member 1 – SDN Control Plane, QoS Monitoring and Telemetry

---

## 1. Software-Defined Networking (SDN)

Software-Defined Networking (SDN) is a networking architecture that separates the network control logic from packet forwarding. In a traditional network, individual routers and switches contain both control-plane logic and data-plane forwarding functions. In SDN, the control logic is moved to a logically centralized and programmable SDN controller, while network switches primarily perform packet forwarding according to rules installed by the controller.

This separation provides centralized network visibility and programmability. The controller can collect information from multiple switches, maintain a broader view of network conditions, and dynamically modify forwarding behavior.

For this project, SDN provides the programmable networking foundation required to monitor traffic conditions and eventually make proactive QoS-aware traffic-engineering and self-healing decisions.

---

## 2. Control Plane vs. Data Plane

The **data plane** is responsible for forwarding packets through the network. In our software-based testbed, the data plane is represented by Mininet hosts and Open vSwitch (OVS) switches. OVS maintains flow tables and forwards packets according to the installed OpenFlow rules.

The **control plane** is responsible for deciding how network traffic should be handled. Our control plane is implemented using **OS-Ken 4.2.1**, which communicates with OpenFlow-enabled switches using **OpenFlow 1.3**.

The relationship can be summarized as:

| Component | Responsibility | Project Implementation |
|---|---|---|
| Data Plane | Forward packets | Mininet + Open vSwitch |
| Control Plane | Make and install forwarding decisions | OS-Ken 4.2.1 |
| Southbound Interface | Controller-switch communication | OpenFlow 1.3 |

The controller does not directly forward every packet. Instead, it programs forwarding rules into the switch. Once a flow rule is installed, the switch can forward matching packets locally in the data plane.

---

## 3. Three-Tier SDN Architecture

The logical SDN architecture used by this project consists of three major layers:

### 3.1 Data Plane

The data plane contains the network devices responsible for packet forwarding.

**Project mapping:**
- Mininet hosts
- Open vSwitch switches
- Virtual network links
- Flow tables

### 3.2 Control Plane

The control plane contains the SDN controller responsible for network control and monitoring.

**Project mapping:**
- OS-Ken 4.2.1
- OpenFlow 1.3
- MAC-learning and forwarding logic
- Network monitoring
- Telemetry collection
- Future QoS and traffic-engineering decisions

### 3.3 Application / Intelligence Plane

The application plane contains higher-level network applications and intelligence that use information exposed by the controller.

**Project mapping:**
- Traffic analysis
- QoS intelligence
- Future traffic prediction model
- Congestion prediction
- Future traffic-engineering and self-healing logic

The three layers communicate through well-defined interfaces. OpenFlow 1.3 provides the southbound communication between the controller and OVS switches, while telemetry provides network-state information that can be consumed by higher-level intelligence.

---

## 4. Mapping the Architecture to This Project

The project applies the SDN architecture as follows:

```text
┌──────────────────────────────────────────────────────────┐
│              APPLICATION / AI PLANE                      │
│                                                          │
│  Traffic Analysis │ QoS Intelligence │ AI Prediction    │
│  Congestion Prediction │ Traffic Engineering            │
└───────────────────────────┬──────────────────────────────┘
                            │
                     Network intelligence
                            │
┌───────────────────────────▼──────────────────────────────┐
│                    CONTROL PLANE                         │
│                                                          │
│                 OS-Ken 4.2.1                             │
│                                                          │
│  • OpenFlow 1.3 communication                            │
│  • MAC learning and forwarding                           │
│  • Network monitoring                                    │
│  • Telemetry collection                                  │
│  • Future QoS / TE / self-healing decisions              │
└───────────────────────────┬──────────────────────────────┘
                            │
                       OpenFlow 1.3
                            │
┌───────────────────────────▼──────────────────────────────┐
│                      DATA PLANE                          │
│                                                          │
│              Mininet + Open vSwitch                      │
│                                                          │
│                  h1 ─── s1 ─── h2                        │
│                                                          │
│              Packet forwarding                           │
│              Flow tables                                 │
└──────────────────────────────────────────────────────────┘

The currently verified prototype uses a simple h1 — s1 — h2 topology. This topology demonstrates controller-switch communication, packet forwarding, and flow installation. The architecture above represents the logical project architecture that will be extended as additional traffic, QoS, AI and self-healing components are developed.

## 5. Why This Project Needs SDN

Traditional decentralized routing is designed to make forwarding decisions using information available to individual network devices. This can become less effective when traffic conditions change rapidly or when network failures require coordinated adaptation.

Our project requires visibility across the network because congestion and QoS conditions are not necessarily isolated to a single switch. An SDN controller provides a centralized control point from which network statistics can be collected and forwarding behavior can be coordinated.

In this project, OpenFlow statistics are collected from OVS switches at regular intervals. These measurements form the telemetry foundation for understanding network behavior.

Therefore, SDN provides:

- Centralized network visibility
- Programmable forwarding control
- Network-wide telemetry collection
- Dynamic flow management
- A control interface for future QoS and traffic-engineering mechanisms
## 6. Why This Project Needs AI

SDN provides visibility and control, but visibility alone does not predict future network conditions.

The project aims to move from reactive network management toward predictive traffic engineering. Historical telemetry can be used to identify traffic patterns and provide input to a future traffic-prediction model.

The intended workflow is:

Network Traffic
      ↓
OVS / OpenFlow Statistics
      ↓
Telemetry Collection
      ↓
Raw Dataset
      ↓
Validation & Feature Engineering
      ↓
AI / Traffic Prediction
      ↓
Predicted Network Condition
      ↓
QoS / Traffic Engineering Decision
      ↓
SDN Controller
      ↓
OpenFlow
      ↓
Network

AI is therefore positioned above the SDN control layer as an intelligence component. The controller provides the interface through which network state can be observed and, in later stages, network actions can be applied.

## 7. Role of OS-Ken and OpenFlow 1.3

This project uses OS-Ken 4.2.1 as the SDN controller framework.

OpenFlow 1.3 is used as the southbound protocol between OS-Ken and Open vSwitch. The controller can receive switch events and statistics and can install forwarding rules using OpenFlow messages.

The verified controller implementation includes:

- OpenFlow 1.3 support
- Switch connection handling
- Table-miss flow installation
- Packet-In handling
- MAC learning
- Flow-Mod installation
- Packet-Out handling
- Forwarding logic
- Periodic port-statistics collection

This provides the working control-plane foundation for the later QoS, traffic-engineering and AI components.

## 8. Current Prototype and Future System

It is important to distinguish between the currently verified prototype and the proposed complete system.

Current verified prototype
h1 ─── OVS s1 ─── h2
          │
          │ OpenFlow 1.3
          │
    OS-Ken 4.2.1
          │
          ▼
   Telemetry CSV

The prototype has already demonstrated successful controller connectivity, packet forwarding, flow installation, and collection of real OpenFlow statistics.

Proposed complete system

The final project will extend this foundation with:

- Repeatable TCP and UDP traffic generation
- QoS-aware traffic classification
- Traffic prediction
- Congestion-aware traffic engineering
- QoS policy enforcement
- Self-healing / fast-failover mechanisms
- Performance evaluation

These components will be developed incrementally and will be validated using measured network data rather than fabricated QoS values.

## 9. Conclusion

SDN provides the programmable control and network-wide visibility required by the proposed system. By separating the control plane from the data plane, the project can collect network telemetry centrally and program forwarding behavior through OpenFlow 1.3.

OS-Ken 4.2.1 forms the current control-plane foundation, while Mininet and Open vSwitch provide the software-defined data plane. The resulting telemetry pipeline creates the foundation for the project's future AI-driven QoS-aware predictive traffic-engineering and self-healing mechanisms.

The key architectural principle is:

SDN provides visibility and control; telemetry provides measured network state; AI provides predictive intelligence; and the controller provides the mechanism for applying future network decisions.
