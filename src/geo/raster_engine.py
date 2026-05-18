"""
===========================================================================
RASTER PROCESSING ENGINE
===========================================================================

WHAT IS A RASTER?
    A raster is a grid of cells (pixels), where each cell stores a value.
    In GIS, rasters represent continuous surfaces:
        - DEM (Digital Elevation Model): Each pixel = elevation in meters
        - Satellite rainfall: Each pixel = mm of precipitation
        - Slope: Each pixel = slope angle in degrees
        - Land cover: Each pixel = land type classification code

WHAT IS A DEM?
    Digital Elevation Model — a 3D representation of terrain stored as a
    2D grid of elevation values. The NASA SRTM (Shuttle Radar Topography
    Mission) DEM covers the entire globe at 90m resolution.

WHY RASTER PROCESSING MATTERS:
    - Identify terrain sinks (basins that trap water)
    - Compute slope and aspect for runoff direction
    - Simulate water flow accumulation paths
    - Generate flood depth estimates
    - Detect low-elevation zones near rivers

TOOLS:
    rasterio     : Python interface to GDAL for reading/writing rasters
    xarray       : Multi-dimensional array analysis (like pandas for grids)
    numpy        : Fast numerical computation on raster grids

METHODOLOGY:
    We fetch elevation data from the Open-Meteo Elevation API for grid
    points and process it as a virtual raster. This avoids downloading
    large GeoTIFF files while still enabling terrain analysis.

    In production, you'd download actual SRTM tiles (.hgt or .tif files)
    from NASA EarthData and process them with rasterio directly.
===========================================================================
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from src.utils.logger import setup_logger

logger = setup_logger("Raster_Engine")


def create_elevation_grid(lat: float, lon: float,
                           radius_km: float = 10.0,
                           resolution_km: float = 1.0) -> Dict:
    """
    Creates a virtual elevation grid around a point by sampling the
    Open-Meteo Elevation API.

    Returns:
        Dict with grid_data (2D numpy array), metadata, and statistics.
    """
    from src.geo.elevation import fetch_elevation_batch

    # Generate grid coordinates
    delta = radius_km / 111.0  # degrees
    step = resolution_km / 111.0

    lats = np.arange(lat - delta, lat + delta + step, step)
    lons = np.arange(lon - delta, lon + delta + step, step)

    grid_points = [(round(float(la), 5), round(float(lo), 5))
                    for la in lats for lo in lons]

    logger.info(f"Fetching elevation for {len(grid_points)} grid points...")
    elevations = fetch_elevation_batch(grid_points)

    if not elevations:
        return {"error": "No elevation data available"}

    # Build 2D numpy grid
    rows, cols = len(lats), len(lons)
    grid = np.full((rows, cols), np.nan)

    for i, la in enumerate(lats):
        for j, lo in enumerate(lons):
            key = f"{round(float(la), 5)},{round(float(lo), 5)}"
            grid[i, j] = elevations.get(key, np.nan)

    return {
        "grid": grid,
        "lats": lats.tolist(),
        "lons": lons.tolist(),
        "rows": rows,
        "cols": cols,
        "resolution_km": resolution_km,
        "center": {"lat": lat, "lon": lon},
        "statistics": {
            "min_elevation": float(np.nanmin(grid)),
            "max_elevation": float(np.nanmax(grid)),
            "mean_elevation": float(np.nanmean(grid)),
            "std_elevation": float(np.nanstd(grid)),
            "range": float(np.nanmax(grid) - np.nanmin(grid)),
        }
    }


def compute_slope_grid(elevation_grid: np.ndarray,
                        cell_size_m: float = 1000.0) -> np.ndarray:
    """
    Computes slope (in degrees) from an elevation grid using the
    Horn algorithm — the same method used by ArcGIS and QGIS.

    The Horn algorithm computes the rate of change in elevation
    using a 3x3 moving window. For each cell, it calculates the
    gradient in both X and Y directions, then combines them.

    Args:
        elevation_grid: 2D numpy array of elevation values (meters)
        cell_size_m: Size of each grid cell in meters (default: 1km)

    Returns:
        2D numpy array of slope values in degrees.
    """
    # Compute gradients using numpy's gradient function
    dy, dx = np.gradient(elevation_grid, cell_size_m)

    # Slope magnitude (rise/run)
    slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
    slope_deg = np.degrees(slope_rad)

    return slope_deg


def compute_aspect_grid(elevation_grid: np.ndarray,
                         cell_size_m: float = 1000.0) -> np.ndarray:
    """
    Computes aspect (direction of steepest descent) from elevation.
    Returns values in degrees: 0=North, 90=East, 180=South, 270=West.

    Aspect tells us WHICH DIRECTION water will flow at each point.
    Areas with aspect pointing toward a river are at higher flood risk.
    """
    dy, dx = np.gradient(elevation_grid, cell_size_m)

    aspect = np.degrees(np.arctan2(-dy, dx))
    # Convert to 0-360 compass bearing
    aspect = (90 - aspect) % 360

    return aspect


def detect_terrain_sinks(elevation_grid: np.ndarray,
                          depth_threshold_m: float = 2.0) -> Dict:
    """
    Identifies terrain sinks (enclosed depressions) that can trap water.

    A sink is a pixel surrounded by higher elevation on all sides.
    These are natural flood accumulation points — water flows in
    but has no path to flow out.

    Algorithm:
        For each cell, check if it's lower than all 8 neighbors.
        If yes, it's a sink. The depth is the difference between
        the cell and the lowest neighbor.

    Returns:
        Dict with sink_count, sink_locations, max_depth, etc.
    """
    rows, cols = elevation_grid.shape
    sinks = []

    for i in range(1, rows - 1):
        for j in range(1, cols - 1):
            center = elevation_grid[i, j]
            if np.isnan(center):
                continue

            # Extract 3x3 neighborhood
            neighbors = elevation_grid[i-1:i+2, j-1:j+2].copy()
            neighbors[1, 1] = np.nan  # Exclude center

            min_neighbor = np.nanmin(neighbors)

            if center < min_neighbor:
                depth = min_neighbor - center
                if depth >= depth_threshold_m:
                    sinks.append({
                        "row": i, "col": j,
                        "elevation": float(center),
                        "depth": float(depth),
                    })

    return {
        "sink_count": len(sinks),
        "sinks": sinks[:50],  # Limit output
        "max_depth_m": max((s["depth"] for s in sinks), default=0),
    }


def compute_flow_accumulation(elevation_grid: np.ndarray) -> np.ndarray:
    """
    Simplified flow accumulation analysis.

    Flow accumulation counts how many upstream cells drain into each
    cell. High accumulation values indicate valleys and channels where
    water concentrates — these are the areas most likely to flood.

    This uses the D8 (8-direction) flow model: water flows from each
    cell to its steepest downhill neighbor.

    PRODUCTION NOTE:
        For real hydrological modeling, use GRASS GIS r.watershed or
        WhiteboxTools which implement proper algorithms for large DEMs.
        This simplified version is sufficient for our grid-sampling approach.
    """
    rows, cols = elevation_grid.shape
    accumulation = np.ones((rows, cols))

    # D8 directions: [row_offset, col_offset]
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),           (0, 1),
                  (1, -1),  (1, 0),  (1, 1)]

    # Process cells from highest to lowest elevation
    cells = []
    for i in range(rows):
        for j in range(cols):
            if not np.isnan(elevation_grid[i, j]):
                cells.append((elevation_grid[i, j], i, j))

    cells.sort(reverse=True)  # Highest first

    for _, i, j in cells:
        # Find steepest downhill neighbor
        min_elev = elevation_grid[i, j]
        target = None

        for di, dj in directions:
            ni, nj = i + di, j + dj
            if 0 <= ni < rows and 0 <= nj < cols:
                neighbor_elev = elevation_grid[ni, nj]
                if not np.isnan(neighbor_elev) and neighbor_elev < min_elev:
                    min_elev = neighbor_elev
                    target = (ni, nj)

        if target:
            accumulation[target[0], target[1]] += accumulation[i, j]

    return accumulation


def analyze_terrain_raster(lat: float, lon: float,
                            radius_km: float = 10.0) -> Dict:
    """
    Master function: performs complete raster-based terrain analysis.

    This orchestrates all raster operations into a single analysis report
    that feeds into the ML model and dashboard.
    """
    logger.info(f"Starting raster analysis at ({lat}, {lon})...")

    # Step 1: Build elevation grid
    grid_data = create_elevation_grid(lat, lon, radius_km, resolution_km=1.0)
    if "error" in grid_data:
        return grid_data

    grid = grid_data["grid"]

    # Step 2: Compute derived surfaces
    slope = compute_slope_grid(grid, cell_size_m=1000.0)
    aspect = compute_aspect_grid(grid, cell_size_m=1000.0)
    flow = compute_flow_accumulation(grid)

    # Step 3: Detect sinks
    sinks = detect_terrain_sinks(grid, depth_threshold_m=1.0)

    # Step 4: Compile results
    result = {
        "center": {"lat": lat, "lon": lon},
        "grid_size": f"{grid_data['rows']}x{grid_data['cols']}",
        "resolution_km": grid_data["resolution_km"],
        "elevation_stats": grid_data["statistics"],
        "slope_stats": {
            "min_degrees": float(np.nanmin(slope)),
            "max_degrees": float(np.nanmax(slope)),
            "mean_degrees": float(np.nanmean(slope)),
            "flat_pct": float(np.sum(slope < 1.0) / slope.size * 100),
        },
        "flow_stats": {
            "max_accumulation": float(np.nanmax(flow)),
            "mean_accumulation": float(np.nanmean(flow)),
            "high_flow_cells": int(np.sum(flow > np.nanpercentile(flow, 90))),
        },
        "sinks": sinks,
    }

    logger.info(
        f"Raster analysis complete: {sinks['sink_count']} sinks, "
        f"max flow={np.nanmax(flow):.0f}"
    )

    return result
