import pandas as pd
from typing import Dict, Any
from src.config.settings import TARGET_CITIES
from src.utils.logger import setup_logger

# Database imports
from src.db.database import SessionLocal
from src.db.models import WeatherData
from sqlalchemy.dialects.postgresql import insert

logger = setup_logger("Master_Storage_DB")

def init_master_dataset() -> None:
    """
    Deprecated for PostgreSQL. Database init handled via Alembic/init_db.py
    """
    pass

def save_to_master(city: str, raw_data: Dict[str, Any]) -> None:
    """
    Safely upserts a new record to the PostgreSQL TimescaleDB hypertable, 
    preventing duplicates inherently via SQL unique constraints.
    """
    if not raw_data:
        return

    try:
        # Construct the SQL row
        timestamp = pd.to_datetime(raw_data.get("time"))
        
        row_data = {
            "timestamp": timestamp,
            "city": city,
            "latitude": TARGET_CITIES[city]["lat"],
            "longitude": TARGET_CITIES[city]["lon"],
            "temperature_2m": raw_data.get("temperature_2m"),
            "relative_humidity_2m": raw_data.get("relative_humidity_2m"),
            "precipitation": raw_data.get("precipitation"),
            "rain": raw_data.get("rain"),
            "surface_pressure": raw_data.get("surface_pressure"),
            "wind_speed_10m": raw_data.get("wind_speed_10m"),
            "wind_direction_10m": raw_data.get("wind_direction_10m"),
            "cloud_cover": raw_data.get("cloud_cover"),
            "soil_temperature_0_to_7cm": raw_data.get("soil_temperature_0cm"),
            "soil_moisture_0_to_1cm": raw_data.get("soil_moisture_0_to_1cm")
        }

        # Handle NaNs safely for SQL insertion
        for k, v in row_data.items():
            if pd.isna(v):
                row_data[k] = None

        with SessionLocal() as db:
            stmt = insert(WeatherData).values(**row_data)
            
            # TimescaleDB requires timestamp + city for unique identification
            stmt = stmt.on_conflict_do_nothing(
                index_elements=['timestamp', 'city']
            )
            
            result = db.execute(stmt)
            db.commit()
            
            if result.rowcount > 0:
                logger.info(f"Successfully upserted {city} data to PostgreSQL.")
            else:
                logger.info(f"Duplicate avoided: {city} at {timestamp} already exists in DB.")

    except Exception as e:
        logger.error(f"Error saving to PostgreSQL for {city}: {e}")
