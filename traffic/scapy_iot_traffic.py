#!/usr/bin/env python3
"""
Member 3 -- Scapy-based bursty IoT traffic generator (Weeks 3 & 4)
==================================================================

Generates ON/OFF "bursty" UDP IoT-style traffic with periodic idle gaps.
This is deliberately different from Member 1's continuous iPerf3 flows:

    iPerf3 (Member 1)     -> continuous TCP/UDP at a fixed bitrate
    Scapy IoT (Member 3)  -> short bursts + idle gaps (duty cycled)

A scripted traffic spike ("anomaly") is injected inside a configurable
timestamp window.  The exact wall-clock start/end of the anomaly is
appended to:

    docs/week3/anomaly-event-timestamps.md

which scripts/process_telemetry.py reads to label the raw telemetry
dataset with the binary `is_anomalous` column.

Port / IP allocation -- no conflict with Member 1's iPerf3 experiment:

    iPerf3 (Member 1): h1 (10.0.0.1) -> h2 (10.0.0.2), L4 port 5201
    Scapy  (Member 3): h3 (10.0.0.3) -> h4 (10.0.0.4), L4 port 5202

Example run (inside the shared Mininet testbed, 4-host fat-tree edge):

    # Receiver, started on h4:
    python3 traffic/scapy_iot_traffic.py --mode server \
        --port 5202 --total-duration 60

    # Sender, started on h3 (concurrently):
    python3 traffic/scapy_iot_traffic.py --mode client \
        --server-ip 10.0.0.4 --port 5202 --total-duration 60 \
        --burst-duration 2 --idle-duration 3 --burst-rate 500 \
        --payload-size 128 --anomaly-start 20 \
        --anomaly-duration 10 --anomaly-rate 4000
"""

import argparse
import socket
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = PROJECT_ROOT / "results" / "week3"
ANOMALY_EVENT_FILE = PROJECT_ROOT / "docs" / "week3" / "anomaly-event-timestamps.md"

BROADCAST_MAC = "ff:ff:ff:ff:ff:ff"
EVENT_SECTION_MARKER = "## Recorded Events"


# ---------------------------------------------------------------------------
# Anomaly event log helpers
# ---------------------------------------------------------------------------
def ensure_event_file():
    """Create the anomaly-event log with a header + marker if missing."""
    ANOMALY_EVENT_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not ANOMALY_EVENT_FILE.exists():
        ANOMALY_EVENT_FILE.write_text(
            "# Anomaly Event Timestamps\n\n"
            "Machine-readable anomaly windows, appended by "
            "traffic/scapy_iot_traffic.py and consumed by "
            "scripts/process_telemetry.py.\n\n"
            + EVENT_SECTION_MARKER
            + "\n\n"
            "<!-- Events appended below by traffic/scapy_iot_traffic.py -->\n\n",
            encoding="utf-8",
        )


def append_anomaly_event(event_id, anomaly_start, anomaly_end):
    """Append one anomaly window as three `key: value` lines."""
    ensure_event_file()
    with ANOMALY_EVENT_FILE.open("a", encoding="utf-8") as fh:
        fh.write(
            "- event_id: {}\n"
            "- anomaly_start: {}\n"
            "- anomaly_end: {}\n\n".format(
                event_id,
                anomaly_start.isoformat(),
                anomaly_end.isoformat(),
            )
        )
    print("Anomaly event logged -> {}".format(ANOMALY_EVENT_FILE))
    print("  event_id:       {}".format(event_id))
    print("  anomaly_start:  {}".format(anomaly_start.isoformat()))
    print("  anomaly_end:    {}".format(anomaly_end.isoformat()))


