"""
===========================================================================
TERRAIN & ELEVATION INTELLIGENCE ENGINE
===========================================================================

WHY ELEVATION MATTERS FOR FLOOD PREDICTION:
    Traditional weather-only models miss a fundamental truth: water flows
    downhill. Two cities can receive identical rainfall, but the one sitting
    in a low-lying river basin floods while the hilltop city stays dry.

    This module fetches elevation data from the Open-Meteo Elevation API
    (which wraps NASA SRTM 90m resolution data) and computes terrain-derived
    flood susceptibility features:

    1. Elevation (meters above sea level)
       - Lower elevation = higher flood risk
       - Coastal cities (<10m) are extremely vulnerable

    2. Relative Elevation Score
       - How low a location is compared to regional average
       - Normalised 0-1, where 1 = maximum flood susceptibility

    3. Flood Zone Classification
       - CRITICAL: <10m (coastal/delta zones)
       - HIGH:     10-50m (floodplains)
       - MODERATE: 50-200m (transitional)
       - LOW:      >200m (highlands)

DATA SOURCE:
    Open-Meteo Elevation API (free, no API key required)
    Resolution: ~90 meters (NASA SRTM)
    Coverage: Global (60°S to 60°N)
===========================================================================
"""

import requests
import time
from typing import Dict, List, Optional, Tuple
from src.utils.logger import setup_logger

logger = setup_logger("Elevation_Engine")

# Open-Meteo's free elevation API (wraps NASA SRTM 90m data)
ELEVATION_API_URL = "https://api.open-meteo.com/v1/elevation"


