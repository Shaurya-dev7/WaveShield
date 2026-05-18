"""
===========================================================================
SPATIAL INTELLIGENCE API ENDPOINTS — PostGIS-Powered
===========================================================================

These endpoints leverage PostGIS spatial queries for sub-millisecond
geospatial operations. All polygon/geometry responses use the GeoJSON
standard (RFC 7946) for compatibility with any mapping library.

ENDPOINTS:
    /spatial/risk-map         — GeoJSON of all active risk regions
    /spatial/flood-polygons   — Flood zone polygons for a city/area
    /spatial/rivers           — River segments near a coordinate
    /spatial/nearby-risks     — Risk zones within radius of a point
    /spatial/events           — Spatial event log near a point
    /spatial/analyze          — Trigger floodplain analysis for a city
    /spatial/stats            — Aggregate spatial statistics
===========================================================================
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional
from src.config.settings import TARGET_CITIES
from src.utils.logger import setup_logger

logger = setup_logger("Spatial_API")

router = APIRouter(prefix="/spatial", tags=["Spatial Intelligence (PostGIS)"])


@router.get("/risk-map")
async def get_risk_map() -> Dict[str, Any]:
    """
    Returns a GeoJSON FeatureCollection of all active risk regions
    from the past 24 hours.

    This is the primary endpoint for rendering dynamic risk overlays
    on the dashboard map. Each feature is a polygon with risk metadata.
    """
    from src.db.spatial_queries import find_active_risk_regions

    regions = find_active_risk_regions()

    features = []
    for r in regions:
        feature = {
            "type": "Feature",
            "geometry": r.get("boundary_geojson"),
            "properties": {
                "city": r.get("city"),
                "risk_level": r.get("risk_level"),
                "fsi": r.get("fsi"),
                "confidence": r.get("confidence"),
                "area_sq_km": r.get("area_sq_km"),
                "population_exposed": r.get("population_exposed"),
                "trigger_source": r.get("trigger_source"),
                "timestamp": r.get("timestamp"),
            }
        }
        features.append(feature)

    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "count": len(features),
            "source": "PostGIS risk_regions",
            "period": "last_24_hours",
        }
    }


@router.get("/flood-polygons")
async def get_flood_polygons(
    city: Optional[str] = Query(None, description="Filter by city name"),
    lat: Optional[float] = Query(None, description="Latitude for point-in-polygon query"),
    lon: Optional[float] = Query(None, description="Longitude for point-in-polygon query"),
) -> Dict[str, Any]:
    """
    Returns flood zone polygons as GeoJSON.

    Two query modes:
        1. By city name: Returns all flood zones for that city
        2. By coordinate: Returns flood zones containing that point
           (uses PostGIS ST_Contains with GiST index)
    """
    from src.db.spatial_queries import find_flood_zones_at_point
    from sqlalchemy import text
    from src.db.database import SessionLocal
    import json

    features = []

    if lat is not None and lon is not None:
        # Point-in-polygon query using PostGIS
        zones = find_flood_zones_at_point(lat, lon)
        for z in zones:
            features.append({
                "type": "Feature",
                "geometry": z.get("boundary_geojson"),
                "properties": {
                    "name": z.get("name"),
                    "city": z.get("city"),
                    "risk_level": z.get("risk_level"),
                    "zone_type": z.get("zone_type"),
                    "area_sq_km": z.get("area_sq_km"),
                    "elevation_min_m": z.get("elevation_min_m"),
                }
            })
    elif city:
        # City filter query
        query = text("""
            SELECT id, name, risk_level, zone_type, area_sq_km,
                   elevation_min_m, elevation_max_m,
                   ST_AsGeoJSON(boundary) as boundary_geojson
            FROM flood_zones
            WHERE LOWER(city) = LOWER(:city)
            ORDER BY risk_level ASC
        """)
        try:
            with SessionLocal() as db:
                result = db.execute(query, {"city": city})
                for row in result.mappings():
                    features.append({
                        "type": "Feature",
                        "geometry": json.loads(row["boundary_geojson"])
                                    if row["boundary_geojson"] else None,
                        "properties": {
                            "name": row["name"],
                            "risk_level": row["risk_level"],
                            "zone_type": row["zone_type"],
                            "area_sq_km": row["area_sq_km"],
                            "elevation_min_m": row["elevation_min_m"],
                        }
                    })
        except Exception as e:
            logger.error(f"Flood polygon query failed: {e}")
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either 'city' or 'lat'+'lon' query parameters."
        )

    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {"count": len(features)},
    }


@router.get("/rivers")
async def get_nearby_rivers(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    radius_km: float = Query(10.0, description="Search radius in km"),
) -> Dict[str, Any]:
    """
    Returns river segments within a radius as GeoJSON LineStrings.

    Uses PostGIS ST_DWithin with geography type for true meter-accurate
    distance computation on a spherical Earth model.
    """
    from src.db.spatial_queries import find_rivers_within_radius

    rivers = find_rivers_within_radius(lat, lon, radius_km)

    features = []
    for r in rivers:
        features.append({
            "type": "Feature",
            "geometry": r.get("geom_geojson"),
            "properties": {
                "name": r.get("name"),
                "type": r.get("type"),
                "distance_km": r.get("distance_km"),
                "strahler_order": r.get("strahler_order"),
                "upstream_area_sq_km": r.get("upstream_area_sq_km"),
            }
        })

    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "count": len(features),
            "center": {"lat": lat, "lon": lon},
            "radius_km": radius_km,
        }
    }


@router.get("/nearby-risks")
async def get_nearby_risks(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    radius_km: float = Query(50.0, description="Search radius in km"),
) -> Dict[str, Any]:
    """
    Returns ALL spatial risk intelligence near a coordinate:
        - Flood zones containing the point
        - Active risk regions within radius
        - Recent geospatial events
    """
    from src.db.spatial_queries import (
        find_flood_zones_at_point,
        find_active_risk_regions,
        find_nearby_events,
    )

    zones = find_flood_zones_at_point(lat, lon)
    regions = find_active_risk_regions(lat, lon, radius_km)
    events = find_nearby_events(lat, lon, radius_km, hours=72)

    return {
        "query": {"lat": lat, "lon": lon, "radius_km": radius_km},
        "flood_zones": zones,
        "active_risk_regions": regions,
        "recent_events": events,
        "summary": {
            "inside_flood_zones": len(zones),
            "active_risk_regions": len(regions),
            "recent_events_72h": len(events),
            "highest_risk": zones[0]["risk_level"] if zones else "NONE",
        }
    }


@router.get("/events")
async def get_spatial_events(
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
    radius_km: float = Query(100.0),
    hours: int = Query(72, description="Time window in hours"),
) -> Dict[str, Any]:
    """
    Returns geospatial events (flood detections, alerts, anomalies)
    optionally filtered by proximity.
    """
    from src.db.spatial_queries import find_nearby_events

    if lat is not None and lon is not None:
        events = find_nearby_events(lat, lon, radius_km, hours)
    else:
        # Return recent events globally
        from sqlalchemy import text
        from src.db.database import SessionLocal
        try:
            with SessionLocal() as db:
                result = db.execute(text("""
                    SELECT id, timestamp, event_type, severity, city, description,
                           flood_susceptibility_index, rainfall_mm, confidence
                    FROM geospatial_events
                    WHERE timestamp > NOW() - make_interval(hours => :hours)
                    ORDER BY timestamp DESC LIMIT 50
                """), {"hours": hours})
                events = [dict(row._mapping) for row in result]
                for e in events:
                    e["timestamp"] = str(e["timestamp"])
        except Exception as ex:
            logger.error(f"Global events query failed: {ex}")
            events = []

    return {"events": events, "count": len(events)}


@router.post("/analyze/{city}")
async def trigger_floodplain_analysis(city: str) -> Dict[str, Any]:
    """
    Triggers a full floodplain analysis for a city: generates flood-prone
    polygons from elevation data and stores them in PostGIS.

    This is an admin/on-demand endpoint — computationally expensive.
    """
    city_match = None
    for name, coords in TARGET_CITIES.items():
        if name.lower() == city.lower():
            city_match = (name, coords)
            break

    if not city_match:
        raise HTTPException(status_code=404, detail=f"City '{city}' not monitored")

    name, coords = city_match

    from src.geo.floodplain import analyze_floodplain, store_floodplain_results

    analysis = analyze_floodplain(name, coords["lat"], coords["lon"])
    stored = store_floodplain_results(name, analysis)

    return {
        "city": name,
        "analysis": analysis.get("statistics", {}),
        "polygons_generated": len(analysis.get("floodplain_polygons", [])),
        "polygons_stored_to_postgis": stored,
    }


@router.get("/stats")
async def get_spatial_statistics() -> Dict[str, Any]:
    """
    Returns aggregate statistics about the spatial intelligence database.
    """
    from src.db.spatial_queries import get_flood_zone_statistics
    from sqlalchemy import text
    from src.db.database import SessionLocal

    stats = get_flood_zone_statistics()

    # Add table counts
    try:
        with SessionLocal() as db:
            counts = {}
            for table in ["flood_zones", "river_segments", "risk_regions", "geospatial_events"]:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                counts[table] = result.scalar() or 0
            stats["table_counts"] = counts
    except Exception as e:
        stats["table_counts"] = {"error": str(e)}

    return stats
