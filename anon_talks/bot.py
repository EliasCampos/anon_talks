import asyncio

from aiogram.types import Message
from aiogram.bot import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.webhook import SendMessage

from anon_talks import config
from anon_talks.integrations.botlytics import BotlyticsClient
from anon_talks.models import TelegramUser
from anon_talks.services import BotService


bot = Bot(token=config.BOT_API_TOKEN)  # Initialize bot and dispatcher
dispatcher = Dispatcher(bot)


@dispatcher.message_handler(commands=['start'])
async def register_user(message: Message):
    await BotService(bot).register_user(user_id=message.from_user.id, chat_id=message.chat.id)


@dispatcher.message_handler(commands=['help'])
async def display_help(message: Message):
    return SendMessage(message.chat.id, BotService.HELP_TEXT)


@dispatcher.message_handler()
async def handle_custom_message(message: Message):
    await BotService(bot).handle_message(message)


class AnalyticsMiddleware(BaseMiddleware):
    ANON_USER_ID = 'anon_user'

    def __init__(self, analytic_client: BotlyticsClient):
        super().__init__()
        self.analytic_client = analytic_client

    async def on_process_message(self, message: Message, __):
        # create a task for analytic logging to not block next message processing:
        asyncio.create_task(self.log_to_analytic(message=message))

    async def log_to_analytic(self, message: Message):
        tg_user = await TelegramUser.filter(tg_id=message.from_user.id).first()
        sender_id = f'user_{tg_user.pk}' if tg_user else self.ANON_USER_ID
        text = self.private_text(message.text)
        await self.analytic_client.send_message(
            text=text, kind=BotlyticsClient.KIND_INCOMING, sender_id=sender_id,
        )

    @staticmethod
    def private_text(text: str):
        """
        Check if user text is bot command or button click. If it's not, returns stub text.

        The method is used to prevent exposing of user sensitive data, when sending it to third-party service.
        """
        bot_keywords = (
            '/start',
            '/help',
            BotService.START_CONVERSATION_BTN,
            BotService.CANCEL_WAITING_OPPONENT_BTN,
            BotService.COMPLETE_CONVERSATION_BTN,
        )

        if text.strip() in bot_keywords:
            return text

        return '<private message>'
