import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt

def evaluate_and_plot():
    model = joblib.load('models/traffic_predictor.joblib')
    df = pd.read_csv('data/processed_features.csv')

    df = df.sort_values(by=['port_no', 'timestamp'])
    df['prev_tx_mbps'] = df.groupby('port_no')['tx_throughput_mbps'].shift(1)
    df['prev_rx_mbps'] = df.groupby('port_no')['rx_throughput_mbps'].shift(1)
    df['prev_tx_pkts'] = df.groupby('port_no')['tx_packet_rate'].shift(1)
    df['target_tx_mbps'] = df.groupby('port_no')['tx_throughput_mbps'].shift(-1)
    df = df.dropna()

    feature_cols = ['port_no', 'tx_throughput_mbps', 'rx_throughput_mbps', 
                    'tx_packet_rate', 'prev_tx_mbps', 'prev_rx_mbps', 'prev_tx_pkts']
    
    X = df[feature_cols]
    df['predicted_tx_mbps'] = model.predict(X)

    # Plot performance for Port 2 (TCP) and Port 3 (UDP)
    plt.figure(figsize=(12, 6))
    
    for port in [2, 3]:
        port_data = df[df['port_no'] == port].reset_index()
        plt.plot(port_data.index, port_data['target_tx_mbps'], label=f'Actual Tx (Port {port})', linewidth=2)
        plt.plot(port_data.index, port_data['predicted_tx_mbps'], '--', label=f'Predicted Tx (Port {port})', linewidth=1.5)

    plt.title('Predictive Traffic Engineering: Actual vs. Predicted Port Throughput')
    plt.xlabel('Time Step Sequence')
    plt.ylabel('Throughput (Mbps)')
    plt.legend()
    plt.grid(True)
    
    plt.savefig('logs/traffic_prediction_plot.png')
    print("Plot generated successfully -> logs/traffic_prediction_plot.png")

if __name__ == '__main__':
    evaluate_and_plot()
