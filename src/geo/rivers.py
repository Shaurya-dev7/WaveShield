"""
River & Watershed Intelligence
"""

import requests
import math
from typing import Dict, List, Optional, Tuple
from src.utils.logger import setup_logger

logger = setup_logger("River_Intelligence")

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates the great-circle distance between two points on Earth.
    Used to compute the straight-line distance to the nearest river.
    """
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def fetch_nearby_waterways(lat: float, lon: float, radius_m: int = 10000) -> List[Dict]:
    """
    Queries OpenStreetMap for all waterways (rivers, streams, canals, drains)
    within a given radius of a coordinate.

    The Overpass API is the standard free way to query OSM data.

    Args:
        lat: Center latitude
        lon: Center longitude
        radius_m: Search radius in meters (default 10km)

    Returns:
        List of waterway dictionaries with name, type, and coordinates.
    """
    # Overpass QL query: find all 'waterway' elements within radius
    query = f"""
    [out:json][timeout:25];
    (
      way["waterway"~"river|stream|canal|drain"](around:{radius_m},{lat},{lon});
    );
    out center;
    """

    try:
        headers = {"User-Agent": "DisasterAlertApp/1.0 (contact@example.com)"}
        response = requests.post(OVERPASS_URL, data={"data": query}, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        waterways = []
        for element in data.get("elements", []):
            center = element.get("center", {})
            tags = element.get("tags", {})

            if center:
                waterways.append({
                    "name": tags.get("name", "unnamed"),
                    "type": tags.get("waterway", "unknown"),
                    "lat": center.get("lat"),
                    "lon": center.get("lon"),
                })

        logger.info(f"Found {len(waterways)} waterways within {radius_m/1000:.0f}km of ({lat}, {lon})")
        return waterways

    except requests.exceptions.RequestException as e:
        logger.error(f"Overpass API request failed: {e}")
        return []


def compute_river_proximity(lat: float, lon: float, waterways: List[Dict]) -> Dict:
    """
    Computes the distance (km) from the target location to the nearest
    waterway, and calculates river density metrics.

    River Density:
        Number of waterways per km² within the search area.
        Higher density = more drainage channels = faster runoff response.
        (This can be good OR bad — well-drained areas handle rain better,
        but dense river networks near a floodplain amplify overflow risk.)
    """
    if not waterways:
        return {
            "distance_to_nearest_river_km": 99.0,  # Sentinel: no river found
            "nearest_river_name": "none_found",
            "nearest_river_type": "none",
            "river_count_10km": 0,
            "river_density_per_km2": 0.0,
        }

    # Calculate distances to all waterways
    distances = []
    for ww in waterways:
        if ww["lat"] is not None and ww["lon"] is not None:
            dist = _haversine_km(lat, lon, ww["lat"], ww["lon"])
            distances.append((dist, ww))

    if not distances:
        return {
            "distance_to_nearest_river_km": 99.0,
            "nearest_river_name": "none_found",
            "nearest_river_type": "none",
            "river_count_10km": 0,
            "river_density_per_km2": 0.0,
        }

    # Sort by distance
    distances.sort(key=lambda x: x[0])
    nearest_dist, nearest_ww = distances[0]

    # River density: count within 10km, area = π * r²
    search_area_km2 = math.pi * 10 ** 2  # ~314 km²
    river_count = len(distances)
    density = river_count / search_area_km2

    return {
        "distance_to_nearest_river_km": round(nearest_dist, 3),
        "nearest_river_name": nearest_ww["name"],
        "nearest_river_type": nearest_ww["type"],
        "river_count_10km": river_count,
        "river_density_per_km2": round(density, 4),
    }


def compute_river_risk_score(distance_km: float, river_count: int,
                              river_type: str = "river") -> float:
    """
    Computes a normalized river-based flood risk score (0.0 - 1.0).

    Logic:
        - Distance: exponential decay — risk halves every 2km
        - Type: major rivers (river) are riskier than streams/drains
        - Density: more rivers = higher aggregate risk

    A location 200m from a major river gets ~0.95.
    A location 15km from the nearest stream gets ~0.05.
    """
    # Distance factor: exponential decay
    # At 0km = 1.0, at 2km = 0.5, at 5km = 0.18, at 10km = 0.03
    distance_factor = math.exp(-0.35 * distance_km)

    # Type multiplier
    type_multiplier = {
        "river": 1.0,
        "canal": 0.8,
        "stream": 0.6,
        "drain": 0.4,
    }.get(river_type, 0.5)

    # Density bonus: more rivers in the area = amplified risk
    density_bonus = min(river_count / 20.0, 0.3)  # Cap at 0.3 bonus

    risk = (distance_factor * type_multiplier) + density_bonus
    return round(min(max(risk, 0.0), 1.0), 4)


def get_river_features(lat: float, lon: float) -> Dict:
    """
    Master function: computes all river/watershed features for a location.
    Called by the geospatial feature engineering pipeline.

    Returns:
        Flat dictionary of ML-ready river proximity features.
    """
    logger.info(f"Computing river features for ({lat}, {lon})...")

    waterways = fetch_nearby_waterways(lat, lon, radius_m=10000)
    proximity = compute_river_proximity(lat, lon, waterways)

    risk_score = compute_river_risk_score(
        proximity["distance_to_nearest_river_km"],
        proximity["river_count_10km"],
        proximity["nearest_river_type"]
    )

    features = {
        "distance_to_river_km": proximity["distance_to_nearest_river_km"],
        "river_count_10km": proximity["river_count_10km"],
        "river_density_per_km2": proximity["river_density_per_km2"],
        "river_risk_score": risk_score,
    }

    logger.info(
        f"River features: dist={features['distance_to_river_km']:.1f}km, "
        f"count={features['river_count_10km']}, risk={risk_score}"
    )
    return features
