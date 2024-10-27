from aiogram import types
from data import config
from loader import dp, db, bot
import pandas as pd


@dp.message_handler(text="/userlist")
async def get_all_users(message: types.Message):
    if message.from_user.id in config.admins:
        users = await db.select_all_users()
        telegram_id = []
        name = []
        username = []
        
        for user in users:
            telegram_id.append(user[3])
            name.append(user[1])
            username.append(user[2])
        
        data = {
            "Telegram ID": telegram_id,
            "Name": name,
            "Username": username
        }
        
        pd.options.display.max_rows = 10000
        df = pd.DataFrame(data)

        chunk_size = 50
        if len(df) > chunk_size:
            for x in range(0, len(df), chunk_size):
                await bot.send_message(message.chat.id, df[x:x + chunk_size].to_string(index=False))
        else:
            await bot.send_message(message.chat.id, df.to_string(index=False))



@dp.message_handler(commands='profile')
async def get_user_profile(message: types.Message):
    if message.from_user.id in config.admins:
        user_data = message.get_args()
        
        if user_data:
            try:

                user = await db.select_user(telegram_id=int(user_data))
                if user:
                    await message.reply(f"Ссылка на профиль пользователя: <a href='tg://user?id={user_data}'>{user[1]}</a>")
                else:
                    await message.reply("Такого пользователя нет в Базе данных!")

            except ValueError:

                user = await db.select_user(username=user_data)
                if user:
                    await message.reply(f"Ссылка на профиль пользователя: @{user_data}")
                else:
                    await message.reply("Такого пользователя нет в Базе данных!")
        else:
            await message.reply(
                "Напишите <b>Telegram ID</b> или же <b>Username</b> пользователя вместе с командой чтобы открыть его профиль!\n\n"
                "Чтобы узнать <b>нужные данные</b> введите /userlist и, если позволят настройки конфеденциальности вы получите профиль пользователя!"
            )

@dp.message_handler(commands="udelete")
async def delete_user(message: types.Message):
    if message.from_user.id in config.admins:
        try:
            telegram_id = int(message.get_args())
        except ValueError:
            await message.reply("Введите Telegram ID пользователя вместе с командой!")
            return

        user = await db.select_user(telegram_id=telegram_id)
        if user is not None:
            name = user[1]
            await db.delete_user(telegram_id)
            await message.reply(f"Пользователь {name} удален!")
        else:
            await message.reply("Такого пользователя в БД нет!")
