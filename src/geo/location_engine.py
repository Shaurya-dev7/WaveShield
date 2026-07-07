"""
===========================================================================
GLOBAL LOCATION ENGINE — DYNAMIC CITY GEOCODING & MANAGEMENT
===========================================================================

This module replaces the hardcoded TARGET_CITIES dictionary with a dynamic
system that can:
    1. Geocode any city name to lat/lon using the free Nominatim API
    2. Cache results in PostgreSQL to avoid repeated lookups
    3. Support adding/removing monitored locations via API
    4. Provide worldwide coordinate support

This is the foundation for scaling from 5 Indian cities to hundreds
of global locations.

DATA SOURCE:
    OpenStreetMap Nominatim (free, rate-limited to 1 request/second)
===========================================================================
"""

import requests
import time
from typing import Dict, List, Optional, Tuple
from src.utils.logger import setup_logger

logger = setup_logger("Location_Engine")

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OPENMETEO_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"

# In-memory cache to avoid hammering Nominatim
_geocode_cache: Dict[str, Dict] = {}


def geocode_city(city_name: str, country: str = "") -> Optional[Dict]:
    """
    Converts a city name to lat/lon coordinates using Open-Meteo Geocoding
    with a fallback to OpenStreetMap Nominatim.

    Args:
        city_name: Human-readable city name (e.g., "Mumbai", "Tokyo")
        country: Optional country code for disambiguation (e.g., "IN", "JP")

    Returns:
        Dict with lat, lon, display_name, or None if not found.
    """
    cache_key = f"{city_name}_{country}".lower()
    if cache_key in _geocode_cache:
        return _geocode_cache[cache_key]

    # --- PRIMARY: Open-Meteo Geocoding ---
    try:
        om_params = {
            "name": city_name,
            "count": 1,
            "language": "en",
            "format": "json"
        }
        om_resp = requests.get(OPENMETEO_GEOCODE_URL, params=om_params, timeout=10)
        om_resp.raise_for_status()
        om_data = om_resp.json()
        
        if "results" in om_data and len(om_data["results"]) > 0:
            result = om_data["results"][0]
            # Verify country if provided
            if not country or country.lower() in result.get("country", "").lower() or country.lower() in result.get("country_code", "").lower():
                location = {
                    "city": city_name,
                    "lat": float(result["latitude"]),
                    "lon": float(result["longitude"]),
                    "display_name": f"{result.get('name', city_name)}, {result.get('country', 'Unknown')}",
                    "country": result.get("country", "Unknown"),
                    "country_code": result.get("country_code", ""),
                }
                _geocode_cache[cache_key] = location
                logger.info(f"Open-Meteo Geocoded '{city_name}' → ({location['lat']}, {location['lon']})")
                return location
    except Exception as e:
        logger.warning(f"Open-Meteo geocoding failed for '{city_name}': {e}. Falling back to Nominatim.")
    
    # --- SECONDARY: Nominatim OpenStreetMap ---
    logger.info(f"Attempting Nominatim fallback for '{city_name}'")
    query = f"{city_name}, {country}" if country else city_name

    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
    }

    headers = {
        "User-Agent": "DisasterIntelPlatform/2.0 (research project)"
    }

    try:
        # Nominatim requires 1 request per second
        time.sleep(1.1)
        response = requests.get(NOMINATIM_URL, params=params,
                                headers=headers, timeout=10)
        response.raise_for_status()
        results = response.json()

        if not results:
            logger.warning(f"Nominatim Geocoding failed: '{city_name}' not found")
            return None

        result = results[0]
        location = {
            "city": city_name,
            "lat": float(result["lat"]),
            "lon": float(result["lon"]),
            "display_name": result.get("display_name", city_name),
            "country": result.get("address", {}).get("country", "Unknown"),
            "country_code": result.get("address", {}).get("country_code", ""),
        }

        _geocode_cache[cache_key] = location
        logger.info(f"Nominatim Geocoded '{city_name}' → ({location['lat']}, {location['lon']})")
        return location

    except requests.exceptions.RequestException as e:
        logger.error(f"Nominatim Geocoding request failed: {e}")
        return None


def geocode_batch(cities: List[str], country: str = "") -> List[Dict]:
    """
    Geocodes multiple cities. Respects Nominatim rate limits.
    """
    results = []
    for city in cities:
        result = geocode_city(city, country)
        if result:
            results.append(result)
    return results


def get_expanded_city_registry() -> Dict[str, Dict]:
    """
    Returns an expanded city registry that combines the hardcoded
    TARGET_CITIES with any dynamically-added locations.

    This function is called by the scheduler to determine which
    locations to monitor.
    """
    from src.config.settings import TARGET_CITIES

    # Start with existing hardcoded cities
    registry = {}
    for city_name, coords in TARGET_CITIES.items():
        registry[city_name] = {
            "lat": coords["lat"],
            "lon": coords["lon"],
            "country": "India",
            "source": "hardcoded",
        }

    # In a production system, we'd also query the database for
    # dynamically-added locations here. For now, we extend with
    # additional high-risk global cities.

    global_flood_hotspots = {
        "Dhaka": {"lat": 23.8103, "lon": 90.4125, "country": "Bangladesh"},
        "Bangkok": {"lat": 13.7563, "lon": 100.5018, "country": "Thailand"},
        "Jakarta": {"lat": -6.2088, "lon": 106.8456, "country": "Indonesia"},
        "Ho Chi Minh City": {"lat": 10.8231, "lon": 106.6297, "country": "Vietnam"},
        "Manila": {"lat": 14.5995, "lon": 120.9842, "country": "Philippines"},
        "Lagos": {"lat": 6.5244, "lon": 3.3792, "country": "Nigeria"},
        "Houston": {"lat": 29.7604, "lon": -95.3698, "country": "USA"},
    }

    for city_name, info in global_flood_hotspots.items():
        if city_name not in registry:
            registry[city_name] = {
                "lat": info["lat"],
                "lon": info["lon"],
                "country": info.get("country", "Unknown"),
                "source": "global_hotspot",
            }

    return registry
