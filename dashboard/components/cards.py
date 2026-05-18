import streamlit as st

def render_metric_card(title: str, value: str, icon: str, delta: str = None, color: str = "#FFFFFF"):
    """
    Renders a futuristic glassmorphic metric card using HTML/CSS.
    """
    delta_html = ""
    if delta:
        delta_color = "#34C759" if "+" in delta else "#FF3B30"
        delta_html = f"<span style='font-size: 0.9rem; color: {delta_color}; margin-left: 10px;'>{delta}</span>"
        
    html = f"""
    <div class="metric-card">
        <div class="metric-title">{icon} {title}</div>
        <div class="metric-value" style="color: {color}">{value} {delta_html}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_alert_panel(alerts: list):
    """
    Renders the emergency blinking alert panel.
    """
    if not alerts:
        st.markdown("""
        <div style="background: rgba(52, 199, 89, 0.1); border-left: 4px solid #34C759; padding: 15px; border-radius: 8px;">
            <h4 style="color: #34C759; margin:0;">✅ System Nominal</h4>
            <p style="margin:0; font-size: 0.9rem;">No active disaster alerts.</p>
        </div>
        """, unsafe_allow_html=True)
        return
        
    for a in alerts[:5]:
        if a['risk_level'] == "HIGH":
            st.markdown(f"""
            <div class="alert-panel">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h4 style="color: #FF3B30; margin:0;">🚨 HIGH RISK: {a['city']}</h4>
                    <span style="color: #94A3B8; font-size:0.8rem;">{a['timestamp']}</span>
                </div>
                <p style="margin:5px 0 0 0; font-size: 0.95rem;">{a['message']}</p>
                <div style="margin-top:8px; font-size:0.85rem; color:#FF9500;">
                    AI Confidence: {a['confidence']*100:.1f}%
                </div>
            </div>
            """, unsafe_allow_html=True)
        elif a['risk_level'] == "MEDIUM":
            st.warning(f"**{a['city']}** - {a['message']}")
