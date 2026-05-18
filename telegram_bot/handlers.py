import httpx
from telegram import Update
from telegram.ext import ContextTypes
from telegram_bot.config import FASTAPI_BASE_URL
from src.utils.logger import setup_logger

logger = setup_logger("Telegram_Handlers")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /start command.
    """
    user = update.effective_user.first_name
    msg = f"👋 Hello, {user}!\n\n"
    msg += "I am the *AI Disaster Intelligence Bot* 🌊🤖\n\n"
    msg += "I monitor real-time weather streams and use Machine Learning to predict floods before they happen.\n\n"
    msg += "*Commands:*\n"
    msg += "/status - Check API and ML System Health\n"
    msg += "/alerts - View active disaster warnings\n"
    msg += "/predict <city> - Run a live AI prediction for a city\n"
    
    await update.message.reply_text(msg, parse_mode="Markdown")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Fetches the /health endpoint from our FastAPI backend.
    """
    await update.message.reply_chat_action(action="typing")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{FASTAPI_BASE_URL}/health", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                msg = "⚙️ *System Status*\n\n"
                msg += f"Status: `{data['status'].upper()}`\n"
                msg += f"ML Engine Loaded: `{'Yes' if data['model_loaded'] else 'No'}`\n"
                msg += f"Data Points: `{data['dataset_rows']:,}`\n"
                msg += f"Uptime: `{data['uptime']}`\n"
                await update.message.reply_text(msg, parse_mode="Markdown")
            else:
                await update.message.reply_text("⚠️ FastAPI Backend returned an error.")
    except Exception as e:
        logger.error(f"Telegram status_command failed: {e}")
        await update.message.reply_text("🚨 Could not reach the FastAPI backend. Is it running?")

async def predict_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Runs an on-demand prediction by querying the FastAPI /predict endpoint.
    Usage: /predict Mumbai
    """
    if not context.args:
        await update.message.reply_text("Please specify a city. Example: `/predict Mumbai`", parse_mode="Markdown")
        return
        
    city = " ".join(context.args)
    await update.message.reply_chat_action(action="typing")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{FASTAPI_BASE_URL}/predict/{city}", timeout=5.0)
            
            if response.status_code == 404:
                await update.message.reply_text(f"❌ City '{city}' not found in the tracking system.")
                return
            elif response.status_code == 200:
                data = response.json()
                risk = data['risk_level']
                emoji = "🚨" if risk == "HIGH" else "⚠️" if risk == "MEDIUM" else "✅"
                
                msg = f"{emoji} *Prediction for {data['city']}*\n\n"
                msg += f"Risk Level: *{risk}*\n"
                msg += f"Confidence: *{data['confidence']*100:.1f}%*\n\n"
                msg += f"🌡️ *Current Metrics:*\n"
                msg += f"Rain (24h): `{data['weather']['rainfall_last_24h']} mm`\n"
                msg += f"Temperature: `{data['weather']['temperature_2m']} °C`\n"
                msg += f"Soil Moisture: `{data['weather']['soil_moisture_0_to_1cm']} m³/m³`"
                
                await update.message.reply_text(msg, parse_mode="Markdown")
            else:
                await update.message.reply_text("⚠️ FastAPI Backend encountered an error.")
    except Exception as e:
        logger.error(f"Telegram predict_command failed: {e}")
        await update.message.reply_text("🚨 Could not reach the FastAPI backend.")

async def alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Fetches active alerts from the FastAPI /alerts endpoint.
    """
    await update.message.reply_chat_action(action="typing")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{FASTAPI_BASE_URL}/alerts", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                alerts = data.get("alerts", []) if isinstance(data, dict) else data
                if not alerts:
                    await update.message.reply_text("✅ No active alerts at this time. All clear.")
                    return
                
                # Show only top 3
                msg = "🚨 *ACTIVE DISASTER ALERTS* 🚨\n\n"
                for a in alerts[:3]:
                    msg += f"*{a['city']}* - {a['risk_level']} RISK ({a['confidence']*100:.1f}%)\n"
                    msg += f"_{a['timestamp']}_\n\n"
                
                await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("🚨 Could not fetch alerts from the backend.")