def build_run_id():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# ---------------------------------------------------------------------------
# Receiver (server) mode -- plain UDP socket, no Scapy required
# ---------------------------------------------------------------------------
def run_server(args):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    run_id = build_run_id()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((args.bind_ip, args.port))
    sock.settimeout(1.0)

    print("Scapy IoT receiver listening on udp {}:{}".format(args.bind_ip, args.port))

    start_mono = time.monotonic()
    received = 0
    rx_bytes = 0
    first_packet_iso = None

    try:
        while True:
            elapsed = time.monotonic() - start_mono
            if args.total_duration > 0 and elapsed >= args.total_duration:
                break
            try:
                data, _ = sock.recvfrom(65535)
            except socket.timeout:
                continue
            if first_packet_iso is None:
                first_packet_iso = datetime.now(timezone.utc).isoformat()
            received += 1
            rx_bytes += len(data)
    except KeyboardInterrupt:
        print("\nReceiver interrupted.")
    finally:
        sock.close()

    summary = (
        "Scapy IoT receiver summary\n"
        "  run_id: {}\n"
        "  listen: udp {}:{}\n"
        "  total_duration_s: {}\n"
        "  packets_received: {}\n"
        "  bytes_received: {}\n"
        "  first_packet_ts: {}\n"
    ).format(
        run_id,
        args.bind_ip,
        args.port,
        args.total_duration,
        received,
        rx_bytes,
        first_packet_iso,
    )
    print(summary)

    log_file = RESULTS_DIR / "scapy_iot_server_{}.log".format(run_id)
    log_file.write_text(summary, encoding="utf-8")
    print("Server log: {}".format(log_file))


# ---------------------------------------------------------------------------
# Sender (client) mode -- Scapy-crafted bursty UDP frames into the switch
# ---------------------------------------------------------------------------
def _in_burst_window(elapsed, args):
    """Duty-cycle test: True while a burst is active, False during the idle gap."""
    cycle = args.burst_duration + args.idle_duration
    if cycle <= 0:
        return True
    position = elapsed % cycle
    return position < args.burst_duration


def run_client(args):
    # Scapy is imported lazily only for the sender so the plain-UDP
    # receiver (`--mode server`) works even without Scapy installed.
    from scapy.all import IP, UDP, Ether, Raw, conf, get_if_hwaddr, getmacbyip

    if args.server_ip is None:
        raise SystemExit("error: --mode client requires --server-ip")

    if args.burst_duration <= 0:
        raise SystemExit("error: --burst-duration must be > 0 (bursty traffic)")

    conf.verb = 0
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    run_id = build_run_id()

    # Resolve outbound interface, source IP and peer MACs.
    iface, gateway_ip, route_src_ip = conf.route.route(args.server_ip)
    src_ip = args.source_ip or route_src_ip or "0.0.0.0"
    src_mac = get_if_hwaddr(iface)

    dst_mac = None
    for _ in range(3):
        dst_mac = getmacbyip(args.server_ip)
        if dst_mac:
            break
        time.sleep(0.5)
    dst_mac = dst_mac or BROADCAST_MAC

    print("Scapy IoT client")
    print("  iface        : {}".format(iface))
    print("  src          : {} ({})".format(src_ip, src_mac))
    print("  dst          : {} ({})".format(args.server_ip, dst_mac))
    print("  udp          : {} -> {}".format(args.source_port, args.port))
    print("  burst        : {}s on / {}s idle @ {} pps".format(
        args.burst_duration,
        args.idle_duration,
        args.burst_rate,
    ))
    print("  anomaly      : t=[{}, {}) @ {} pps".format(
        args.anomaly_start,
        args.anomaly_start + args.anomaly_duration,
        args.anomaly_rate,
    ))

    payload = b"\x42" * args.payload_size  # 'B' bytes, IoT-style fixed payload
    sender = conf.L2socket(iface=iface)

    start_mono = time.monotonic()
    start_wall = datetime.now(timezone.utc)

    # Deterministic wall-clock bounds for the anomaly window.
    anomaly_start_wall = start_wall + timedelta(seconds=args.anomaly_start)
    anomaly_end_wall = start_wall + timedelta(
        seconds=args.anomaly_start + args.anomaly_duration
    )
    experiment_end_wall = start_wall + timedelta(seconds=args.total_duration)
    if anomaly_end_wall > experiment_end_wall:
        anomaly_end_wall = experiment_end_wall

    event_id = "anomaly-" + run_id
    anomaly_entered = False
    sent_total = 0
    sent_burst = 0
    sent_anomaly = 0
    next_send_ts = start_mono

    try:
        while True:
            now_mono = time.monotonic()
            elapsed = now_mono - start_mono
            if elapsed >= args.total_duration:
                break

            in_anomaly = (
                args.anomaly_duration > 0
                and args.anomaly_start <= elapsed
                and elapsed < args.anomaly_start + args.anomaly_duration
            )

            if in_anomaly and not anomaly_entered:
                anomaly_entered = True
                print("Anomaly window entered at t=%.3fs" % elapsed)

            if in_anomaly:
                rate = args.anomaly_rate
            elif _in_burst_window(elapsed, args):
                rate = args.burst_rate
            else:
                # Idle gap -- do not send anything.
                time.sleep(min(0.05, args.idle_duration))
                continue

            if now_mono >= next_send_ts:
                packet = (
                    Ether(src=src_mac, dst=dst_mac)
                    / IP(src=src_ip, dst=args.server_ip)
                    / UDP(sport=args.source_port, dport=args.port)
                    / Raw(load=payload)
                )
                sender.send(packet)
                sent_total += 1
                if in_anomaly:
                    sent_anomaly += 1
                else:
                    sent_burst += 1
                next_send_ts = now_mono + (1.0 / rate)
            else:
                time.sleep(0.0005)
    except KeyboardInterrupt:
        print("\nSender interrupted.")
    finally:
        sender.close()

        # Log the anomaly window only if the experiment actually entered it
        # AND the window is non-degenerate.
        event_logged = False
        if anomaly_entered and anomaly_end_wall > anomaly_start_wall:
            append_anomaly_event(event_id, anomaly_start_wall, anomaly_end_wall)
            event_logged = True

        summary = (
            "Scapy IoT client summary\n"
            "  run_id: {}\n"
            "  src: {} -> dst: {}\n"
            "  duration_s: {}\n"
            "  burst_rate_pps: {}\n"
            "  idle_gap_s: {}\n"
            "  anomaly_window: t=[{}, {})\n"
            "  anomaly_rate_pps: {}\n"
            "  packets_sent_total: {}\n"
            "  packets_sent_burst: {}\n"
            "  packets_sent_anomaly: {}\n"
            "  anomaly_event_logged: {}\n"
        ).format(
            run_id,
            src_ip,
            args.server_ip,
            args.total_duration,
            args.burst_rate,
            args.idle_duration,
            args.anomaly_start,
            args.anomaly_start + args.anomaly_duration,
            args.anomaly_rate,
            sent_total,
            sent_burst,
            sent_anomaly,
            event_logged,
        )
        print(summary)

        log_file = RESULTS_DIR / "scapy_iot_client_{}.log".format(run_id)
        log_file.write_text(summary, encoding="utf-8")
        print("Client log: {}".format(log_file))


