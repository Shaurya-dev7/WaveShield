"""
===========================================================================
FLOOD SUSCEPTIBILITY MODEL — MULTI-LAYER COMPOSITE SCORING
===========================================================================

WHAT THIS MODULE DOES:
    Combines ALL geospatial intelligence layers into a single, unified
    Flood Susceptibility Index (FSI) for any coordinate on Earth.

    This is the "brain" of the geospatial system — it fuses:
        1. Terrain elevation & basin topology
        2. Satellite rainfall intensity & anomalies
        3. River proximity & drainage density
        4. Ground weather conditions (soil moisture, humidity, pressure)

    The output is a physics-informed composite score (0.0 - 1.0) that
    dramatically improves ML prediction accuracy compared to weather-only
    features.

ARCHITECTURE:
    Weather API ─────────┐
    Satellite Rainfall ──┤
    Elevation Engine ────┼──► Flood Susceptibility Model ──► ML Feature Vector
    River Intelligence ──┤
    Soil Conditions ─────┘

SCORING METHODOLOGY:
    Each sub-score is weighted based on hydrological research:

    FACTOR                  WEIGHT   RATIONALE
    ─────────────────────────────────────────────────────
    Rainfall Intensity      0.30     Primary trigger for floods
    Terrain & Elevation     0.20     Controls where water accumulates
    River Proximity         0.15     Direct overflow exposure
    Soil Saturation         0.15     Determines infiltration vs runoff
    Rainfall Anomaly        0.10     Detects unusual weather patterns
    Drainage Quality        0.10     Urban vs natural runoff

    These weights are based on the HAND (Height Above Nearest Drainage)
    methodology and WHO/UNDRR flood risk assessment frameworks.
===========================================================================
"""

from typing import Dict, Optional
from src.utils.logger import setup_logger

logger = setup_logger("Flood_Susceptibility")

# Hydrological weighting factors (sum = 1.0)
WEIGHTS = {
    "rainfall_intensity": 0.30,
    "terrain_elevation": 0.20,
    "river_proximity": 0.15,
    "soil_saturation": 0.15,
    "rainfall_anomaly": 0.10,
    "drainage_quality": 0.10,
}


def _normalize(value: float, min_val: float, max_val: float) -> float:
    """Safely normalize a value to 0.0 - 1.0 range."""
    if max_val <= min_val:
        return 0.0
    clamped = max(min(value, max_val), min_val)
    return (clamped - min_val) / (max_val - min_val)


def compute_rainfall_intensity_score(precip_24h_mm: float,
                                      max_hourly_mm: float) -> float:
    """
    Scores rainfall intensity from 0 (dry) to 1 (extreme).

    Calibration based on IMD (India Meteorological Department) thresholds:
        Light:    < 15mm/24h
        Moderate: 15-64mm/24h
        Heavy:    65-115mm/24h
        Very Heavy: 116-204mm/24h
        Extremely Heavy: > 204mm/24h

    We also factor in hourly intensity — 50mm in 1 hour is far more
    dangerous than 50mm spread over 24 hours.
    """
    # 24h accumulation factor (0-1, mapped to 0-200mm)
    daily_factor = _normalize(precip_24h_mm, 0, 200)

    # Peak hourly intensity factor (0-1, mapped to 0-50mm/h)
    hourly_factor = _normalize(max_hourly_mm, 0, 50)

    # Weighted combination: burst intensity is more dangerous
    return round(daily_factor * 0.6 + hourly_factor * 0.4, 4)


def compute_soil_saturation_score(soil_moisture: float,
                                   humidity: float,
                                   recent_rainfall_mm: float) -> float:
    """
    Scores soil saturation from 0 (dry, absorbent) to 1 (saturated, runoff).

    When soil is already saturated, additional rainfall has nowhere to go
    and runs off directly into rivers and drains — this is the primary
    mechanism of flash flooding.

    Inputs:
        soil_moisture: volumetric water content (m³/m³), typically 0.0-0.6
        humidity: relative humidity (%), affects evapotranspiration
        recent_rainfall_mm: last 72h rainfall, indicates pre-saturation
    """
    # Soil moisture factor (0.5 m³/m³ = fully saturated for most soils)
    moisture_factor = _normalize(soil_moisture, 0.0, 0.5)

    # Humidity factor (high humidity = less evaporation = slower drainage)
    humidity_factor = _normalize(humidity, 40.0, 100.0)

    # Pre-saturation from recent rain (0-1, mapped to 0-150mm over 72h)
    presaturation = _normalize(recent_rainfall_mm, 0, 150)

    return round(moisture_factor * 0.5 + humidity_factor * 0.2 + presaturation * 0.3, 4)


