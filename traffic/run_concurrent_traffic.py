#!/usr/bin/env python3
"""
Integration verification (Weeks 3 & 4)
=======================================

Runs Member 1's iPerf3 flow and Member 3's Scapy bursty-IoT generator
CONCURRENTLY inside the SAME Mininet testbed, proving that the two
generators do not conflict on ports or IPs.

Resource allocation matrix (FatTreeEdgeTopo from mininet/topo.py):

    Generator          Hosts     IPs          L4 port  Type
    -----------------  --------  -----------  -------  --------------------------
    iPerf3 (Member 1)  h1 -> h2  10.0.0.1/.2  5201     continuous UDP/TCP
    Scapy  (Member 3)  h3 -> h4  10.0.0.3/.4  5202     bursty UDP + anomaly spike

Prerequisite: the OS-Ken controller (scripts/run_controller.py) must be
running and listening on 127.0.0.1:6633.

Usage:
    sudo python3 traffic/run_concurrent_traffic.py \
        --duration 30 --protocol udp --bitrate 5M
"""

import argparse
import importlib.util
import socket
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from mininet.link import TCLink
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, RemoteController

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOPOLOGY_FILE = PROJECT_ROOT / "mininet" / "topo.py"
SCAPY_SCRIPT = PROJECT_ROOT / "traffic" / "scapy_iot_traffic.py"
RESULTS_DIR = PROJECT_ROOT / "results" / "week3"

IPERF3_PORT = 5201   # Member 1 -- iPerf3 default listener
SCAPY_PORT = 5202    # Member 3 -- UDP IoT bursts (distinct from 5201)
CONTROLLER_PORT = 6633


def ensure_controller_reachable(ip, port):
    """Warn early if the OS-Ken controller is not up yet."""
    try:
        with socket.create_connection((ip, port), timeout=3):
            return True
    except OSError as exc:
        print("ERROR: SDN controller not reachable at %s:%s (%s)" % (ip, port, exc))
        print("Start it first with:  python3 scripts/run_controller.py")
        return False


def load_project_topology():
    """
    Import mininet/topo.py under a private module name so it cannot clash
    with the installed Mininet package namespace.
    """
    spec = importlib.util.spec_from_file_location("project_fattree_topo", TOPOLOGY_FILE)
    topo_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(topo_module)
    return topo_module.FatTreeEdgeTopo


def connectivity_ok(host, target_ip, count=3):
    out = host.cmd("ping -c %d %s" % (count, target_ip))
    return ("0% packet loss" in out) and ("bytes from" in out), out


def member1_iperf(net, args):
    """Member 1 -- continuous iPerf3 flow on h1 -> h2, port 5201."""
    h1, h2 = net.get("h1"), net.get("h2")

    h2.cmd("iperf3 -s -D -p %d > /dev/null 2>&1" % IPERF3_PORT)
    time.sleep(1)

    if args.protocol == "tcp":
        command = "iperf3 -c %s -p %d -t %s" % (h2.IP(), IPERF3_PORT, args.duration)
    else:
        command = "iperf3 -c %s -p %d -u -b %s -t %s" % (
            h2.IP(),
            IPERF3_PORT,
            args.bitrate,
            args.duration,
        )

    output = h1.cmd(command)
    log_file = RESULTS_DIR / f"concurrent_iperf_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_file.write_text(output, encoding="utf-8")
    print("[Member 1] iPerf3 completed -> %s" % log_file)
    print(output)

    h2.cmd("pkill -f 'iperf3 -s' > /dev/null 2>&1")


