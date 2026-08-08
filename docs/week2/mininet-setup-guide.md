# Mininet Setup & Verification Guide

## 1. Network Topology Summary
This setup implements the starter topology for our SDN-Based Edge Network project:
* **Switches**: 2 Edge Switches (`s1`, `s2`) and 1 Core Switch (`s3`).
* **Hosts**: Host A (`h1` - 10.0.0.1) and Host B (`h2` - 10.0.0.2).
* **Controller**: Configured in `RemoteController` mode pointing to `127.0.0.1:6653` for Ryu integration[cite: 1].
* **Link Bandwidths**: Host-to-Edge links set to 10 Mbps; Edge-to-Core links set to 100 Mbps[cite: 1].

## 2. Setup & Execution Instructions
1. Install Mininet and Open vSwitch:
   ```bash
   sudo apt update
   sudo apt install -y mininet openvswitch-switch openvswitch-testcontroller
