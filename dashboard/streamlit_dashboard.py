import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from dashboard.utils.api_client import (
    fetch_live_predictions, fetch_alerts, fetch_system_health,
    fetch_historical_data, fetch_global_risk, fetch_geo_profile,
    fetch_spatial_risk_map, fetch_spatial_flood_polygons,
    fetch_spatial_stats, fetch_spatial_events
)
from dashboard.styles.custom_css import apply_custom_css
from dashboard.components.cards import render_metric_card, render_alert_panel
from dashboard.components.charts import (
    render_rainfall_chart, render_soil_moisture_chart, render_confidence_gauge
)
from dashboard.components.global_map import (
    render_global_flood_map, render_fsi_breakdown, render_spatial_stats_panel
)

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="Enterprise Spatial Flood Intelligence",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_css()
st_autorefresh(interval=60000, limit=None, key="dashboard_autorefresh")

# ==========================================
# DATA FETCHING
# ==========================================
health = fetch_system_health()
predictions = fetch_live_predictions()
alerts = fetch_alerts()
df_history = fetch_historical_data()
geo_risk = fetch_global_risk()
spatial_stats = fetch_spatial_stats()

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 10px 0;">
        <span style="font-size: 48px;">🛰️</span>
        <h2 style="margin: 5px 0 0 0; background: linear-gradient(135deg, #00BFFF, #AF52DE);
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                   font-size: 20px;">Spatial Flood Intelligence</h2>
        <p style="color: #64748B; font-size: 12px; margin-top: 2px;">v3.0 | PostGIS Enterprise</p>
    </div>
    """, unsafe_allow_html=True)

    cities = [p['city'] for p in predictions] if predictions else []
    selected_city = st.selectbox("🌍 Target Region", ["Global Overview"] + cities)

    st.markdown("<hr style='border-color: rgba(255,255,255,0.1);'/>", unsafe_allow_html=True)

    # Infrastructure status
    st.markdown("### ⚙️ Infrastructure")
    if health.get("status") == "healthy":
        st.markdown("🟢 **API Gateway:** Online")
        st.markdown("🟢 **ML Engine:** Loaded")
        st.markdown("🟢 **PostGIS:** Active")
        st.markdown("🟢 **GIS Engine:** Active")
        st.markdown(f"💾 **Data Lake:** {health.get('dataset_rows', 0):,} rows")
        st.markdown(f"⏱️ **Uptime:** {health.get('uptime', '0h 0m')}")
    else:
        st.markdown("🔴 **API Gateway:** Offline")
        st.error("Backend unreachable.")

    st.markdown("<hr style='border-color: rgba(255,255,255,0.1);'/>", unsafe_allow_html=True)
    st.markdown("### 📡 Data Sources")
    st.markdown("✅ Open-Meteo Weather API")
    st.markdown("✅ NASA SRTM Elevation")
    st.markdown("✅ GPM Satellite Precip")
    st.markdown("✅ OSM River Networks")
    st.markdown("✅ PostGIS Spatial DB")

    # PostGIS stats in sidebar
    counts = spatial_stats.get("table_counts", {})
    if counts and "error" not in counts:
        st.markdown("<hr style='border-color: rgba(255,255,255,0.1);'/>", unsafe_allow_html=True)
        st.markdown("### 🗄️ PostGIS Data")
        st.markdown(f"🟣 Flood Zones: **{counts.get('flood_zones', 0)}**")
        st.markdown(f"🔵 River Segments: **{counts.get('river_segments', 0)}**")
        st.markdown(f"🔴 Risk Regions: **{counts.get('risk_regions', 0)}**")
        st.markdown(f"🟡 Spatial Events: **{counts.get('geospatial_events', 0)}**")


# ==========================================
# TAB NAVIGATION
# ==========================================
tab_overview, tab_spatial, tab_geo, tab_drill = st.tabs([
    "🌐 Global Overview",
    "🗺️ Spatial Intelligence",
    "🛰️ Geospatial Profiles",
    "📍 City Drilldown"
])

# ==========================================
# TAB 1: GLOBAL OVERVIEW
# ==========================================
with tab_overview:
    st.markdown("""
    <div style="text-align: center; padding: 20px 0 10px;">
        <h1 style="background: linear-gradient(135deg, #00BFFF, #0080FF, #AF52DE);
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                   font-size: 32px; margin-bottom: 5px;">
            Enterprise Spatial Flood Intelligence
        </h1>
        <p style="color: #64748B; font-size: 14px; max-width: 700px; margin: 0 auto;">
            PostGIS-powered multi-layer analysis fusing satellite rainfall,
            terrain topology, river networks, flood zone polygons, and XGBoost ML.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Fetch flood polygons for map overlay
    flood_polys = fetch_spatial_flood_polygons(
        city=selected_city if selected_city != "Global Overview" else None
    )

    col_map, col_alerts = st.columns([2, 1])

    with col_map:
        st.markdown("### 🗺️ Live Spatial Risk Map")
        render_global_flood_map(
            predictions, geo_risk,
            flood_geojson=flood_polys if flood_polys.get("features") else None,
        )

    with col_alerts:
        st.markdown("### 🚨 Emergency Broadcasts")
        display_alerts = alerts if selected_city == "Global Overview" else \
            [a for a in alerts if a.get('city') == selected_city]
        render_alert_panel(display_alerts)

    # Global Metrics
    st.markdown("<br/>", unsafe_allow_html=True)
    if predictions:
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            high_risk = sum(1 for p in predictions if p.get('risk_level') == "HIGH")
            render_metric_card("High Risk", str(high_risk), "🚨", color="#FF3B30")
        with m2:
            render_metric_card("Cities", str(len(predictions)), "🌍", color="#0080FF")
        with m3:
            render_metric_card("Data Points", f"{health.get('dataset_rows', 0):,}",
                             "💾", color="#34C759")
        with m4:
            avg_conf = sum(p.get('confidence', 0) for p in predictions) / max(len(predictions), 1)
            render_metric_card("Avg Confidence", f"{avg_conf*100:.1f}%",
                             "🎯", color="#AF52DE")
        with m5:
            fz_count = counts.get("flood_zones", 0) if counts and "error" not in counts else 0
            render_metric_card("Flood Zones", str(fz_count), "🗺️", color="#FF9500")


