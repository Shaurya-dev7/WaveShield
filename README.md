# Disaster Alert Pipeline

An automated data collection pipeline for a Multi-Disaster Prediction and Alert System.
This pipeline fetches live weather data for multiple target cities using the Open-Meteo API and stores it in CSV files for future Machine Learning model training.

## Setup

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   python main.py
   ```

## Project Structure
- `data/`: CSV files (generated automatically)
- `logs/`: Application logs (generated automatically)
- `src/config.py`: System configurations (Cities, API params, etc.)
- `src/fetcher.py`: Open-Meteo API integration
- `src/storage.py`: Handles saving logic (pandas, deduplication)
- `src/logger.py`: Logging setup
- `src/scheduler.py`: Scheduling engine
