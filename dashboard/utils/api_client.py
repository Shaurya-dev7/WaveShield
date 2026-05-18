import requests
import streamlit as st
import pandas as pd
from pathlib import Path
import os

API_BASE_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
ENGINEERED_CSV = Path("data/engineered/engineered_master.csv")

@st.cache_data(ttl=30)
def fetch_live_predictions():
    try:
        response = requests.get(f"{API_BASE_URL}/predict-all", timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        pass
    return []

@st.cache_data(ttl=30)
def fetch_alerts():
    try:
        response = requests.get(f"{API_BASE_URL}/alerts", timeout=5)
        if response.status_code == 200:
            return response.json().get("alerts", [])
    except requests.exceptions.RequestException:
        pass
    return []

@st.cache_data(ttl=30)
def fetch_system_health():
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        pass
    return {"status": "offline", "dataset_rows": 0, "uptime": "0h 0m"}

@st.cache_data(ttl=60)
def fetch_historical_data():
    try:
        response = requests.get(f"{API_BASE_URL}/historical", timeout=5)
        if response.status_code == 200:
            data = response.json().get("data", [])
            if data:
                df = pd.DataFrame(data)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                return df.sort_values('timestamp')
    except requests.exceptions.RequestException:
        pass
    return pd.DataFrame()

@st.cache_data(ttl=120)
def fetch_global_risk():
    """Fetches geospatial risk data for all monitored locations."""
    try:
        response = requests.get(f"{API_BASE_URL}/geo/global-risk", timeout=10)
        if response.status_code == 200:
            return response.json().get("locations", [])
    except requests.exceptions.RequestException:
        pass
    return []

@st.cache_data(ttl=120)
def fetch_geo_profile(city: str):
    """Fetches the full geospatial profile for a specific city."""
    try:
        response = requests.get(f"{API_BASE_URL}/geo/profile/{city}", timeout=10)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        pass
    return {}

@st.cache_data(ttl=120)
def fetch_flood_zones():
    """Fetches GeoJSON flood zone data for map rendering."""
    try:
        response = requests.get(f"{API_BASE_URL}/geo/flood-zones", timeout=10)
        if response.status_code == 200:
            return response.json().get("geojson", {})
    except requests.exceptions.RequestException:
        pass
    return {}

# =====================================================================
# POSTGIS SPATIAL INTELLIGENCE API CLIENT
# =====================================================================

@st.cache_data(ttl=60)
def fetch_spatial_risk_map():
    """Fetches GeoJSON FeatureCollection of active risk regions from PostGIS."""
    try:
        response = requests.get(f"{API_BASE_URL}/spatial/risk-map", timeout=10)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        pass
    return {"type": "FeatureCollection", "features": []}

@st.cache_data(ttl=120)
def fetch_spatial_flood_polygons(city: str = None, lat: float = None, lon: float = None):
    """Fetches flood zone polygons from PostGIS."""
    try:
        params = {}
        if city:
            params["city"] = city
        if lat is not None and lon is not None:
            params["lat"] = lat
            params["lon"] = lon
        response = requests.get(f"{API_BASE_URL}/spatial/flood-polygons",
                                params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        pass
    return {"type": "FeatureCollection", "features": []}

@st.cache_data(ttl=120)
def fetch_spatial_rivers(lat: float, lon: float, radius_km: float = 10.0):
    """Fetches nearby river segments from PostGIS as GeoJSON."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/spatial/rivers",
            params={"lat": lat, "lon": lon, "radius_km": radius_km},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        pass
    return {"type": "FeatureCollection", "features": []}

@st.cache_data(ttl=60)
def fetch_nearby_risks(lat: float, lon: float, radius_km: float = 50.0):
    """Fetches comprehensive nearby risk intelligence from PostGIS."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/spatial/nearby-risks",
            params={"lat": lat, "lon": lon, "radius_km": radius_km},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        pass
    return {}

@st.cache_data(ttl=60)
def fetch_spatial_events(hours: int = 72):
    """Fetches recent geospatial events."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/spatial/events",
            params={"hours": hours},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        pass
    return {"events": [], "count": 0}

@st.cache_data(ttl=300)
def fetch_spatial_stats():
    """Fetches aggregate spatial intelligence statistics."""
    try:
        response = requests.get(f"{API_BASE_URL}/spatial/stats", timeout=10)
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException:
        pass
    return {}