def compute_drainage_quality_score(river_density: float,
                                    elevation_m: float,
                                    slope_percent: float) -> float:
    """
    Estimates how well an area can drain water.

    High drainage quality (low score) = water flows away quickly
    Low drainage quality (high score) = water pools and floods

    Factors:
        - Flat terrain (low slope) = poor drainage
        - Low elevation = water accumulates
        - Low river density = fewer drainage paths
        - Urban areas implicitly have low drainage (impervious surfaces)
    """
    # Flat land drains poorly (slope < 0.5% is essentially flat)
    flatness_factor = 1.0 - _normalize(abs(slope_percent), 0, 5)

    # Low elevation drains poorly (water from upstream collects here)
    low_elev_factor = 1.0 - _normalize(elevation_m or 50, 0, 500)

    # Paradoxically, LOW river density means poor drainage
    # (no channels for water to escape through)
    poor_drainage = 1.0 - _normalize(river_density, 0, 0.1)

    return round(flatness_factor * 0.4 + low_elev_factor * 0.3 + poor_drainage * 0.3, 4)


def compute_flood_susceptibility_index(
    terrain_features: Dict,
    satellite_features: Dict,
    river_features: Dict,
    weather_features: Dict
) -> Dict:
    """
    MASTER FUNCTION: Computes the Global Flood Susceptibility Index (FSI).

    This fuses all geospatial intelligence layers into a single composite
    score using hydrologically-weighted factors.

    Args:
        terrain_features: Output from elevation.get_terrain_features()
        satellite_features: Output from satellite_rainfall.get_satellite_features()
        river_features: Output from rivers.get_river_features()
        weather_features: Dict with keys like soil_moisture_0_to_1cm,
                         relative_humidity_2m, rainfall_last_72h, rain

    Returns:
        Dictionary containing the composite FSI (0-1), individual sub-scores,
        risk classification, and all component features.
    """
    # === Extract values with safe defaults ===
    precip_24h = satellite_features.get("satellite_precip_24h_mm", 0.0)
    max_hourly = satellite_features.get("satellite_max_hourly_mm", 0.0)
    anomaly = satellite_features.get("rainfall_anomaly_score", 0.0)

    elevation = terrain_features.get("elevation_m", 50.0)
    slope = terrain_features.get("slope_percent", 0.0)
    basin_score = terrain_features.get("basin_score", 0.5)
    elevation_risk = terrain_features.get("elevation_risk_score", 0.5)

    river_risk = river_features.get("river_risk_score", 0.3)
    river_density = river_features.get("river_density_per_km2", 0.0)

    soil_moisture = weather_features.get("soil_moisture_0_to_1cm", 0.2)
    humidity = weather_features.get("relative_humidity_2m", 60.0)
    rainfall_72h = weather_features.get("rainfall_last_72h", 0.0)

    # === Compute sub-scores ===
    rainfall_score = compute_rainfall_intensity_score(precip_24h, max_hourly)
    soil_score = compute_soil_saturation_score(soil_moisture, humidity, rainfall_72h)
    anomaly_score = _normalize(anomaly, 0, 5)  # 5x baseline = max anomaly
    drainage_score = compute_drainage_quality_score(river_density, elevation, slope)

    # === Weighted composite ===
    fsi = (
        WEIGHTS["rainfall_intensity"] * rainfall_score +
        WEIGHTS["terrain_elevation"] * elevation_risk +
        WEIGHTS["river_proximity"] * river_risk +
        WEIGHTS["soil_saturation"] * soil_score +
        WEIGHTS["rainfall_anomaly"] * anomaly_score +
        WEIGHTS["drainage_quality"] * drainage_score
    )

    fsi = round(min(max(fsi, 0.0), 1.0), 4)

    # === Risk classification ===
    if fsi >= 0.75:
        risk_class = "CRITICAL"
    elif fsi >= 0.55:
        risk_class = "HIGH"
    elif fsi >= 0.35:
        risk_class = "MODERATE"
    else:
        risk_class = "LOW"

    result = {
        # Composite
        "flood_susceptibility_index": fsi,
        "fsi_risk_class": risk_class,

        # Sub-scores (for explainability / SHAP-like breakdown)
        "score_rainfall_intensity": rainfall_score,
        "score_terrain_elevation": elevation_risk,
        "score_river_proximity": river_risk,
        "score_soil_saturation": soil_score,
        "score_rainfall_anomaly": anomaly_score,
        "score_drainage_quality": drainage_score,

        # Raw geospatial features for ML
        "elevation_m": elevation,
        "slope_percent": slope,
        "basin_score": basin_score,
        "distance_to_river_km": river_features.get("distance_to_river_km", 99.0),
        "river_count_10km": river_features.get("river_count_10km", 0),
        "satellite_precip_24h_mm": precip_24h,
        "rainfall_anomaly_score": anomaly,
    }

    logger.info(
        f"FSI computed: {fsi:.3f} ({risk_class}) | "
        f"rain={rainfall_score:.2f} terrain={elevation_risk:.2f} "
        f"river={river_risk:.2f} soil={soil_score:.2f}"
    )

    return result
