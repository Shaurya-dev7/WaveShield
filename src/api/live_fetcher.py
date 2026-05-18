import requests
import time
from typing import Dict, Any, Optional
from src.utils.logger import setup_logger
from src.config.settings import OPEN_METEO_LIVE_URL, WEATHER_PARAMS

logger = setup_logger("Live_API_Fetcher")

def fetch_live_weather(city: str, lat: float, lon: float, retries: int = 3) -> Optional[Dict[str, Any]]:
    """
    Fetches real-time weather data for a single city.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": ",".join(WEATHER_PARAMS),
        "timezone": "auto"
    }

    for attempt in range(retries):
        try:
            response = requests.get(OPEN_METEO_LIVE_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "current" in data:
                return data["current"]
            else:
                logger.warning(f"Unexpected response structure for {city}: {data}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Live API request failed for {city}: {e}")
            if attempt < retries - 1:
                logger.info(f"Retrying {city} in 5 seconds...")
                time.sleep(5)
            else:
                logger.error(f"Failed to fetch live data for {city} after {retries} attempts.")
                return None
