import requests
import time
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
from src.utils.logger import setup_logger
from src.config.settings import OPEN_METEO_HISTORICAL_URL, WEATHER_PARAMS, TARGET_CITIES
from src.data.storage import save_to_master

logger = setup_logger("Historical_API_Fetcher")

def fetch_historical_weather(city: str, start_date: str, end_date: str, retries: int = 3) -> Optional[pd.DataFrame]:
    """
    Fetches historical weather data for a city within a date range.
    Open-Meteo returns historical data in an 'hourly' array.
    """
    lat = TARGET_CITIES[city]["lat"]
    lon = TARGET_CITIES[city]["lon"]

    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": ",".join(WEATHER_PARAMS),
        "timezone": "auto"
    }

    for attempt in range(retries):
        try:
            logger.info(f"Fetching historical data for {city} from {start_date} to {end_date}...")
            response = requests.get(OPEN_METEO_HISTORICAL_URL, params=params, timeout=30)
            
            # Catch Rate Limits (Open-Meteo allows ~10k calls/day free, but bulk is heavy)
            if response.status_code == 429:
                logger.warning("Rate limit hit! Sleeping for 60 seconds...")
                time.sleep(60)
                continue
                
            response.raise_for_status()
            data = response.json()
            
            if "hourly" in data:
                logger.info(f"Successfully fetched historical data for {city}.")
                
                # Convert the 'hourly' dictionary of lists into a DataFrame
                df = pd.DataFrame(data["hourly"])
                return df
            else:
                logger.warning(f"Unexpected historical response structure for {city}: {data}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Historical API request failed for {city}: {e}")
            if attempt < retries - 1:
                logger.info(f"Retrying {city} in 10 seconds...")
                time.sleep(10)
            else:
                logger.error(f"Failed to fetch historical data for {city} after {retries} attempts.")
                return None

def backfill_historical_data(start_date: str, end_date: str):
    """
    Utility function to download and save historical data for all target cities.
    This prepares the Master Dataset for Machine Learning.
    """
    logger.info(f"Starting Historical Data Backfill from {start_date} to {end_date}")
    
    for city in TARGET_CITIES.keys():
        df = fetch_historical_weather(city, start_date, end_date)
        if df is not None:
            # We iterate through the rows and save to master dataset
            # (In a truly massive scenario, we would write the dataframe in chunks)
            records = df.to_dict(orient='records')
            for record in records:
                save_to_master(city, record)
        
        # Sleep to be polite to the free API
        time.sleep(2)
        
    logger.info("Historical Data Backfill Complete.")
