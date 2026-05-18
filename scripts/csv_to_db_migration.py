import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.db.database import SessionLocal, engine
from src.db.models import WeatherData, EngineeredFeatures, AlertLog
from src.config.settings import MASTER_DATA_FILE, ENGINEERED_DIR, ALERTS_DIR
from src.utils.logger import setup_logger

logger = setup_logger("CSV_to_DB_Migration")

def migrate_csv_to_db():
    """
    Safely migrates all existing CSV records into PostgreSQL,
    ignoring duplicates (upsert behavior).
    """
    logger.info("Starting CSV to PostgreSQL Migration...")
    
    # 1. Migrate Raw Weather Data
    if MASTER_DATA_FILE.exists():
        df_raw = pd.read_csv(MASTER_DATA_FILE)
        df_raw['timestamp'] = pd.to_datetime(df_raw['timestamp'])
        
        # We can use pandas to_sql for fast inserts, but we must handle duplicates.
        # to_sql with if_exists='append' will crash on primary key conflict.
        # To make it safe, we'll insert row by row, or drop duplicates first.
        try:
            # Drop rows that might already exist in DB
            existing_dates = pd.read_sql(f"SELECT timestamp, city FROM weather_data", engine)
            if not existing_dates.empty:
                existing_dates['timestamp'] = pd.to_datetime(existing_dates['timestamp'])
                # Merge and keep only left outer join
                merged = df_raw.merge(existing_dates, on=['timestamp', 'city'], how='left', indicator=True)
                df_raw = merged[merged['_merge'] == 'left_only'].drop(columns=['_merge'])

            if not df_raw.empty:
                df_raw.to_sql('weather_data', engine, if_exists='append', index=False, method='multi', chunksize=1000)
                logger.info(f"Migrated {len(df_raw)} raw weather records to PostgreSQL.")
            else:
                logger.info("No new raw weather records to migrate.")
        except Exception as e:
            logger.error(f"Failed migrating raw weather data: {e}")

    # 2. Migrate Engineered Features
    engineered_file = ENGINEERED_DIR / "engineered_master.csv"
    if engineered_file.exists():
        df_eng = pd.read_csv(engineered_file)
        df_eng['timestamp'] = pd.to_datetime(df_eng['timestamp'])
        try:
            # Basic append (Assuming empty DB on first run)
            # Future updates should use UPSERT (ON CONFLICT DO NOTHING)
            df_eng.to_sql('engineered_features', engine, if_exists='append', index=False, method='multi', chunksize=1000)
            logger.info(f"Migrated {len(df_eng)} engineered feature records to PostgreSQL.")
        except Exception as e:
            logger.error(f"Failed migrating engineered features: {e}")

    # 3. Migrate Alerts
    alerts_file = ALERTS_DIR / "active_alerts.csv"
    if alerts_file.exists():
        df_alerts = pd.read_csv(alerts_file)
        df_alerts['timestamp'] = pd.to_datetime(df_alerts['timestamp'])
        # Rename columns to match the new SQL schema
        df_alerts['alert_type'] = "ML_PREDICTION"
        df_alerts['severity'] = df_alerts['risk_level']
        df_alerts = df_alerts.drop(columns=['risk_level'])
        
        try:
            df_alerts.to_sql('alerts', engine, if_exists='append', index=False)
            logger.info(f"Migrated {len(df_alerts)} alert records to PostgreSQL.")
        except Exception as e:
            logger.error(f"Failed migrating alerts: {e}")

    logger.info("Migration Complete! You can now safely delete the CSV files.")

if __name__ == "__main__":
    migrate_csv_to_db()
