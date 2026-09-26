import re
import csv
import os

def parse_iperf_log(file_path, flow_type):
    metrics = []
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return metrics

    with open(file_path, 'r') as f:
        lines = f.readlines()

    # Pattern for interval lines e.g., [  5]   0.00-1.00   sec  1.00 MBytes  8.38 Mbits/sec  0   297 KBytes
    interval_pattern = re.compile(
        r'\[\s*\d+\]\s+(\d+\.\d+-\d+\.\d+)\s+sec\s+[\d\.]+\s+[KM]Bytes\s+([\d\.]+)\s+Mbits/sec'
    )

    for line in lines:
        # Avoid summary lines (0.00-10.00)
        if "0.00-10.00" in line or "sender" in line or "receiver" in line:
            continue
        
        match = interval_pattern.search(line)
        if match:
            interval = match.group(1)
            bitrate_mbps = float(match.group(2))
            
            # Extract optional fields if present
            retr = 0
            if flow_type == "TCP":
                retr_match = re.search(r'Mbits/sec\s+(\d+)', line)
                if retr_match:
                    retr = int(retr_match.group(1))

            metrics.append({
                "flow_type": flow_type,
                "interval": interval,
                "bitrate_mbps": bitrate_mbps,
                "retransmissions": retr
            })

    return metrics

def export_to_csv():
    os.makedirs('data', exist_ok=True)
    csv_file = 'data/telemetry_dataset.csv'

    tcp_data = parse_iperf_log('logs/iperf_tcp_client.log', 'TCP')
    udp_data = parse_iperf_log('logs/iperf_udp_client.log', 'UDP')

    all_data = tcp_data + udp_data

    fieldnames = ["flow_type", "interval", "bitrate_mbps", "retransmissions"]

    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_data)

    print(f"Successfully generated dataset with {len(all_data)} records -> {csv_file}")

if __name__ == '__main__':
    export_to_csv()
