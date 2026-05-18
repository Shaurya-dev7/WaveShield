import streamlit as st

def apply_custom_css():
    st.markdown("""
    <style>
        /* Global Background & Font */
        .stApp {
            background-color: #0B0E14;
            font-family: 'Inter', 'Segoe UI', sans-serif;
            color: #E2E8F0;
        }
        
        /* Glassmorphism Cards */
        .metric-card {
            background: rgba(18, 24, 38, 0.6);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
            margin-bottom: 1rem;
        }
        
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 40px 0 rgba(0, 255, 128, 0.1);
            border: 1px solid rgba(0, 255, 128, 0.2);
        }
        
        .metric-title {
            color: #94A3B8;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            margin-bottom: 8px;
            font-weight: 600;
        }
        
        .metric-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: #FFFFFF;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        /* Neon Highlights for Risk Levels */
        .risk-HIGH {
            color: #FF3B30;
            text-shadow: 0 0 10px rgba(255, 59, 48, 0.5);
        }
        .risk-MEDIUM {
            color: #FF9500;
            text-shadow: 0 0 10px rgba(255, 149, 0, 0.5);
        }
        .risk-LOW {
            color: #34C759;
            text-shadow: 0 0 10px rgba(52, 199, 89, 0.4);
        }
        
        /* Emergency Alert Panel */
        .alert-panel {
            background: linear-gradient(135deg, rgba(40,10,10,0.8) 0%, rgba(20,5,5,0.9) 100%);
            border-left: 4px solid #FF3B30;
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            animation: pulse-red 2s infinite;
        }
        
        @keyframes pulse-red {
            0% { box-shadow: 0 0 0 0 rgba(255, 59, 48, 0.4); }
            70% { box-shadow: 0 0 0 10px rgba(255, 59, 48, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 59, 48, 0); }
        }
        
        /* Glowing Header */
        .hero-header {
            text-align: center;
            padding: 40px 0;
            background: radial-gradient(circle at 50% -20%, rgba(0, 128, 255, 0.15), transparent 60%);
            margin-bottom: 30px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        
        .hero-header h1 {
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(90deg, #FFFFFF, #8AB4F8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .hero-subtitle {
            color: #94A3B8;
            font-size: 1.1rem;
            max-width: 600px;
            margin: 0 auto;
        }
        
        /* Fix Streamlit Defaults */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {background-color: transparent !important;}
        
        /* Hide block fullScreen buttons on charts */
        button[title="View fullscreen"] {
            display: none;
        }
    </style>
    """, unsafe_allow_html=True)
