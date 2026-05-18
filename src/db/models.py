"""
===========================================================================
ENTERPRISE SPATIAL DATABASE MODELS — PostGIS + GeoAlchemy2
===========================================================================

WHAT CHANGED FROM THE PREVIOUS MODELS:
    Before: We stored latitude and longitude as plain Float columns.
            Every spatial calculation (distance, containment, overlap)
            ran in Python, which is 100-1000x slower than database-native
            spatial operations.

    After:  We use PostGIS geometry columns via GeoAlchemy2. The database
            itself performs spatial math using GiST-indexed R-tree lookups.

KEY CONCEPTS:

    GEOMETRY vs GEOGRAPHY:
        geometry:   Uses a flat coordinate system (projected). Fast math,
                    but distances are in "coordinate units" not meters.
        geography:  Uses a spherical model of Earth. Slightly slower, but
                    distances are in TRUE meters. Critical for global systems.

        We use geography(POINT, 4326) for all location columns because
        we operate globally and need real-world meter-accurate distances.

    SRID 4326 (EPSG:4326):
        The coordinate reference system used by GPS, Google Maps, and
        virtually all web mapping. Coordinates are (longitude, latitude)
        in degrees. Every location on Earth maps to this system.

    GiST INDEX:
        Generalized Search Tree — a spatial index that organizes geometries
        into a hierarchical bounding-box tree. This turns "find all flood
        zones within 5km of this point" from a full table scan into a
        sub-millisecond indexed lookup.

    POLYGON:
        A closed shape representing an area (flood zone, watershed, city
        boundary). PostGIS stores these natively and can test intersection,
        containment, overlap, and area in SQL.

TABLES:
    weather_data           : Raw weather telemetry (TimescaleDB hypertable)
    engineered_features    : ML feature vectors (TimescaleDB hypertable)
    geospatial_profiles    : Static terrain/river profiles per city
    flood_zones            : Polygon boundaries for flood-prone areas
    river_segments         : Linestring geometries for river networks
    risk_regions           : Dynamic risk polygons (updated by scheduler)
    geospatial_events      : Spatial event log (floods, alerts with geometry)
    predictions            : ML prediction audit trail
    alerts                 : Emergency alert audit trail
===========================================================================
"""

from geoalchemy2 import Geometry, Geography
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, Index,
    CheckConstraint
)
from sqlalchemy.sql import func
from src.db.database import Base


# =====================================================================
# EXISTING TABLES (upgraded with spatial columns)
# =====================================================================

class WeatherData(Base):
    """
    Raw weather telemetry from Open-Meteo. TimescaleDB hypertable.
    Now includes a PostGIS geography column for spatial queries.
    """
    __tablename__ = "weather_data"

    timestamp = Column(DateTime(timezone=True), primary_key=True)
    city = Column(String, primary_key=True, index=True)

    latitude = Column(Float)
    longitude = Column(Float)

    # PostGIS geography point — enables "find all weather readings within
    # 50km of this coordinate" as a single indexed SQL query.
    location = Column(
        Geography(geometry_type='POINT', srid=4326),
        nullable=True
    )

    temperature_2m = Column(Float)
    relative_humidity_2m = Column(Float)
    precipitation = Column(Float)
    rain = Column(Float)
    surface_pressure = Column(Float)
    wind_speed_10m = Column(Float)
    wind_direction_10m = Column(Float)
    cloud_cover = Column(Float)
    soil_temperature_0_to_7cm = Column(Float)
    soil_moisture_0_to_1cm = Column(Float)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class EngineeredFeatures(Base):
    """
    Time-series engineered features for ML. TimescaleDB hypertable.
    Contains both weather-derived and geospatial intelligence features.
    """
    __tablename__ = "engineered_features"

    timestamp = Column(DateTime(timezone=True), primary_key=True)
    city = Column(String, primary_key=True, index=True)

    # Weather-derived features
    temp_change_24h = Column(Float)
    rainfall_last_24h = Column(Float)
    rainfall_last_72h = Column(Float)
    soil_moisture_trend = Column(Float)
    pressure_change_24h = Column(Float)
    wind_speed_change = Column(Float)
    weather_severity_score = Column(Float)

    # Terrain intelligence
    elevation_m = Column(Float)
    slope_percent = Column(Float)
    basin_score = Column(Float)
    elevation_risk_score = Column(Float)

    # River proximity
    distance_to_river_km = Column(Float)
    river_count_10km = Column(Integer)
    river_density_per_km2 = Column(Float)
    river_risk_score = Column(Float)

    # Satellite rainfall
    satellite_precip_24h_mm = Column(Float)
    satellite_precip_72h_mm = Column(Float)
    satellite_max_hourly_mm = Column(Float)
    rainfall_anomaly_score = Column(Float)

    # Flood Susceptibility Index (composite)
    flood_susceptibility_index = Column(Float)
    score_rainfall_intensity = Column(Float)
    score_terrain_elevation = Column(Float)
    score_river_proximity = Column(Float)
    score_soil_saturation = Column(Float)
    score_drainage_quality = Column(Float)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


