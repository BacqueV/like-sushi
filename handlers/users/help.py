from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandHelp

from loader import dp


@dp.message_handler(CommandHelp(), state="*")
async def bot_help(message: types.Message):
    text = ("Команды: ",
            "/start - Начало всех начал",
            "/help - Показывает данное сообщение :D",
            "/adminhelp - Админские команды. Работает только если ты админ :D",
            "/reset - Нажимайте сюда что все починить",
    )
    
    await message.answer("\n".join(text))
