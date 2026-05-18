"""
===========================================================================
GEOSPATIAL FEATURE ENGINEERING PIPELINE
===========================================================================

This is the orchestration layer that calls all geospatial intelligence
modules and produces a unified feature vector for the ML model.

PIPELINE:
    For each monitored location:
    1. Fetch terrain features (elevation, slope, basin)   — CACHED
    2. Fetch satellite rainfall (24h/72h accumulation)    — LIVE
    3. Fetch river proximity (distance, density, risk)    — CACHED
    4. Compute Flood Susceptibility Index                 — LIVE
    5. Merge with existing weather features               — LIVE
    6. Store enriched features in PostgreSQL

CACHING STRATEGY:
    Terrain and river data are STATIC — a city's elevation and distance
    to the nearest river don't change hourly. We compute these once per
    location and cache them in a dictionary (and optionally in the DB).

    Satellite rainfall and weather features are DYNAMIC and must be
    refreshed on every scheduler cycle.

FEATURE VECTOR (added to the existing engineered features):
    - elevation_m
    - slope_percent
    - basin_score
    - elevation_risk_score
    - distance_to_river_km
    - river_count_10km
    - river_density_per_km2
    - river_risk_score
    - satellite_precip_24h_mm
    - satellite_precip_72h_mm
    - satellite_max_hourly_mm
    - rainfall_anomaly_score
    - flood_susceptibility_index
    - score_rainfall_intensity
    - score_terrain_elevation
    - score_river_proximity
    - score_soil_saturation
    - score_drainage_quality
===========================================================================
"""

import json
from pathlib import Path
from typing import Dict, Optional
from src.utils.logger import setup_logger
from src.config.settings import BASE_DIR

logger = setup_logger("Geo_Feature_Pipeline")

# Cache file for static geospatial features (terrain + rivers)
STATIC_CACHE_PATH = BASE_DIR / "data" / "geo_cache.json"

# In-memory cache
_static_cache: Dict[str, Dict] = {}


def _load_cache():
    """Load the static geospatial cache from disk."""
    global _static_cache
    if STATIC_CACHE_PATH.exists():
        try:
            with open(STATIC_CACHE_PATH, "r") as f:
                _static_cache = json.load(f)
            logger.info(f"Loaded geo cache: {len(_static_cache)} locations")
        except Exception as e:
            logger.error(f"Failed to load geo cache: {e}")
            _static_cache = {}


def _save_cache():
    """Persist the static cache to disk."""
    try:
        STATIC_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(STATIC_CACHE_PATH, "w") as f:
            json.dump(_static_cache, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save geo cache: {e}")


def get_static_features(city: str, lat: float, lon: float,
                         force_refresh: bool = False) -> Dict:
    """
    Retrieves or computes the STATIC geospatial features for a location.
    These are terrain and river features that don't change over time.

    On first call for a city, this makes API calls to fetch elevation
    and river data. Subsequent calls return the cached result instantly.

    Args:
        city: City name (used as cache key)
        lat: Latitude
        lon: Longitude
        force_refresh: If True, bypass cache and recompute

    Returns:
        Dictionary of static geospatial features.
    """
    global _static_cache

    if not _static_cache:
        _load_cache()

    cache_key = city.lower().strip()

    if cache_key in _static_cache and not force_refresh:
        logger.info(f"Static geo cache HIT for {city}")
        return _static_cache[cache_key]

    logger.info(f"Static geo cache MISS for {city} — computing...")

    # Import here to avoid circular imports and allow graceful degradation
    from src.geo.elevation import get_terrain_features
    from src.geo.rivers import get_river_features

    terrain = get_terrain_features(lat, lon)
    rivers = get_river_features(lat, lon)

    static_features = {**terrain, **rivers}
    _static_cache[cache_key] = static_features
    _save_cache()

    logger.info(f"Cached static geo features for {city}: {len(static_features)} features")
    return static_features


def get_dynamic_features(lat: float, lon: float) -> Dict:
    """
    Computes DYNAMIC geospatial features that change over time.
    Currently this means satellite rainfall data.

    In production, this runs on every scheduler cycle.
    """
    from src.geo.satellite_rainfall import get_satellite_features
    return get_satellite_features(lat, lon)


def compute_full_geospatial_features(
    city: str,
    lat: float,
    lon: float,
    weather_features: Dict,
    force_refresh_static: bool = False
) -> Dict:
    """
    MASTER FUNCTION: Computes the complete geospatial feature vector
    for a single location by orchestrating all intelligence layers.

    This is called by the scheduler during each ingestion cycle.

    Args:
        city: City name
        lat: Latitude
        lon: Longitude
        weather_features: Current weather data dict (from Open-Meteo)
        force_refresh_static: Recompute terrain/river data

    Returns:
        Complete dictionary of all geospatial features, including
        the Flood Susceptibility Index.
    """
    logger.info(f"Computing full geospatial features for {city}...")

    # 1. Static features (cached)
    static = get_static_features(city, lat, lon, force_refresh_static)

    # 2. Dynamic features (satellite rainfall)
    dynamic = get_dynamic_features(lat, lon)

    # 3. Compute composite Flood Susceptibility Index
    from src.geo.flood_susceptibility import compute_flood_susceptibility_index

    fsi_result = compute_flood_susceptibility_index(
        terrain_features=static,
        satellite_features=dynamic,
        river_features=static,  # River features are part of the static dict
        weather_features=weather_features
    )

    # 4. Merge everything into a flat feature vector
    geo_features = {
        # From static cache
        "elevation_m": static.get("elevation_m"),
        "slope_percent": static.get("slope_percent", 0.0),
        "basin_score": static.get("basin_score", 0.5),
        "elevation_risk_score": static.get("elevation_risk_score", 0.5),
        "distance_to_river_km": static.get("distance_to_river_km", 99.0),
        "river_count_10km": static.get("river_count_10km", 0),
        "river_density_per_km2": static.get("river_density_per_km2", 0.0),
        "river_risk_score": static.get("river_risk_score", 0.3),

        # From dynamic satellite data
        "satellite_precip_24h_mm": dynamic.get("satellite_precip_24h_mm", 0.0),
        "satellite_precip_72h_mm": dynamic.get("satellite_precip_72h_mm", 0.0),
        "satellite_max_hourly_mm": dynamic.get("satellite_max_hourly_mm", 0.0),
        "rainfall_anomaly_score": dynamic.get("rainfall_anomaly_score", 0.0),

        # From composite FSI
        "flood_susceptibility_index": fsi_result["flood_susceptibility_index"],
        "fsi_risk_class": fsi_result["fsi_risk_class"],
        "score_rainfall_intensity": fsi_result["score_rainfall_intensity"],
        "score_terrain_elevation": fsi_result["score_terrain_elevation"],
        "score_river_proximity": fsi_result["score_river_proximity"],
        "score_soil_saturation": fsi_result["score_soil_saturation"],
        "score_drainage_quality": fsi_result["score_drainage_quality"],
    }

    logger.info(
        f"Geospatial features complete for {city}: "
        f"FSI={fsi_result['flood_susceptibility_index']:.3f} "
        f"({fsi_result['fsi_risk_class']})"
    )

    return geo_features
