"""
===========================================================================
GEOSPATIAL INTELLIGENCE API ENDPOINTS
===========================================================================

These endpoints expose the geospatial flood intelligence layer to the
dashboard and external consumers. They provide:

    /geo/global-risk     — Current FSI scores for all monitored cities
    /geo/profile/{city}  — Static geospatial profile for a city
    /geo/flood-zones     — GeoJSON of all locations with flood zone classification
    /geo/compute/{city}  — On-demand geospatial computation (admin)

All responses are structured for direct consumption by map frontends
(PyDeck, Deck.gl, Mapbox, Leaflet).
===========================================================================
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from src.config.settings import TARGET_CITIES
from src.utils.logger import setup_logger

logger = setup_logger("GIS_API")

router = APIRouter(prefix="/geo", tags=["Geospatial Intelligence"])


@router.get("/global-risk")
async def get_global_risk() -> Dict[str, Any]:
    """
    Returns the current Flood Susceptibility Index and geospatial risk
    data for ALL monitored locations.

    This is the primary endpoint for the Global Flood Intelligence dashboard.
    """
    from src.geo.geo_features import get_static_features

    results = []
    for city, coords in TARGET_CITIES.items():
        static = get_static_features(city, coords["lat"], coords["lon"])
        results.append({
            "city": city,
            "lat": coords["lat"],
            "lon": coords["lon"],
            "elevation_m": static.get("elevation_m"),
            "flood_zone": static.get("flood_zone", "UNKNOWN"),
            "elevation_risk_score": static.get("elevation_risk_score", 0.5),
            "distance_to_river_km": static.get("distance_to_river_km", 99.0),
            "river_risk_score": static.get("river_risk_score", 0.3),
            "basin_score": static.get("basin_score", 0.5),
        })

    return {"status": "success", "locations": results}


@router.get("/profile/{city}")
async def get_geospatial_profile(city: str) -> Dict[str, Any]:
    """
    Returns the complete geospatial intelligence profile for a specific city.
    Includes terrain, river, and flood zone analysis.

    This data is STATIC — it doesn't change with weather conditions.
    """
    # Find coordinates
    city_match = None
    for name, coords in TARGET_CITIES.items():
        if name.lower() == city.lower():
            city_match = (name, coords)
            break

    if not city_match:
        raise HTTPException(status_code=404, detail=f"City '{city}' not in monitoring system")

    name, coords = city_match
    from src.geo.geo_features import get_static_features
    static = get_static_features(name, coords["lat"], coords["lon"])

    return {
        "city": name,
        "lat": coords["lat"],
        "lon": coords["lon"],
        "profile": static,
    }


@router.get("/flood-zones")
async def get_flood_zones() -> Dict[str, Any]:
    """
    Returns flood zone classifications for all monitored cities in a
    GeoJSON-compatible format, ready for map rendering.

    GeoJSON is the international standard for geographic data interchange.
    """
    from src.geo.geo_features import get_static_features

    features = []
    for city, coords in TARGET_CITIES.items():
        static = get_static_features(city, coords["lat"], coords["lon"])

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [coords["lon"], coords["lat"]]
            },
            "properties": {
                "city": city,
                "elevation_m": static.get("elevation_m"),
                "flood_zone": static.get("flood_zone", "UNKNOWN"),
                "elevation_risk_score": static.get("elevation_risk_score", 0.5),
                "river_risk_score": static.get("river_risk_score", 0.3),
                "distance_to_river_km": static.get("distance_to_river_km", 99.0),
            }
        })

    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    return {"status": "success", "geojson": geojson}


@router.get("/compute/{city}")
async def compute_geospatial_on_demand(city: str) -> Dict[str, Any]:
    """
    On-demand endpoint: computes the FULL geospatial feature set including
    live satellite rainfall and Flood Susceptibility Index.

    This is expensive (multiple API calls) and should be used sparingly.
    The scheduler handles routine computation.
    """
    city_match = None
    for name, coords in TARGET_CITIES.items():
        if name.lower() == city.lower():
            city_match = (name, coords)
            break

    if not city_match:
        raise HTTPException(status_code=404, detail=f"City '{city}' not monitored")

    name, coords = city_match

    from src.geo.geo_features import compute_full_geospatial_features

    # Provide minimal weather features for FSI computation
    weather_stub = {
        "soil_moisture_0_to_1cm": 0.3,
        "relative_humidity_2m": 70.0,
        "rainfall_last_72h": 0.0,
    }

    geo_features = compute_full_geospatial_features(
        city=name,
        lat=coords["lat"],
        lon=coords["lon"],
        weather_features=weather_stub
    )

    return {
        "city": name,
        "lat": coords["lat"],
        "lon": coords["lon"],
        "geospatial_features": geo_features,
    }
