from aiogram import types
from data.config import ADMINS
from loader import dp, db, bot
import pandas as pd


@dp.message_handler(text="/userlist", user_id=ADMINS)
async def get_all_users(message: types.Message):
    users = await db.select_all_users()
    telegram_id = []
    name = []
    is_admin = []
    for user in users:
        telegram_id.append(user[-2])
        name.append(user[1])
        is_admin.append(user[-1])
    data = {
        "Telegram ID": telegram_id,
        "Name": name,
        "Is admin": is_admin
    }
    pd.options.display.max_rows = 10000
    df = pd.DataFrame(data)
    if len(df) > 50:
        for x in range(0, len(df), 50):
            await bot.send_message(message.chat.id, df[x:x + 50])
    else:
        await bot.send_message(message.chat.id, df)


@dp.message_handler(text="/cleandb", user_id=ADMINS)
async def get_all_users(message: types.Message):
    await db.delete_users()
    await message.answer("База данных пользователей очищена!")


@dp.message_handler(text="/dropusers", user_id=ADMINS)
async def get_all_users(message: types.Message):
    await db.drop_users()
    await message.answer("База данных пользователей удалена!")