# ==========================================
# TAB 2: SPATIAL INTELLIGENCE (PostGIS)
# ==========================================
with tab_spatial:
    st.markdown("### 🗺️ PostGIS Spatial Intelligence Layer")
    st.markdown("Polygon-based flood zone analysis, river networks, and spatial event intelligence.")

    # Spatial database stats
    render_spatial_stats_panel(spatial_stats)

    st.markdown("---")

    # Spatial events timeline
    st.markdown("#### 📋 Recent Spatial Events")
    events_data = fetch_spatial_events(hours=72)
    events_list = events_data.get("events", [])
    if events_list:
        df_events = pd.DataFrame(events_list)
        display_cols = [c for c in ["timestamp", "event_type", "severity",
                                    "city", "description", "fsi", "confidence"]
                       if c in df_events.columns]
        st.dataframe(
            df_events[display_cols].rename(columns={
                "timestamp": "Time",
                "event_type": "Event Type",
                "severity": "Severity",
                "city": "City",
                "description": "Description",
                "fsi": "FSI",
                "confidence": "Confidence"
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No spatial events in the last 72 hours. The system is monitoring...")


# ==========================================
# TAB 3: GEOSPATIAL PROFILES
# ==========================================
with tab_geo:
    st.markdown("### 🛰️ Geospatial Intelligence Profiles")
    st.markdown("Static terrain, elevation, and river proximity for all monitored locations.")

    if geo_risk:
        geo_df = pd.DataFrame(geo_risk)
        if not geo_df.empty:
            display_cols = [c for c in [
                "city", "elevation_m", "flood_zone",
                "elevation_risk_score", "distance_to_river_km",
                "river_risk_score", "basin_score"
            ] if c in geo_df.columns]

            st.dataframe(
                geo_df[display_cols].rename(columns={
                    "city": "City",
                    "elevation_m": "Elevation (m)",
                    "flood_zone": "Flood Zone",
                    "elevation_risk_score": "Terrain Risk",
                    "distance_to_river_km": "River Dist (km)",
                    "river_risk_score": "River Risk",
                    "basin_score": "Basin Score"
                }),
                use_container_width=True,
                hide_index=True
            )

        st.markdown("---")
        selected_geo_city = st.selectbox(
            "Select city for detailed profile:",
            [g["city"] for g in geo_risk],
            key="geo_city_select"
        )
        if selected_geo_city:
            profile_data = fetch_geo_profile(selected_geo_city)
            profile = profile_data.get("profile", {})
            if profile:
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("⛰️ Elevation", f"{profile.get('elevation_m', 'N/A')}m")
                    st.metric("📐 Slope", f"{profile.get('slope_percent', 0):.2f}%")
                with c2:
                    st.metric("🏔️ Basin Score", f"{profile.get('basin_score', 0):.2f}")
                    st.metric("🗺️ Flood Zone", profile.get("flood_zone", "N/A"))
                with c3:
                    st.metric("🌊 River Distance", f"{profile.get('distance_to_river_km', 0):.1f} km")
                    st.metric("⚠️ River Risk", f"{profile.get('river_risk_score', 0):.2f}")
    else:
        st.info("Geospatial data loading... Ensure the GIS engine has computed profiles.")


# ==========================================
# TAB 4: CITY DRILLDOWN
# ==========================================
with tab_drill:
    drill_city = selected_city if selected_city != "Global Overview" else (
        cities[0] if cities else None
    )

    if drill_city:
        st.markdown(f"### 📍 Region Drilldown: {drill_city}")
        city_preds = [p for p in predictions if p['city'] == drill_city]
        target = city_preds[0] if city_preds else None

        if target:
            weather = target.get('weather', {})

            # Metrics
            m1, m2, m3, m4, m5 = st.columns(5)
            risk = target.get('risk_level', 'LOW')
            with m1:
                render_metric_card("Risk Level", risk, "🛡️",
                    color="#FF3B30" if risk == "HIGH" else "#FF9500" if risk == "MEDIUM" else "#34C759")
            with m2:
                render_metric_card("Temperature", f"{weather.get('temperature_2m', 0)}°C", "🌡️")
            with m3:
                render_metric_card("Rain (24h)", f"{weather.get('rainfall_last_24h', 0)}mm", "🌧️")
            with m4:
                render_metric_card("Soil Moisture", f"{weather.get('soil_moisture_0_to_1cm', 0):.2f}", "💧")
            with m5:
                render_metric_card("Wind Speed", f"{weather.get('wind_speed_10m', 0)}km/h", "💨")

            # Charts
            st.markdown("<br/>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns([1, 1, 1])

            city_history = df_history[df_history['city'] == target['city']] \
                if not df_history.empty and 'city' in df_history.columns else pd.DataFrame()

            with c1:
                render_confidence_gauge(target.get('confidence', 0))
            with c2:
                if not city_history.empty and 'rain' in city_history.columns:
                    render_rainfall_chart(city_history.tail(24))
            with c3:
                if not city_history.empty and 'soil_moisture_trend' in city_history.columns:
                    render_soil_moisture_chart(city_history.tail(24))
    else:
        st.info("No city data available. Ensure the API backend and scheduler are running.")
