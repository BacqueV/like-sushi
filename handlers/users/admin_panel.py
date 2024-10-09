from aiogram import types
from loader import dp, db, bot
import pandas as pd
from data import config
import logging


async def notify_admins(notify_message):
    for admin in config.admins:
        try:
            await dp.bot.send_message(admin, f"<i>Уведомление для администрации!</i>\n" + notify_message)

        except Exception as err:
            logging.exception(err)


@dp.message_handler(text="/adminhelp", state="*")
async def get_all_users(message: types.Message):
    if message.from_user.id in config.admins:
        await message.answer(
            "/mcontrol - Открыть панель работы с позициями в меню\n\n"
            "/advert - Отправить рекламное сообщение\n\n"
            "/userlist - Выводит список пользователей \n"
            "/adminlist - Выаодит список администраторов \n\n"
            "/adminadd - Добавить админа \n"
            "/adminremove - Разжаловать админа с должности \n\n"
            "/passwd - Задать пароль <b>самостоятельного</b> подключения к администраторскому доступу. ГОВОРИТЬ ЛИЧНО ТОЛЬКО СВОИМ В КОНФЕДЕНЦИАЛЬНЫХ ЧАТАХ, А ЛУЧШЕ ВЖИВУЮ!!!\n\n"
            "/imadmin - Самостоятельное получение администраторского доступа \n\n"
            "/cleandb - <b>ОПАСНО!</b> Очищает БД пользователей \n"
            "/dropusers - <b>СМЕРТЕЛЬНО ОПАСНО!</b> Удаляет БД пользователей с сервера. Для пересоздания нажать /start\n\n"
            "/profile - Введите <b>Telegram ID</b> пользователя вместе с этой командой и получите его профиль, если позваляют найстроки конфеденциальности"
        )
    else:
        await message.reply("Только для админов :D")


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
        await notify_admins(new_passwd)
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
        user = await db.select_user(telegram_id=message.from_user.id)
        await notify_admins(f"Новый администратор - {user[1]}, @{user[2]}")
    else:
        print("Пароли не совпадают!")


@dp.message_handler(commands='adminadd')
async def add_admin(message: types.Message):
    if message.from_user.id in config.admins:
        if message.get_args():

            telegram_id = int(message.get_args())
            try:
                config.admins.append(telegram_id)
                await db.make_him_admin(telegram_id)
                await message.reply("Теперь он новый администратор!")
                await dp.bot.send_message(telegram_id, "Вам был предоставлен администорский доступ!")
            except Exception as exception:
                await message.reply(str(exception) + "\n" + "Ошибка возможно в том что вы неправильно ввели телеграм id, или такого пользователя в базе нет!")
        else:
            await message.reply("Напииши телеграм id пользователя которого хочешь сделать админом вместе с командой!")


@dp.message_handler(commands='adminremove')
async def remove_admin(message: types.Message):
    if message.from_user.id in config.admins:
        if message.get_args():

            telegram_id = int(message.get_args())
            try:
                config.admins.remove(telegram_id)
                await db.remove_admin(telegram_id)
                await message.reply("Администратор разжалован с позиции!")
                await dp.bot.send_message(telegram_id, "Вы были разжалованы с позиции администратора!")
            except Exception as exception:
                await message.reply(str(exception))
        else:
            await message.reply("Напииши телеграм id админа которого хочешь разжаловать с должности вместе с командой!")
