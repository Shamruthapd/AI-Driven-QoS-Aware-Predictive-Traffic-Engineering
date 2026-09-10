# Week 2 — SDN Controller Implementation and Verification Report

## 1. Project Information

**Project Title:** AI-driven QoS-Aware Predictive Traffic Engineering and Self-Healing in SDN-Based Edge Networks

**Role:** Member 1

**Week:** 2

**Primary Responsibility:** SDN Controller Implementation

---

## 2. Week 2 Objective

The objective of Week 2 was to establish and verify the Software-Defined Networking control plane for the proposed system.

The implementation connects a Mininet/Open vSwitch data plane to an OS-Ken SDN controller using OpenFlow 1.3.

The controller provides the basic forwarding functionality required for the later QoS monitoring, traffic generation, telemetry collection, and predictive traffic-engineering stages of the project.

---

## 3. Implementation Environment

The verified implementation uses:

| Component | Version / Configuration |
|---|---|
| Operating System | Ubuntu/Linux VM |
| Python | 3.12.3 |
| SDN Controller Framework | OS-Ken 4.2.1 |
| Network Emulator | Mininet 2.3.0 |
| Virtual Switch | Open vSwitch 3.3.4 |
| Southbound Protocol | OpenFlow 1.3 |
| Controller Endpoint | 127.0.0.1:6633 |
| Virtual Environment | `~/SDN-Lab/venv` |

---

## 4. Controller Architecture

The Week 2 controller implementation is divided into modular components.

                    SDN Control Plane
                           |
                    OS-Ken Controller
                           |
              +------------+------------+
              |            |            |
        controller/app.py monitor.py telemetry.py
              |            |            |
              |       Port Statistics   Raw CSV
              |            |            |
              +------------+------------+
                           |
                    OpenFlow 1.3
                           |
                    Open vSwitch
                           |
                     Mininet Hosts
                       h1     h2
## 4.1 Controller Launcher

The controller is launched using:

scripts/run_controller.py

The launcher uses the OS-Ken AppManager and loads:

os_ken.controller.ofp_handler
controller.app
controller.telemetry
controller.monitor

The project root is added to the Python path to ensure that the project modules can be imported correctly.

## 4.2 Main Controller

The main SDN application is implemented in:

controller/app.py

The controller is implemented as an OS-Ken application and explicitly declares:

OpenFlow 1.3

The implemented functionality includes:

switch feature handling;
table-miss flow installation;
Packet-In handling;
MAC learning;
destination lookup;
forwarding decision;
Flow-Mod installation;
Packet-Out transmission.
## 5. Switch Connection and OpenFlow 1.3

The Mininet topology was started using:

sudo mn --topo single,2 --mac \
  --switch ovsk,protocols=OpenFlow13 \
  --controller=remote,ip=127.0.0.1,port=6633

This creates a single-switch topology containing two hosts:

h1 ---- s1 ---- h2

The switch is configured to use OpenFlow 1.3 and connect to the remote OS-Ken controller at:

127.0.0.1:6633

The controller-switch connection was successfully established during verification.

## 6. Table-Miss Flow

When the switch connects, the controller handles the OpenFlow switch-features event.

A table-miss rule is then installed with priority:

0

The rule sends packets that do not match an existing forwarding entry to the controller.

This provides the Packet-In mechanism required for the controller to learn previously unknown MAC addresses.

## 7. Packet-In Processing

The controller processes OpenFlow Packet-In events.

For each Ethernet packet, the controller:

obtains the ingress port;
parses the Ethernet frame;
identifies the source MAC address;
identifies the destination MAC address;
records the source MAC and ingress port;
checks the MAC learning table;
determines the appropriate output port.

LLDP packets are explicitly ignored by the controller.

## 8. MAC Learning

The controller maintains a per-switch MAC learning table:

datapath ID
      |
      +-- MAC address → switch port

When a source MAC address is observed, its ingress port is recorded.

If the destination MAC address is known, the corresponding learned output port is selected.

If the destination is unknown, the controller uses flooding.

This provides the initial Layer-2 forwarding behavior of the SDN prototype.

## 9. Flow-Mod Installation

When the destination is known, the controller installs a forwarding flow on the switch.

The implemented match fields include:

in_port
eth_dst

The forwarding rule uses priority:

10

and outputs packets through the learned destination port.

This allows subsequent matching traffic to be forwarded directly by the switch rather than requiring controller processing for every packet.

