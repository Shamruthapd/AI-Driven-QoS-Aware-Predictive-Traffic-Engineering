# Week 1 — Conceptual Foundation Summary

## Project

**AI-Driven QoS-Aware Predictive Traffic Engineering and Self-Healing in SDN-Based Edge Networks**

## 1. Introduction

Modern edge networks carry different types of traffic such as video, IoT data,
and high-volume bulk data. These applications have different network
requirements. For example, video traffic is sensitive to delay and packet loss,
while bulk TCP traffic mainly requires high throughput.

Traditional networks mainly depend on distributed and reactive routing.
Network devices make decisions using local information and usually react only
after congestion, link failure, or packet loss has already occurred.

This creates a problem for highly dynamic edge networks. By the time a routing
decision is changed, congestion may already have affected application
performance.

Our project addresses this problem by combining:

- Software-Defined Networking (SDN)
- OpenFlow 1.3
- Network telemetry
- Machine learning / LSTM prediction
- Quality of Service (QoS)
- Fast-Failover mechanisms

The main idea is:

**Monitor → Predict → Decide → Act → Recover**

---

## 2. Why Traditional Networks Are Not Enough

Traditional networks are largely distributed. Each router or switch makes
routing decisions using its available local information.

This approach works well for normal and relatively stable traffic, but it has
limitations when traffic changes rapidly.

### Main problems

1. **Limited global visibility**

   Individual network devices do not have a complete view of the entire
   network state.

2. **Reactive decisions**

   Routing changes usually happen after congestion or failure is detected.

3. **Slow recovery**

   A link failure may require routing protocols to detect the failure,
   exchange information, and calculate a new path.

4. **Poor handling of unpredictable traffic**

   Sudden IoT bursts or high-volume video traffic can overload links before
   the network reacts.

5. **No traffic prediction**

   Traditional routing generally reacts to current conditions rather than
   predicting future traffic conditions.

Therefore, traditional routing is not ideal for a network that needs
proactive QoS management and rapid recovery.

---

## 3. What SDN Adds

Software-Defined Networking separates the network into logical planes.

### Data Plane

The data plane contains the actual network devices that forward packets.

In our project, the data plane is implemented using:

- Mininet
- Open vSwitch (OVS)
- Hosts
- Network links

The switches forward packets according to flow rules installed by the
controller.

### Control Plane

The control plane contains the SDN controller.

Our implementation uses **OS-Ken** with **OpenFlow 1.3**.

The controller:

- communicates with OpenFlow switches
- receives Packet-In messages
- learns MAC addresses
- installs Flow-Mod rules
- collects network information
- participates in traffic engineering
- supports future QoS and self-healing decisions

### Application / AI Plane

The application layer contains the intelligence that analyzes network
information.

Our planned AI layer uses **PyTorch and LSTM-based prediction** to analyze
time-series telemetry and predict future traffic conditions.

The predicted information can then be used for QoS-aware traffic engineering.

---

## 4. Project Architecture

The project can therefore be viewed as three connected layers:

```text
+------------------------------------------------------+
|                APPLICATION / AI PLANE                |
|                                                      |
|   Traffic Prediction → QoS Decision → Routing        |
|                 PyTorch / LSTM                       |
+--------------------------↑---------------------------+
                           |
                    Network Information
                           |
+--------------------------↓---------------------------+
|                    CONTROL PLANE                     |
|                                                      |
|                 OS-Ken Controller                    |
|                                                      |
|  Telemetry | MAC Learning | QoS | Traffic Engineering|
|             | Self-Healing / Fast-Failover            |
+--------------------------↑---------------------------+
                           |
                     OpenFlow 1.3
                  Flow Rules / Statistics
                           |
+--------------------------↓---------------------------+
|                     DATA PLANE                      |
|                                                      |
|             Mininet + Open vSwitch                  |
|                                                      |
|       Hosts → Edge Switches → Core Switch           |
|                    ↘ Backup Path                    |
+------------------------------------------------------+