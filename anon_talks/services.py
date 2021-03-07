import asyncio
from typing import Optional

from aiogram.bot import Bot
from aiogram.types.message import Message
from aiogram.types.reply_keyboard import ReplyKeyboardMarkup, KeyboardButton
from tortoise.exceptions import DoesNotExist

from anon_talks.models import Conversation, TelegramUser


class BotService:
    START_CONVERSATION_BTN = "Начать общение"
    CANCEL_WAITING_OPPONENT_BTN = "Отменить"
    COMPLETE_CONVERSATION_BTN = "Закончить общение"

    def __init__(self, bot: Bot):
        self._bot = bot

    async def register_user(self, user_id: int, chat_id: int) -> TelegramUser:
        user, is_created = await TelegramUser.get_or_create(tg_id=user_id, defaults={'tg_chat_id': chat_id})
        if not is_created:
            message_text = "Вы уже зарегистрированы."
        else:
            message_text = (
                "Добро пожаловать в анонимный чат!\n"
                "Здесь вы можете общаться с другими, не расскрывая своей личности."
            )
        await self._bot.send_message(chat_id, message_text)
        return user

    async def handle_message(self, message: Message):
        user = await self.authenticate_user(user_id=message.from_user.id, chat_id=message.chat.id)
        if not user:
            return

        handlers_mapping = {
            TelegramUser.Status.IN_MENU: self.handle_in_menu,
            TelegramUser.Status.WAITING_OPPONENT: self.handle_waiting_opponent,
            TelegramUser.Status.IN_CONVERSATION: self.handle_in_conversation,
        }
        handler = handlers_mapping[user.status]
        await handler(message)

    async def authenticate_user(self, user_id: int, chat_id: int) -> Optional[TelegramUser]:
        try:
            return await TelegramUser.get(tg_id=user_id)
        except DoesNotExist:
            await self._bot.send_message(chat_id, "Вы не зарегистрированы. Пожалуста, используйте комманду /start.")
            return None

    async def handle_in_menu(self, message: Message, user: TelegramUser):
        if message.text == self.START_CONVERSATION_BTN:
            conversation = await Conversation.start(user=user)
            bot = self._bot
            if conversation.opponent:
                message_text = "Собеседник найден. Можете общаться."
                tasks = [
                    bot.send_message(user.tg_chat_id, message_text, reply_markup=self.get_end_conversation_keyboard())
                    for user in (conversation.initiator, conversation.opponent)
                ]
                await asyncio.gather(*tasks)
            else:
                await bot.send_message(
                    conversation.initiator.tg_chat_id, "Ожидаем собеседника...",
                    reply_markup=self.get_cancel_waiting_opponent_keyboard(),
                )

    async def handle_waiting_opponent(self, message: Message, user: TelegramUser):
        raise NotImplementedError

    async def handle_in_conversation(self, message: Message, user: TelegramUser):
        raise NotImplementedError

    @classmethod
    def get_menu_keyboard(cls):
        markup = ReplyKeyboardMarkup(row_width=1)
        markup.add(KeyboardButton(str(cls.START_CONVERSATION_BTN)))
        return markup

    @classmethod
    def get_cancel_waiting_opponent_keyboard(cls):
        markup = ReplyKeyboardMarkup(row_width=1)
        markup.add(KeyboardButton(str(cls.CANCEL_WAITING_OPPONENT_BTN)))
        return markup

    @classmethod
    def get_end_conversation_keyboard(cls):
        markup = ReplyKeyboardMarkup(row_width=1)
        markup.add(KeyboardButton(str(cls.COMPLETE_CONVERSATION_BTN)))
        return markup
