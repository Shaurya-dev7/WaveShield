import pandas as pd
from pathlib import Path
from src.config.settings import MASTER_DATASET_PATH, ENGINEERED_DIR
from src.utils.logger import setup_logger

logger = setup_logger("Feature_Engineer")

def generate_ml_features(input_path: Path = MASTER_DATASET_PATH, output_filename: str = "engineered_master.csv") -> None:
    """
    Reads the master dataset and engineers ML-ready features such as 
    rolling averages and rate-of-change.
    Saves the result to the data/engineered directory.
    """
    if not input_path.exists():
        logger.error(f"Cannot engineer features: {input_path} does not exist.")
        return

    logger.info("Starting Feature Engineering process...")
    try:
        # Load dataset
        df = pd.read_csv(input_path)
        
        # Ensure timestamp is datetime and sort the data chronologically per city
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values(by=['city', 'timestamp']).reset_index(drop=True)

        # We must group by city before calculating rolling windows to prevent
        # cross-city contamination (e.g. Mumbai's last hour affecting Delhi's first hour)
        
        # 1. Rolling Rainfall (Flood Risk Indicators)
        # Assuming hourly data, 24 periods = 24 hours
        df['rainfall_last_24h'] = df.groupby('city')['rain'].transform(lambda x: x.rolling(window=24, min_periods=1).sum())
        df['rainfall_last_72h'] = df.groupby('city')['rain'].transform(lambda x: x.rolling(window=72, min_periods=1).sum())
        df['rolling_rainfall_average'] = df.groupby('city')['rain'].transform(lambda x: x.rolling(window=24, min_periods=1).mean())
        
        # 2. Rate of Change Features (Storm/Anomaly Indicators)
        # Difference between current hour and 24 hours ago
        df['temp_change_24h'] = df.groupby('city')['temperature_2m'].transform(lambda x: x.diff(periods=24))
        df['pressure_change_24h'] = df.groupby('city')['surface_pressure'].transform(lambda x: x.diff(periods=24))
        df['wind_speed_change'] = df.groupby('city')['wind_speed_10m'].transform(lambda x: x.diff(periods=1))
        
        # 3. Averages & Trends
        df['avg_humidity_24h'] = df.groupby('city')['relative_humidity_2m'].transform(lambda x: x.rolling(window=24, min_periods=1).mean())
        df['soil_moisture_trend'] = df.groupby('city')['soil_moisture_0_to_1cm'].transform(lambda x: x.diff(periods=12)) # 12 hr trend

        # 4. Severity Scores (Heuristics)
        # Simple weighted sum representing immediate weather severity
        df['weather_severity_score'] = (
            (df['wind_speed_10m'] / 50) + 
            (df['rain'] / 10) + 
            (df['temperature_2m'] / 40)
        )
        
        # 5. Rainfall Intensity Score
        # Heavy rain in short time is worse than light rain over a long time.
        df['rainfall_intensity_score'] = df['rain'] * df['relative_humidity_2m'] / 100

        # Save engineered dataset to PostgreSQL instead of CSV
        records = df.to_dict(orient='records')
        
        from src.db.database import SessionLocal
        from src.db.models import EngineeredFeatures
        from sqlalchemy.dialects.postgresql import insert
        
        with SessionLocal() as db:
            for r in records:
                # Handle NaNs safely
                for k, v in r.items():
                    if pd.isna(v): r[k] = None
                    
                stmt = insert(EngineeredFeatures).values(
                    timestamp=r['timestamp'],
                    city=r['city'],
                    temp_change_24h=r.get('temp_change_24h'),
                    rainfall_last_24h=r.get('rainfall_last_24h'),
                    rainfall_last_72h=r.get('rainfall_last_72h'),
                    soil_moisture_trend=r.get('soil_moisture_trend'),
                    pressure_change_24h=r.get('pressure_change_24h'),
                    wind_speed_change=r.get('wind_speed_change'),
                    weather_severity_score=r.get('weather_severity_score')
                )
                
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=['timestamp', 'city']
                )
                db.execute(stmt)
                
            db.commit()
            
        logger.info(f"Feature Engineering complete. Upserted {len(records)} engineered records to PostgreSQL.")

    except Exception as e:
        logger.error(f"Feature Engineering failed: {e}")
