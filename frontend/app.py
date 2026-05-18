import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

# ============================================
# PAGE CONFIGURATION & STYLING
# ============================================
st.set_page_config(
    page_title="Flood Prediction AI",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        background-color: #0d6efd;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px 24px;
        border: none;
        width: 100%;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #0b5ed7;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .risk-low { color: #198754; font-weight: bold; }
    .risk-medium { color: #ffc107; font-weight: bold; }
    .risk-high { color: #dc3545; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# ============================================
# CONSTANTS & API
# ============================================
API_URL = "http://127.0.0.1:8000"

FEATURES = [
    'MonsoonIntensity', 'TopographyDrainage', 'RiverManagement', 'Deforestation',
    'Urbanization', 'ClimateChange', 'DamsQuality', 'Siltation', 'AgriculturalPractices',
    'Encroachments', 'IneffectiveDisasterPreparedness', 'DrainageSystems',
    'CoastalVulnerability', 'Landslides', 'Watersheds', 'DeterioratingInfrastructure',
    'PopulationScore', 'WetlandLoss', 'InadequatePlanning', 'PoliticalFactors'
]

# ============================================
# SIDEBAR: PROJECT INFO & METRICS
# ============================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3039/3039535.png", width=80)
    st.title("AI System Info")
    st.markdown("---")
    
    st.subheader("🤖 Model Info")
    st.markdown("- **Algorithm**: XGBoost Regressor")
    st.markdown("- **Type**: Gradient Boosting")
    st.markdown("- **Trees**: 300")
    
    st.markdown("---")
    st.subheader("📊 Performance Metrics")
    st.markdown("- **MAE**: ~0.015")
    st.markdown("- **RMSE**: ~0.020")
    st.markdown("- **R² Score**: ~0.85")
    
    st.markdown("---")
    st.subheader("🔌 Backend Status")
    try:
        res = requests.get(f"{API_URL}/")
        if res.status_code == 200:
            st.success("API is Online")
        else:
            st.warning("API returned an error")
    except Exception:
        st.error("API is Offline")

# ============================================
# MAIN UI: SECTION 1 (OVERVIEW)
# ============================================
st.title("🌊 Flood Risk Prediction System")
st.markdown("""
This professional dashboard leverages an advanced **XGBoost Machine Learning Model** to assess flood probabilities. 
Adjust the environmental and socio-political factors below to simulate different scenarios and predict the associated flood risk.
""")
st.markdown("---")

# ============================================
# MAIN UI: SECTION 2 (INPUTS)
# ============================================
st.subheader("🌍 Environmental & Regional Factors (0-20 scale)")

# Create a 4-column layout for the 20 inputs
col1, col2, col3, col4 = st.columns(4)
columns = [col1, col2, col3, col4]

input_data = {}

for i, feature in enumerate(FEATURES):
    # Determine which column to place the input in
    col = columns[i % 4]
    with col:
        # Format feature name for display (e.g., "MonsoonIntensity" -> "Monsoon Intensity")
        display_name = "".join([" " + c if c.isupper() else c for c in feature]).strip()
        # Use number_input for precision, slider can be clunky for 20 items
        input_data[feature] = st.slider(display_name, min_value=0, max_value=20, value=5, step=1)

st.markdown("---")

# ============================================
# PREDICTION LOGIC & GAUGE CHART
# ============================================
st.subheader("🎯 Risk Assessment")

col_btn, col_res = st.columns([1, 2])

with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    predict_clicked = st.button("Predict Flood Risk 🚀")

with col_res:
    if predict_clicked:
        with st.spinner("Analyzing environmental data..."):
            try:
                # Send POST request to FastAPI backend
                response = requests.post(f"{API_URL}/predict", json=input_data, timeout=10)
                response.raise_for_status()
                
                result = response.json()
                prob = result["predicted_flood_probability"]
                risk_level = result["risk_assessment"]
                
                # Determine colors based on risk
                if risk_level == "LOW":
                    color = "#198754" # Green
                elif risk_level == "MEDIUM":
                    color = "#ffc107" # Yellow
                else:
                    color = "#dc3545" # Red
                
                # Plotly Gauge Chart
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = prob * 100,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': f"<b>Risk Level: {risk_level}</b><br><span style='font-size:0.8em;color:gray'>Predicted Probability (%)</span>", 'font': {'size': 20}},
                    gauge = {
                        'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                        'bar': {'color': color},
                        'bgcolor': "white",
                        'borderwidth': 2,
                        'bordercolor': "gray",
                        'steps': [
                            {'range': [0, 30], 'color': 'rgba(25, 135, 84, 0.2)'},
                            {'range': [30, 60], 'color': 'rgba(255, 193, 7, 0.2)'},
                            {'range': [60, 100], 'color': 'rgba(220, 53, 69, 0.2)'}],
                        'threshold': {
                            'line': {'color': "black", 'width': 4},
                            'thickness': 0.75,
                            'value': prob * 100}
                    }
                ))
                
                fig.update_layout(height=350, margin=dict(l=10, r=10, t=50, b=10))
                st.plotly_chart(fig, use_container_width=True)
                
            except requests.exceptions.ConnectionError:
                st.error("🚨 **Connection Error:** Could not reach the FastAPI backend. Make sure it is running on http://127.0.0.1:8000.")
            except requests.exceptions.HTTPError as e:
                st.error(f"🚨 **API Error:** {e.response.text}")
            except Exception as e:
                st.error(f"🚨 **Unexpected Error:** {str(e)}")
    else:
        st.info("Adjust the parameters and click 'Predict Flood Risk' to see the assessment.")
