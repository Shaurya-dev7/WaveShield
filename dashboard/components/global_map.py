"""
===========================================================================
GLOBAL SPATIAL FLOOD INTELLIGENCE MAP — PostGIS-Powered
===========================================================================

Renders a multi-layer 3D interactive map with:
    Layer 1: Risk Scatter (city points colored by flood zone)
    Layer 2: Elevation Columns (3D terrain height bars)
    Layer 3: Flood Zone Polygons (PostGIS polygon overlays)
    Layer 4: River Network Lines (PostGIS linestring overlays)
    Layer 5: Rainfall Heatmap (satellite precipitation intensity)
    Layer 6: Risk Pulse (animated pulsing for active risk regions)

All polygon and linestring data is fetched from PostGIS via the
/spatial/* API endpoints in GeoJSON format.
===========================================================================
"""

import streamlit as st
import pydeck as pdk
from typing import List, Dict, Optional


def _risk_color(flood_zone: str) -> List[int]:
    """Maps flood zone classification to RGBA colors."""
    colors = {
        "CRITICAL": [255, 0, 50, 200],
        "HIGH":     [255, 100, 0, 180],
        "MODERATE": [255, 200, 0, 150],
        "LOW":      [0, 200, 100, 130],
        "UNKNOWN":  [150, 150, 150, 100],
    }
    return colors.get(flood_zone, colors["UNKNOWN"])


def _polygon_color(risk_level: str) -> List[int]:
    """Maps risk level to semi-transparent fill colors for polygons."""
    colors = {
        "CRITICAL": [255, 0, 50, 80],
        "HIGH":     [255, 100, 0, 60],
        "MODERATE": [255, 200, 0, 40],
        "LOW":      [0, 200, 100, 30],
    }
    return colors.get(risk_level, [150, 150, 150, 30])


def render_global_flood_map(predictions: list, geo_profiles: list = None,
                             flood_geojson: dict = None,
                             river_geojson: dict = None):
    """
    Renders the Global Spatial Flood Intelligence Map using PyDeck.

    This is the primary visualization component of the platform.
    It combines multiple spatial data layers into a single interactive
    3D map with dark satellite basemap.
    """
    if not predictions:
        st.info("No prediction data available for map rendering.")
        return

    # === Build scatter data (city points) ===
    scatter_data = []
    column_data = []

    for pred in predictions:
        lat = pred.get("lat", 0)
        lon = pred.get("lon", 0)
        city = pred.get("city", "Unknown")
        risk = pred.get("risk_level", "LOW")

        geo = {}
        if geo_profiles:
            matches = [g for g in geo_profiles if g.get("city", "").lower() == city.lower()]
            if matches:
                geo = matches[0]

        flood_zone = geo.get("flood_zone", "UNKNOWN")
        elevation = geo.get("elevation_m", 50)
        fsi = geo.get("elevation_risk_score", 0.3)
        color = _risk_color(flood_zone)

        scatter_data.append({
            "lat": lat, "lon": lon, "city": city, "risk": risk,
            "flood_zone": flood_zone, "elevation": elevation or 50,
            "fsi": fsi, "color": color,
            "radius": 30000 + (fsi * 50000),
        })

        if elevation:
            column_data.append({
                "lat": lat, "lon": lon,
                "elevation": max(elevation, 5),
                "color": color,
            })

    # === PyDeck Layers ===
    layers = []

    # Layer 1: Risk Scatter
    layers.append(pdk.Layer(
        "ScatterplotLayer",
        data=scatter_data,
        get_position=["lon", "lat"],
        get_radius="radius",
        get_fill_color="color",
        pickable=True, opacity=0.6, auto_highlight=True,
    ))

    # Layer 2: Elevation Columns
    if column_data:
        layers.append(pdk.Layer(
            "ColumnLayer",
            data=column_data,
            get_position=["lon", "lat"],
            get_elevation="elevation",
            elevation_scale=100,
            radius=15000,
            get_fill_color="color",
            pickable=True, auto_highlight=True,
        ))

    # Layer 3: Flood Zone Polygons (from PostGIS)
    if flood_geojson and flood_geojson.get("features"):
        # Add fill colors to each feature
        for feature in flood_geojson["features"]:
            props = feature.get("properties", {})
            risk = props.get("risk_level", "MODERATE")
            props["fill_color"] = _polygon_color(risk)
            props["line_color"] = _risk_color(risk)

        layers.append(pdk.Layer(
            "GeoJsonLayer",
            data=flood_geojson,
            opacity=0.4,
            stroked=True,
            filled=True,
            extruded=False,
            wireframe=True,
            get_fill_color="properties.fill_color",
            get_line_color="properties.line_color",
            get_line_width=2,
            pickable=True,
        ))

    # Layer 4: River Network Lines (from PostGIS)
    if river_geojson and river_geojson.get("features"):
        layers.append(pdk.Layer(
            "GeoJsonLayer",
            data=river_geojson,
            opacity=0.7,
            stroked=True,
            filled=False,
            get_line_color=[64, 176, 255, 180],
            get_line_width=3,
            pickable=True,
        ))

    # Layer 5: Rainfall Heatmap (generated from predictions with rainfall data)
    heatmap_data = []
    for pred in predictions:
        rainfall = pred.get("weather", {}).get("rainfall_last_24h", 0)
        if rainfall and rainfall > 0:
            heatmap_data.append({
                "lat": pred.get("lat", 0),
                "lon": pred.get("lon", 0),
                "weight": min(rainfall / 50.0, 1.0),
            })

    if heatmap_data:
        layers.append(pdk.Layer(
            "HeatmapLayer",
            data=heatmap_data,
            get_position=["lon", "lat"],
            get_weight="weight",
            radiusPixels=80,
            intensity=1,
            threshold=0.1,
            color_range=[
                [0, 100, 255, 0],
                [0, 150, 255, 60],
                [0, 200, 255, 120],
                [255, 200, 0, 150],
                [255, 100, 0, 200],
                [255, 0, 50, 255],
            ],
        ))

    # === View State ===
    if scatter_data:
        avg_lat = sum(d["lat"] for d in scatter_data) / len(scatter_data)
        avg_lon = sum(d["lon"] for d in scatter_data) / len(scatter_data)
    else:
        avg_lat, avg_lon = 20.0, 78.0

    view_state = pdk.ViewState(
        latitude=avg_lat, longitude=avg_lon,
        zoom=4, pitch=45, bearing=0,
    )

    tooltip = {
        "html": """
        <div style="background: rgba(0,0,0,0.9); padding: 14px; border-radius: 10px;
                    border: 1px solid rgba(0,191,255,0.3); font-family: Inter, sans-serif;
                    backdrop-filter: blur(8px);">
            <b style="color: #00BFFF; font-size: 15px;">{city}</b><br/>
            <span style="color: #FF6B35;">🗺️ Flood Zone: {flood_zone}</span><br/>
            <span style="color: #94A3B8;">⛰️ Elevation: {elevation}m</span><br/>
            <span style="color: #FF3B30;">🤖 ML Risk: {risk}</span>
        </div>
        """,
        "style": {"backgroundColor": "transparent", "color": "white"}
    }

    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style="mapbox://styles/mapbox/dark-v11",
    )

    st.pydeck_chart(deck, use_container_width=True)


