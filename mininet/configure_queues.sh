#!/bin/bash
# Script to configure Open vSwitch QoS Queues on s1

echo "=== Cleaning existing QoS configurations on s1 ==="
ovs-vsctl clear Port s1-eth2 qos
ovs-vsctl clear Port s1-eth3 qos
ovs-vsctl destroy QoS s1
ovs-vsctl destroy Queue s1

echo "=== Setting up QoS and Queues on s1-eth2 and s1-eth3 ==="
# Link capacity constraint: 10 Mbps (10,000,000 bps)
# Queue 0: Rate-limited Bulk Data (Max: 4 Mbps)
# Queue 1: Guaranteed Priority Stream (Min: 8 Mbps, Max: 10 Mbps)

for PORT in s1-eth2 s1-eth3; do
  ovs-vsctl set Port $PORT qos=@newqos -- \
    --id=@newqos create QoS type=linux-htb other-config:max-rate=10000000 queues=0=@q0,1=@q1 -- \
    --id=@q0 create Queue other-config:max-rate=4000000 -- \
    --id=@q1 create Queue other-config:min-rate=8000000 other-config:max-rate=10000000
done

echo "=== QoS Queue Configuration Completed Successfully ==="
