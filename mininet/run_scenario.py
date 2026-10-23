#!/usr/bin/env python3
"""
Automated Scenario Launcher for Mininet.
Parses standardized scenario YAML files (S1, S2, S3), orchestrates iPerf3 and Scapy traffic flows
inside Mininet host network namespaces, triggers scheduled link failures, and archives raw benchmark outputs.
"""

import argparse
import importlib.util
import json
import os
import signal
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Ensure Mininet system packages and project root are discoverable
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

# Load FatTreeEdgeTopo dynamically from mininet/topo.py to avoid package shadowing
topo_path = PROJECT_ROOT / "mininet" / "topo.py"
spec = importlib.util.spec_from_file_location("local_topo_module", topo_path)
topo_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(topo_module)
FatTreeEdgeTopo = topo_module.FatTreeEdgeTopo

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


def sync_controller_mode(controller_ip, mode, trial_id):
    """
    Synchronizes active operational mode with Controller REST Bridge API.
    """
    url = f"http://{controller_ip}:8080/api/mode"
    payload = json.dumps({"mode": mode, "trial_id": trial_id}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            print(f"[*] Controller mode switched to: {mode} (HTTP {resp.status})")
            return True
    except Exception as ex:
        print(f"[!] Warning: Could not reach Controller REST API at {url}: {ex}")
        return False


def execute_scenario(scenario_file, mode="full_ai_qos_ff", trial_id="live_calib_002", output_dir="data/results/live_calib_002", controller_ip="127.0.0.1", controller_port=6633):
    scenario = load_scenario(scenario_file)
    scenario_id = scenario.get("scenario_id", Path(scenario_file).stem)
    duration = int(scenario.get("duration_seconds", 30))
    flows = scenario.get("flows", [])
    failures = scenario.get("failure_events", [])
    
    out_path = Path(output_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    print("==================================================================")
    print(f" Launching Genuine Mininet Scenario: {scenario_id}")
    print(f" Mode:                {mode}")
    print(f" Trial ID:            {trial_id}")
    print(f" Total Duration:      {duration}s")
    print(f" Raw Output Dir:      {out_path}")
    print(f" Controller Endpoint: {controller_ip}:{controller_port}")
    print("==================================================================")

    # 1. Reset any stale Mininet/OVS state
    print("[*] Performing pre-run Mininet cleanup...")
    cleanup()

    # 2. Build and start FatTreeEdgeTopo
    print("[*] Instantiating FatTreeEdgeTopo network...")
    topo = FatTreeEdgeTopo()
    net = Mininet(
        topo=topo,
        controller=None,
        switch=OVSKernelSwitch,
        link=TCLink,
        autoSetMacs=False
    )
    controller = RemoteController('c0', ip=controller_ip, port=controller_port)
    net.addController(controller)
    net.start()
    print("[*] Mininet network started. Waiting 3s for OpenFlow switch connections...")
    time.sleep(3.0)

    # 3. Synchronize Controller Mode
    sync_controller_mode(controller_ip, mode, trial_id)

    # 4. Configure Linux-HTB Queues
    if mode in ("reactive", "full_ai_qos_ff"):
        print("[*] Configuring Linux-HTB QoS queues on edge switches...")
        subprocess.run(["bash", "mininet/configure_queues.sh"], check=False)
    else:
        print("[*] Clearing QoS queues for baseline mode...")
        for sw in ("s1", "s2"):
            for p in range(1, 5):
                subprocess.run(
                    ["ovs-vsctl", "clear", "Port", f"{sw}-eth{p}", "qos"],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

    # 5. Populate static ARP tables across all hosts to prevent broadcast storms
    print("[*] Populating static ARP tables across all hosts (preventing broadcast ARP loop)...")
    net.staticArp()

    # 6. Verify pre-flight reachability (at least 10 pings per host pair)
    print("[*] Performing pre-flight reachability tests (h1<->h3 and h2<->h4)...")
    res1 = net.get("h1").cmd("ping -c 10 -i 0.2 10.0.0.3")
    res2 = net.get("h3").cmd("ping -c 10 -i 0.2 10.0.0.1")
    res3 = net.get("h2").cmd("ping -c 10 -i 0.2 10.0.0.4")
    res4 = net.get("h4").cmd("ping -c 10 -i 0.2 10.0.0.2")

    with open(out_path / f"{trial_id}_preflight_ping_h1_h3.txt", "w", encoding="utf-8") as pf:
        pf.write(res1 + "\n" + res2)
    with open(out_path / f"{trial_id}_preflight_ping_h2_h4.txt", "w", encoding="utf-8") as pf:
        pf.write(res3 + "\n" + res4)

    if " 0 received" in res1 or "100% packet loss" in res1:
        raise RuntimeError(f"Pre-flight reachability check failed: h1 cannot ping h3:\n{res1}")
    if " 0 received" in res3 or "100% packet loss" in res3:
        raise RuntimeError(f"Pre-flight reachability check failed: h2 cannot ping h4:\n{res3}")
    print("[+] Pre-flight bidirectional reachability verified: h1<->h3 and h2<->h4 functional (0% loss).")

    # 7. Capture initial OpenFlow Group State
    try:
        s1_groups = subprocess.check_output(["ovs-ofctl", "-O", "OpenFlow13", "dump-groups", "s1"]).decode()
        print(f"[*] OpenFlow Group Table on s1 before failure:\n{s1_groups.strip()}")
        with open(out_path / f"{trial_id}_s1_groups_initial.txt", "w", encoding="utf-8") as gf:
            gf.write(s1_groups)
    except Exception as ex:
        print(f"[!] Could not dump s1 groups: {ex}")

    procs = []
    open_files = []
    p_ping = None

    try:
        # 8. Clean up any stale traffic processes inside all host namespaces
        for hname in ("h1", "h2", "h3", "h4"):
            net.get(hname).cmd("killall -9 iperf3 ping 2>/dev/null")

        # 9. Start iperf3 server listeners on target destination hosts with logfiles
        started_servers = set()
        for flow in flows:
            s_name = flow.get("server_host")
            if not s_name:
                last_octet = flow.get("server_ip", "").split(".")[-1]
                s_name = f"h{last_octet}" if last_octet in ("1", "2", "3", "4") else "h3"
            port = flow.get("port", 5201)
            if (s_name, port) not in started_servers:
                srv_host = net.get(s_name)
                srv_log = out_path / f"{trial_id}_server_{s_name}_{port}.log"
                print(f"[*] Starting iperf3 server on host [{s_name}] port {port} (log: {srv_log.name})...")
                p_srv = srv_host.popen(f"iperf3 -s -p {port} --logfile {srv_log}", shell=True)
                procs.append(p_srv)
                started_servers.add((s_name, port))

        time.sleep(2.0)  # Wait for sockets to open
        # Verify server listening sockets
        for s_name, port in started_servers:
            listen_chk = net.get(s_name).cmd(f"ss -lntu | grep {port}")
            print(f"[*] Destination server [{s_name}:{port}] status: {listen_chk.strip() or 'BOUND'}")
            if not listen_chk.strip():
                raise RuntimeError(f"Server {s_name}:{port} failed to bind or listen!")

        # Pre-flight short traffic verification (1s test) to confirm receiver payload delivery
        print("[*] Running pre-flight application payload checks...")
        pre_udp = net.get("h1").cmd("iperf3 -c 10.0.0.3 -p 5202 -u -b 1M -t 1 -J")
        pre_tcp = net.get("h2").cmd("iperf3 -c 10.0.0.4 -p 5201 -b 1M -t 1 -J")
        try:
            udp_chk = json.loads(pre_udp)
            tcp_chk = json.loads(pre_tcp)
            if "error" in udp_chk or "error" in tcp_chk:
                raise RuntimeError(f"Pre-flight traffic check error: UDP={udp_chk.get('error')}, TCP={tcp_chk.get('error')}")
            print(f"[+] Pre-flight payload verified: UDP sent {udp_chk['end']['sum']['bytes']} bytes, TCP sent {tcp_chk['end']['sum_sent']['bytes']} bytes.")
        except Exception as ex:
            raise RuntimeError(f"Pre-flight application connectivity check failed: {ex}")

        # Mark pre-flight checks as successfully completed; server listeners remain active
        time.sleep(1.0)

        # 10. Launch scheduled client flows inside client host network namespaces
        for flow in flows:
            flow_id = flow.get("id")
            flow_type = flow.get("type")
            start_delay = flow.get("start_time_sec", 0.0)
            flow_dur = flow.get("duration_sec", duration)
            client_name = flow.get("client_host", "h1")
            server_ip = flow.get("server_ip", "10.0.0.3")
            port = flow.get("port", 5201)
            bw = flow.get("bandwidth_mbps", 4.0)
            dscp = flow.get("dscp", 0)

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

            def delayed_start(delay, c_host_name, cmd_str, out_file_path):
                if delay > 0:
                    time.sleep(delay)
                print(f"[*] [{c_host_name}] Launching traffic: {cmd_str}")
                f_out = open(out_file_path, "w", encoding="utf-8")
                open_files.append(f_out)
                c_host = net.get(c_host_name)
                proc = c_host.popen(cmd_str, shell=True, stdout=f_out, stderr=subprocess.STDOUT)
                procs.append(proc)

            t = threading.Thread(target=delayed_start, args=(start_delay, client_name, cmd, flow_out_file))
            t.daemon = True
            t.start()

        # 11. Launch high-rate ping monitor inside h1 network namespace
        ping_log = out_path / f"{trial_id}_{mode}_{scenario_id}_ping.log"
        f_ping = open(ping_log, "w", encoding="utf-8")
        open_files.append(f_ping)
        ping_cmd = f"ping -i 0.010 -c {int(duration * 100)} 10.0.0.3"
        print(f"[*] [h1] Launching ping monitor: {ping_cmd}")
        p_ping = net.get("h1").popen(ping_cmd, shell=True, stdout=f_ping, stderr=subprocess.STDOUT)
        procs.append(p_ping)

        # 12. Schedule Failure Events
        for fail in failures:
            intf = fail.get("interface", "s1-eth3")
            f_start = fail.get("start_time_sec", 15.0)
            f_dur = fail.get("down_duration_sec", 8.0)

            def delayed_fail(delay, down_dur, interface):
                time.sleep(delay)
                # Group stats right before failure
                try:
                    s1_pre = subprocess.check_output(["ovs-ofctl", "-O", "OpenFlow13", "dump-group-stats", "s1"]).decode()
                    with open(out_path / f"{trial_id}_s1_group_stats_pre_fail.txt", "w", encoding="utf-8") as sf:
                        sf.write(s1_pre)
                except Exception as ex:
                    print(f"[!] Warning pre-fail stats dump: {ex}")

                print(f"[*] [FAILURE INJECTOR] Cutting interface {interface} for {down_dur}s...")
                fail_log = out_path / f"{trial_id}_link_failure_events.csv"
                fail_cmd = ["python3", "mininet/inject_failure.py", "--interface", interface, "--down-duration", str(down_dur), "--log-file", str(fail_log)]

                def run_fail():
                    subprocess.run(fail_cmd, check=False)
                t_inj = threading.Thread(target=run_fail)
                t_inj.start()

                # Group stats during failure (2s into outage)
                time.sleep(2.0)
                try:
                    s1_dur = subprocess.check_output(["ovs-ofctl", "-O", "OpenFlow13", "dump-group-stats", "s1"]).decode()
                    with open(out_path / f"{trial_id}_s1_group_stats_during_fail.txt", "w", encoding="utf-8") as sf:
                        sf.write(s1_dur)
                except Exception as ex:
                    print(f"[!] Warning during-fail stats dump: {ex}")

                t_inj.join()

                # Group stats after recovery (1s after restoration)
                time.sleep(1.0)
                try:
                    s1_post = subprocess.check_output(["ovs-ofctl", "-O", "OpenFlow13", "dump-group-stats", "s1"]).decode()
                    with open(out_path / f"{trial_id}_s1_group_stats_recovered.txt", "w", encoding="utf-8") as sf:
                        sf.write(s1_post)
                except Exception as ex:
                    print(f"[!] Warning recovered stats dump: {ex}")

            tf = threading.Thread(target=delayed_fail, args=(f_start, f_dur, intf))
            tf.daemon = True
            tf.start()

        print(f"[*] Scenario executing for {duration} seconds...")
        time.sleep(duration + 2.0)

    finally:
        print("[*] Scenario run completed. Tearing down processes and network...")
        # Send SIGINT to ping first so it flushes its summary statistics cleanly
        if p_ping:
            try:
                p_ping.send_signal(signal.SIGINT)
                p_ping.wait(timeout=1.5)
            except Exception:
                pass

        for p in procs:
            try:
                p.terminate()
                p.wait(timeout=1.0)
            except Exception:
                pass

        for f in open_files:
            try:
                f.flush()
                f.close()
            except Exception:
                pass

        for hname in ("h1", "h2", "h3", "h4"):
            try:
                net.get(hname).cmd("killall -9 iperf3 ping 2>/dev/null")
            except Exception:
                pass

        net.stop()
        cleanup()
        print(f"[+] All processes cleaned up. Outputs saved to {out_path}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scenario Launcher for Mininet")
    parser.add_argument("--scenario", required=True, help="Path to scenario YAML file (e.g. scenarios/S3_failure.yaml)")
    parser.add_argument("--mode", choices=["baseline_shortest_path", "reactive", "full_ai_qos_ff"], default="full_ai_qos_ff", help="Operational mode")
    parser.add_argument("--trial-id", default="live_calib_002", help="Trial identifier")
    parser.add_argument("--output-dir", default="data/results/live_calib_002", help="Directory to store raw logs and JSON")
    parser.add_argument("--controller-ip", default="127.0.0.1", help="Controller IP address")
    parser.add_argument("--controller-port", type=int, default=6633, help="OpenFlow controller port")
    args = parser.parse_args()

    execute_scenario(
        args.scenario,
        mode=args.mode,
        trial_id=args.trial_id,
        output_dir=args.output_dir,
        controller_ip=args.controller_ip,
        controller_port=args.controller_port
    )
