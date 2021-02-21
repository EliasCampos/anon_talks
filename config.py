import os

from dotenv import load_dotenv


load_dotenv()

BOT_API_TOKEN = os.getenv('BOT_API_TOKEN')
BOT_WEBHOOK_HOST = os.getenv('BOT_WEBHOOK_HOST')

WEBAPP_HOST = os.getenv('WEBAPP_HOST', 'localhost')
WEBAPP_PORT = os.getenv('WEBAPP_PORT', 3001)
