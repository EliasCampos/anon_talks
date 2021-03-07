import logging
from urllib.parse import urljoin

from aiogram.utils.executor import start_webhook
from tortoise import run_async, Tortoise
from tortoise.backends.base.config_generator import generate_config

from anon_talks import config
from anon_talks.bot import bot, dispatcher


logging.basicConfig(level=logging.INFO)


WEBHOOK_PATH = f'/callback/{config.BOT_API_TOKEN}/'


def start():
    start_webhook(
        dispatcher=dispatcher,
        webhook_path=WEBHOOK_PATH,
        on_startup=_on_startup,
        on_shutdown=_on_shutdown,
        skip_updates=True,
        host=config.WEBAPP_HOST,
        port=config.WEBAPP_PORT,
    )


def sync_db():
    run_async(_sync_db())


async def _on_startup(__):
    webhook_url = urljoin(f'https://{config.BOT_WEBHOOK_HOST}', WEBHOOK_PATH)
    await bot.set_webhook(webhook_url)
    await _init_db()


async def _on_shutdown(__):
    logging.warning('Shutting down...')
    await Tortoise.close_connections()
    logging.info("Tortoise-ORM shutdown.")

    await bot.delete_webhook()


async def _init_db():
    db_config = generate_config(
        db_url=config.DATABASE_URL,
        app_modules={'anon_talks': ['anon_talks.models']},
        connection_label='anon_talks',
    )
    await Tortoise.init(config=db_config)
    logging.info("Tortoise-ORM started.")


async def _sync_db():
    await _init_db()
    await Tortoise.generate_schemas(safe=False)
    logging.info("Model schemes are generated.")
