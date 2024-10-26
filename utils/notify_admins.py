import logging

from aiogram import Dispatcher

from data.config import admins


async def on_startup_notify(dp: Dispatcher):
    for admin in admins:
        try:
            await dp.bot.send_message(admin, "Бот запущен!")
        except Exception:
            pass  # cuz we don't need to see if there is a poroblem to notify a certain admin
