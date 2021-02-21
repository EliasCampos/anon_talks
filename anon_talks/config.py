import os
from pathlib import Path

from dotenv import load_dotenv


ROOT_PATH = Path(__file__).resolve().parent.parent
for env_dir in ('bot', 'db'):
    load_dotenv(dotenv_path=(ROOT_PATH / 'envs' / env_dir / '.env'))


BOT_API_TOKEN = os.getenv('BOT_API_TOKEN')
BOT_WEBHOOK_HOST = os.getenv('BOT_WEBHOOK_HOST')

WEBAPP_HOST = os.getenv('WEBAPP_HOST', 'localhost')
WEBAPP_PORT = 3001

DATABASE_CREDENTIALS = {
    'host': os.getenv('POSTGRES_HOST'),
    'port': os.getenv('POSTGRES_PORT'),
    'database': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD')
}
