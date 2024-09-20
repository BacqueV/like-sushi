from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandHelp

from loader import dp


@dp.message_handler(CommandHelp())
async def bot_help(message: types.Message):
    text = ("Команды: ",
            "/start - Запуск бота",
            "/help - Помощь в работе бота")
    
    await message.answer("\n".join(text))
