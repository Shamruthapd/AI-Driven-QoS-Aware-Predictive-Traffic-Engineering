#!/usr/bin/env python3
"""
Repeatable Link Failure Injection Script for Mininet / OVS.
Simulates hard link failures by toggling interfaces down and up with high-precision timestamping.
Used for Week 9 Fast-Failover switch verification and Week 11 failure simulation trials.
"""

import argparse
import csv
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def log_event(log_path, event_type, interface, extra=""):
    now_iso = datetime.now(timezone.utc).isoformat()
    epoch_ts = time.time()
    row = {
        "timestamp_iso": now_iso,
        "timestamp_epoch": f"{epoch_ts:.6f}",
        "interface": interface,
        "event_type": event_type,
        "details": extra
    }
    
    if log_path:
        log_file = Path(log_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_exists = log_file.exists()
        with open(log_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["timestamp_iso", "timestamp_epoch", "interface", "event_type", "details"])
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
            f.flush()
            
    print(f"[{now_iso}] [{event_type}] Interface: {interface} | Epoch: {epoch_ts:.6f} | {extra}")
    return epoch_ts


def set_link_state(interface, state):
    """
    Sets link state using ip link. Requires root/sudo privileges.
    """
    cmd = ["ip", "link", "set", "dev", interface, state]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error changing state of {interface} to {state}: {e.stderr.decode().strip()}", file=sys.stderr)
        return False
    except FileNotFoundError:
        # If running outside Linux/Mininet container or in simulation mode
        print(f"[Simulated] ip link set dev {interface} {state}")
        return True


def run_failure_cycle(interface, down_duration, log_file, cycle=1, total_cycles=1):
    desc = f"Cycle {cycle}/{total_cycles}"
    log_event(log_file, "LINK_DOWN_SCHEDULED", interface, f"Duration: {down_duration}s - {desc}")
    
    # 1. Bring interface down
    set_link_state(interface, "down")
    ts_down = log_event(log_file, "LINK_DOWN", interface, desc)
    
    # 2. Wait set duration
    time.sleep(down_duration)
    
    # 3. Bring interface back up (failback)
    set_link_state(interface, "up")
    ts_up = log_event(log_file, "LINK_UP", interface, f"Recovered after {down_duration}s - {desc}")
    
    return ts_down, ts_up


def main():
    parser = argparse.ArgumentParser(description="Repeatable Link Failure Injection")
    parser.add_argument("--interface", default="s1-eth3", help="Interface to toggle (default: s1-eth3)")
    parser.add_argument("--down-duration", type=float, default=5.0, help="Duration in seconds link stays down (default: 5.0)")
    parser.add_argument("--log-file", default="data/results/failure_injection_log.csv", help="CSV log destination")
    parser.add_argument("--cycles", type=int, default=1, help="Number of failure cycles (default: 1; >1 for flapping)")
    parser.add_argument("--up-interval", type=float, default=5.0, help="Time between cycles if flapping (default: 5.0)")
    parser.add_argument("--state-only", choices=["down", "up"], help="Set state without restoring")
    args = parser.parse_args()

    print(f"=== Mininet Link Failure Injector ===")
    print(f"Target Interface: {args.interface}")
    print(f"Down Duration:    {args.down_duration}s")
    print(f"Cycles:           {args.cycles}")
    print(f"Log Path:         {args.log_file}")
    print("=====================================")

    if args.state_only:
        set_link_state(args.interface, args.state_only)
        log_event(args.log_file, f"LINK_{args.state_only.upper()}", args.interface, "State-only invocation")
        return

    for c in range(1, args.cycles + 1):
        run_failure_cycle(args.interface, args.down_duration, args.log_file, cycle=c, total_cycles=args.cycles)
        if c < args.cycles:
            print(f"Waiting {args.up_interval}s before next flap cycle...")
            time.sleep(args.up_interval)

    print("=== Failure Injection Sequence Completed ===")


if __name__ == "__main__":
    main()
