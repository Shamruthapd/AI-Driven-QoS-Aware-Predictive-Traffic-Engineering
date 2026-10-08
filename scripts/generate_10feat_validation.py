import csv

input_file = 'data/processed_features.csv'
output_file = 'data/processed_validation_10feat.csv'

with open(input_file, mode='r', newline='') as infile:
    reader = csv.DictReader(infile)
    rows = list(reader)

# Collect throughputs to calculate 85th percentile threshold for anomaly labeling
throughputs = [
    (float(r['rx_throughput_mbps']) + float(r['tx_throughput_mbps'])) * 1e6 
    for r in rows
]
sorted_throughputs = sorted(throughputs)
p85_index = int(len(sorted_throughputs) * 0.85)
threshold_bps = sorted_throughputs[p85_index] if sorted_throughputs else 0

fieldnames = [
    'rx_packets_delta', 'tx_packets_delta',
    'rx_bytes_delta', 'tx_bytes_delta',
    'rx_dropped_delta', 'tx_dropped_delta',
    'rx_errors_delta', 'tx_errors_delta',
    'throughput_bps', 'packet_rate_pps',
    'is_anomalous'
]

with open(output_file, mode='w', newline='') as outfile:
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()

    for row in rows:
        rx_tp = float(row.get('rx_throughput_mbps', 0))
        tx_tp = float(row.get('tx_throughput_mbps', 0))
        total_tp_bps = (rx_tp + tx_tp) * 1e6

        rx_pr = float(row.get('rx_packet_rate', 0))
        tx_pr = float(row.get('tx_packet_rate', 0))
        total_pr_pps = rx_pr + tx_pr

        writer.writerow({
            'rx_packets_delta': row.get('rx_pkts_delta', 0),
            'tx_packets_delta': row.get('tx_pkts_delta', 0),
            'rx_bytes_delta': row.get('rx_bytes_delta', 0),
            'tx_bytes_delta': row.get('tx_bytes_delta', 0),
            'rx_dropped_delta': 0,
            'tx_dropped_delta': 0,
            'rx_errors_delta': 0,
            'tx_errors_delta': 0,
            'throughput_bps': f"{total_tp_bps:.2f}",
            'packet_rate_pps': f"{total_pr_pps:.2f}",
            'is_anomalous': 1 if total_tp_bps > threshold_bps else 0
        })

print(f"Successfully generated {output_file} without pandas!")
