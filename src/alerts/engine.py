import pandas as pd
from datetime import datetime
from src.config.settings import ALERT_THRESHOLDS, ALERTS_DIR
from src.utils.logger import setup_logger

logger = setup_logger("Alert_Engine")

def evaluate_disaster_risk(row: pd.Series) -> str:
    """
    Rule-based engine to classify disaster risk into LOW, MEDIUM, HIGH.
    This acts as a heuristic labeler before we integrate real Machine Learning.
    """
    risk_score = 0
    
    # 1. Rainfall / Flood Risk Check
    if row['rain'] > ALERT_THRESHOLDS["heavy_rainfall_mm"]:
        risk_score += 3  # Immediate high danger
    elif row['rain'] > ALERT_THRESHOLDS["heavy_rainfall_mm"] / 2:
        risk_score += 1
        
    if row['soil_moisture_0_to_1cm'] > ALERT_THRESHOLDS["flood_risk_soil_moisture"]:
        risk_score += 1 # Soil is saturated, higher flood chance
        
    # 2. Wind / Storm Risk Check
    if row['wind_speed_10m'] > ALERT_THRESHOLDS["high_wind_speed_kmh"]:
        risk_score += 2
        
    # 3. Heatwave Risk Check
    if row['temperature_2m'] > ALERT_THRESHOLDS["heatwave_temp_c"]:
        risk_score += 2

    # Map score to label
    if risk_score >= 3:
        return "HIGH"
    elif risk_score >= 1:
        return "MEDIUM"
    else:
        return "LOW"

from src.ml.predict import predictor_instance
from telegram_bot.sender import send_telegram_alert
from src.db.database import SessionLocal
from src.db.models import AlertLog

def generate_alerts(current_data: dict) -> None:
    """
    Takes live engineered weather data, requests an ML prediction,
    and triggers an alert if the ML model identifies HIGH risk.
    Logs all alerts to PostgreSQL.
    """
    try:
        series_data = pd.Series(current_data)
        city = current_data.get('city', 'Unknown City')
        timestamp = pd.to_datetime(current_data.get('time', datetime.now().isoformat()))
        
        # 1. Ask ML Model
        ml_risk_level, confidence = predictor_instance.predict_flood_risk(current_data)
        
        # Fallback to rules if ML fails
        if ml_risk_level == "UNKNOWN":
            ml_risk_level = evaluate_disaster_risk(series_data)
            confidence = 0.0 # Heuristics don't have probability confidence
            
        if ml_risk_level in ["HIGH", "MEDIUM"]:
            alert_msg = f"[ML {ml_risk_level} RISK] {city} | Confidence: {confidence*100:.1f}% | Rain: {series_data.get('rain')}mm"
            telegram_delivered = 0
            
            if ml_risk_level == "HIGH":
                logger.error(alert_msg)
                # TRIGGER REAL-TIME TELEGRAM EMERGENCY BROADCAST
                send_telegram_alert(city, ml_risk_level, confidence, current_data)
                telegram_delivered = 1
            else:
                logger.warning(alert_msg)
                
            # Log Alert to PostgreSQL securely
            with SessionLocal() as db:
                new_alert = AlertLog(
                    timestamp=timestamp,
                    city=city,
                    alert_type="ML_PREDICTION",
                    severity=ml_risk_level,
                    message=alert_msg,
                    telegram_delivered=telegram_delivered
                )
                db.add(new_alert)
                db.commit()
                
    except Exception as e:
        logger.error(f"Failed to generate alerts: {e}")
