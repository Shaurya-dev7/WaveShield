from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path

# Ensure the backend can import modules from 'src'
sys.path.append(str(Path(__file__).resolve().parent.parent))

from api.routes import predictions, system, geospatial, spatial

# 1. Initialize FastAPI app
app = FastAPI(
    title="AI Disaster Intelligence API",
    description="Enterprise Spatial AI Disaster Intelligence Platform. "
                "PostGIS-powered geospatial analysis with flood zone polygons, "
                "river networks, satellite rainfall, and XGBoost ML prediction.",
    version="3.0.0"
)

# 2. Add CORS Middleware
# Security measure: Allows the Streamlit dashboard or any frontend to connect to the API.
# In production, restrict 'allow_origins' to specific domain names.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Include Routers
app.include_router(predictions.router)
app.include_router(system.router)
app.include_router(geospatial.router)
app.include_router(spatial.router)

# 4. Root Endpoint
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to the AI Disaster Intelligence Platform API.",
        "docs": "/docs",
        "health": "/health"
    }

# To run the server locally:
# uvicorn api.main:app --reload
