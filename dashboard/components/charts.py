import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

def set_plotly_theme(fig):
    """Applies futuristic dark theme to any Plotly figure."""
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter", color="#94A3B8"),
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', linecolor='rgba(255,255,255,0.1)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', linecolor='rgba(255,255,255,0.1)'),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

def render_rainfall_chart(df):
    """Renders a neon area chart for historical rainfall."""
    fig = px.area(df, x='timestamp', y='rain', title="Hourly Rainfall Intensity (mm)", 
                  color_discrete_sequence=['#0080FF'])
    fig.update_traces(fillcolor='rgba(0, 128, 255, 0.2)', line=dict(width=3))
    fig = set_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

def render_soil_moisture_chart(df):
    """Renders a line chart for soil moisture trend."""
    fig = px.line(df, x='timestamp', y='soil_moisture_0_to_1cm', title="Soil Moisture Saturation", 
                  color_discrete_sequence=['#34C759'])
    fig.update_traces(line=dict(width=3))
    fig = set_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
def render_confidence_gauge(confidence: float):
    """Renders a probability gauge for AI prediction confidence."""
    color = "#FF3B30" if confidence > 0.8 else "#FF9500" if confidence > 0.5 else "#34C759"
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = confidence * 100,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "AI Confidence Score", 'font': {'color': '#94A3B8', 'size': 14}},
        number = {'suffix': "%", 'font': {'color': '#FFFFFF'}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
            'bar': {'color': color},
            'bgcolor': "rgba(255,255,255,0.05)",
            'borderwidth': 2,
            'bordercolor': "rgba(255,255,255,0.1)",
            'steps': [
                {'range': [0, 50], 'color': 'rgba(52, 199, 89, 0.1)'},
                {'range': [50, 80], 'color': 'rgba(255, 149, 0, 0.1)'},
                {'range': [80, 100], 'color': 'rgba(255, 59, 48, 0.1)'}
            ]
        }
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter"),
        height=250,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
