from fastapi import APIRouter, HTTPException
from typing import List
from api.schemas.responses import PredictionResponse, WeatherMetrics
from api.services.ml_service import ml_engine
from api.services.data_service import DataService

router = APIRouter(prefix="/predict", tags=["Predictions"])

@router.get("/{city}", response_model=PredictionResponse)
async def predict_city(city: str):
    """
    Generate an AI prediction for a specific city using the latest weather data.
    """
    feature_dict = DataService.get_latest_features(city)
    if not feature_dict:
        raise HTTPException(status_code=404, detail=f"No data found for city: {city}")
        
    risk_level, confidence = ml_engine.predict_risk(feature_dict)
    
    # Map raw dictionary to Pydantic models for strict validation
    weather = WeatherMetrics(
        temperature_2m=feature_dict.get("temperature_2m", 0.0),
        rainfall_last_24h=feature_dict.get("rainfall_last_24h", 0.0),
        soil_moisture_0_to_1cm=feature_dict.get("soil_moisture_0_to_1cm", 0.0),
        wind_speed_10m=feature_dict.get("wind_speed_10m", 0.0),
        rain=feature_dict.get("rain", 0.0)
    )
    
    return PredictionResponse(
        city=city.capitalize(),
        risk_level=risk_level,
        confidence=confidence,
        timestamp=feature_dict.get("timestamp", "Unknown"),
        weather=weather
    )

@router.get("-all", response_model=List[PredictionResponse])
async def predict_all():
    """
    Batch predict flood risks for all tracked cities.
    Highly optimized for production dashboards.
    """
    latest_rows = DataService.get_all_latest_features()
    if not latest_rows:
        raise HTTPException(status_code=404, detail="No dataset found.")
        
    predictions = []
    for feature_dict in latest_rows:
        city = feature_dict.get("city", "Unknown")
        risk_level, confidence = ml_engine.predict_risk(feature_dict)
        
        weather = WeatherMetrics(
            temperature_2m=feature_dict.get("temperature_2m", 0.0),
            rainfall_last_24h=feature_dict.get("rainfall_last_24h", 0.0),
            soil_moisture_0_to_1cm=feature_dict.get("soil_moisture_0_to_1cm", 0.0),
            wind_speed_10m=feature_dict.get("wind_speed_10m", 0.0),
            rain=feature_dict.get("rain", 0.0)
        )
        
        predictions.append(PredictionResponse(
            city=city.capitalize(),
            risk_level=risk_level,
            confidence=confidence,
            timestamp=feature_dict.get("timestamp", "Unknown"),
            weather=weather
        ))
        
    return predictions
