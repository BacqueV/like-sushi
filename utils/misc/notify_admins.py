from aiogram import Dispatcher
from loader import db

async def on_startup_notify(dp: Dispatcher):
    admins = await db.admin_id_list()

    if admins is not None:
        for admin in admins:
            try:
                await dp.bot.send_message(admin['telegram_id'], "Бот запущен!")
            except Exception as err:
                continue  # cuz we don't need to know if some admin has blocked the bot