def fetch_elevation(lat: float, lon: float, retries: int = 3) -> Optional[float]:
    """
    Fetches the ground elevation in meters for a single coordinate pair
    using NASA SRTM data via Open-Meteo.

    Args:
        lat: Latitude (-60 to 60)
        lon: Longitude (-180 to 180)
        retries: Number of retry attempts on failure

    Returns:
        Elevation in meters above sea level, or None on failure.
    """
    params = {"latitude": lat, "longitude": lon}

    for attempt in range(retries):
        try:
            response = requests.get(ELEVATION_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # The API returns {"elevation": [value]}
            elevation_list = data.get("elevation", [])
            if elevation_list:
                elev = elevation_list[0]
                logger.info(f"Elevation at ({lat}, {lon}): {elev}m")
                return float(elev)
            else:
                logger.warning(f"No elevation data for ({lat}, {lon})")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Elevation fetch failed (attempt {attempt+1}): {e}")
            if attempt < retries - 1:
                time.sleep(2)

    return None


def fetch_elevation_batch(coordinates: List[Tuple[float, float]]) -> Dict[str, float]:
    """
    Fetches elevation for multiple coordinates in a single API call.
    The Open-Meteo API supports comma-separated lat/lon lists.

    Args:
        coordinates: List of (lat, lon) tuples

    Returns:
        Dictionary mapping "lat,lon" strings to elevation values.
    """
    if not coordinates:
        return {}

    lats = ",".join(str(c[0]) for c in coordinates)
    lons = ",".join(str(c[1]) for c in coordinates)

    params = {"latitude": lats, "longitude": lons}

    try:
        response = requests.get(ELEVATION_API_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        elevations = data.get("elevation", [])
        result = {}
        for i, (lat, lon) in enumerate(coordinates):
            key = f"{lat},{lon}"
            if i < len(elevations):
                result[key] = float(elevations[i])
            else:
                result[key] = None

        logger.info(f"Batch elevation fetch: {len(result)} locations processed")
        return result

    except requests.exceptions.RequestException as e:
        logger.error(f"Batch elevation fetch failed: {e}")
        return {}


def fetch_neighborhood_elevations(lat: float, lon: float, radius_km: float = 5.0) -> Dict:
    """
    Fetches elevation for a grid of points around a central location.
    This allows us to compute slope, drainage direction, and whether
    the location sits in a local basin (depression).

    The grid samples 8 surrounding points at the specified radius.

    Args:
        lat: Center latitude
        lon: Center longitude
        radius_km: Sampling radius in kilometers

    Returns:
        Dict with center elevation, surrounding elevations, slope, and basin score.
    """
    # Convert km to approximate degrees (1 degree ≈ 111km at equator)
    delta = radius_km / 111.0

    # 8 cardinal and ordinal directions + center
    sample_points = [
        (lat, lon),                          # Center
        (lat + delta, lon),                  # N
        (lat - delta, lon),                  # S
        (lat, lon + delta),                  # E
        (lat, lon - delta),                  # W
        (lat + delta, lon + delta),          # NE
        (lat + delta, lon - delta),          # NW
        (lat - delta, lon + delta),          # SE
        (lat - delta, lon - delta),          # SW
    ]

    elevations = fetch_elevation_batch(sample_points)
    if not elevations:
        return {"elevation": None, "slope": None, "basin_score": None}

    center_key = f"{lat},{lon}"
    center_elev = elevations.get(center_key)

    if center_elev is None:
        return {"elevation": None, "slope": None, "basin_score": None}

    # Compute surrounding elevations (exclude center)
    surrounding = []
    for point in sample_points[1:]:
        key = f"{point[0]},{point[1]}"
        elev = elevations.get(key)
        if elev is not None:
            surrounding.append(elev)

    if not surrounding:
        return {"elevation": center_elev, "slope": 0.0, "basin_score": 0.0}

    avg_surrounding = sum(surrounding) / len(surrounding)
    max_surrounding = max(surrounding)
    min_surrounding = min(surrounding)

    # Slope: average gradient in degrees (simplified)
    # Positive slope = location is lower than surroundings (water flows IN)
    # Negative slope = location is higher (water flows OUT)
    elevation_diff = avg_surrounding - center_elev
    slope_degrees = elevation_diff / (radius_km * 1000) * 100  # approximate %

    # Basin Score: how much of a "bowl" the location sits in
    # 1.0 = perfect basin (all neighbors higher), 0.0 = hilltop (all neighbors lower)
    neighbors_higher = sum(1 for e in surrounding if e > center_elev)
    basin_score = neighbors_higher / len(surrounding)

    return {
        "elevation": center_elev,
        "avg_surrounding_elevation": round(avg_surrounding, 1),
        "elevation_diff": round(elevation_diff, 1),
        "slope_percent": round(slope_degrees, 3),
        "basin_score": round(basin_score, 3),
        "max_surrounding": max_surrounding,
        "min_surrounding": min_surrounding,
    }


def classify_flood_zone(elevation_m: float) -> str:
    """
    Classifies a location's flood vulnerability based on elevation.

    Real-world context:
        - Major cities like Mumbai (14m), Kolkata (9m), Chennai (6m) sit in
          CRITICAL or HIGH zones.
        - Bengaluru (920m) sits in a LOW zone — elevation alone reduces risk.
    """
    if elevation_m is None:
        return "UNKNOWN"
    if elevation_m < 10:
        return "CRITICAL"
    elif elevation_m < 50:
        return "HIGH"
    elif elevation_m < 200:
        return "MODERATE"
    else:
        return "LOW"


def compute_elevation_risk_score(elevation_m: float, basin_score: float = 0.5) -> float:
    """
    Computes a normalized risk score (0.0 - 1.0) combining absolute
    elevation and local basin topology.

    Formula:
        risk = (elevation_factor * 0.6) + (basin_factor * 0.4)

    Where:
        elevation_factor: Inversely proportional to elevation (capped at 500m)
        basin_factor: Direct basin score (1.0 = deep bowl)
    """
    if elevation_m is None:
        return 0.5  # Unknown = moderate default

    # Elevation factor: lower = riskier. Cap at 500m for normalization.
    capped = min(elevation_m, 500.0)
    elevation_factor = 1.0 - (capped / 500.0)

    # Combined score
    risk = (elevation_factor * 0.6) + (basin_score * 0.4)
    return round(min(max(risk, 0.0), 1.0), 4)


def get_terrain_features(lat: float, lon: float) -> Dict:
    """
    Master function: computes all terrain-derived features for a location.
    This is the main entry point called by the feature engineering pipeline.

    Returns a dictionary of terrain features ready to be merged into the
    ML feature vector.
    """
    logger.info(f"Computing terrain features for ({lat}, {lon})...")

    terrain = fetch_neighborhood_elevations(lat, lon, radius_km=5.0)

    elevation = terrain.get("elevation")
    basin_score = terrain.get("basin_score", 0.5)

    flood_zone = classify_flood_zone(elevation)
    risk_score = compute_elevation_risk_score(elevation, basin_score)

    features = {
        "elevation_m": elevation,
        "slope_percent": terrain.get("slope_percent", 0.0),
        "basin_score": basin_score,
        "elevation_risk_score": risk_score,
        "flood_zone": flood_zone,
        "elevation_diff": terrain.get("elevation_diff", 0.0),
    }

    logger.info(f"Terrain features: elev={elevation}m, zone={flood_zone}, risk={risk_score}")
    return features
