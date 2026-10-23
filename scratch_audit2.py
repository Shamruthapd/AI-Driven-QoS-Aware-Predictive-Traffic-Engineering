#!/usr/bin/env python3
from scratch_audit import trials, parse_group_stats, analyze_ping

print("=== GROUP STATS TABLE ===")
for name, t in trials.items():
    d = t['dir']
    p = t['prefix']
    pre = parse_group_stats(d / f'{p}_s1_group_stats_pre_fail.txt')
    dur = parse_group_stats(d / f'{p}_s1_group_stats_during_fail.txt')
    rec = parse_group_stats(d / f'{p}_s1_group_stats_recovered.txt')
    print('Trial:', name)
    for gid in (100, 101):
        p0 = pre[gid]['b0_pkts'] if pre and gid in pre else '-'
        p1 = pre[gid]['b1_pkts'] if pre and gid in pre else '-'
        d0 = dur[gid]['b0_pkts'] if dur and gid in dur else '-'
        d1 = dur[gid]['b1_pkts'] if dur and gid in dur else '-'
        r0 = rec[gid]['b0_pkts'] if rec and gid in rec else '-'
        r1 = rec[gid]['b1_pkts'] if rec and gid in rec else '-'
        print(f"  Group {gid}: Pre[B0={p0}, B1={p1}] -> During[B0={d0}, B1={d1}] -> Rec[B0={r0}, B1={r1}]")

print("\n=== PING TABLE ===")
for name, t in trials.items():
    d = t['dir']
    p = t['prefix']
    plog = list(d.glob(f'{p}_*ping.log'))[0]
    res = analyze_ping(plog)
    srtts = sorted(res['rtts'])
    p50 = srtts[len(srtts)//2]
    p95 = srtts[int(len(srtts)*0.95)]
    lost = res['tx'] - res['rx']
    tx = res['tx']
    rx = res['rx']
    pct = res['loss_pct']
    t_ms = res['time_ms']
    mn = min(res['rtts'])
    avg = sum(res['rtts'])/len(res['rtts'])
    mx = max(res['rtts'])
    print(f"{name:10s}: Tx={tx}, Rx={rx}, Lost={lost} ({pct}%), Time={t_ms}ms, Min={mn:.3f}, Mean={avg:.3f}, Med={p50:.3f}, P95={p95:.3f}, Max={mx:.3f}")
    print(f"  Gaps: {res['gaps']}")
