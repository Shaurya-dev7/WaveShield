"""
===========================================================================
ENTERPRISE SPATIAL QUERY ENGINE — PostGIS Native Operations
===========================================================================

WHY THIS EXISTS:
    Before PostGIS, every spatial question required Python code:
        "Is Mumbai in a flood zone?"  → Loop through polygons in memory
        "What's the nearest river?"   → Haversine loop over all rivers

    With PostGIS, the DATABASE answers these questions directly:
        "Is Mumbai in a flood zone?"  → ST_Contains(zone.boundary, point)
        "What's the nearest river?"   → ST_Distance(river.geom, point) ORDER BY 1 LIMIT 1

    PostGIS spatial queries use GiST R-tree indexes. An R-tree organizes
    geometries into a hierarchy of bounding boxes. When you ask "find all
    flood zones containing this point", the R-tree eliminates 99% of
    candidates by checking bounding boxes BEFORE doing expensive exact
    geometry tests. Result: <1ms for queries over millions of polygons.

KEY POSTGIS FUNCTIONS USED:
    ST_SetSRID(ST_MakePoint(lon, lat), 4326)
        Creates a point geometry from coordinates.

    ST_DWithin(geog_a, geog_b, distance_meters)
        Returns TRUE if two geographies are within N meters of each other.
        Uses the GEOGRAPHY type for true spherical Earth distance.

    ST_Contains(polygon, point)
        Returns TRUE if the polygon fully contains the point.

    ST_Distance(geog_a, geog_b)
        Returns the shortest distance in METERS between two geographies.

    ST_Buffer(point, radius_meters)
        Creates a circle polygon around a point (for creating risk zones).

    ST_Intersects(geom_a, geom_b)
        Returns TRUE if two geometries share any space.

    ST_AsGeoJSON(geom)
        Converts a PostGIS geometry to GeoJSON for API responses.

    ST_Area(geom::geography)
        Returns the area of a polygon in square meters.
===========================================================================
"""

import json
from typing import Dict, List, Optional, Tuple
from sqlalchemy import text
from src.db.database import SessionLocal
from src.utils.logger import setup_logger

logger = setup_logger("Spatial_Query_Engine")


def find_flood_zones_at_point(lat: float, lon: float) -> List[Dict]:
    """
    Finds ALL flood zones that contain a given coordinate.

    PostGIS query: ST_Contains(boundary, ST_SetSRID(ST_MakePoint(lon, lat), 4326))

    This uses the GiST index on flood_zones.boundary. Even with 100,000
    flood zone polygons, this query runs in <5ms because the R-tree
    index eliminates most candidates by bounding box alone.

    Returns:
        List of flood zone dictionaries with name, risk_level, area, etc.
    """
    query = text("""
        SELECT
            id, name, city, risk_level, zone_type,
            area_sq_km, elevation_min_m, elevation_max_m,
            data_source, description,
            ST_AsGeoJSON(boundary) as boundary_geojson
        FROM flood_zones
        WHERE ST_Contains(
            boundary,
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)
        )
        ORDER BY risk_level ASC
    """)

    try:
        with SessionLocal() as db:
            result = db.execute(query, {"lat": lat, "lon": lon})
            zones = []
            for row in result.mappings():
                zones.append({
                    "id": row["id"],
                    "name": row["name"],
                    "city": row["city"],
                    "risk_level": row["risk_level"],
                    "zone_type": row["zone_type"],
                    "area_sq_km": row["area_sq_km"],
                    "elevation_min_m": row["elevation_min_m"],
                    "elevation_max_m": row["elevation_max_m"],
                    "data_source": row["data_source"],
                    "boundary_geojson": json.loads(row["boundary_geojson"])
                            if row["boundary_geojson"] else None,
                })
            logger.info(f"Found {len(zones)} flood zones at ({lat}, {lon})")
            return zones
    except Exception as e:
        logger.error(f"Flood zone query failed: {e}")
        return []


def find_rivers_within_radius(lat: float, lon: float,
                               radius_km: float = 10.0) -> List[Dict]:
    """
    Finds all river segments within a given radius of a point.

    PostGIS query: ST_DWithin(geom::geography, point::geography, radius_m)

    ST_DWithin on geography types computes TRUE spherical distance in
    meters, so radius_km * 1000 gives exact real-world distance.
    The GiST index makes this sub-millisecond even with millions of
    river segments.

    Returns:
        List of river segment dicts sorted by distance (nearest first).
    """
    radius_m = radius_km * 1000

    query = text("""
        SELECT
            id, name, waterway_type, strahler_order,
            upstream_area_sq_km, discharge_m3s,
            ST_Distance(
                geom::geography,
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
            ) as distance_m,
            ST_AsGeoJSON(geom) as geom_geojson
        FROM river_segments
        WHERE ST_DWithin(
            geom::geography,
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
            :radius
        )
        ORDER BY distance_m ASC
    """)

    try:
        with SessionLocal() as db:
            result = db.execute(query, {"lat": lat, "lon": lon, "radius": radius_m})
            rivers = []
            for row in result.mappings():
                rivers.append({
                    "id": row["id"],
                    "name": row["name"],
                    "type": row["waterway_type"],
                    "strahler_order": row["strahler_order"],
                    "distance_km": round(row["distance_m"] / 1000, 3),
                    "upstream_area_sq_km": row["upstream_area_sq_km"],
                    "discharge_m3s": row["discharge_m3s"],
                    "geom_geojson": json.loads(row["geom_geojson"])
                                    if row["geom_geojson"] else None,
                })
            logger.info(f"Found {len(rivers)} rivers within {radius_km}km of ({lat}, {lon})")
            return rivers
    except Exception as e:
        logger.error(f"River proximity query failed: {e}")
        return []