def render_fsi_breakdown(geo_features: dict):
    """
    Renders a visual breakdown of the Flood Susceptibility Index
    showing the contribution of each factor as a horizontal bar chart.
    """
    import plotly.graph_objects as go

    factors = [
        ("Rainfall Intensity", geo_features.get("score_rainfall_intensity", 0), "#0080FF"),
        ("Terrain/Elevation", geo_features.get("score_terrain_elevation", 0), "#FF9500"),
        ("River Proximity", geo_features.get("score_river_proximity", 0), "#34C759"),
        ("Soil Saturation", geo_features.get("score_soil_saturation", 0), "#FF3B30"),
        ("Rainfall Anomaly", geo_features.get("score_rainfall_anomaly", 0), "#AF52DE"),
        ("Drainage Quality", geo_features.get("score_drainage_quality", 0), "#FFD60A"),
    ]

    labels = [f[0] for f in factors]
    values = [f[1] for f in factors]
    colors = [f[2] for f in factors]

    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation='h',
        marker_color=colors,
        text=[f"{v:.2f}" for v in values],
        textposition='outside',
    ))

    fig.update_layout(
        title="Flood Susceptibility Breakdown",
        xaxis_title="Risk Contribution (0-1)",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter", color="#94A3B8"),
        xaxis=dict(range=[0, 1.1], showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(showgrid=False),
        height=300,
        margin=dict(l=10, r=10, t=40, b=10),
    )

    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def render_spatial_stats_panel(stats: dict):
    """
    Renders the PostGIS spatial intelligence statistics panel.
    Shows table counts, flood zone breakdown, and spatial index health.
    """
    st.markdown("#### 🗄️ PostGIS Spatial Database")

    # Table counts
    counts = stats.get("table_counts", {})
    if counts and "error" not in counts:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Flood Zones", counts.get("flood_zones", 0))
        c2.metric("River Segments", counts.get("river_segments", 0))
        c3.metric("Risk Regions", counts.get("risk_regions", 0))
        c4.metric("Spatial Events", counts.get("geospatial_events", 0))

    # Flood zone stats
    zone_stats = stats.get("flood_zone_stats", [])
    if zone_stats:
        import pandas as pd
        df = pd.DataFrame(zone_stats)
        st.dataframe(
            df.rename(columns={
                "risk_level": "Risk Level",
                "zone_count": "Zones",
                "total_area_sq_km": "Total Area (km²)",
                "avg_min_elevation": "Avg Min Elevation (m)",
            }),
            use_container_width=True,
            hide_index=True
        )
