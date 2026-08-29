#!/usr/bin/env python3

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

        h2.cmd("iperf3 -s -D")

        if protocol == "tcp":
            command = f"iperf3 -c {h2.IP()} -t {duration}"

        else:
            command = (
                f"iperf3 -c {h2.IP()} "
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
