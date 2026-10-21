import json
import csv
import os
import re

def parse_results():
    results = []
    
    for qos_state in ['off', 'on']:
        bulk_file = f'logs/h2_bulk_{qos_state}.json'
        priority_file = f'logs/h3_priority_{qos_state}.json'
        
        # Priority UDP Flow Metrics
        if os.path.exists(priority_file):
            with open(priority_file) as f:
                data = json.load(f)
                server_text = data.get('server_output_text', '')
                receiver_lines = [
                    line for line in server_text.splitlines()
                    if 'receiver' in line and 'Mbits/sec' in line
                ]
                if not receiver_lines:
                    raise ValueError(f"Receiver summary missing in {priority_file}")
                match = re.search(
                    r'([0-9.]+)\s+Mbits/sec\s+([0-9.]+)\s+ms\s+(\d+)/(\d+)\s+\(([0-9.]+)%\).*receiver',
                    receiver_lines[-1]
                )
                if not match:
                    raise ValueError(f"Could not parse receiver summary in {priority_file}: {receiver_lines[-1]}")
                throughput_mbps = float(match.group(1))
                jitter_ms = float(match.group(2))
                lost_packets = int(match.group(3))
                packets = int(match.group(4))
                loss_percent = float(match.group(5))
                
                results.append({
                    'qos_state': qos_state.upper(),
                    'flow_type': 'Priority_UDP_Video',
                    'throughput_mbps': round(throughput_mbps, 2),
                    'jitter_ms': round(jitter_ms, 3),
                    'packet_loss_pct': round(loss_percent, 2)
                })

        # Bulk TCP Flow Metrics
        if os.path.exists(bulk_file):
            with open(bulk_file) as f:
                data = json.load(f)
                end = data.get('end', {}).get('sum_received', {})
                throughput_mbps = (end.get('bits_per_second', 0)) / 1e6
                results.append({
                    'qos_state': qos_state.upper(),
                    'flow_type': 'Bulk_TCP_Data',
                    'throughput_mbps': round(throughput_mbps, 2),
                    'jitter_ms': 0.0,
                    'packet_loss_pct': 0.0
                })

    out_csv = 'data/results/week8_qos_on_vs_off_measurements.csv'
    os.makedirs('data/results', exist_ok=True)
    
    with open(out_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['qos_state', 'flow_type', 'throughput_mbps', 'jitter_ms', 'packet_loss_pct'])
        writer.writeheader()
        writer.writerows(results)
        
    print(f"\n=== Results Saved to {out_csv} ===")
    for r in results:
        print(r)

if __name__ == '__main__':
    parse_results()
