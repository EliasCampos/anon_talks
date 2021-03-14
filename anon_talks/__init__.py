import logging

from aiogram.dispatcher import Dispatcher
from aiogram.utils.executor import start_webhook
from tortoise import run_async, Tortoise
from tortoise.backends.base.config_generator import generate_config

from anon_talks import config
from anon_talks.integrations.botlytics import BotlyticsClient
from anon_talks.bot import bot, dispatcher, AnalyticsMiddleware


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


async def _on_startup(dp: Dispatcher):
    if config.BOTLYTICS_API_KEY:
        analytics_client = BotlyticsClient(api_key=config.BOTLYTICS_API_KEY)
        dp['analytic_client'] = analytics_client
        dp.middleware.setup(AnalyticsMiddleware(analytic_client=analytics_client))

    await _init_db()


async def _on_shutdown(dp: Dispatcher):
    logging.warning('Shutting down...')
    await Tortoise.close_connections()
    logging.info("Tortoise-ORM shutdown.")

    if 'analytic_client' in dp:
        await dp['analytic_client'].close_session()


async def _init_db(db_url=None):
    db_config = generate_config(
        db_url=db_url or config.DATABASE_URL,
        app_modules={'anon_talks': ['anon_talks.models']},
        connection_label='anon_talks',
    )
    await Tortoise.init(config=db_config)
    logging.info("Tortoise-ORM started.")


async def _sync_db(db_url=None):
    await _init_db(db_url)
    await Tortoise.generate_schemas(safe=False)
    logging.info("Model schemas are generated.")
