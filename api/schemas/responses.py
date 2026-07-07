from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    dataset_rows: int
    uptime: str
    timestamp: str

class WeatherMetrics(BaseModel):
    temperature_2m: float
    rainfall_last_24h: float
    soil_moisture_0_to_1cm: float
    wind_speed_10m: float
    rain: float

class PredictionResponse(BaseModel):
    city: str
    risk_level: str
    confidence: float
    timestamp: str
    weather: WeatherMetrics
    model_version: str
    prediction_timestamp: str
    data_source: str

class AlertResponse(BaseModel):
    city: str
    risk_level: str
    confidence: float
    timestamp: str
    message: str

class ModelInfoResponse(BaseModel):
    version: str
    algorithm: str
    features_used: List[str]
    dataset_size: int
