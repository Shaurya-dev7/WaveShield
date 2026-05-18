import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
ENGINEERED_DIR = DATA_DIR / "engineered"
ALERTS_DIR = DATA_DIR / "alerts"
LOG_DIR = BASE_DIR / "logs"

# Ensure directories exist
for d in [RAW_DIR, PROCESSED_DIR, ENGINEERED_DIR, ALERTS_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# API Configuration
OPEN_METEO_LIVE_URL = os.getenv("OPEN_METEO_LIVE_URL", "https://api.open-meteo.com/v1/forecast")
OPEN_METEO_HISTORICAL_URL = os.getenv("OPEN_METEO_HISTORICAL_URL", "https://archive-api.open-meteo.com/v1/archive")

# Target Cities with their Lat/Lon
TARGET_CITIES = {
    "Mumbai": {"lat": 19.0760, "lon": 72.8777},
    "Delhi": {"lat": 28.7041, "lon": 77.1025},
    "Chennai": {"lat": 13.0827, "lon": 80.2707},
    "Kolkata": {"lat": 22.5726, "lon": 88.3639},
    "Bengaluru": {"lat": 12.9716, "lon": 77.5946}
}

# Parameters to fetch
WEATHER_PARAMS = [
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "rain",
    "surface_pressure",
    "wind_speed_10m",
    "wind_direction_10m",
    "cloud_cover",
    "soil_temperature_0cm",
    "soil_moisture_0_to_1cm"
]

# Collection Configuration
COLLECTION_INTERVAL_MINUTES = int(os.getenv("COLLECTION_INTERVAL_MINUTES", 60))

# Master Dataset Path
MASTER_DATASET_PATH = RAW_DIR / os.getenv("MASTER_DATASET_FILE", "weather_master.csv")

# Alert Thresholds (Configurable)
ALERT_THRESHOLDS = {
    "heavy_rainfall_mm": 50.0, # mm per hour
    "flood_risk_soil_moisture": 0.5, # m3/m3
    "high_wind_speed_kmh": 60.0, # km/h
    "heatwave_temp_c": 45.0 # Celsius
}
