import requests
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Ensure paths
sys.path.append(str(Path(__file__).resolve().parent.parent))

from telegram_bot.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, validate_config
from src.utils.logger import setup_logger

logger = setup_logger("Telegram_Sender")

# State tracking to prevent spam (throttling)
# In production, this would be stored in Redis.
last_alert_sent = {}

def send_telegram_alert(city: str, risk_level: str, confidence: float, metrics: dict):
    """
    Sends a formatted alert message directly to Telegram.
    Implements throttling to prevent spamming the user.
    """
    if not validate_config():
        return
        
    # --- THROTTLING LOGIC ---
    now = datetime.now()
    if city in last_alert_sent:
        time_since_last = now - last_alert_sent[city]
        if time_since_last < timedelta(minutes=60):
            # Block duplicate alerts within 60 minutes for the same city
            logger.info(f"Telegram throttled for {city}. Sent {time_since_last.seconds // 60}m ago.")
            return

    # --- MESSAGE CONSTRUCTION ---
    emoji = "🚨" if risk_level == "HIGH" else "⚠️"
    
    msg = f"{emoji} *{risk_level} FLOOD RISK ALERT* {emoji}\n\n"
    msg += f"📍 *City:* {city}\n"
    msg += f"🎯 *AI Confidence:* {confidence*100:.1f}%\n"
    msg += f"⏰ *Time:* {now.strftime('%Y-%m-%d %H:%M IST')}\n\n"
    
    msg += f"📊 *Live Environmental Metrics:*\n"
    msg += f"• Rain (24h): {metrics.get('rainfall_last_24h', 0):.1f} mm\n"
    msg += f"• Soil Moisture: {metrics.get('soil_moisture_0_to_1cm', 0):.3f} m³/m³\n"
    msg += f"• Current Rain: {metrics.get('rain', 0):.1f} mm/h\n"
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            logger.info(f"Successfully broadcasted Telegram alert for {city}.")
            last_alert_sent[city] = now
        else:
            logger.error(f"Telegram API Error: {response.text}")
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")