def member3_scapy(net, args):
    """Member 3 -- Scapy bursty IoT UDP on h3 -> h4, port 5202."""
    h3, h4 = net.get("h3"), net.get("h4")
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    server_log = RESULTS_DIR / ("concurrent_scapy_server_%s.log" % run_id)
    server_cmd = (
        "python3 '%s' server --bind-ip 0.0.0.0 "
        "--port %d --total-duration %s > '%s' 2>&1 &"
    ) % (SCAPY_SCRIPT, SCAPY_PORT, args.duration, server_log)
    h4.cmd(server_cmd)
    time.sleep(2)

    client_cmd = (
        "python3 '%s' client --server-ip %s --port %d "
        "--total-duration %s --burst-duration 2 --idle-duration 3 "
        "--burst-rate 500 --payload-size 128 "
        "--anomaly-start %s --anomaly-duration %s --anomaly-rate 4000"
    ) % (
        SCAPY_SCRIPT,
        h4.IP(),
        SCAPY_PORT,
        args.duration,
        args.anomaly_start,
        args.anomaly_duration,
    )
    output = h3.cmd(client_cmd)
    client_log = RESULTS_DIR / ("concurrent_scapy_client_%s.log" % run_id)
    client_log.write_text(output, encoding="utf-8")
    print("[Member 3] Scapy IoT client completed -> %s" % client_log)
    print(output)


def main():
    parser = argparse.ArgumentParser(
        description="Run Member 1 iPerf3 + Member 3 Scapy IoT concurrently in one Mininet testbed."
    )
    parser.add_argument("--duration", type=float, default=30.0)
    parser.add_argument("--protocol", choices=["tcp", "udp"], default="udp")
    parser.add_argument("--bitrate", default="5M")
    parser.add_argument("--controller-ip", default="127.0.0.1")
    parser.add_argument("--controller-port", type=int, default=CONTROLLER_PORT)
    parser.add_argument("--anomaly-start", type=float, default=10.0)
    parser.add_argument("--anomaly-duration", type=float, default=10.0)
    parser.add_argument(
        "--allow-connectivity-failure",
        action="store_true",
        help="continue even if the 3-bridge connectivity check fails",
    )
    args = parser.parse_args()

    if not ensure_controller_reachable(args.controller_ip, args.controller_port):
        sys.exit(1)

    setLogLevel("info")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    topo_class = load_project_topology()

    print("=" * 75)
    print(" Concurrency matrix -- no port/IP conflicts")
    print("   Member 1 | iPerf3 continuous  | 10.0.0.1 -> 10.0.0.2 | UDP/TCP %d" % IPERF3_PORT)
    print("   Member 3 | Scapy bursty IoT   | 10.0.0.3 -> 10.0.0.4 | UDP     %d" % SCAPY_PORT)
    print("=" * 75)

    net = Mininet(
        topo=topo_class(),
        controller=lambda name: RemoteController(
            name,
            ip=args.controller_ip,
            port=args.controller_port,
        ),
        switch=OVSKernelSwitch,
        link=TCLink,
    )
    net.start()

    try:
        h1, h2, h3, h4 = (net.get("h1"), net.get("h2"), net.get("h3"), net.get("h4"))
        time.sleep(8)  # let STP converge and table-miss flows install

        ok1, out1 = connectivity_ok(h1, h3.IP())
        print("Connectivity h1 -> h3 (bidirectional over s1-s3-s2):\n%s" % out1)
        ok2, out2 = connectivity_ok(h2, h4.IP())
        print("Connectivity h2 -> h4 (bidirectional over s1-s3-s2):\n%s" % out2)

        if not (ok1 and ok2):
            msg = "3-bridge bidirectional connectivity check FAILED"
            if not args.allow_connectivity_failure:
                print("ERROR: " + msg)
                sys.exit(1)
            print("WARNING: " + msg + " (--allow-connectivity-failure)")

        t1 = threading.Thread(target=member1_iperf, args=(net, args))
        t2 = threading.Thread(target=member3_scapy, args=(net, args))
        t1.start()
        t2.start()
        t1.join()
        t2.join()
    finally:
        net.stop()

    print("Both generators ran concurrently -- see results/week3/ logs.")


if __name__ == "__main__":
    main()
