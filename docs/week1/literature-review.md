# Week 1 — Literature Review

## Project

**AI-Driven QoS-Aware Predictive Traffic Engineering and Self-Healing
in SDN-Based Edge Networks**

---

## 1. Purpose

This literature review studies existing research related to:

- Software-Defined Networking (SDN)
- Machine Learning for traffic prediction
- QoS-aware traffic management
- Adaptive traffic engineering
- Self-healing and network resilience

The main purpose is to understand how existing approaches solve network
congestion and traffic-management problems and identify the gap that our
project aims to address.

---

# 2. Paper 1 — LSTM-Based QoS-Aware Proactive Flow-Rule Placement

### Paper

**P. Sowmya et al., "LSTM-Based QoS-Aware Proactive Flow-Rule Placement
in SDIoV"**

### Problem

Traditional SDN flow placement is often reactive. A flow rule is installed
only after the controller receives a request from the switch.

This can cause additional delay for applications that require fast and
reliable communication.

The paper therefore investigates whether future network conditions can be
predicted and flow rules can be installed in advance.

### Approach

The authors use an **LSTM model** to predict the next access point of a
vehicle.

The model uses time-dependent information such as:

- position
- speed
- direction
- node information

The prediction is then used to proactively install QoS-aware OpenFlow
rules.

In simple terms:

    Past movement information
            ↓
        LSTM model
            ↓
    Predict next AP
            ↓
    Install flow rule early

### Evaluation

The system was evaluated using:

- Mininet
- 10 access points
- 10 nodes
- Caltrans PeMS mobility data

The study considered different QoS traffic classes and compared proactive
flow placement with reactive approaches.

### Key Results

The paper reports approximately:

- **99% training accuracy**
- **88% validation accuracy**

The proactive approach also reduced RTT and packet drops for
latency-sensitive and drop-sensitive traffic compared with reactive
approaches.

### Limitations

The approach has several limitations:

- Focuses mainly on vehicular mobility.
- Uses a specific mobility dataset.
- Assumes a fixed access-point topology.
- Uses LSTM prediction but does not combine it with reinforcement learning.
- Does not study multi-failure recovery or Fast-Failover.

### What We Learn / Adopt

Our project adopts the idea of:

**time-series data → LSTM prediction → proactive network action**

We also use the concept of QoS-based traffic classes.

### Difference From Our Project

Our project is not limited to vehicular networks.

We use an edge/IoT-style environment with:

- bulk TCP traffic
- UDP/video-like traffic
- IoT traffic bursts

We also add **Fast-Failover** so that the network can recover quickly from
link failures.

---

# 3. Paper 2 — Adaptive and Predictive Routing in SDN

### Paper

**Y. Shukla et al., "Adaptive and Predictive Routing in SDN Using
Q-Learning and Neural Networks"**

### Problem

Traffic conditions can change rapidly.

A routing algorithm that only uses current information may not select the
best path when traffic changes.

The paper therefore combines prediction with adaptive routing.

### Approach

The paper uses two main techniques:

1. **Q-learning** for adaptive routing.
2. **Feed-forward Neural Network** for predicting short-term traffic demand.

The basic idea is:

    Current network statistics
              ↓
      Predict future traffic
              ↓
          Q-learning
              ↓
        Routing decision

### Evaluation

The approach was tested using a Mininet three-tier datacenter-style
topology.

The authors measured:

- latency
- throughput
- packet delivery ratio
- jitter
- controller overhead

### Key Results

The study found that adding Q-learning:

- reduced latency
- improved throughput stability

Adding the predictive neural network:

- improved packet delivery
- reduced jitter

The combined adaptive + predictive approach performed better than the
static baseline approaches.

### Limitations

The study:

- Uses a relatively small synthetic topology.
- Uses a feed-forward neural network rather than LSTM.
- Uses basic Q-learning.
- Does not focus on per-QoS traffic classes.
- Does not implement Fast-Failover or explicit backup paths.

### What We Learn / Adopt

We adopt the general idea of combining:

**traffic prediction + adaptive network decisions**

We also use similar performance metrics such as:

- latency
- throughput
- jitter

### Difference From Our Project

Our project focuses on edge/IoT traffic rather than a datacenter-style
network.

We use LSTM-based time-series prediction and combine traffic engineering
with QoS and Fast-Failover.

---

# 4. Paper 3 — 6G-Enabled SDN with DRL-Based Traffic Engineering

### Paper

**Kolakowski et al., "On 6G-Enabled SDN User Plane with DRL-based
Traffic Engineering"**

### Problem

Future 6G networks are expected to support highly dynamic and complex
traffic.

Fixed routing techniques may not be sufficient for such environments.

The paper investigates how Deep Reinforcement Learning (DRL) can be
integrated with SDN traffic engineering.

### Approach

The paper proposes a **hierarchical SDN architecture** in which different
controller levels can use learning-based traffic-engineering decisions.

The basic concept is:

    Network state
         ↓
      DRL agent
         ↓
    Learn routing policy
         ↓
    Traffic engineering decision

