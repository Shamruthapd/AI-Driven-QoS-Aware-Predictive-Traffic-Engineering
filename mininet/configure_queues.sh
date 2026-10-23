#!/bin/bash
# ==============================================================================
# Script to configure Open vSwitch QoS Queues on Edge Switches (s1 and s2)
# Configures both Primary and Backup inter-switch links to guarantee QoS
# protection during normal operation AND during Fast-Failover / Proactive Reroute.
# ==============================================================================

set -e

echo "=== Cleaning existing QoS configurations on s1 and s2 ==="
for SW in s1 s2; do
  for PORT in ${SW}-eth1 ${SW}-eth2 ${SW}-eth3 ${SW}-eth4; do
    ovs-vsctl clear Port $PORT qos 2>/dev/null || true
  done
  ovs-vsctl destroy QoS $SW 2>/dev/null || true
  ovs-vsctl destroy Queue $SW 2>/dev/null || true
done

echo "=== Setting up QoS and Queues on s1 and s2 ports ==="
# Queue 0 (Best-Effort / Bulk Data): Max rate capped at 4 Mbps
# Queue 1 (Guaranteed Priority Stream - VoIP/Video/UDP 5202): Min rate 8 Mbps, Max 10 Mbps
# Applied to primary egress (eth3) and backup egress (eth4) on s1 and s2

PORTS_TO_CONFIGURE=(
  "s1-eth2" # Host h2 egress
  "s1-eth3" # Primary link to s3
  "s1-eth4" # Backup direct link to s2
  "s2-eth2" # Host h4 egress
  "s2-eth3" # Primary link to s3
  "s2-eth4" # Backup direct link to s1
)

for PORT in "${PORTS_TO_CONFIGURE[@]}"; do
  echo "Configuring QoS queues on $PORT..."
  ovs-vsctl set Port $PORT qos=@newqos -- \
    --id=@newqos create QoS type=linux-htb other-config:max-rate=10000000 queues=0=@q0,1=@q1 -- \
    --id=@q0 create Queue other-config:max-rate=4000000 -- \
    --id=@q1 create Queue other-config:min-rate=8000000 other-config:max-rate=10000000
done

echo "=== Verifying Queue Configurations ==="
for PORT in "${PORTS_TO_CONFIGURE[@]}"; do
  echo "--- QoS on $PORT ---"
  ovs-vsctl list queue || true
done

echo "=== QoS Queue Configuration Completed Successfully on Primary & Backup Ports ==="
