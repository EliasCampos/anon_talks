import logging
from urllib.parse import urljoin

from aiogram.types import Message
from aiogram.bot import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.webhook import SendMessage
from aiogram.utils.executor import start_webhook

import config


logging.basicConfig(level=logging.INFO)  # Configure logging


bot = Bot(token=config.BOT_API_TOKEN)  # Initialize bot and dispatcher
dispatcher = Dispatcher(bot)


WEBHOOK_PATH = f'/callback/{config.BOT_API_TOKEN}/'


@dispatcher.message_handler()
async def echo(message: Message):
    return SendMessage(message.chat.id, message.text)  # reply into webhook


async def on_startup(__):
    webhook_url = urljoin(f'https://{config.BOT_WEBHOOK_HOST}', WEBHOOK_PATH)
    await bot.set_webhook(webhook_url)


async def on_shutdown(__):
    logging.warning('Shutting down...')
    await bot.delete_webhook()


if __name__ == '__main__':
    start_webhook(
        dispatcher=dispatcher,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=config.WEBAPP_HOST,
        port=config.WEBAPP_PORT,
    )