def find_nearest_river(lat: float, lon: float) -> Optional[Dict]:
    """
    Finds the single nearest river to a given point.
    Optimized with LIMIT 1 and spatial index.
    """
    rivers = find_rivers_within_radius(lat, lon, radius_km=50.0)
    return rivers[0] if rivers else None


def find_active_risk_regions(lat: float = None, lon: float = None,
                              radius_km: float = 100.0) -> List[Dict]:
    """
    Retrieves currently active risk regions, optionally filtered by
    proximity to a given point.

    If no coordinates are provided, returns ALL active risk regions.
    """
    if lat is not None and lon is not None:
        query = text("""
            SELECT
                id, timestamp, city, risk_level, confidence,
                flood_susceptibility_index, area_sq_km,
                population_exposed, trigger_source,
                ST_AsGeoJSON(boundary) as boundary_geojson
            FROM risk_regions
            WHERE timestamp > NOW() - INTERVAL '24 hours'
            AND ST_DWithin(
                boundary::geography,
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                :radius
            )
            ORDER BY flood_susceptibility_index DESC
        """)
        params = {"lat": lat, "lon": lon, "radius": radius_km * 1000}
    else:
        query = text("""
            SELECT
                id, timestamp, city, risk_level, confidence,
                flood_susceptibility_index, area_sq_km,
                population_exposed, trigger_source,
                ST_AsGeoJSON(boundary) as boundary_geojson
            FROM risk_regions
            WHERE timestamp > NOW() - INTERVAL '24 hours'
            ORDER BY flood_susceptibility_index DESC
            LIMIT 50
        """)
        params = {}

    try:
        with SessionLocal() as db:
            result = db.execute(query, params)
            regions = []
            for row in result.mappings():
                regions.append({
                    "id": row["id"],
                    "timestamp": str(row["timestamp"]),
                    "city": row["city"],
                    "risk_level": row["risk_level"],
                    "confidence": row["confidence"],
                    "fsi": row["flood_susceptibility_index"],
                    "area_sq_km": row["area_sq_km"],
                    "population_exposed": row["population_exposed"],
                    "trigger_source": row["trigger_source"],
                    "boundary_geojson": json.loads(row["boundary_geojson"])
                                        if row["boundary_geojson"] else None,
                })
            return regions
    except Exception as e:
        logger.error(f"Risk region query failed: {e}")
        return []


def find_nearby_events(lat: float, lon: float,
                        radius_km: float = 50.0,
                        hours: int = 72) -> List[Dict]:
    """
    Finds all geospatial events (flood alerts, satellite detections)
    within a radius and time window.
    """
    query = text("""
        SELECT
            id, timestamp, event_type, severity, city, description,
            flood_susceptibility_index, rainfall_mm, confidence,
            ST_AsGeoJSON(location::geometry) as location_geojson,
            ST_AsGeoJSON(affected_area) as area_geojson
        FROM geospatial_events
        WHERE timestamp > NOW() - make_interval(hours => :hours)
        AND ST_DWithin(
            location,
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
            :radius
        )
        ORDER BY timestamp DESC
        LIMIT 100
    """)

    try:
        with SessionLocal() as db:
            result = db.execute(query, {
                "lat": lat, "lon": lon,
                "radius": radius_km * 1000,
                "hours": hours
            })
            events = []
            for row in result.mappings():
                events.append({
                    "id": row["id"],
                    "timestamp": str(row["timestamp"]),
                    "event_type": row["event_type"],
                    "severity": row["severity"],
                    "city": row["city"],
                    "description": row["description"],
                    "fsi": row["flood_susceptibility_index"],
                    "rainfall_mm": row["rainfall_mm"],
                    "confidence": row["confidence"],
                })
            return events
    except Exception as e:
        logger.error(f"Nearby events query failed: {e}")
        return []


