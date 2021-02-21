import logging

from aiogram import Bot, Dispatcher, executor, types

import config


logging.basicConfig(level=logging.INFO)  # Configure logging


bot = Bot(token=config.BOT_API_TOKEN)  # Initialize bot and dispatcher
dispatcher = Dispatcher(bot)


@dispatcher.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """This handler will be called when user sends `/start` or `/help` command."""
    await message.reply("Hi!\nI'm EchoBot!\nPowered by aiogram.")


@dispatcher.message_handler()
async def echo(message: types.Message):
    await message.answer(message.text)


if __name__ == '__main__':
    executor.start_polling(dispatcher, skip_updates=True)
