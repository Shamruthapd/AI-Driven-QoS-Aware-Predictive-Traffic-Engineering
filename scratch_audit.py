#!/usr/bin/env python3
import json
import re
import csv
from pathlib import Path
from datetime import datetime, timezone

BASE = Path("/mnt/c/Users/zenit/AI-Driven-QoS-Aware-Predictive-Traffic-Engineering/data/results")

trials = {
    "baseline": {
        "dir": BASE / "live_s3_baseline",
        "prefix": "live_s3_baseline",
        "mode": "baseline_shortest_path"
    },
    "reactive": {
        "dir": BASE / "live_s3_reactive",
        "prefix": "live_s3_reactive",
        "mode": "reactive"
    },
    "calib003": {
        "dir": BASE / "live_calib_003",
        "prefix": "live_calib_003",
        "mode": "full_ai_qos_ff"
    }
}

print("================================================================================")
print("SECTION 1: FAILURE TIMESTAMPS & PORT STATUS EVENTS")
print("================================================================================")

for name, t in trials.items():
    d = t["dir"]
    p = t["prefix"]
    print(f"\n--- Trial: {name} ({p}) ---")
    fail_csv = d / f"{p}_link_failure_events.csv"
    if fail_csv.exists():
        with open(fail_csv) as f:
            for row in csv.DictReader(f):
                print(f"  Fail CSV: {row['timestamp_iso']} | {row['event_type']} | {row['interface']} | epoch={row['timestamp_epoch']} | {row['details']}")
    else:
        print("  Fail CSV: NOT FOUND")

print("\n--- Port Status Events in port_status_events.csv ---")
ps_csv = BASE / "port_status_events.csv"
if ps_csv.exists():
    with open(ps_csv) as f:
        rows = list(csv.DictReader(f))
        for r in rows:
            # show events from 16:43 (calib003), 17:16 (baseline), 17:23 (reactive)
            ts = r["timestamp_iso"]
            if any(k in ts for k in ("16:43:", "17:16:", "17:23:")):
                print(f"  {r['timestamp_iso']} | DPID={r['dpid']} | Port={r['port_no']} | Reason={r['reason']} | State={r['link_state']}")

print("\n================================================================================")
print("SECTION 2: OPENFLOW GROUP STATISTICS DELTAS")
print("================================================================================")

def parse_group_stats(filepath):
    if not filepath.exists():
        return None
    text = filepath.read_text(encoding="utf-8")
    groups = {}
    for line in text.splitlines():
        line = line.strip()
        if "group_id=" in line:
            m_gid = re.search(r'group_id=(\d+)', line)
            m_dur = re.search(r'duration=([\d\.]+)s', line)
            m_ref = re.search(r'ref_count=(\d+)', line)
            m_pkts = re.search(r'packet_count=(\d+)', line)
            m_bytes = re.search(r'byte_count=(\d+)', line)
            m_b0 = re.search(r'bucket0:packet_count=(\d+),byte_count=(\d+)', line)
            m_b1 = re.search(r'bucket1:packet_count=(\d+),byte_count=(\d+)', line)
            if m_gid:
                gid = int(m_gid.group(1))
                groups[gid] = {
                    "duration": float(m_dur.group(1)) if m_dur else None,
                    "ref_count": int(m_ref.group(1)) if m_ref else None,
                    "packet_count": int(m_pkts.group(1)) if m_pkts else 0,
                    "byte_count": int(m_bytes.group(1)) if m_bytes else 0,
                    "b0_pkts": int(m_b0.group(1)) if m_b0 else 0,
                    "b0_bytes": int(m_b0.group(2)) if m_b0 else 0,
                    "b1_pkts": int(m_b1.group(1)) if m_b1 else 0,
                    "b1_bytes": int(m_b1.group(2)) if m_b1 else 0,
                }
    return groups