# =====================================================================
# SPATIAL PROFILE TABLE (upgraded with PostGIS geometry)
# =====================================================================

class GeospatialProfile(Base):
    """
    Static geospatial profile for each monitored location.
    Terrain, river, and flood zone data computed once and cached.

    The 'location' column is a PostGIS POINT that enables spatial
    queries like "find all monitored cities within 100km of an earthquake
    epicenter" using ST_DWithin.
    """
    __tablename__ = "geospatial_profiles"

    city = Column(String, primary_key=True)
    latitude = Column(Float)
    longitude = Column(Float)
    country = Column(String)

    # PostGIS Point (EPSG:4326 = WGS84 = GPS coordinates)
    location = Column(
        Geography(geometry_type='POINT', srid=4326),
        nullable=True
    )

    # Terrain
    elevation_m = Column(Float)
    slope_percent = Column(Float)
    basin_score = Column(Float)
    elevation_risk_score = Column(Float)
    flood_zone = Column(String)

    # River
    distance_to_river_km = Column(Float)
    river_count_10km = Column(Integer)
    river_density_per_km2 = Column(Float)
    river_risk_score = Column(Float)
    nearest_river_name = Column(String)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# =====================================================================
# NEW: FLOOD ZONE POLYGON TABLE
# =====================================================================

class FloodZone(Base):
    """
    Stores flood-prone area boundaries as PostGIS POLYGON geometries.

    Each flood zone is a closed polygon representing an area classified
    by risk level. Sources include:
        - Computed from elevation analysis (areas below 10m near rivers)
        - Imported from government flood maps (GeoJSON/Shapefile)
        - Generated by the floodplain analysis engine

    The 'boundary' column uses geometry (not geography) because
    polygon operations like ST_Area and ST_Intersection are more
    efficient with projected coordinates for large polygons.

    GiST INDEXING:
        The boundary column is automatically indexed by GeoAlchemy2,
        enabling sub-millisecond spatial queries like:
        "Does this coordinate fall inside any flood zone?"
        → SELECT * FROM flood_zones WHERE ST_Contains(boundary, point)
    """
    __tablename__ = "flood_zones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, index=True)
    city = Column(String, index=True)
    country = Column(String)

    # Risk classification
    risk_level = Column(String, nullable=False)  # CRITICAL, HIGH, MODERATE, LOW
    zone_type = Column(String)   # FLOODPLAIN, COASTAL, RIVER_BASIN, URBAN_LOWLAND

    # PostGIS polygon boundary (SRID 4326)
    boundary = Column(
        Geometry(geometry_type='POLYGON', srid=4326),
        nullable=False
    )

    # Metadata
    area_sq_km = Column(Float)
    elevation_min_m = Column(Float)
    elevation_max_m = Column(Float)
    data_source = Column(String)  # "computed", "government", "copernicus"
    description = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # GiST spatial index on boundary (created explicitly for clarity)
    __table_args__ = (
        Index('idx_flood_zones_boundary', 'boundary', postgresql_using='gist'),
        CheckConstraint("risk_level IN ('CRITICAL','HIGH','MODERATE','LOW')", name='chk_fz_risk'),
    )


# =====================================================================
# NEW: RIVER SEGMENT TABLE
# =====================================================================

