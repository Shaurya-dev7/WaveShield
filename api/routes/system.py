from fastapi import APIRouter
from typing import List
from datetime import datetime
import time

from api.schemas.responses import HealthResponse, AlertResponse, ModelInfoResponse
from api.services.ml_service import ml_engine
from api.services.data_service import DataService

router = APIRouter(tags=["System & Monitoring"])

# Store the start time to calculate uptime
START_TIME = time.time()

@router.get("/health", response_model=HealthResponse)
async def get_health():
    """
    Standard Kubernetes/Cloud health check endpoint.
    Used by load balancers to ensure the API is alive.
    """
    uptime_seconds = int(time.time() - START_TIME)
    uptime_str = f"{uptime_seconds // 3600}h {(uptime_seconds % 3600) // 60}m"
    
    return HealthResponse(
        status="healthy" if ml_engine.is_loaded else "degraded",
        model_loaded=ml_engine.is_loaded,
        dataset_rows=DataService.get_total_dataset_rows(),
        uptime=uptime_str,
        timestamp=datetime.now().isoformat()
    )

@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts():
    """
    Retrieve the most recent active disaster alerts.
    """
    alerts = DataService.get_active_alerts()
    response = []
    
    for a in alerts:
        response.append(AlertResponse(
            city=a.get("city", "Unknown"),
            risk_level=a.get("risk_level", "UNKNOWN"),
            confidence=float(a.get("confidence", 0.0)),
            timestamp=str(a.get("timestamp", "")),
            message=str(a.get("message", ""))
        ))
        
    return response

@router.get("/model-info", response_model=ModelInfoResponse)
async def get_model_info():
    """
    ML Observability endpoint. Useful for verifying which version
    of the model is currently active in production.
    """
    return ModelInfoResponse(
        version="v1.0.0",
        algorithm="XGBoost Classifier",
        features_used=ml_engine.features,
        dataset_size=DataService.get_total_dataset_rows()
    )

@router.get("/historical")
async def get_historical_data():
    """
    Returns time-series data for dashboard visualization from PostgreSQL.
    """
    data = DataService.get_historical_data()
    return data
