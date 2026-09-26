import csv
import os
import time
import joblib
import pandas as pd
import numpy as np
from os_ken.base import app_manager
from os_ken.controller import ofp_event
from os_ken.controller.handler import MAIN_DISPATCHER, CONFIG_DISPATCHER, set_ev_cls
from os_ken.ofproto import ofproto_v1_3
from os_ken.lib import hub
from os_ken.lib.packet import packet, ethernet, ether_types, ipv4, udp

class PredictiveQoSController(app_manager.OSKenApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(PredictiveQoSController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.datapaths = {}
        self.stats_file = 'data/switch_stats.csv'
        self.model_path = 'models/traffic_predictor.joblib'
        self.model = None
        self.port_history = {}  # Store previous readings per port
        self.congestion_threshold_mbps = 10.0  # Trigger threshold

        self._load_model()
        self.monitor_thread = hub.spawn(self._monitor)

    def _load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                self.logger.info("Successfully loaded ML Traffic Predictor.")
            except Exception as e:
                self.logger.error(f"Failed to load ML model: {e}")
        else:
            self.logger.warning("ML model not found. Running in baseline routing mode.")

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, CONFIG_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            self.datapaths[datapath.id] = datapath
        elif evThe time-series dataset expansion succeeded. With **279 samples**, the model has crossed into meaningful predictive capacity, jumping from a negative baseline to an **$R^2$ score of 0.6143**. The predictor is now capturing real multi-rate traffic dynamics and transitions.

Here is the breakdown of the training run:

* **Dataset Volume:** 279 time-series observations covering multiple variable-bitrate dynamic traffic waves.
* **Predictive Accuracy ($R^2 = 0.6143$):** The Random Forest Regressor explains over 61% of the variance in next-step port throughput based on recent window metrics ($t-1$).
* **RMSE ($4.7176\text{ Mbps}$):** The prediction error margin reflects the sudden onset and termination steps of high-bandwidth bursts (e.g., jump from $\sim 0.003\text{ Mbps}$ to $\sim 15.4\text{ Mbps}$ at index 275).

---

## Step 4: Evaluate & Visualize Predictions (`scripts/evaluate_model.py`)

To inspect how closely the predicted throughput tracks the actual traffic load across time, create a visualization script.

Run this command in **Terminal 3**:

```bash
cat << 'EOF' > scripts/evaluate_model.py
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
