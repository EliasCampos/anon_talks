import logging

from aiogram.utils.executor import start_webhook
from tortoise import run_async, Tortoise
from tortoise.backends.base.config_generator import generate_config

from anon_talks import config
from anon_talks.bot import bot, dispatcher


logging.basicConfig(level=logging.INFO)


def start(socket_name=None):
    if socket_name:
        path = str(config.ROOT_PATH / 'socks' / socket_name)
        host = None
        port = None
    else:
        path = None
        host = config.WEBAPP_HOST
        port = config.WEBAPP_PORT

    webhook_path = f'/callback/{config.BOT_API_TOKEN}/'
    start_webhook(
        dispatcher=dispatcher,
        webhook_path=webhook_path,
        on_startup=_on_startup,
        on_shutdown=_on_shutdown,
        skip_updates=True,
        host=host,
        port=port,
        path=path,
    )


def sync_db():
    run_async(_sync_db())


async def _on_startup(__):
    await _init_db()


async def _on_shutdown(__):
    logging.warning('Shutting down...')
    await Tortoise.close_connections()
    logging.info("Tortoise-ORM shutdown.")


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
    logging.info("Model schemas are generated.")