class RiverSegment(Base):
    """
    Stores river network segments as PostGIS LINESTRING geometries.

    Each row represents a section of a river/stream/canal. Sources:
        - OpenStreetMap Overpass API (existing rivers.py module)
        - HydroRIVERS shapefiles (future integration)

    Spatial queries enabled:
        - ST_DWithin(geom, point, distance): "rivers within 5km of a city"
        - ST_Length(geom): total river length
        - ST_Intersects(geom, polygon): "rivers crossing a flood zone"
    """
    __tablename__ = "river_segments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, index=True)
    waterway_type = Column(String)  # river, stream, canal, drain

    # PostGIS linestring
    geom = Column(
        Geometry(geometry_type='LINESTRING', srid=4326),
        nullable=False
    )

    # Hydrology metadata
    upstream_area_sq_km = Column(Float)
    discharge_m3s = Column(Float)        # Average discharge (m³/s)
    strahler_order = Column(Integer)     # Stream order (1=headwater, 7+=major)
    data_source = Column(String)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_river_segments_geom', 'geom', postgresql_using='gist'),
    )


# =====================================================================
# NEW: DYNAMIC RISK REGION TABLE
# =====================================================================

class RiskRegion(Base):
    """
    Dynamic risk polygons computed by the spatial analysis engine.
    Updated on every scheduler cycle based on current weather + FSI.

    These represent "areas currently at elevated risk" — they change
    hourly as weather conditions evolve. The dashboard renders these
    as animated overlays on the map.

    Unlike FloodZone (static, based on terrain), RiskRegion is dynamic
    and weather-dependent.
    """
    __tablename__ = "risk_regions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), index=True, nullable=False)
    city = Column(String, index=True)

    risk_level = Column(String, nullable=False)
    confidence = Column(Float)
    flood_susceptibility_index = Column(Float)

    # PostGIS polygon for the affected area
    boundary = Column(
        Geometry(geometry_type='POLYGON', srid=4326),
        nullable=False
    )

    area_sq_km = Column(Float)
    population_exposed = Column(Integer)
    trigger_source = Column(String)  # ML_PREDICTION, SATELLITE, HEURISTIC

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_risk_regions_boundary', 'boundary', postgresql_using='gist'),
        Index('idx_risk_regions_time', 'timestamp'),
    )


# =====================================================================
# NEW: GEOSPATIAL EVENT LOG
# =====================================================================

class GeospatialEvent(Base):
    """
    Spatial event log — records every flood alert, satellite detection,
    and ML trigger with its geographic context.

    This is the audit trail for the spatial intelligence system.
    Each event has a location (point) and optionally an affected area
    (polygon), enabling queries like:
        "Show all flood events within 50km of Mumbai in 2026"
    """
    __tablename__ = "geospatial_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), index=True, nullable=False)

    event_type = Column(String, nullable=False, index=True)
    # ML_PREDICTION, SATELLITE_DETECTION, HEURISTIC_ALERT,
    # RAINFALL_ANOMALY, RIVER_OVERFLOW

    severity = Column(String)  # LOW, MODERATE, HIGH, CRITICAL
    city = Column(String, index=True)
    country = Column(String)
    description = Column(Text)

    # Spatial columns
    location = Column(
        Geography(geometry_type='POINT', srid=4326),
        nullable=True
    )
    affected_area = Column(
        Geometry(geometry_type='POLYGON', srid=4326),
        nullable=True
    )

    # Context
    flood_susceptibility_index = Column(Float)
    rainfall_mm = Column(Float)
    confidence = Column(Float)
    model_version = Column(String)

    # Resolution
    resolved = Column(Integer, default=0)
    resolved_at = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_geo_events_location', 'location', postgresql_using='gist'),
        Index('idx_geo_events_area', 'affected_area', postgresql_using='gist'),
    )


# =====================================================================
# EXISTING TABLES (preserved, upgraded with spatial context)
# =====================================================================

class PredictionLog(Base):
    """ML prediction audit trail."""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), index=True)
    city = Column(String, index=True)

    risk_level = Column(String)
    confidence = Column(Float)
    model_version = Column(String, default="xgboost_v1")

    flood_susceptibility_index = Column(Float)
    fsi_risk_class = Column(String)

    # Spatial context
    location = Column(
        Geography(geometry_type='POINT', srid=4326),
        nullable=True
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AlertLog(Base):
    """Emergency alert audit trail."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), index=True)
    city = Column(String, index=True)

    alert_type = Column(String)
    severity = Column(String)
    message = Column(String)
    telegram_delivered = Column(Integer, default=0)

    flood_susceptibility_index = Column(Float)

    # Spatial context
    location = Column(
        Geography(geometry_type='POINT', srid=4326),
        nullable=True
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
