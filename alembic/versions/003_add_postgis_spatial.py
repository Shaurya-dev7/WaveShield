"""add postgis spatial infrastructure

Revision ID: 003_postgis_spatial
Revises: 002_geo_intelligence
Create Date: 2026-05-17
"""

from alembic import op
import sqlalchemy as sa

revision = '003_postgis_spatial'
down_revision = '002_geo_intelligence'
branch_labels = None
depends_on = None


def upgrade():
    # =====================================================================
    # 1. Install PostGIS extensions
    # =====================================================================
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis CASCADE;")
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis_topology CASCADE;")

    # =====================================================================
    # 2. Add PostGIS geography columns to existing tables
    # =====================================================================

    # weather_data: spatial point for each reading
    try:
        op.add_column('weather_data',
            sa.Column('location', sa.Text(), nullable=True))
        op.execute("""
            ALTER TABLE weather_data
            ALTER COLUMN location TYPE geography(POINT, 4326)
            USING ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography;
        """)
    except Exception:
        pass

    # geospatial_profiles: spatial point
    try:
        op.add_column('geospatial_profiles',
            sa.Column('location', sa.Text(), nullable=True))
        op.execute("""
            ALTER TABLE geospatial_profiles
            ALTER COLUMN location TYPE geography(POINT, 4326)
            USING ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography;
        """)
    except Exception:
        pass

    # predictions: spatial point
    try:
        op.add_column('predictions',
            sa.Column('location', sa.Text(), nullable=True))
        op.execute("""
            ALTER TABLE predictions
            ALTER COLUMN location TYPE geography(POINT, 4326);
        """)
    except Exception:
        pass

    # alerts: spatial point
    try:
        op.add_column('alerts',
            sa.Column('location', sa.Text(), nullable=True))
        op.execute("""
            ALTER TABLE alerts
            ALTER COLUMN location TYPE geography(POINT, 4326);
        """)
    except Exception:
        pass

    # =====================================================================
    # 3. Create new spatial tables
    # =====================================================================

    # Flood Zones (polygon boundaries)
    op.execute("""
        CREATE TABLE IF NOT EXISTS flood_zones (
            id SERIAL PRIMARY KEY,
            name VARCHAR NOT NULL,
            city VARCHAR,
            country VARCHAR,
            risk_level VARCHAR NOT NULL CHECK (risk_level IN ('CRITICAL','HIGH','MODERATE','LOW')),
            zone_type VARCHAR,
            boundary geometry(POLYGON, 4326) NOT NULL,
            area_sq_km FLOAT,
            elevation_min_m FLOAT,
            elevation_max_m FLOAT,
            data_source VARCHAR,
            description TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_flood_zones_boundary ON flood_zones USING gist(boundary);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_flood_zones_city ON flood_zones(city);")

    # River Segments (linestring geometries)
    op.execute("""
        CREATE TABLE IF NOT EXISTS river_segments (
            id SERIAL PRIMARY KEY,
            name VARCHAR,
            waterway_type VARCHAR,
            geom geometry(LINESTRING, 4326) NOT NULL,
            upstream_area_sq_km FLOAT,
            discharge_m3s FLOAT,
            strahler_order INTEGER,
            data_source VARCHAR,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_river_segments_geom ON river_segments USING gist(geom);")

    # Dynamic Risk Regions
    op.execute("""
        CREATE TABLE IF NOT EXISTS risk_regions (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ NOT NULL,
            city VARCHAR,
            risk_level VARCHAR NOT NULL,
            confidence FLOAT,
            flood_susceptibility_index FLOAT,
            boundary geometry(POLYGON, 4326) NOT NULL,
            area_sq_km FLOAT,
            population_exposed INTEGER,
            trigger_source VARCHAR,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_risk_regions_boundary ON risk_regions USING gist(boundary);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_risk_regions_time ON risk_regions(timestamp);")

    # Geospatial Events
    op.execute("""
        CREATE TABLE IF NOT EXISTS geospatial_events (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ NOT NULL,
            event_type VARCHAR NOT NULL,
            severity VARCHAR,
            city VARCHAR,
            country VARCHAR,
            description TEXT,
            location geography(POINT, 4326),
            affected_area geometry(POLYGON, 4326),
            flood_susceptibility_index FLOAT,
            rainfall_mm FLOAT,
            confidence FLOAT,
            model_version VARCHAR,
            resolved INTEGER DEFAULT 0,
            resolved_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_geo_events_location ON geospatial_events USING gist(location);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_geo_events_area ON geospatial_events USING gist(affected_area);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_geo_events_time ON geospatial_events(timestamp);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_geo_events_type ON geospatial_events(event_type);")

    # =====================================================================
    # 4. Create spatial indexes on existing tables
    # =====================================================================
    try:
        op.execute("CREATE INDEX IF NOT EXISTS idx_weather_location ON weather_data USING gist(location);")
    except Exception:
        pass
    try:
        op.execute("CREATE INDEX IF NOT EXISTS idx_profiles_location ON geospatial_profiles USING gist(location);")
    except Exception:
        pass


def downgrade():
    op.execute("DROP TABLE IF EXISTS geospatial_events CASCADE;")
    op.execute("DROP TABLE IF EXISTS risk_regions CASCADE;")
    op.execute("DROP TABLE IF EXISTS river_segments CASCADE;")
    op.execute("DROP TABLE IF EXISTS flood_zones CASCADE;")
