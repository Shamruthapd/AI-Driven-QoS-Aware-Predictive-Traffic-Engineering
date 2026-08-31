# Week 3 – Integration Testing

## Objective

The purpose of integration testing is to verify that the Mininet topology,
OpenFlow switches, and OS-Ken controller communicate correctly.

## Components Tested

The following components are involved:

1. Mininet topology
2. Open vSwitch switches
3. OS-Ken SDN controller
4. OpenFlow 1.3 communication
5. Host-to-host connectivity

## Test Topology

The topology contains:

- 4 hosts: h1, h2, h3, h4
- 3 switches: s1, s2, s3
- 1 SDN controller

Host connections:

- h1 → s1
- h2 → s1
- h3 → s2
- h4 → s2

Switch connections:

- s1 → s3
- s2 → s3
- s1 → s2 (backup link)

## Integration Test Procedure

### Step 1 – Start the Controller

The OS-Ken controller is started first so that the switches can connect to it.

### Step 2 – Start Mininet

The Mininet topology is started using the configured topology script.

### Step 3 – Verify Switch Connections

The controller output is checked to verify that the switches successfully
connect using OpenFlow 1.3.

### Step 4 – Verify Topology

Inside the Mininet CLI:

```text
nodes
net