### Evaluation

The work is mainly architectural and conceptual.

It does not provide the same type of detailed Mininet experiment and
performance measurements as the other two papers.

### Key Contribution

The main contribution is the idea of integrating learning-based decision
making into the SDN control architecture for future dynamic networks.

### Limitations

The paper:

- is mainly conceptual
- does not provide a complete implementation
- does not present real traffic-data evaluation
- does not provide detailed QoS evaluation
- does not implement Fast-Failover

### What We Learn / Adopt

We adopt the broader concept that machine learning can be integrated into
the SDN control layer to make traffic-engineering decisions more
intelligent and adaptive.

### Difference From Our Project

Our project uses a simpler single-controller architecture.

Instead of a hierarchical DRL system, our planned AI component uses
**PyTorch and LSTM-based traffic prediction**.

We additionally include QoS and Fast-Failover.

---

# 5. Comparison of the Three Papers

| Paper | Main Technique | ML Technique | Main Focus | Fast-Failover |
|---|---|---|---|---|
| Sowmya et al. | Proactive flow placement | LSTM | Vehicular QoS | No |
| Shukla et al. | Predictive adaptive routing | NN + Q-learning | Traffic engineering | No |
| Kolakowski et al. | Intelligent traffic engineering | DRL | 6G / SDN architecture | No |
| **Our Project** | Predictive QoS-aware traffic engineering + self-healing | **LSTM** | **Edge / IoT** | **Yes** |

---

# 6. Research Gap

The reviewed papers show that machine learning can improve SDN traffic
management.

However, the approaches do not combine all the requirements of our project
in one system.

### Gap 1 — Prediction and failure recovery

Existing works mainly focus on prediction or adaptive routing.

Our project combines traffic prediction with Fast-Failover.

### Gap 2 — QoS + self-healing

The reviewed approaches do not combine QoS-aware traffic management with
hardware-level Fast-Failover.

Our project aims to combine both.

### Gap 3 — Edge / IoT traffic

The reviewed works mainly consider vehicular, datacenter, or conceptual
6G environments.

Our project focuses on an edge/IoT-style traffic mix.

### Gap 4 — Proactive instead of only reactive operation

Traditional SDN forwarding can still depend on Packet-In events and
controller decisions after a flow appears.

Our project aims to use telemetry and prediction to make traffic-management
decisions proactively.

---

# 7. What Our Project Adopts

From the literature, our project adopts the following ideas:

| Literature Idea | Used in Our Project |
|---|---|
| SDN centralized control | Yes |
| OpenFlow-based control | Yes |
| Network telemetry | Yes |
| Time-series data | Yes |
| LSTM prediction | Planned |
| QoS classification | Planned |
| Predictive traffic engineering | Planned |
| Adaptive routing concepts | Partially |
| Fast-Failover | Yes |
| Edge / IoT traffic | Yes |

---

# 8. What Makes Our Approach Different

The main idea of our project is to combine the strengths of the reviewed
approaches.

    Network Traffic
          ↓
       Telemetry
          ↓
    Data Processing
          ↓
    LSTM Prediction
          ↓
     QoS Decision
          ↓
  Traffic Engineering
          ↓
     Flow Rules
          ↓
    Normal Forwarding
          ↓
      Link Failure?
        /       \
      No         Yes
      ↓           ↓
  Continue    Fast-Failover
                  ↓
             Backup Path

Therefore, the project aims to provide both:

1. **Proactive intelligence** through traffic prediction.
2. **Fast recovery** through OpenFlow Fast-Failover.

---

# 9. Implementation Difference — Ryu vs OS-Ken

Some of the reviewed papers use the Ryu SDN controller.

Our actual implementation uses **OS-Ken**.

The controller was changed from Ryu to OS-Ken because of compatibility and
dependency issues during project setup.

Therefore:

- The literature review describes the controllers actually used by the
  papers.
- Our implementation is documented as **OS-Ken**.
- The project uses **OpenFlow 1.3** for communication between the controller
  and Open vSwitch.

The current project architecture is:

    Mininet + Open vSwitch
              ↓
          OpenFlow 1.3
              ↓
        OS-Ken Controller
              ↓
       Telemetry / Control
              ↓
        PyTorch / LSTM
              ↓
     QoS + Traffic Engineering
              ↓
        Fast-Failover

---

# 10. Overall Literature Conclusion

The three papers demonstrate that SDN becomes more powerful when combined
with machine learning.

Sowmya et al. demonstrate the usefulness of LSTM-based prediction for
proactive QoS-aware flow placement.

Shukla et al. demonstrate that combining traffic prediction with adaptive
routing can improve network performance.

Kolakowski et al. show how learning-based traffic engineering can be
integrated into future SDN architectures.

However, these works do not combine:

**LSTM prediction + QoS + edge/IoT traffic + Fast-Failover**

in the same practical testbed.

Our project therefore builds on these ideas and combines them into a
predictive and self-healing SDN framework.