#!/usr/bin/env python3

"""
Member 1 -- repeatable iPerf3 baseline traffic experiments (Week 3).

Standalone usage creates its own single-switch topology (h1 <-> h2,
controller 127.0.0.1:6633) and uses iPerf3 UDP/TCP port 5201.

For CONCURRENT experiments with Member 3's Scapy bursty-IoT generator
use traffic/run_concurrent_traffic.py, which runs both generators inside
ONE Mininet testbed with a disjoint allocation matrix:

    iPerf3 (Member 1): h1 (10.0.0.1) -> h2 (10.0.0.2), L4 port 5201
    Scapy  (Member 3): h3 (10.0.0.3) -> h4 (10.0.0.4), L4 port 5202
"""

import argparse
from datetime import datetime
from pathlib import Path

from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.topo import SingleSwitchTopo


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results" / "week3"


def run_experiment(protocol, duration, bitrate):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = RESULTS_DIR / f"{protocol}_{timestamp}.log"

    topo = SingleSwitchTopo(k=2)

    net = Mininet(
        topo=topo,
        controller=None,
        switch=OVSKernelSwitch,
        autoSetMacs=True
    )

    controller = RemoteController(
        "c0",
        ip="127.0.0.1",
        port=6633
    )

    net.addController(controller)

    try:
        net.start()

        h1 = net.get("h1")
        h2 = net.get("h2")

        iperf_port = 5201  # iPerf3 default; Member 3 Scapy IoT uses 5202

        h2.cmd(f"iperf3 -s -D -p {iperf_port}")

        if protocol == "tcp":
            command = (
                f"iperf3 -c {h2.IP()} "
                f"-p {iperf_port} -t {duration}"
            )

        else:
            command = (
                f"iperf3 -c {h2.IP()} "
                f"-p {iperf_port} "
                f"-u -b {bitrate} -t {duration}"
            )

        result = h1.cmd(command)

        output_file.write_text(result, encoding="utf-8")

        print(result)
        print(f"\nExperiment log: {output_file}")

    finally:
        h2.cmd("pkill -f 'iperf3 -s'")
        net.stop()


def main():
    parser = argparse.ArgumentParser(
        description="Run repeatable iPerf3 traffic experiments."
    )

    parser.add_argument(
        "--protocol",
        choices=["tcp", "udp"],
        required=True
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=10
    )

    parser.add_argument(
        "--bitrate",
        default="10M"
    )

    args = parser.parse_args()

    run_experiment(
        args.protocol,
        args.duration,
        args.bitrate
    )


if __name__ == "__main__":
    main()
