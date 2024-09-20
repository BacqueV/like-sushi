from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandStart
from loader import dp, db, bot
from data.config import ADMINS


@dp.message_handler(CommandStart())
async def bot_start(message: types.Message):
    await db.create_table_users()  # just in case if somebody droped the table of users
    
    username = message.from_user.username
    user = await db.select_user(telegram_id=message.from_user.id)

    if user is None:
        user = await db.add_user(
            full_name=message.from_user.full_name,
            username=message.from_user.username,
            telegram_id=message.from_user.id,
        )
        # informing admins
        count = await db.count_users()
        msg = f"У нас новый пользователей! @{user[2]}\n" + f"Общее количество пользователей - {count}"
        await bot.send_message(chat_id=ADMINS[0], text=msg)

    await message.answer(f"Добро пожаловать! @{username}")
