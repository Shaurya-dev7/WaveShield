import sys
from pathlib import Path

# Ensure paths
sys.path.append(str(Path(__file__).resolve().parent.parent))

from telegram.ext import Application, CommandHandler
from telegram_bot.config import TELEGRAM_BOT_TOKEN, validate_config
from telegram_bot.handlers import start_command, status_command, predict_command, alerts_command
from src.utils.logger import setup_logger

logger = setup_logger("Telegram_Bot_Engine")

def main():
    """
    Initializes and starts the asynchronous Telegram bot.
    """
    logger.info("Initializing Telegram Bot Engine...")
    
    if not validate_config():
        logger.error("Bot failed to start. Missing credentials in .env")
        return

    # Build the application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("predict", predict_command))
    application.add_handler(CommandHandler("alerts", alerts_command))

    logger.info("Telegram Bot Engine is now ONLINE and polling for messages.")
    
    # Run the bot until the user presses Ctrl-C
    # In production, this runs as a background service via systemd or Docker
    application.run_polling()

if __name__ == "__main__":
    main()