## 10. Packet-Out Processing

The controller also sends the current Packet-In packet using an OpenFlow Packet-Out message.

The implementation handles both cases where the switch has buffered the packet and where the packet data must be explicitly included.

Therefore, the current packet can be forwarded immediately while a forwarding flow is installed for subsequent packets.

## 11. Telemetry Monitoring Integration

Although detailed telemetry processing is part of the later Week 4 work, the Week 2 controller launcher already loads the monitoring and telemetry applications.

controller/monitor.py:

tracks connected datapaths;
removes disconnected datapaths;
periodically sends OpenFlow port-statistics requests.

The configured polling interval is:

5 seconds

controller/telemetry.py receives OpenFlow port-statistics replies and stores raw measurements in:

datasets/raw/telemetry.csv

The raw telemetry architecture is intentionally separated from later feature processing so that derived QoS metrics can be generated reproducibly.

## 12. Connectivity Verification

Network connectivity was verified using Mininet:

pingall

The observed result was:

*** Results: 0% dropped (2/2 received)

This confirms successful end-to-end connectivity between the two Mininet hosts through the OpenFlow-controlled switch.

## 13. Flow-Table Verification

The live OVS flow table was inspected while the Mininet topology was running using:

sudo ovs-ofctl -O OpenFlow13 dump-flows s1

The verified flow table contained the following forwarding behavior.

h1 → h2
priority=10,
in_port="s1-eth1",
dl_dst=00:00:00:00:00:02
actions=output:"s1-eth2"
h2 → h1
priority=10,
in_port="s1-eth2",
dl_dst=00:00:00:00:00:01
actions=output:"s1-eth1"
Table-Miss
priority=0
actions=CONTROLLER:65535

The observed flow counters were non-zero, demonstrating that traffic had actually traversed the installed forwarding rules.

The evidence screenshot is stored at:

screenshots/week2-ovs-flow-table.jpg
## 14. Verification Results
Verification Item	Result
OS-Ken controller launch	Passed
OpenFlow 1.3	Passed
Remote controller connection	Passed
OVS switch connection	Passed
Table-miss installation	Passed
Packet-In processing	Passed
MAC learning	Passed
Flow-Mod installation	Passed
Packet-Out implementation	Passed
Mininet connectivity	Passed
pingall packet loss	0%
OVS forwarding flows	Verified
Flow counters	Non-zero
Flow-table evidence	Captured
## 15. Challenges and Resolution
Challenge 1 — Correct location for OVS flow inspection

The ovs-ofctl command was initially attempted inside the Mininet CLI.

The Mininet CLI reported the command as unknown because ovs-ofctl is a Linux shell utility rather than a Mininet CLI command.

Resolution: The Mininet topology was kept running while the flow table was inspected from a separate Linux terminal using:

sudo ovs-ofctl -O OpenFlow13 dump-flows s1
Challenge 2 — Switch unavailable after Mininet cleanup

After exiting Mininet, the OVS bridge s1 was removed as part of Mininet cleanup.

Consequently, attempting to inspect s1 after exiting Mininet produced:

s1 is not a bridge or a socket

Resolution: The topology was restarted, traffic was generated using pingall, and the live switch flow table was inspected before exiting Mininet.

## 16. Week 2 Deliverables

The completed Week 2 deliverables include:

OS-Ken-based SDN controller.
OpenFlow 1.3 switch integration.
Controller launcher.
Table-miss handling.
Packet-In processing.
MAC learning.
Dynamic Flow-Mod installation.
Packet-Out processing.
Mininet/OVS connectivity verification.
OVS flow-table verification.
Controller setup documentation.
Week 2 implementation report.
Flow-table verification screenshot.
## 17. Week 2 Outcome

Week 2 successfully establishes the functional SDN control-plane foundation of the project.

The verified implementation demonstrates that the OS-Ken controller can communicate with an Open vSwitch switch using OpenFlow 1.3, learn host MAC addresses, install forwarding flows dynamically, and forward traffic successfully between Mininet hosts.

The verified control-plane implementation provides the foundation for the next stages of the project:

SDN Controller
      ↓
Traffic Generation
      ↓
Telemetry Collection
      ↓
QoS Feature Extraction
      ↓
Predictive Traffic Engineering
      ↓
Self-Healing

Week 3 will focus on reproducible traffic generation and baseline traffic measurements.
