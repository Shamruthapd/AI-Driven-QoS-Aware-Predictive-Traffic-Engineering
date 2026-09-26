import pandas as pd
import numpy as np
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

def train_predictive_model():
    # Process features first
    os.system('python3 scripts/feature_engineering.py')
    
    feature_file = 'data/processed_features.csv'
    if not os.path.exists(feature_file):
        print(f"Error: {feature_file} not found.")
        return

    df = pd.read_csv(feature_file)
    
    # Create lag features (predict step t using step t-1 metrics)
    df = df.sort_values(by=['port_no', 'timestamp'])
    df['prev_tx_mbps'] = df.groupby('port_no')['tx_throughput_mbps'].shift(1)
    df['prev_rx_mbps'] = df.groupby('port_no')['rx_throughput_mbps'].shift(1)
    df['prev_tx_pkts'] = df.groupby('port_no')['tx_packet_rate'].shift(1)
    
    # Target: Predict next-step transmit throughput
    df['target_tx_mbps'] = df.groupby('port_no')['tx_throughput_mbps'].shift(-1)
    
    # Drop NA rows caused by shifting
    df = df.dropna()

    feature_cols = ['port_no', 'tx_throughput_mbps', 'rx_throughput_mbps', 
                    'tx_packet_rate', 'prev_tx_mbps', 'prev_rx_mbps', 'prev_tx_pkts']
    
    X = df[feature_cols]
    y = df['target_tx_mbps']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    print("\n=== Time-Series Model Training Results ===")
    print(f"Dataset Size: {len(df)} samples")
    print(f"Root Mean Squared Error (RMSE): {rmse:.4f} Mbps")
    print(f"R^2 Score: {r2:.4f}")

    os.makedirs('models', exist_ok=True)
    model_path = 'models/traffic_predictor.joblib'
    joblib.dump(model, model_path)
    print(f"Model saved successfully to -> {model_path}")

if __name__ == '__main__':
    train_predictive_model()
