import pandas as pd
from xgboost import XGBRegressor
import joblib
import os

# Create models directory
if not os.path.exists('models'):
    os.makedirs('models')

# Load data
print("Loading data...")
df = pd.read_csv('data/train.csv')

# Prepare features and target
X = df.drop(columns=['FloodProbability', 'id'])
y = df['FloodProbability']

# Train model (using a subset for speed in this setup check if needed, but let's do full)
print("Training model...")
model = XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=6, random_state=42, n_jobs=-1)
model.fit(X, y)

# Save model
joblib.dump(model, 'models/xgboost_flood_model.pkl')
print("Model saved to models/xgboost_flood_model.pkl")
