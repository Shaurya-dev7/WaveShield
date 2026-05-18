import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.api.historical_fetcher import backfill_historical_data
from src.features.engineer import generate_ml_features

def main():
    print("AI Disaster Prediction - ML Data Preparation Pipeline")
    print("1. Fetch Historical Data (Last 30 Days)")
    print("2. Engineer Features")
    print("3. Run Both")
    
    choice = input("Select an option (1/2/3): ")
    
    if choice in ['1', '3']:
        # For demonstration, pulling just the last 30 days to avoid huge API delays.
        # In production, change to 2021-01-01 to 2023-12-31
        from datetime import datetime, timedelta
        end_date = datetime.now() - timedelta(days=2) # Open-meteo historical is 2-5 days delayed
        start_date = end_date - timedelta(days=30)
        
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        backfill_historical_data(start_str, end_str)
        
    if choice in ['2', '3']:
        generate_ml_features()
        
    print("Pipeline Execution Complete!")

if __name__ == "__main__":
    main()
