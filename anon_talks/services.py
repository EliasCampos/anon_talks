import asyncio
from typing import Optional

from aiogram.bot import Bot
from aiogram.types.message import Message
from aiogram.types.reply_keyboard import ReplyKeyboardMarkup, KeyboardButton
from tortoise.exceptions import DoesNotExist

from anon_talks.models import Conversation, TelegramUser


class BotService:
    MARKDOWN_MODE = 'MarkdownV2'

    START_TEXT = (
        "Приветствую\\! Это _AnonTalks бот_\\!\n\n"
        "Здесь вы можете общаться с другими, не расскрывая своей личности\\. _AnonTalks_ \\- это\\:\n"
        "*Анонимно и приватно* \\- бот обеспечивает приватность ваших персональных контактов\\.\n"
        "*Безопасно* \\- выражайтесь свободно, не боясь осуждения и неприятных для вас последствий\\.\n"
        "*Искренне* \\- здесь ценят ваши мысли и ощущения, а не имя и положение в обществе\\.\n"
    )
    HELP_TEXT = (
        "Приветствую!\n\n"
        "Чтобы начать ознакомление с ботом, введите комманду /start."
    )

    START_CONVERSATION_BTN = "[Искать собеседника]"
    CANCEL_WAITING_OPPONENT_BTN = "[Остановить]"
    COMPLETE_CONVERSATION_BTN = "[Отключиться]"

    def __init__(self, bot: Bot):
        self._bot = bot

    async def register_user(self, user_id: int, chat_id: int) -> TelegramUser:
        user, is_created = await TelegramUser.get_or_create(tg_id=user_id, defaults={'tg_chat_id': chat_id})
        if is_created:
            keyboard = self.get_menu_keyboard()
        else:
            keyboard = None

        await self._bot.send_message(chat_id, self.START_TEXT, parse_mode=self.MARKDOWN_MODE, reply_markup=keyboard)
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
        await handler(message, user)

    async def authenticate_user(self, user_id: int, chat_id: int) -> Optional[TelegramUser]:
        try:
            return await TelegramUser.get(tg_id=user_id)
        except DoesNotExist:
            await self._bot.send_message(chat_id, "Пожалуйста, введите комманду /start, чтобы начать.")
            return None

    async def handle_in_menu(self, message: Message, user: TelegramUser):
        if message.text == self.START_CONVERSATION_BTN:
            conversation = await Conversation.start(user=user)
            bot = self._bot
            if conversation.opponent:
                message_text = "*Собеседник найден \\- общайтесь*"
                end_conversation_keyboard = self.get_end_conversation_keyboard()
                coros = [
                    bot.send_message(
                        user.tg_chat_id, message_text,
                        reply_markup=end_conversation_keyboard, parse_mode=self.MARKDOWN_MODE,
                    )
                    for user in (conversation.initiator, conversation.opponent)
                ]
                await asyncio.gather(*coros)
            else:
                await bot.send_message(
                    conversation.initiator.tg_chat_id, "Ищем свободного собеседника...",
                    reply_markup=self.get_cancel_waiting_opponent_keyboard(),
                )

    async def handle_waiting_opponent(self, message: Message, user: TelegramUser):
        if message.text == self.CANCEL_WAITING_OPPONENT_BTN:
            chats = (Conversation
                     .waiting_opponent()
                     .select_related('initiator')
                     .order_by('-id')
                     .filter(initiator_id=user.pk))
            chat = await chats.first()
            await chat.finish()
            message_text = "*Поиск отменён\\.*"
            await self._bot.send_message(
                user.tg_chat_id, message_text, parse_mode=self.MARKDOWN_MODE, reply_markup=self.get_menu_keyboard(),
            )

    async def handle_in_conversation(self, message: Message, user: TelegramUser):
        conversation_qs = (Conversation
                           .with_user_participant(user)
                           .filter(opponent_id__isnull=False, finished_at__isnull=True)
                           .select_related('initiator', 'opponent')
                           .order_by('-id'))
        conversation = await conversation_qs.first()
        opponent = conversation.get_opponent(user)

        if message.text == self.COMPLETE_CONVERSATION_BTN:
            await conversation.finish()

            user_text = "*Вы завершили чат\\.*"
            opponent_text = "*Собеседник завершил чат\\.*"

            menu_keyboard = self.get_menu_keyboard()
            coros = [
                self._bot.send_message(chat_id, text, reply_markup=menu_keyboard, parse_mode=self.MARKDOWN_MODE)
                for chat_id, text in [(user.tg_chat_id, user_text), (opponent.tg_chat_id, opponent_text)]
            ]
            await asyncio.gather(*coros)
        else:
            await self._bot.send_message(opponent.tg_chat_id, message.text)

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