# ---------------------------------------------------------------------------
def build_parser():
    parser = argparse.ArgumentParser(
        description="Scapy-based bursty IoT UDP traffic generator (Member 3)."
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    server = subparsers.add_parser("server", help="UDP receiver for the IoT bursts")
    server.add_argument("--bind-ip", default="0.0.0.0")
    server.add_argument(
        "--port",
        type=int,
        default=5202,
        help="UDP port (5202, distinct from iPerf3's 5201)",
    )
    server.add_argument(
        "--total-duration",
        type=float,
        default=0.0,
        help="seconds to listen (0 = until interrupted)",
    )

    client = subparsers.add_parser(
        "client",
        help="Scapy sender: bursty UDP with idle gaps + anomaly spike",
    )
    client.add_argument("--server-ip", required=True, help="destination IP (h4)")
    client.add_argument("--port", type=int, default=5202)
    client.add_argument("--source-ip", default=None)
    client.add_argument("--source-port", type=int, default=5202)
    client.add_argument("--total-duration", type=float, default=60.0)
    client.add_argument("--burst-duration", type=float, default=2.0)
    client.add_argument("--idle-duration", type=float, default=3.0)
    client.add_argument(
        "--burst-rate",
        type=float,
        default=500.0,
        help="packets/s inside bursts",
    )
    client.add_argument("--payload-size", type=int, default=128)
    client.add_argument(
        "--anomaly-start",
        type=float,
        default=20.0,
        help="seconds into the run when the spike begins",
    )
    client.add_argument(
        "--anomaly-duration",
        type=float,
        default=10.0,
        help="seconds (0 = disabled)",
    )
    client.add_argument(
        "--anomaly-rate",
        type=float,
        default=4000.0,
        help="packets/s during the anomaly spike",
    )

    return parser


def main():
    args = build_parser().parse_args()

    if args.mode == "server":
        run_server(args)
    else:
        run_client(args)


if __name__ == "__main__":
    main()