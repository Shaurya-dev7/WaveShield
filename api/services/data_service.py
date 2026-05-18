import pandas as pd
from sqlalchemy import text
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from src.db.database import engine

class DataService:
    @staticmethod
    def get_latest_features(city: str) -> dict:
        """
        Retrieves the absolute most recent weather data row for a specific city
        from PostgreSQL using raw SQL for maximum performance.
        """
        query = text("""
            SELECT * FROM engineered_features 
            WHERE lower(city) = :city 
            ORDER BY timestamp DESC 
            LIMIT 1
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {"city": city.lower()}).fetchone()
            
        if not result:
            return None
            
        # Convert SQLAlchemy Row to dictionary safely handling Decimal/Timestamp objects
        return dict(result._mapping)

    @staticmethod
    def get_all_latest_features() -> list[dict]:
        """
        Retrieves the most recent record for ALL cities efficiently
        using PostgreSQL DISTINCT ON functionality.
        """
        query = text("""
            SELECT DISTINCT ON (city) *
            FROM engineered_features
            ORDER BY city, timestamp DESC
        """)
        
        with engine.connect() as conn:
            results = conn.execute(query).fetchall()
            
        return [dict(r._mapping) for r in results]

    @staticmethod
    def get_active_alerts() -> list[dict]:
        """
        Retrieves the 50 most recent active disaster alerts from PostgreSQL.
        """
        query = text("""
            SELECT timestamp, city, severity as risk_level, message, 0.0 as confidence
            FROM alerts
            ORDER BY timestamp DESC
            LIMIT 50
        """)
        
        with engine.connect() as conn:
            results = conn.execute(query).fetchall()
            
        return [dict(r._mapping) for r in results]
        
    @staticmethod
    def get_historical_data(hours: int = 48) -> list[dict]:
        """
        Retrieves the last N hours of time-series data for charting from PostgreSQL.
        """
        query = text("""
            SELECT timestamp, city, rain, temp_change_24h, 
                   soil_moisture_trend, weather_severity_score
            FROM engineered_features
            ORDER BY timestamp DESC
            LIMIT :limit
        """)
        # Roughly N hours * number of cities
        limit_val = hours * 8 
        
        with engine.connect() as conn:
            results = conn.execute(query, {"limit": limit_val}).fetchall()
            
        return [dict(r._mapping) for r in results]

    @staticmethod
    def get_total_dataset_rows() -> int:
        """
        Returns exact count from weather_data table.
        """
        query = text("SELECT COUNT(*) FROM weather_data")
        try:
            with engine.connect() as conn:
                return conn.execute(query).scalar()
        except Exception:
            # DB might not be initialized yet
            return 0
