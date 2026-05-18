import pydeck as pdk
import streamlit as st
import pandas as pd

# Coordinates for mapping
CITY_COORDS = {
    "Mumbai": [19.0760, 72.8777],
    "Delhi": [28.7041, 77.1025],
    "Kolkata": [22.5726, 88.3639],
    "Chennai": [13.0827, 80.2707],
    "Bengaluru": [12.9716, 77.5946]
}

def render_risk_map(predictions: list):
    """
    Renders a stunning 3D PyDeck map showing city risk levels.
    """
    if not predictions:
        st.warning("No live map data available.")
        return
        
    map_data = []
    for p in predictions:
        city = p['city']
        if city in CITY_COORDS:
            lat, lon = CITY_COORDS[city]
            risk = p['risk_level']
            
            # Color coding
            if risk == "HIGH":
                color = [255, 59, 48, 200]
                radius = 50000
            elif risk == "MEDIUM":
                color = [255, 149, 0, 150]
                radius = 30000
            else:
                color = [52, 199, 89, 100]
                radius = 15000
                
            map_data.append({
                "city": city,
                "lat": lat,
                "lon": lon,
                "risk": risk,
                "confidence": p.get('confidence', 0),
                "color": color,
                "radius": radius
            })
            
    df_map = pd.DataFrame(map_data)
    
    if df_map.empty:
        return

    # PyDeck Map
    view_state = pdk.ViewState(
        latitude=20.5937, 
        longitude=78.9629, 
        zoom=3.5, 
        pitch=45
    )
    
    layer = pdk.Layer(
        "ScatterplotLayer",
        df_map,
        pickable=True,
        opacity=0.8,
        stroked=True,
        filled=True,
        radius_scale=1,
        radius_min_pixels=10,
        radius_max_pixels=100,
        line_width_min_pixels=1,
        get_position="[lon, lat]",
        get_radius="radius",
        get_fill_color="color",
        get_line_color=[255, 255, 255, 100],
    )

    tooltip = {
        "html": "<b>{city}</b><br/>Risk Level: {risk}<br/>AI Confidence: {confidence}",
        "style": {"background": "rgba(20, 20, 20, 0.9)", "color": "white", "font-family": "Inter", "z-index": "10000"}
    }
    
    r = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip, map_style="mapbox://styles/mapbox/dark-v10")
    st.pydeck_chart(r)
