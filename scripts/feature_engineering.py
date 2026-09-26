import pandas as pd
import numpy as np
import os

def process_switch_features():
    stats_file = 'data/switch_stats.csv'
    output_file = 'data/processed_features.csv'

    if not os.path.exists(stats_file):
        print("switch_stats.csv missing.")
        return

    df = pd.read_csv(stats_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Sort by port and time
    df = df.sort_values(by=['port_no', 'timestamp'])

    # Calculate deltas for packets and bytes per port over the polling interval
    df['rx_bytes_delta'] = df.groupby('port_no')['rx_bytes'].diff().fillna(0)
    df['tx_bytes_delta'] = df.groupby('port_no')['tx_bytes'].diff().fillna(0)
    df['rx_pkts_delta'] = df.groupby('port_no')['rx_packets'].diff().fillna(0)
    df['tx_pkts_delta'] = df.groupby('port_no')['tx_packets'].diff().fillna(0)

    # Time step delta in seconds (5-second polling interval)
    df['time_delta'] = df.groupby('port_no')['timestamp'].diff().dt.total_seconds().fillna(5.0)

    # Calculate Throughput (Mbps) and Packet Rate (packets/sec)
    df['rx_throughput_mbps'] = (df['rx_bytes_delta'] * 8) / (df['time_delta'] * 1e6)
    df['tx_throughput_mbps'] = (df['tx_bytes_delta'] * 8) / (df['time_delta'] * 1e6)
    df['rx_packet_rate'] = df['rx_pkts_delta'] / df['time_delta']
    df['tx_packet_rate'] = df['tx_pkts_delta'] / df['time_delta']

    # Drop initial reference rows with zero delta
    processed_df = df[df['rx_bytes_delta'] >= 0].copy()

    processed_df.to_csv(output_file, index=False)
    print(f"Feature dataset created successfully -> {output_file}")
    print("\nSummary of Processed Port Features:")
    print(processed_df[['timestamp', 'port_no', 'rx_throughput_mbps', 'tx_throughput_mbps', 'tx_packet_rate']].tail(9))

if __name__ == '__main__':
    process_switch_features()
