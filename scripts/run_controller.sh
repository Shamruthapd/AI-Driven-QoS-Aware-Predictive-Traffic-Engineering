#!/usr/bin/env bash
# ==============================================================================
# Unified Controller Launcher
# AI-Driven QoS-Aware Predictive Traffic Engineering & Self-Healing
# Supports both Local (127.0.0.1) and Remote (Tailscale) endpoints
# ==============================================================================

set -e

# Default parameters
OF_PORT=6633
ENDPOINT_TYPE="${1:-local}"

echo "=================================================================="
echo " Starting AI-QoS-Aware SDN Controller Application "
echo "=================================================================="

if [ "$ENDPOINT_TYPE" == "remote" ] || [ "$ENDPOINT_TYPE" == "tailscale" ]; then
    echo "[*] Launching in REMOTE / TAILSCALE mode"
    CONTROLLER_IP="100.85.20.10"
else
    echo "[*] Launching in LOCAL fallback mode"
    CONTROLLER_IP="127.0.0.1"
fi

echo "[*] Binding OpenFlow Port: $OF_PORT"
echo "[*] Bridge Host: $CONTROLLER_IP"

# Ensure log and results directory exist
mkdir -p data/results/week11_controller_timelines
mkdir -p logs

# Run controller with Fast-Failover groups, Flow Classifier, Telemetry, and AI Bridge
export PYTHONPATH=".:$PYTHONPATH"

python3 scripts/run_controller.py \
    --controller-port $OF_PORT \
    --app controller.app \
    --app controller.ff_groups \
    --app controller.port_status_logger
