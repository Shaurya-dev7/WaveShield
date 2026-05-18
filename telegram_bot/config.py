import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# FastAPI endpoint for the bot to fetch predictions
FASTAPI_BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://localhost:8000")

def validate_config():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("WARNING: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing from .env file.")
        print("Telegram bot functionality will be disabled.")
        return False
    return True
