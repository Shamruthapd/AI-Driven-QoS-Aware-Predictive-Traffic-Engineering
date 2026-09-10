# Week 3 – Traffic Profiles

## Objective

The objective of Week 3 is to define different network traffic conditions that
can be used to test the QoS-aware SDN system.

The traffic profiles represent normal traffic as well as congested traffic.
These profiles will later be used for telemetry collection, QoS evaluation,
and AI-based traffic prediction.

## Traffic Types

### 1. Normal Traffic

Normal traffic represents regular network operation with low to moderate
network utilization.

Characteristics:
- Low packet loss
- Low to moderate bandwidth usage
- Normal latency
- Stable network conditions

Expected behavior:
The controller should forward traffic normally without requiring major
rerouting or QoS intervention.

### 2. High-Bandwidth Traffic

High-bandwidth traffic represents situations where one or more links carry
large amounts of data.

Characteristics:
- High bandwidth utilization
- Increased queue usage
- Possible increase in latency
- Higher probability of congestion

Expected behavior:
The controller should identify heavily utilized links and provide suitable
traffic forwarding decisions.

### 3. Congested Traffic

Congested traffic represents a network condition where traffic demand is
higher than the available link capacity.

Characteristics:
- High link utilization
- Increased delay
- Packet loss may occur
- Queue buildup

Expected behavior:
The SDN controller should detect the congestion through network telemetry
and use an alternate path when available.

### 4. Link Failure Condition

A link failure represents a network failure where one forwarding path becomes
unavailable.

Characteristics:
- Link becomes unavailable
- Existing traffic path is disrupted
- Connectivity may be temporarily affected

Expected behavior:
The SDN network should use the available backup path and restore connectivity.

## QoS Metrics

The following metrics are considered while evaluating the traffic profiles:

- Bandwidth utilization
- Throughput
- Latency
- Packet loss
- Queue usage
- Link availability

These metrics provide the input required for later QoS-aware traffic
engineering and prediction.