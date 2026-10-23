#!/usr/bin/env python3
"""
Verification Script for Core Forwarding and Bidirectional Connectivity.
Tests:
1. Static ARP and bidirectional ping reachability (h1<->h3, h2<->h4)
2. Group tables on s1, s2, and transit forwarding on s3
3. iPerf3 UDP transfer (h1 -> h3:5202) and server byte reception
4. iPerf3 TCP transfer (h2 -> h4:5201) and server byte reception
"""

import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
for p in ("/usr/lib/python3/dist-packages", "/usr/local/lib/python3/dist-packages"):
    if p not in sys.path and Path(p).exists():
        sys.path.append(p)

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.link import TCLink
from mininet.clean import cleanup

# Load FatTreeEdgeTopo dynamically from mininet/topo.py
topo_path = PROJECT_ROOT / "mininet" / "topo.py"
spec = importlib.util.spec_from_file_location("local_topo_mod", topo_path)
topo_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(topo_mod)
FatTreeEdgeTopo = topo_mod.FatTreeEdgeTopo


def run_checks():
    print("==================================================================")
    print(" Running Core Forwarding & Application Delivery Verification")
    print("==================================================================")

    # 1. Cleanup
    cleanup()

    # 2. Build and start Mininet
    topo = FatTreeEdgeTopo()
    net = Mininet(
        topo=topo,
        controller=None,
        switch=OVSKernelSwitch,
        link=TCLink,
        autoSetMacs=False
    )
    c0 = net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6633)
    net.start()
    print("[*] Mininet network started. Waiting 3s for controller connection...")
    time.sleep(3.0)

    # 3. Static ARP
    print("[*] Installing static ARP entries on all hosts...")
    net.staticArp()

    # 4. Configure Queues
    print("[*] Configuring Linux-HTB QoS queues on edge switches...")
    subprocess.run(["bash", "mininet/configure_queues.sh"], check=False)

    report = {}

    try:
        # 5. Clean stale processes
        for h in ("h1", "h2", "h3", "h4"):
            net.get(h).cmd("killall -9 iperf3 ping 2>/dev/null")

        # 6. Bidirectional Ping Checks
        print("\n--- [Check 1] Bidirectional ICMP Ping Tests ---")
        pings = [
            ("h1", "h3", "10.0.0.3"),
            ("h3", "h1", "10.0.0.1"),
            ("h2", "h4", "10.0.0.4"),
            ("h4", "h2", "10.0.0.2"),
        ]
        ping_results = {}
        for src, dst, dst_ip in pings:
            out = net.get(src).cmd(f"ping -c 5 -i 0.2 -W 2 {dst_ip}")
            print(f"[*] Ping {src} -> {dst} ({dst_ip}):")
            summary_line = [l for l in out.splitlines() if "packet loss" in l or "rtt" in l]
            for sl in summary_line:
                print(f"    {sl}")
            ping_results[f"{src}->{dst}"] = summary_line
        report["ping_tests"] = ping_results

        # 7. Dump Group and Flow Tables
        print("\n--- [Check 2] OpenFlow Group & Flow Table State ---")
        s1_groups = subprocess.check_output(["ovs-ofctl", "-O", "OpenFlow13", "dump-groups", "s1"]).decode().strip()
        s2_groups = subprocess.check_output(["ovs-ofctl", "-O", "OpenFlow13", "dump-groups", "s2"]).decode().strip()
        s3_flows = subprocess.check_output(["ovs-ofctl", "-O", "OpenFlow13", "dump-flows", "s3"]).decode().strip()
        print(f"[*] Switch s1 Groups:\n{s1_groups}")
        print(f"[*] Switch s2 Groups:\n{s2_groups}")
        print(f"[*] Switch s3 Flow Table:\n{s3_flows}")
        report["s1_groups"] = s1_groups
        report["s2_groups"] = s2_groups
        report["s3_flows"] = s3_flows

        # 8. Start iperf3 servers with log files
        print("\n--- [Check 3] Starting iperf3 Servers on h3 and h4 ---")
        srv_h3_log = "/tmp/iperf3_srv_h3.log"
        srv_h4_log = "/tmp/iperf3_srv_h4.log"
        subprocess.run(["rm", "-f", srv_h3_log, srv_h4_log])
        
        p_srv3 = net.get("h3").popen(f"iperf3 -s -p 5202 --logfile {srv_h3_log}", shell=True)
        p_srv4 = net.get("h4").popen(f"iperf3 -s -p 5201 --logfile {srv_h4_log}", shell=True)
        time.sleep(1.5)

        h3_stat = net.get("h3").cmd("ss -lntu | grep 5202").strip()
        h4_stat = net.get("h4").cmd("ss -lntu | grep 5201").strip()
        print(f"[*] h3 server status (port 5202): {h3_stat}")
        print(f"[*] h4 server status (port 5201): {h4_stat}")

        # 9. Test iperf3 Priority UDP Flow (h1 -> h3:5202)
        print("\n--- [Check 4] Testing Priority UDP Flow: h1 -> h3:5202 ---")
        udp_client_out = net.get("h1").cmd("iperf3 -c 10.0.0.3 -p 5202 -u -b 3M -t 4 -J --dscp 46")
        try:
            udp_data = json.loads(udp_client_out)
            udp_sent = udp_data.get("end", {}).get("sum", {}).get("bytes", 0)
            udp_bps = udp_data.get("end", {}).get("sum", {}).get("bits_per_second", 0)
            udp_lost = udp_data.get("end", {}).get("sum", {}).get("lost_percent", 0)
            print(f"[+] UDP Client Success: Bytes={udp_sent:,} | Throughput={udp_bps/1e6:.2f} Mbps | Loss={udp_lost:.1f}%")
            report["udp_client"] = {"bytes": udp_sent, "bps": udp_bps, "loss_pct": udp_lost}
        except Exception as ex:
            print(f"[!] UDP Client JSON Error: {ex}\nRaw Output: {udp_client_out[:300]}")
            report["udp_client"] = {"error": str(ex), "raw": udp_client_out[:300]}

        # Check server-side reception
        time.sleep(1.0)
        srv3_content = Path(srv_h3_log).read_text(encoding="utf-8", errors="replace") if Path(srv_h3_log).exists() else ""
        print(f"[*] h3 Server Log Snippet:\n{srv3_content[-500:] if len(srv3_content) > 500 else srv3_content}")
        report["h3_server_log"] = srv3_content

        # 10. Test iperf3 Bulk TCP Flow (h2 -> h4:5201)
        print("\n--- [Check 5] Testing Bulk TCP Flow: h2 -> h4:5201 ---")
        tcp_client_out = net.get("h2").cmd("iperf3 -c 10.0.0.4 -p 5201 -b 5M -t 4 -J")
        try:
            tcp_data = json.loads(tcp_client_out)
            tcp_sent = tcp_data.get("end", {}).get("sum_sent", {}).get("bytes", 0)
            tcp_bps = tcp_data.get("end", {}).get("sum_sent", {}).get("bits_per_second", 0)
            print(f"[+] TCP Client Success: Bytes={tcp_sent:,} | Throughput={tcp_bps/1e6:.2f} Mbps")
            report["tcp_client"] = {"bytes": tcp_sent, "bps": tcp_bps}
        except Exception as ex:
            print(f"[!] TCP Client JSON Error: {ex}\nRaw Output: {tcp_client_out[:300]}")
            report["tcp_client"] = {"error": str(ex), "raw": tcp_client_out[:300]}

        # Check server-side reception
        time.sleep(1.0)
        srv4_content = Path(srv_h4_log).read_text(encoding="utf-8", errors="replace") if Path(srv_h4_log).exists() else ""
        print(f"[*] h4 Server Log Snippet:\n{srv4_content[-500:] if len(srv4_content) > 500 else srv4_content}")
        report["h4_server_log"] = srv4_content

        # Dump s1 group stats to see bucket packet distribution
        s1_gstats = subprocess.check_output(["ovs-ofctl", "-O", "OpenFlow13", "dump-group-stats", "s1"]).decode().strip()
        print(f"\n[*] Switch s1 Group Stats after traffic:\n{s1_gstats}")
        report["s1_group_stats"] = s1_gstats

    finally:
        print("\n[*] Tearing down test network...")
        for h in ("h1", "h2", "h3", "h4"):
            try:
                net.get(h).cmd("killall -9 iperf3 ping 2>/dev/null")
            except Exception:
                pass
        net.stop()
        cleanup()
        print("[+] Verification complete.")

    # Save summary report
    out_json = PROJECT_ROOT / "data" / "results" / "connectivity_verification_report.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"[+] Report written to {out_json}")


if __name__ == "__main__":
    run_checks()
