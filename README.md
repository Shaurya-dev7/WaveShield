# 🌊 WaveShield – Multi-Disaster Prediction & Alert System

<div align="center">

[![Python](https://img.shields.io/badge/Python-77%25-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Jupyter](https://img.shields.io/badge/Jupyter-21.3%25-F37726?style=for-the-badge&logo=jupyter&logoColor=white)](https://jupyter.org/)
[![ML/AI](https://img.shields.io/badge/Machine_Learning-Disaster_Prediction-FF6B6B?style=for-the-badge&logo=tensorflow&logoColor=white)](/features)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

**Real-time disaster prediction system** with automated data collection, multi-location weather monitoring, and machine learning-powered alert generation.

*Monitor Global Weather. Predict Disasters. Save Lives.* – Early warning system powered by real-time data intelligence.

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [System Architecture](#system-architecture)
- [Data Pipeline](#data-pipeline)
- [Disaster Predictions](#disaster-predictions)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

**WaveShield** is a comprehensive multi-disaster prediction and alert system that leverages real-time global weather data to generate early warnings for natural disasters including hurricanes, floods, earthquakes, and severe storms.

The system operates as an intelligent data collection pipeline that:
- Fetches live weather data for multiple target cities
- Stores data in time-series optimized CSV format
- Trains machine learning models on historical patterns
- Generates real-time disaster predictions and alerts

### Why WaveShield?

- 🌍 **Global Monitoring** - Track weather in 100+ cities worldwide
- ⚡ **Real-Time Data** - Hourly weather updates via Open-Meteo API
- 🤖 **ML-Powered** - Advanced prediction models for disaster detection
- 📊 **Data-Driven** - Historical data collection for pattern learning
- 🚨 **Early Alerts** - Timely warnings before disasters strike
- 🔓 **Open Source** - Transparent, auditable disaster prediction
- 📦 **Containerized** - Docker support for easy deployment

---

## ✨ Features

### Data Collection & Management
- 🌐 **Multi-City Monitoring** - Track weather in 100+ target cities
- 📡 **Real-Time Data Fetching** - Hourly API calls to Open-Meteo
- 💾 **Intelligent Storage** - Optimized CSV format with deduplication
- 📈 **Time-Series Data** - Historical data for ML model training
- 🔄 **Automated Scheduler** - Continuous background data collection
- 🔍 **Data Validation** - Quality checks and anomaly detection
- 📉 **Data Aggregation** - Multi-source weather data consolidation

### Machine Learning & Analysis
- 🧠 **Predictive Models** - Neural networks for disaster prediction
- 📊 **Pattern Recognition** - Identify disaster precursor patterns
- 🎯 **Ensemble Methods** - Multiple ML models for accuracy
- 📉 **Trend Analysis** - Detect dangerous weather trends
- ⚖️ **Risk Scoring** - Quantify disaster probability
- 🔮 **Forecasting** - Multi-day ahead predictions

### Alert & Notification System
- 🚨 **Multi-Level Alerts** - Critical, High, Medium, Low severity
- 📱 **Multi-Channel Alerts** - Email, SMS, Push notifications
- 🗺️ **Geo-Targeted Alerts** - Location-specific warnings
- ⏰ **Smart Timing** - Alerts sent at optimal times
- 📋 **Alert History** - Track all predictions and alerts
- 👥 **User Subscriptions** - Customizable alert preferences

### Visualization & Analytics
- 📊 **Interactive Dashboards** - Real-time weather visualization
- 🗺️ **Global Heat Maps** - Disaster risk heat maps
- 📈 **Analytics Reports** - Comprehensive system analytics
- 🎨 **Data Visualization** - Beautiful charts and graphs
- 📉 **Historical Analysis** - Pattern trends over time

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Data Collection** | Python 3.9+, Requests | API integration |
| **Weather API** | Open-Meteo | Real-time weather data |
| **Data Storage** | Pandas, CSV | Time-series storage |
| **Scheduling** | APScheduler | Automated task scheduling |
| **Machine Learning** | scikit-learn, TensorFlow | Prediction models |
| **Notebooks** | Jupyter (21.3%) | Model development & analysis |
| **Containerization** | Docker (1.1%) | Easy deployment |
| **Logging** | Python logging | System monitoring |

---

## 📊 Monitored Weather Parameters

| Parameter | Description | Units |
|-----------|-------------|-------|
| **Temperature** | Current, min, max | °C / °F |
| **Humidity** | Relative humidity | % |
| **Precipitation** | Rainfall amount | mm |
| **Wind Speed** | Current wind speed | km/h |
| **Wind Direction** | Wind direction | Degrees |
| **Pressure** | Atmospheric pressure | hPa |
| **Cloud Cover** | Cloud coverage | % |
| **Visibility** | Atmospheric visibility | km |
| **UV Index** | UV radiation intensity | - |
| **Feels Like** | Apparent temperature | °C |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- ~2GB disk space for data
- Internet connection
- Docker (optional, for containerization)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Shaurya-dev7/WaveShield.git
   cd WaveShield
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure system**
   ```bash
   cp config_template.yaml config.yaml
   # Edit config.yaml with your target cities and preferences
   ```

5. **Run the system**
   ```bash
   python main.py
   ```

### Docker Deployment

```bash
# Build Docker image
docker build -t waveshield:latest .

# Run container
docker run -d \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --name waveshield \
  waveshield:latest

# View logs
docker logs -f waveshield
```

---

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────┐
│         Open-Meteo Weather API                  │
│  (Global real-time weather data provider)       │
└──────────────────┬──────────────────────────────┘
                   │
         ┌─────────▼─────────┐
         │  Data Fetcher     │
         │ (requests module) │
         └─────────┬─────────┘
                   │
         ┌─────────▼──────────┐
         │  Data Validator    │
         │ (quality checks)   │
         └─────────┬──────────┘
                   │
         ┌─────────▼──────────────────┐
         │  Storage Engine            │
         │ (pandas + CSV format)      │
         │ (deduplication)            │
         └─────────┬──────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
    ┌───▼────┐        ┌──────▼────┐
    │ CSV    │        │ Historical│
    │Files   │        │ Data DB   │
    └────────┘        └───────────┘
        │
    ┌───▼──────────────────────┐
    │ ML Model Training         │
    │ (Jupyter Notebooks)       │
    │ (scikit-learn, TensorFlow)│
    └───┬──────────────────────┘
        │
    ┌───▼────────────────────┐
    │ Prediction Engine       │
    │ (Disaster Detection)    │
    └───┬────────────────────┘
        │
    ┌───▼──────────────────��─┐
    │ Alert Generation       │
    │ (Multi-channel)        │
    └────────────────────────┘
```

### Data Flow Pipeline

```
Schedule Trigger (Hourly)
        │
        ▼
Fetch Weather Data
        │
        ▼
Validate Data Quality
        │
        ▼
Check for Duplicates
        │
        ▼
Transform & Normalize
        │
        ▼
Append to CSV File
        │
        ▼
Update Time-Series DB
        │
        ▼
Run Prediction Models
        │
        ▼
Generate Risk Scores
        │
        ▼
Check Alert Thresholds
        │
        ▼
Send Alerts (if needed)
        │
        ▼
Log Operations
```

---

## 📁 Project Structure

```
WaveShield/
├── src/
│   ├── __init__.py
│   ├── config.py               # System configuration
│   ├── fetcher.py              # Open-Meteo API integration
│   ├── storage.py              # Data storage logic (pandas, CSV)
│   ├── logger.py               # Logging configuration
│   ├── scheduler.py            # Task scheduling engine
│   ├── data_validator.py       # Data quality validation
│   ├── ml_models.py            # ML prediction models
│   ├── alert_generator.py      # Alert generation logic
│   └── utils.py                # Helper functions
├── notebooks/
│   ├── exploratory_analysis.ipynb      # Data exploration
│   ├── model_training.ipynb             # ML model development
│   ├── disaster_pattern_analysis.ipynb  # Pattern discovery
│   └── forecast_validation.ipynb        # Model validation
├── data/
│   ├── weather_data/           # CSV files (auto-generated)
│   │   ├── city_1_data.csv
│   │   ├── city_2_data.csv
│   │   └── ...
│   └── models/                 # Trained ML models
├── logs/
│   └── waveshield.log          # Application logs (auto-generated)
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── config_template.yaml        # Configuration template
├── Dockerfile                  # Docker containerization
└── README.md                   # This file
```

---

## ⚙️ Configuration

### Edit `config.yaml`

```yaml
# Target cities for monitoring
cities:
  - name: "New York"
    latitude: 40.7128
    longitude: -74.0060
  - name: "Los Angeles"
    latitude: 34.0522
    longitude: -118.2437
  - name: "Tokyo"
    latitude: 35.6762
    longitude: 139.6503
  # Add more cities...

# API settings
api:
  base_url: "https://api.open-meteo.com/v1/forecast"
  timeout: 30  # seconds

# Scheduling
scheduler:
  fetch_interval: 3600  # seconds (1 hour)
  model_retrain_interval: 86400  # seconds (24 hours)

# Storage
storage:
  data_dir: "./data/weather_data"
  retention_days: 365  # Keep 1 year of data
  batch_size: 100  # Rows per batch

# ML Models
ml:
  model_type: "ensemble"  # or "neural_network"
  disaster_types:
    - "hurricane"
    - "flood"
    - "storm"
    - "earthquake"
  prediction_horizon: 7  # days ahead

# Alerts
alerts:
  channels:
    - "email"
    - "sms"
    - "push"
  severity_levels:
    critical: 0.9
    high: 0.75
    medium: 0.5
    low: 0.3

# Logging
logging:
  level: "INFO"
  log_file: "./logs/waveshield.log"
  max_size: "10MB"
```

---

## 📊 Data Collection

### Weather Data Schema

```python
{
    'timestamp': datetime,           # UTC time
    'city': str,                     # City name
    'latitude': float,               # Location latitude
    'longitude': float,              # Location longitude
    'temperature': float,            # °C
    'humidity': float,               # %
    'precipitation': float,          # mm
    'wind_speed': float,             # km/h
    'wind_direction': float,         # degrees
    'pressure': float,               # hPa
    'cloud_cover': float,            # %
    'visibility': float,             # km
    'uv_index': float,               # -
    'feels_like': float,             # °C
    'weather_code': int,             # WMO code
}
```

### Sample CSV Format

```
timestamp,city,latitude,longitude,temperature,humidity,precipitation,wind_speed,wind_direction,pressure,cloud_cover,visibility,uv_index,feels_like,weather_code
2024-01-15T12:00Z,New York,40.7128,-74.0060,5.2,65,0.0,15.4,230,1013.2,45,10.0,1.5,2.1,1
2024-01-15T13:00Z,New York,40.7128,-74.0060,6.1,60,0.0,16.2,235,1013.5,50,10.5,1.8,3.2,1
```

---

## 🤖 Machine Learning Models

### Model Types

#### 1. **Ensemble Model** (Recommended)
- Combines multiple algorithms
- Better accuracy and robustness
- Voting mechanism for predictions

#### 2. **Neural Network Model**
- Deep learning approach
- LSTM for time-series
- Best for complex patterns

#### 3. **Gradient Boosting Model**
- XGBoost/LightGBM
- Fast training and inference
- Feature importance analysis

### Training Pipeline

```python
from src.ml_models import DisasterPredictor

# Initialize predictor
predictor = DisasterPredictor(model_type='ensemble')

# Load historical data
data = pd.read_csv('data/historical_weather.csv')

# Train models
predictor.train(data, disaster_types=['hurricane', 'flood', 'storm'])

# Save models
predictor.save_models('data/models/')

# Make predictions
risk_scores = predictor.predict(current_weather_data)
```

---

## 🚨 Disaster Predictions

### Supported Disaster Types

| Disaster | Indicators | Lead Time |
|----------|-----------|-----------|
| **Hurricane** | Wind speed, pressure, temp | 3-7 days |
| **Flood** | Precipitation, humidity, pressure | 1-3 days |
| **Severe Storm** | Cloud cover, wind, pressure | 6-24 hours |
| **Tornado** | Wind shear, humidity, pressure | 2-12 hours |
| **Drought** | Temperature, precipitation, humidity | 1-4 weeks |
| **Landslide** | Precipitation, soil data | 1-7 days |

### Risk Scoring System

```
Risk Score = Σ(weight_i × indicator_i) / Σ(weight_i)

Where:
- Risk Score ∈ [0, 1]
- 0.0-0.3 = Low Risk
- 0.3-0.6 = Medium Risk
- 0.6-0.8 = High Risk
- 0.8-1.0 = Critical Risk
```

---

## 📈 Analytics & Monitoring

### System Metrics

```bash
# View system health
python -c "from src import metrics; metrics.print_system_health()"

# Generate report
python src/analytics.py --report daily --output report.pdf
```

### Jupyter Notebooks

Run analysis in Jupyter:

```bash
jupyter notebook

# Available notebooks:
# - exploratory_analysis.ipynb: Data exploration and visualization
# - model_training.ipynb: ML model development
# - disaster_pattern_analysis.ipynb: Pattern discovery
# - forecast_validation.ipynb: Model accuracy validation
```

---

## 🧪 Testing

### Run Unit Tests

```bash
# All tests
python -m pytest tests/ -v

# Specific module
python -m pytest tests/test_fetcher.py -v

# With coverage
python -m pytest tests/ --cov=src
```

### Integration Testing

```bash
# Test full pipeline
python tests/test_integration.py

# Test API integration
python tests/test_api_integration.py
```

---

## 🔄 Continuous Operation

### System Monitoring

```bash
# Start with systemd
systemctl start waveshield
systemctl status waveshield

# Or use supervisor
supervisord -c supervisord.conf

# Or screen/tmux
screen -S waveshield
python main.py
```

### Performance Monitoring

```bash
# Monitor resource usage
python -c "from src import monitor; monitor.start_monitoring()"

# View metrics dashboard
python src/dashboard.py
```

---

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

1. **Model Improvements**
   - New disaster prediction algorithms
   - Improved accuracy on existing models
   - Real-time model updates

2. **Feature Additions**
   - New weather parameters
   - Additional disaster types
   - Multi-language support

3. **Data Sources**
   - Additional weather APIs
   - Satellite imagery integration
   - Seismic data integration

4. **Infrastructure**
   - Distributed computing
   - Cloud deployment optimization
   - Database optimization

### Steps to Contribute

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/NewModel`
3. Make changes and test: `pytest tests/`
4. Commit: `git commit -m 'Add: New disaster prediction model'`
5. Push: `git push origin feature/NewModel`
6. Open a Pull Request

---

## 📝 License

This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.

---

## 👨‍💻 Author

**Shaurya Deep Rai** - AI/ML & Data Science Engineer

- GitHub: [@Shaurya-dev7](https://github.com/Shaurya-dev7)

---

## 🙏 Acknowledgments

- [Open-Meteo](https://open-meteo.com/) - Free weather API
- [pandas](https://pandas.pydata.org/) - Data manipulation
- [scikit-learn](https://scikit-learn.org/) - Machine learning
- [TensorFlow](https://www.tensorflow.org/) - Deep learning
- All contributors and researchers

---

## 📚 References

- [Open-Meteo API Documentation](https://open-meteo.com/en/docs)
- [scikit-learn User Guide](https://scikit-learn.org/stable/user_guide.html)
- [TensorFlow Documentation](https://www.tensorflow.org/guide)
- [Disaster Prediction Research](https://scholar.google.com/)

---

<div align="center">

### ⭐ If you find this project helpful, please consider giving it a star!

**[🚀 Get Started](#-quick-start)** • **[📊 Data Pipeline](#data-pipeline)** • **[🐛 Report Issue](https://github.com/Shaurya-dev7/WaveShield/issues)**

</div>
