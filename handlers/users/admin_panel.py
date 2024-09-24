from aiogram import types
from loader import dp, db, bot
import pandas as pd
from data import config


@dp.message_handler(text="/adminhelp")
async def get_all_users(message: types.Message):
    if message.from_user.id in config.admins:
        await message.answer(
            "/userlist - Выводит список пользователей \n"
            "/cleandb - !ОПАСНО! Очищает БД пользователей \n"
            "/dropusers - !СМЕРТЕЛЬНО ОПАСНО! Удаляет БД пользователей с сервера. Для пересоздания нажать /start \n"
            "/adminlist - Дает список всех администраторов \n"
            "/passwd - ГОВОРИТЬ ЛИЧНО ТОЛЬКО СВОИМ В КОНФЕДЕНЦИАЛЬНЫХ ЧАТАХ, А ЛУЧШЕ ВЖИВУЮ!!! Задать код самостоятельного подключения к администраторскому доступу \n"
            "/imadmin - Надо писать код passwd (!) после вместе с этой командой чтобы самостоятельно стать админом \n"
            "/adminadd - Добавить админа \n"
            "/adminremove - Разжаловать его с должности \n"
        )


@dp.message_handler(text="/adminlist")
async def get_all_users(message: types.Message):
    if message.from_user.id in config.admins:
        users = await db.admin_list()
        telegram_id = []
        name = []
        for user in users:
            telegram_id.append(user[-2])
            name.append(user[1])
        data = {
            "Telegram ID": telegram_id,
            "Name": name
        }
        pd.options.display.max_rows = 10000
        df = pd.DataFrame(data)
        if len(df) > 50:
            for x in range(0, len(df), 50):
                await bot.send_message(message.chat.id, df[x:x + 50])
        else:
            await bot.send_message(message.chat.id, df)


@dp.message_handler(commands='passwd')
async def passwd(message: types.Message):
    new_passwd = message.get_args()
    if new_passwd:
        await db.change_passwd(new_passwd)
        await message.reply("Новый пароль сохранен!")
    else:
        await message.reply("Введи новый пароль!")


@dp.message_handler(commands='imadmin')
async def imadmin(message: types.message):
    passwd = message.get_args()
    if not passwd:
        await message.reply("Введи пароль вместе с командой!")
        return 0

    result = await db.make_him_admin_magically(message.from_user.id, passwd)

    if result:
        config.admins.append(str(message.from_user.id))
        await message.answer("Ты теперь админ!")
    else:
        print("Пароли не совпадают!")


@dp.message_handler(commands='adminadd')
async def add_admin(message: types.Message):
    if message.from_user.id in config.admins:
        if message.get_args():

            telegram_id = message.get_args()
            try:
                config.admins.append(int(telegram_id))
                await db.make_him_admin(int(telegram_id))
                await message.reply("Теперь он новый администратор!")
            except Exception as exception:
                await message.reply(str(exception) + "\n" + "Ошибка возможно в том что вы неправильно ввели телеграм id, или такого пользователя в базе нет!")
        else:
            await message.reply("Напииши телеграм id пользователя которого хочешь сделать админом вместе с командой!")


@dp.message_handler(commands='adminremove')
async def remove_admin(message: types.Message):
    if message.from_user.id in config.admins:
        if message.get_args():

            telegram_id = message.get_args()
            try:
                config.admins.remove(int(telegram_id))
                await db.remove_admin(int(telegram_id))
                await message.reply("Администратор разжалован с позиции!")
            except Exception as exception:
                await message.reply(str(exception))
        else:
            await message.reply("Напииши телеграм id админа которого хочешь разжаловать с должности вместе с командой!")
