from aiogram.bot import Bot

from anon_talks.models import TelegramUser


class BotService:

    def __init__(self, bot: Bot):
        self._bot = bot

    async def register_user(self, user_id: int, chat_id: int) -> TelegramUser:
        user, is_created = await TelegramUser.get_or_create(tg_user_id=user_id, defaults={'tg_chat_id': chat_id})
        if not is_created:
            message_text = "Вы уже зарегистрированы."
        else:
            message_text = (
                "Добро пожаловать в анонимный чат!\n"
                "Здесь вы можете общаться с другими, не расскрывая своей личности."
            )
        await self._bot.send_message(chat_id, message_text)
        return user
