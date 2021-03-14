import os
from pathlib import Path

from dotenv import load_dotenv


ROOT_PATH = Path(__file__).resolve().parent.parent

load_dotenv(dotenv_path=(ROOT_PATH / 'envs' / 'bot' / '.env'))


# Database
# ------------------------------------------------------------------------------
DATABASE_URL = os.getenv('DATABASE_URL')

# Telegram Bot
# ------------------------------------------------------------------------------
BOT_API_TOKEN = os.getenv('BOT_API_TOKEN')

WEBAPP_HOST = os.getenv('WEBAPP_HOST', 'localhost')
WEBAPP_PORT = os.getenv('WEBAPP_PORT', 3001)

# Bot analytics
# https://botlytics.api-docs.io/v1/
# ------------------------------------------------------------------------------
BOTLYTICS_API_KEY = os.getenv('BOTLYTICS_API_KEY', '')

# Custom settings
# ------------------------------------------------------------------------------
RECENT_OPPONENT_TIMEOUT = 5  # in minutes