for name, t in trials.items():
    d = t["dir"]
    p = t["prefix"]
    print(f"\n--- Group Stats: {name} ---")
    initial_f = d / f"{p}_s1_groups_initial.txt"
    pre_f = d / f"{p}_s1_group_stats_pre_fail.txt"
    dur_f = d / f"{p}_s1_group_stats_during_fail.txt"
    rec_f = d / f"{p}_s1_group_stats_recovered.txt"

    if initial_f.exists():
        print(f"  Initial description:\n    {initial_f.read_text().strip()}")
    pre = parse_group_stats(pre_f)
    dur = parse_group_stats(dur_f)
    rec = parse_group_stats(rec_f)

    for gid in (100, 101):
        print(f"  Group {gid}:")
        for stage, data in [("Pre-Fail", pre), ("During-Fail", dur), ("Recovered", rec)]:
            if data and gid in data:
                g = data[gid]
                print(f"    {stage:12s} (dur={g['duration']}s, ref={g['ref_count']}): Total pkts={g['packet_count']}, bytes={g['byte_count']} | Bucket0(p3) pkts={g['b0_pkts']}, bytes={g['b0_bytes']} | Bucket1(p4) pkts={g['b1_pkts']}, bytes={g['b1_bytes']}")
            else:
                print(f"    {stage:12s}: Not found")
        # calculate deltas
        if pre and rec and gid in pre and gid in rec:
            g_pre = pre[gid]
            g_rec = rec[gid]
            dpkts = g_rec['packet_count'] - g_pre['packet_count']
            dbytes = g_rec['byte_count'] - g_pre['byte_count']
            db0_p = g_rec['b0_pkts'] - g_pre['b0_pkts']
            db0_b = g_rec['b0_bytes'] - g_pre['b0_bytes']
            db1_p = g_rec['b1_pkts'] - g_pre['b1_pkts']
            db1_b = g_rec['b1_bytes'] - g_pre['b1_bytes']
            print(f"    --> Delta (Pre->Rec): Total pkts=+{dpkts}, bytes=+{dbytes} | B0(p3)=+{db0_p} pkts, +{db0_b} bytes | B1(p4)=+{db1_p} pkts, +{db1_b} bytes")
        if pre and dur and gid in pre and gid in dur:
            g_pre = pre[gid]
            g_dur = dur[gid]
            db1_fail = g_dur['b1_pkts'] - g_pre['b1_pkts']
            db1_b_fail = g_dur['b1_bytes'] - g_pre['b1_bytes']
            print(f"    --> Delta during 2s into fail: B1(p4)=+{db1_fail} pkts, +{db1_b_fail} bytes")

print("\n================================================================================")
print("SECTION 3: PING MEASUREMENTS & CADENCE RECONCILIATION")
print("================================================================================")

def analyze_ping(log_path):
    if not log_path.exists():
        return None
    lines = log_path.read_text(encoding="utf-8").splitlines()
    summary_line = ""
    rtts = []
    seqs = []
    first_probe = None
    last_probe = None
    first_line_time = None
    
    for l in lines:
        if "bytes from" in l:
            m_seq = re.search(r'icmp_seq=(\d+)', l)
            m_rtt = re.search(r'time=([\d\.]+)\s*ms', l)
            if m_seq:
                s = int(m_seq.group(1))
                seqs.append(s)
                if first_probe is None:
                    first_probe = s
                last_probe = s
            if m_rtt:
                rtts.append(float(m_rtt.group(1)))
        elif "packets transmitted" in l:
            summary_line = l
        elif "rtt min/avg/max/mdev" in l:
            rtt_line = l

    gaps = []
    for i in range(len(seqs)-1):
        diff = seqs[i+1] - seqs[i]
        if diff > 1:
            gaps.append((seqs[i], seqs[i+1], diff - 1))

    m_tx = re.search(r'(\d+)\s+packets transmitted,\s+(\d+)\s+received,\s+([\d\.]+)%\s+packet loss,\s+time\s+(\d+)ms', summary_line)
    
    return {
        "summary": summary_line,
        "tx": int(m_tx.group(1)) if m_tx else None,
        "rx": int(m_tx.group(2)) if m_tx else len(rtts),
        "loss_pct": float(m_tx.group(3)) if m_tx else None,
        "time_ms": int(m_tx.group(4)) if m_tx else None,
        "rtts": rtts,
        "gaps": gaps,
        "first_probe": first_probe,
        "last_probe": last_probe
    }

