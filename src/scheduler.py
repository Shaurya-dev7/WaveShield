import time
import schedule
from src.config.settings import TARGET_CITIES, COLLECTION_INTERVAL_MINUTES
from src.api.live_fetcher import fetch_live_weather
from src.data.storage import save_to_master
from src.alerts.engine import generate_alerts
from src.utils.logger import setup_logger

logger = setup_logger("Scheduler")

def job():
    """
    Main scheduled job: 
    1. Fetches live weather for all cities.
    2. Saves data to the unified Master Dataset.
    3. Runs the real-time alert engine on the new data.
    """
    logger.info("--- Starting Automated Data Collection & Alert Cycle ---")
    
    for city, coords in TARGET_CITIES.items():
        data = fetch_live_weather(city, coords["lat"], coords["lon"])
        if data:
            # Save to Master CSV
            save_to_master(city, data)
            
            # Prepare data dict for the alert engine
            alert_data = data.copy()
            alert_data['city'] = city
            
            # Trigger Real-Time Alerts
            generate_alerts(alert_data)
            
    logger.info("--- Cycle Complete ---")

def run_scheduler():
    """
    Initializes the recurring job scheduler.
    """
    logger.info(f"System Online. Scheduler running every {COLLECTION_INTERVAL_MINUTES} minutes.")
    
    # Run immediately on startup
    job()
    
    # Schedule the recurring job
    schedule.every(COLLECTION_INTERVAL_MINUTES).minutes.do(job)
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1) # Sleep to avoid 100% CPU usage
    except KeyboardInterrupt:
        logger.info("System gracefully shut down by user.")

if __name__ == "__main__":
    run_scheduler()
