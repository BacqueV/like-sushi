from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandStart
from loader import dp, db, bot
from data import config
from keyboards.default.main_menu import main_menu_kb
from aiogram.utils.exceptions import BotBlocked


@dp.message_handler(CommandStart())
async def bot_start(message: types.Message):
    await db.create_table_users()  # just in case if someone has droped the table of users

    name = message.from_user.full_name
    user = await db.select_user(telegram_id=message.from_user.id)

    if user is None:
        user = await db.add_user(
            full_name=message.from_user.full_name,
            username=message.from_user.username,
            telegram_id=message.from_user.id,
        )
        # informing admins
        count = await db.count_users()

        msg = f"У нас новый пользователь!\n\n" + \
        f"<a href='tg://user?id={user[-2]}'>{user[1]}</a>, @{user[2]}\n\n" + \
        f"<b>Общее количество пользователей - {count}</b>"

        for admin in config.admins:
            try:
                await bot.send_message(chat_id=admin, text=msg)
            except BotBlocked:
                continue  # we don't need to know if some admin has blocked this bot

    try:
        await message.answer(f"Добро пожаловать, {name}!", reply_markup=main_menu_kb)
    except BotBlocked:
        pass
