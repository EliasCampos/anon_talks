import logging
from urllib.parse import urljoin

from aiogram.utils.executor import start_webhook
from tortoise import Tortoise

from anon_talks.bot import bot, dispatcher
from anon_talks import config

logging.basicConfig(level=logging.INFO)  # Configure logging


_WEBHOOK_PATH = f'/callback/{config.BOT_API_TOKEN}/'


async def _init_orm():
    db_config = {
        'connections': {
            'default': {
                'engine': 'tortoise.backends.asyncpg',
                'credentials': config.DATABASE_CREDENTIALS,
            }
        },
        'apps': {
            'conversations': {
                'models': ['anon_talks.models'],
            }
        },
        'use_tz': False,
        'timezone': 'UTC'
    }

    await Tortoise.init(config=db_config)
    logging.info("Tortoise-ORM started.")
    await Tortoise.generate_schemas()


async def _close_orm():
    await Tortoise.close_connections()
    logging.info("Tortoise-ORM shutdown.")


async def _on_startup(__):
    webhook_url = urljoin(f'https://{config.BOT_WEBHOOK_HOST}', _WEBHOOK_PATH)
    await bot.set_webhook(webhook_url)
    await _init_orm()


async def _on_shutdown(__):
    logging.warning('Shutting down...')
    await bot.delete_webhook()
    await _close_orm()


def start():
    start_webhook(
        dispatcher=dispatcher,
        webhook_path=_WEBHOOK_PATH,
        on_startup=_on_startup,
        on_shutdown=_on_shutdown,
        skip_updates=True,
        host=config.WEBAPP_HOST,
        port=config.WEBAPP_PORT,
    )
