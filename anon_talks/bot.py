from aiogram.types import Message
from aiogram.bot import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.webhook import SendMessage

from anon_talks import config
from anon_talks.services import BotService


bot = Bot(token=config.BOT_API_TOKEN)  # Initialize bot and dispatcher
dispatcher = Dispatcher(bot)


@dispatcher.message_handler(commands=['start'])
async def register_user(message: Message):
    await BotService(bot).register_user(user_id=message.from_user.id, chat_id=message.chat.id)


@dispatcher.message_handler()
async def echo(message: Message):
    return SendMessage(message.chat.id, message.text)
