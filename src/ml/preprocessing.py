import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from pathlib import Path
import joblib

def load_and_clean_data(file_path: Path) -> pd.DataFrame:
    """
    Loads the engineered dataset, sorts chronologically, and cleans it.
    """
    df = pd.read_csv(file_path)
    
    # Fill NaN values with 0. 
    # Historical APIs often miss certain parameters (like soil moisture).
    # Rolling diffs also generate NaNs for the first 24 hours.
    df = df.fillna(0).reset_index(drop=True)
    
    # Sort by time to ensure time-series integrity
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    return df

def generate_training_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates rule-based flood risk labels to act as the target variable for ML training.
    In a real-world scenario, this column would come from historical flood records.
    """
    def heuristic_labeler(row):
        score = 0
        if row['rain'] > 50.0:
            score += 3
        elif row['rain'] > 25.0:
            score += 1
            
        if row['soil_moisture_0_to_1cm'] > 0.5:
            score += 1
            
        if score >= 3:
            return "HIGH"
        elif score >= 1:
            return "MEDIUM"
        else:
            return "LOW"
            
    df['risk_level'] = df.apply(heuristic_labeler, axis=1)
    
    # FOR DEMONSTRATION: Ensure at least one instance of each class exists 
    # to prevent XGBoost from crashing on small, calm weather datasets.
    # We artificially inject a severe storm into the first row, and moderate rain into the second.
    if len(df) > 2:
        df.loc[0, 'risk_level'] = "HIGH"
        df.loc[1, 'risk_level'] = "MEDIUM"
        df.loc[2, 'risk_level'] = "LOW"
        
    return df

def prepare_features_and_target(df: pd.DataFrame, models_dir: Path):
    """
    Selects features, encodes the target label, and creates the ML-ready arrays.
    """
    # Exclude non-predictive or target columns
    exclude_cols = ['timestamp', 'city', 'risk_level']
    features = [col for col in df.columns if col not in exclude_cols]
    
    X = df[features]
    y = df['risk_level']
    
    # Encode 'LOW', 'MEDIUM', 'HIGH' mapping explicitly
    le = LabelEncoder()
    le.fit(["LOW", "MEDIUM", "HIGH"])
    y_encoded = le.transform(y)
    
    # Save the encoder for live prediction later
    models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(le, models_dir / "label_encoder.pkl")
    
    return X, y_encoded, features, le

def time_series_split(X: pd.DataFrame, y: np.ndarray, train_ratio=0.8):
    """
    Splits the data chronologically to prevent data leakage.
    DO NOT use random train_test_split for weather!
    """
    split_index = int(len(X) * train_ratio)
    
    X_train, X_test = X.iloc[:split_index], X.iloc[split_index:]
    y_train, y_test = y[:split_index], y[split_index:]
    
    return X_train, X_test, y_train, y_test
