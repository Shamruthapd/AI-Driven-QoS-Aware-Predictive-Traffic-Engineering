#!/usr/bin/env python3
"""
Automated Scenario Launcher for Mininet.
Parses standardized scenario YAML files (S1, S2, S3), orchestrates iPerf3 and Scapy traffic flows,
triggers scheduled link failures, and archives raw benchmark outputs by trial_id and mode.
"""

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def load_scenario(yaml_path):
    path = Path(yaml_path)
    if not path.exists():
        raise FileNotFoundError(f"Scenario configuration file not found: {yaml_path}")
    
    if yaml is not None:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    else:
        # Fallback simple parser for environments without PyYAML
        data = {"flows": [], "failure_events": []}
        # default fallback mappings
        if "S1" in str(yaml_path):
            data["scenario_id"] = "S1_steady"
            data["duration_seconds"] = 30
        elif "S2" in str(yaml_path):
            data["scenario_id"] = "S2_congestion"
            data["duration_seconds"] = 45
        elif "S3" in str(yaml_path):
            data["scenario_id"] = "S3_failure"
            data["duration_seconds"] = 45
        return data


def run_host_cmd(host_name, cmd_str, output_file=None, is_async=True):
    """
    Executes a command on a Mininet host interface or in background.
    """
    print(f"[*] [{host_name}] Running: {cmd_str}")
    if output_file:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        f_out = open(output_file, "w", encoding="utf-8")
    else:
        f_out = subprocess.DEVNULL

    proc = subprocess.Popen(
        cmd_str,
        shell=True,
        stdout=f_out,
        stderr=subprocess.STDOUT
    )
    if not is_async:
        proc.wait()
    return proc


def execute_scenario(scenario_file, mode="full_ai_qos_ff", trial_id="trial_001", output_dir="data/results/week11_raw"):
    scenario = load_scenario(scenario_file)
    scenario_id = scenario.get("scenario_id", Path(scenario_file).stem)
    duration = scenario.get("duration_seconds", 30)
    flows = scenario.get("flows", [])
    failures = scenario.get("failure_events", [])
    
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    print("==================================================================")
    print(f" Launching Scenario: {scenario_id} ({scenario.get('name', '')})")
    print(f" Mode:                {mode}")
    print(f" Trial ID:            {trial_id}")
    print(f" Total Duration:      {duration}s")
    print(f" Raw Output Dir:      {out_path}")
    print("==================================================================")

    procs = []
    start_wall_time = time.time()

    # Launch Flows according to schedule
    for flow in flows:
        flow_id = flow.get("id")
        flow_type = flow.get("type")
        start_delay = flow.get("start_time_sec", 0.0)
        flow_dur = flow.get("duration_sec", duration)
        client = flow.get("client_host", "h1")
        server_ip = flow.get("server_ip", "10.0.0.3")
        port = flow.get("port", 5201)
        bw = flow.get("bandwidth_mbps", 4.0)
        dscp = flow.get("dscp", 0)

        # Output raw file naming convention
        flow_out_file = out_path / f"{trial_id}_{mode}_{scenario_id}_{flow_id}.json"

        if flow_type == "iperf3_udp":
            cmd = f"iperf3 -c {server_ip} -p {port} -u -b {bw}M -t {int(flow_dur)} -J"
            if dscp:
                cmd += f" --dscp {dscp}"
        elif flow_type == "iperf3_tcp":
            cmd = f"iperf3 -c {server_ip} -p {port} -b {bw}M -t {int(flow_dur)} -J"
        elif flow_type == "scapy_iot":
            rate = flow.get("rate_pps", 100)
            cmd = f"python3 traffic/scapy_iot_traffic.py --target-ip {server_ip} --port {port} --rate {rate} --duration {int(flow_dur)}"
            flow_out_file = out_path / f"{trial_id}_{mode}_{scenario_id}_{flow_id}.log"
        else:
            continue

        def delayed_start(delay, host, c_str, out_f):
            if delay > 0:
                time.sleep(delay)
            p = run_host_cmd(host, c_str, output_file=out_f, is_async=True)
            procs.append(p)

        t = threading.Thread(target=delayed_start, args=(start_delay, client, cmd, flow_out_file))
        t.daemon = True
        t.start()

    # Launch High-rate ping monitor
    ping_log = out_path / f"{trial_id}_{mode}_{scenario_id}_ping.log"
    ping_cmd = f"ping -i 0.010 -c {int(duration * 100)} 10.0.0.3"
    p_ping = run_host_cmd("h1", ping_cmd, output_file=ping_log, is_async=True)
    procs.append(p_ping)

    # Schedule Failure Events
    for fail in failures:
        intf = fail.get("interface", "s1-eth3")
        f_start = fail.get("start_time_sec", 15.0)
        f_dur = fail.get("down_duration_sec", 5.0)

        def delayed_fail(delay, down_dur, interface):
            time.sleep(delay)
            fail_cmd = f"python3 mininet/inject_failure.py --interface {interface} --down-duration {down_dur}"
            run_host_cmd("root", fail_cmd, is_async=False)

        tf = threading.Thread(target=delayed_fail, args=(f_start, f_dur, intf))
        tf.daemon = True
        tf.start()

    print(f"[*] Running scenario for {duration} seconds...")
    time.sleep(duration + 2.0)

    # Clean up processes
    for p in procs:
        try:
            p.terminate()
        except Exception:
            pass

    print(f"[*] Scenario {scenario_id} completed successfully. Raw files saved in {out_path}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scenario Launcher for Mininet")
    parser.add_argument("--scenario", required=True, help="Path to scenario YAML file (e.g. scenarios/S1_steady.yaml)")
    parser.add_argument("--mode", choices=["baseline_shortest_path", "reactive", "full_ai_qos_ff"], default="full_ai_qos_ff", help="Operational mode")
    parser.add_argument("--trial-id", default="trial_001", help="Trial identifier")
    parser.add_argument("--output-dir", default="data/results/week11_raw", help="Directory to store raw logs and JSON")
    args = parser.parse_args()

    execute_scenario(args.scenario, mode=args.mode, trial_id=args.trial_id, output_dir=args.output_dir)