for name, t in trials.items():
    d = t["dir"]
    p = t["prefix"]
    m = t["mode"]
    print(f"\n--- Ping Analysis: {name} ---")
    # find ping log
    matches = list(d.glob(f"{p}_*ping.log"))
    if matches:
        plog = matches[0]
        res = analyze_ping(plog)
        print(f"  File: {plog.name}")
        print(f"  Summary: {res['summary']}")
        print(f"  Probes: Tx={res['tx']}, Rx={res['rx']}, Lost={(res['tx']-res['rx']) if res['tx'] else None} ({res['loss_pct']}%)")
        print(f"  Total wall time reported by ping: {res['time_ms']} ms ({res['time_ms']/1000.0:.2f} s)")
        if res['rtts']:
            srtts = sorted(res['rtts'])
            p50 = srtts[len(srtts)//2]
            p95 = srtts[int(len(srtts)*0.95)]
            print(f"  RTTs: Min={min(res['rtts']):.3f} ms, Avg={sum(res['rtts'])/len(res['rtts']):.3f} ms, Median={p50:.3f} ms, P95={p95:.3f} ms, Max={max(res['rtts']):.3f} ms")
        print(f"  Sequence Gaps (prev_seq, next_seq, lost_count): {res['gaps']}")
    else:
        print("  Ping log: NOT FOUND")

print("\n================================================================================")
print("SECTION 4: UDP TRAFFIC (SENDER JSON vs RECEIVER LOG)")
print("================================================================================")

for name, t in trials.items():
    d = t["dir"]
    p = t["prefix"]
    print(f"\n--- UDP Traffic: {name} ---")
    json_files = list(d.glob(f"{p}_*priority_udp.json"))
    srv_files = list(d.glob(f"{p}_server_*5202.log"))

    if json_files:
        jf = json_files[0]
        with open(jf) as f:
            jdata = json.load(f)
        end = jdata.get("end", {})
        # client side has "sum"
        c_sum = end.get("sum", {})
        print(f"  Client JSON: {jf.name}")
        print(f"    Duration: {c_sum.get('seconds'):.2f}s | Bytes: {c_sum.get('bytes')} ({c_sum.get('bytes')/(1024*1024):.2f} MB)")
        print(f"    Bitrate: {c_sum.get('bits_per_second')/1e6:.3f} Mbps")
        print(f"    Packets sent: {c_sum.get('packets')}, Lost: {c_sum.get('lost_packets')} ({c_sum.get('lost_percent'):.3f}%)")
        print(f"    Jitter: {c_sum.get('jitter_ms')} ms")
    else:
        print("  Client JSON: NOT FOUND")

    if srv_files:
        sf = srv_files[0]
        stext = sf.read_text(encoding="utf-8")
        print(f"  Server Log: {sf.name}")
        # find intervals with 0 bytes
        zero_intervals = []
        loss_intervals = []
        for l in stext.splitlines():
            if "sec" in l and ("KBytes" in l or "MBytes" in l or "Bytes" in l):
                if "0.00 Bytes" in l or "0.00 bits/sec" in l:
                    zero_intervals.append(l.strip())
                m_loss = re.search(r'(\d+)/(\d+)\s+\(([\d\.]+)%\)', l)
                if m_loss and int(m_loss.group(1)) > 0 and "receiver" not in l:
                    loss_intervals.append(l.strip())
                if "receiver" in l and "0.00-" in l:
                    print(f"    Receiver Final Summary: {l.strip()}")
            if "out-of-order" in l:
                print(f"    Out-of-order: {l.strip()}")
        print(f"    Zero-throughput intervals count: {len(zero_intervals)}")
        for zi in zero_intervals:
            print(f"      {zi}")
        print(f"    Intervals with loss count: {len(loss_intervals)}")
        for li in loss_intervals:
            print(f"      {li}")
    else:
        print("  Server Log: NOT FOUND")

print("\n================================================================================")
print("SECTION 5: TCP TRAFFIC (SENDER JSON vs RECEIVER LOG)")
print("================================================================================")

for name, t in trials.items():
    d = t["dir"]
    p = t["prefix"]
    print(f"\n--- TCP Traffic: {name} ---")
    json_files = list(d.glob(f"{p}_*bulk_tcp.json"))
    srv_files = list(d.glob(f"{p}_server_*5201.log"))

    if json_files:
        jf = json_files[0]
        with open(jf) as f:
            jdata = json.load(f)
        end = jdata.get("end", {})
        c_sum_sent = end.get("sum_sent", {})
        c_sum_recv = end.get("sum_received", {})
        print(f"  Client JSON: {jf.name}")
        print(f"    Sender   sum_sent:     duration={c_sum_sent.get('seconds'):.2f}s, bytes={c_sum_sent.get('bytes')} ({c_sum_sent.get('bytes')/(1024*1024):.2f} MB), bitrate={c_sum_sent.get('bits_per_second')/1e6:.3f} Mbps, retransmits={c_sum_sent.get('retransmits')}")
        print(f"    Receiver sum_received: duration={c_sum_recv.get('seconds'):.2f}s, bytes={c_sum_recv.get('bytes')} ({c_sum_recv.get('bytes')/(1024*1024):.2f} MB), bitrate={c_sum_recv.get('bits_per_second')/1e6:.3f} Mbps")
    else:
        print("  Client JSON: NOT FOUND")

    if srv_files:
        sf = srv_files[0]
        stext = sf.read_text(encoding="utf-8")
        print(f"  Server Log: {sf.name}")
        zero_intervals = []
        for l in stext.splitlines():
            if "sec" in l and ("KBytes" in l or "MBytes" in l or "Bytes" in l):
                if "0.00 Bytes" in l or "0.00 bits/sec" in l:
                    zero_intervals.append(l.strip())
                if "receiver" in l and "0.00-" in l:
                    print(f"    Receiver Final Summary: {l.strip()}")
        print(f"    Zero-throughput intervals count: {len(zero_intervals)}")
        for zi in zero_intervals:
            print(f"      {zi}")
    else:
        print("  Server Log: NOT FOUND")

print("\n================================================================================")
print("SECTION 6: CONTROLLER UNIFIED LOGS & AI TELEMETRY")
print("================================================================================")

for name, t in trials.items():
    p = t["prefix"]
    print(f"\n--- Unified Event Log entries for trial_id: {p} ---")
    unif_csv = BASE / "unified_event_log.csv"
    if unif_csv.exists():
        with open(unif_csv) as f:
            rows = [r for r in csv.DictReader(f) if r["trial_id"] == p]
            print(f"  Total event rows: {len(rows)}")
            for r in rows:
                print(f"    {r['timestamp_iso']} | Event={r['event_type']} | DPID={r['dpid']} | Port={r['port']} | Mode={r['mode']} | Details={r['details']}")
