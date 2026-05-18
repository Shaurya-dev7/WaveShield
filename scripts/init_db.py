"""
===========================================================================
DATABASE INITIALIZATION SCRIPT — PostGIS + TimescaleDB
===========================================================================

This script initializes the complete database infrastructure:
    1. Creates PostGIS spatial extensions (postgis, topology, raster)
    2. Creates TimescaleDB time-series extension
    3. Creates all SQLAlchemy ORM tables
    4. Converts weather tables into TimescaleDB Hypertables
    5. Creates GiST spatial indexes
    6. Seeds initial flood zone polygons for monitored cities
    7. Verifies all extensions and tables

Run this ONCE after starting the Docker container for the first time,
or after wiping the database volume.

Usage:
    python scripts/init_db.py
===========================================================================
"""

import sys
from pathlib import Path
from sqlalchemy import text, inspect

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.db.database import engine, Base
from src.db.models import (
    WeatherData, EngineeredFeatures, PredictionLog, AlertLog,
    GeospatialProfile, FloodZone, RiverSegment, RiskRegion,
    GeospatialEvent
)
from src.utils.logger import setup_logger

logger = setup_logger("DB_Initializer")


def init_extensions():
    """Install PostGIS and TimescaleDB extensions."""
    logger.info("Installing database extensions...")
    extensions = [
        "CREATE EXTENSION IF NOT EXISTS postgis CASCADE;",
        "CREATE EXTENSION IF NOT EXISTS postgis_topology CASCADE;",
        "CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;",
    ]

    with engine.connect() as conn:
        for ext_sql in extensions:
            try:
                conn.execute(text(ext_sql))
                logger.info(f"  ✓ {ext_sql.split('IF NOT EXISTS ')[1].split(' ')[0]}")
            except Exception as e:
                logger.warning(f"  ⚠ Extension warning: {e}")
        conn.commit()

    # Verify PostGIS
    with engine.connect() as conn:
        try:
            result = conn.execute(text("SELECT PostGIS_Version();"))
            version = result.scalar()
            logger.info(f"PostGIS version: {version}")
        except Exception:
            logger.warning("PostGIS version check failed — extension may not be available.")


def init_tables():
    """Create all SQLAlchemy ORM tables."""
    logger.info("Creating database tables from ORM models...")
    Base.metadata.create_all(bind=engine)

    # List created tables
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    for t in tables:
        logger.info(f"  ✓ Table: {t}")
    logger.info(f"Total tables: {len(tables)}")


def init_hypertables():
    """Convert time-series tables to TimescaleDB Hypertables."""
    logger.info("Converting to TimescaleDB Hypertables...")
    hypertable_queries = [
        "SELECT create_hypertable('weather_data', 'timestamp', if_not_exists => TRUE);",
        "SELECT create_hypertable('engineered_features', 'timestamp', if_not_exists => TRUE);",
    ]

    with engine.connect() as conn:
        for query in hypertable_queries:
            try:
                conn.execute(text(query))
                table_name = query.split("'")[1]
                logger.info(f"  ✓ Hypertable: {table_name}")
            except Exception as e:
                logger.warning(f"  ⚠ Hypertable warning: {e}")
        conn.commit()


def init_spatial_indexes():
    """Create additional GiST spatial indexes for performance."""
    logger.info("Creating spatial indexes...")
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_weather_location ON weather_data USING gist(location);",
        "CREATE INDEX IF NOT EXISTS idx_profiles_location ON geospatial_profiles USING gist(location);",
        "CREATE INDEX IF NOT EXISTS idx_predictions_location ON predictions USING gist(location);",
        "CREATE INDEX IF NOT EXISTS idx_alerts_location ON alerts USING gist(location);",
    ]

    with engine.connect() as conn:
        for idx_sql in indexes:
            try:
                conn.execute(text(idx_sql))
                idx_name = idx_sql.split("EXISTS ")[1].split(" ")[0]
                logger.info(f"  ✓ Index: {idx_name}")
            except Exception as e:
                logger.warning(f"  ⚠ Index warning: {e}")
        conn.commit()


def seed_initial_flood_zones():
    """
    Seeds approximate flood zone polygons for the monitored Indian cities.
    These are rough approximations based on known floodplain geography.
    Real-world systems import government flood maps or Copernicus EMS data.
    """
    logger.info("Seeding initial flood zone polygons...")

    from src.config.settings import TARGET_CITIES

    with engine.connect() as conn:
        # Check if zones already exist
        result = conn.execute(text("SELECT COUNT(*) FROM flood_zones"))
        existing = result.scalar()
        if existing and existing > 0:
            logger.info(f"  Flood zones already seeded ({existing} existing). Skipping.")
            return

        # Generate approximate flood zone buffers around each city
        for city, coords in TARGET_CITIES.items():
            lat, lon = coords["lat"], coords["lon"]

            # Create a ~10km radius buffer as an approximate flood zone
            try:
                conn.execute(text("""
                    INSERT INTO flood_zones (name, city, risk_level, zone_type, boundary,
                                            area_sq_km, data_source, description)
                    VALUES (
                        :name, :city, 'MODERATE', 'URBAN_LOWLAND',
                        ST_Buffer(
                            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                            10000
                        )::geometry,
                        314.16,
                        'auto_generated',
                        :desc
                    )
                """), {
                    "name": f"{city} Urban Flood Zone",
                    "city": city,
                    "lat": lat,
                    "lon": lon,
                    "desc": f"Auto-generated 10km buffer flood zone for {city}",
                })
                logger.info(f"  ✓ Seeded flood zone for {city}")
            except Exception as e:
                logger.warning(f"  ⚠ Failed to seed {city}: {e}")

        conn.commit()


def verify_installation():
    """Run verification queries to confirm everything works."""
    logger.info("Verifying installation...")
    checks = [
        ("PostGIS", "SELECT PostGIS_Version();"),
        ("TimescaleDB", "SELECT extversion FROM pg_extension WHERE extname='timescaledb';"),
        ("Spatial Functions", "SELECT ST_AsText(ST_MakePoint(72.8777, 19.0760));"),
        ("Geography Distance", "SELECT ST_Distance("
         "ST_MakePoint(72.8777, 19.0760)::geography, "
         "ST_MakePoint(77.1025, 28.7041)::geography);"),
    ]

    with engine.connect() as conn:
        for name, query in checks:
            try:
                result = conn.execute(text(query))
                val = result.scalar()
                logger.info(f"  ✓ {name}: {val}")
            except Exception as e:
                logger.warning(f"  ⚠ {name} check failed: {e}")


def init_database():
    """Master initialization function."""
    logger.info("=" * 60)
    logger.info("ENTERPRISE SPATIAL DATABASE INITIALIZATION")
    logger.info("=" * 60)

    init_extensions()
    init_tables()
    init_hypertables()
    init_spatial_indexes()
    seed_initial_flood_zones()
    verify_installation()

    logger.info("=" * 60)
    logger.info("DATABASE INITIALIZATION COMPLETE")
    logger.info("=" * 60)


if __name__ == "__main__":
    init_database()