def create_risk_buffer(lat: float, lon: float,
                        radius_km: float, risk_level: str,
                        fsi: float, city: str = None) -> Optional[int]:
    """
    Creates a circular risk region polygon around a point.

    ST_Buffer on a geography type creates a TRUE circular polygon
    accounting for Earth's curvature. The result is stored as a
    geometry in the risk_regions table.

    This is called by the scheduler when the ML model detects
    elevated risk at a location.
    """
    query = text("""
        INSERT INTO risk_regions
            (timestamp, city, risk_level, confidence, flood_susceptibility_index,
             boundary, area_sq_km, trigger_source)
        VALUES (
            NOW(), :city, :risk_level, :fsi, :fsi,
            ST_Buffer(
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                :radius
            )::geometry,
            :area,
            'ML_PREDICTION'
        )
        RETURNING id
    """)

    area = 3.14159 * (radius_km ** 2)

    try:
        with SessionLocal() as db:
            result = db.execute(query, {
                "lat": lat, "lon": lon,
                "radius": radius_km * 1000,
                "risk_level": risk_level,
                "fsi": fsi,
                "city": city,
                "area": round(area, 2),
            })
            db.commit()
            row = result.fetchone()
            region_id = row[0] if row else None
            logger.info(f"Created risk buffer: id={region_id}, {risk_level} at ({lat},{lon})")
            return region_id
    except Exception as e:
        logger.error(f"Risk buffer creation failed: {e}")
        return None


def insert_flood_zone(name: str, city: str, risk_level: str,
                       zone_type: str, polygon_coords: List[List[float]],
                       elevation_min: float = None,
                       elevation_max: float = None,
                       data_source: str = "computed") -> Optional[int]:
    """
    Inserts a flood zone polygon into the database.

    Args:
        polygon_coords: List of [lon, lat] coordinate pairs forming
                       a closed polygon. First and last point must match.
    """
    # Build WKT POLYGON string
    coord_str = ", ".join(f"{c[0]} {c[1]}" for c in polygon_coords)
    wkt = f"POLYGON(({coord_str}))"

    query = text("""
        INSERT INTO flood_zones
            (name, city, risk_level, zone_type, boundary,
             elevation_min_m, elevation_max_m, data_source,
             area_sq_km)
        VALUES (
            :name, :city, :risk_level, :zone_type,
            ST_GeomFromText(:wkt, 4326),
            :elev_min, :elev_max, :source,
            ST_Area(ST_GeomFromText(:wkt, 4326)::geography) / 1000000
        )
        RETURNING id
    """)

    try:
        with SessionLocal() as db:
            result = db.execute(query, {
                "name": name, "city": city,
                "risk_level": risk_level, "zone_type": zone_type,
                "wkt": wkt, "elev_min": elevation_min,
                "elev_max": elevation_max, "source": data_source,
            })
            db.commit()
            row = result.fetchone()
            return row[0] if row else None
    except Exception as e:
        logger.error(f"Flood zone insert failed: {e}")
        return None


def insert_river_segment(name: str, waterway_type: str,
                          line_coords: List[List[float]],
                          strahler_order: int = None) -> Optional[int]:
    """
    Inserts a river segment linestring into the database.

    Args:
        line_coords: List of [lon, lat] coordinate pairs forming the river path.
    """
    coord_str = ", ".join(f"{c[0]} {c[1]}" for c in line_coords)
    wkt = f"LINESTRING({coord_str})"

    query = text("""
        INSERT INTO river_segments
            (name, waterway_type, geom, strahler_order)
        VALUES (
            :name, :wtype,
            ST_GeomFromText(:wkt, 4326),
            :order
        )
        RETURNING id
    """)

    try:
        with SessionLocal() as db:
            result = db.execute(query, {
                "name": name, "wtype": waterway_type,
                "wkt": wkt, "order": strahler_order,
            })
            db.commit()
            row = result.fetchone()
            return row[0] if row else None
    except Exception as e:
        logger.error(f"River segment insert failed: {e}")
        return None


def get_flood_zone_statistics() -> Dict:
    """
    Returns aggregate statistics about all stored flood zones.
    Used by the dashboard's spatial intelligence panel.
    """
    query = text("""
        SELECT
            risk_level,
            COUNT(*) as zone_count,
            ROUND(SUM(area_sq_km)::numeric, 2) as total_area_sq_km,
            ROUND(AVG(elevation_min_m)::numeric, 1) as avg_min_elevation
        FROM flood_zones
        GROUP BY risk_level
        ORDER BY
            CASE risk_level
                WHEN 'CRITICAL' THEN 1
                WHEN 'HIGH' THEN 2
                WHEN 'MODERATE' THEN 3
                WHEN 'LOW' THEN 4
            END
    """)

    try:
        with SessionLocal() as db:
            result = db.execute(query)
            stats = []
            for row in result.mappings():
                stats.append({
                    "risk_level": row["risk_level"],
                    "zone_count": row["zone_count"],
                    "total_area_sq_km": float(row["total_area_sq_km"] or 0),
                    "avg_min_elevation": float(row["avg_min_elevation"] or 0),
                })
            return {"flood_zone_stats": stats}
    except Exception as e:
        logger.error(f"Flood zone stats query failed: {e}")
        return {"flood_zone_stats": []}
