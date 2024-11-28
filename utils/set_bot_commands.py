from aiogram import types


async def set_default_commands(dp):
    await dp.bot.set_my_commands(
        [
            types.BotCommand("start", "Запуск"),
            types.BotCommand("help", "Как работает бот?"),
            types.BotCommand("reset", "Если что-то сломалось - нажимать сюда"),
        ]
    )
