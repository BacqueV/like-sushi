from aiogram import types
from loader import dp, db, bot
import pandas as pd
import logging
from filters.is_admin import IsAdminFilter
import asyncio


async def notify_admins(notify_message):
    admins = await db.admin_id_list()

    if admins is not None:
        for admin in admins:
            try:
                await dp.bot.send_message(admin['telegram_id'], f"<i>Уведомление для администрации!</i>\n\n" + notify_message)
            except Exception as err:
                logging.exception(err)
            await asyncio.sleep(.05)


@dp.message_handler(IsAdminFilter(is_admin=True), text="/adminhelp")
async def get_all_users(message: types.Message):
    await message.answer(
        "/advert - Отправить рекламное сообщение\n\n"
        "/mcontrol - Открыть панель работы с позициями в меню\n\n"
        "/reset - Прервать любое состояние <b>[опасно, но иногда необхадимо]</b>\n\n"
        "/orders - Выводит список всех заказов\n"
        "/order - Выводит информацию по определенному заказу\n\n"
        "/userlist - Выводит список пользователей\n"
        "/adminlist - Выводит список администраторов\n"
        "/managerlist - Выводит список менеджеров\n"
        "/branchlist - Выводит список всех филиалов\n\n"
        "/adminadd - Добавить админа ( Может добавлять, удалять еду из меню )\n"
        "/manageradd - Добавить менеджера ( Может принимать заказы )\n"
        "/branchadd - Добавить новый филиал (надо скинуть геолокацию после введения команды)\n\n"
        "/adminremove - Разжаловать админа с должности\n"
        "/managerremove - Разжаловать менеджера с должности\n"
        "/branchdel - Удалить филиал из базы данных\n\n"
        "/passwd - Задать пароль <b>самостоятельного</b> подключения к администраторскому доступу. ГОВОРИТЬ ЛИЧНО ТОЛЬКО СВОИМ В КОНФЕДЕНЦИАЛЬНЫХ ЧАТАХ, А ЛУЧШЕ ВЖИВУЮ!!!\n\n"
        "/imadmin - Самостоятельное получение администраторского доступа\n\n"
        "/profile - Введите <b>Telegram ID</b> или <b>Username</b> пользователя вместе с этой командой и получите его профиль, если позваляют найстройки конфеденциальности"
    )


@dp.message_handler(IsAdminFilter(is_admin=True), text="/adminlist")
async def get_admins(message: types.Message):
    users = await db.admin_list()
    telegram_id = []
    name = []

    for user in users:
        telegram_id.append(user[3])
        name.append(user[1])

    data = {
        "Telegram ID": telegram_id,
        "Name": name
    }

    pd.options.display.max_rows = 10000
    df = pd.DataFrame(data)

    chunk_size = 50
    if len(df) > chunk_size:
        for x in range(0, len(df), chunk_size):
            await bot.send_message(message.chat.id, df[x:x + chunk_size].to_string(index=False))
    else:
        await bot.send_message(message.chat.id, df.to_string(index=False))


@dp.message_handler(commands='passwd')
async def passwd(message: types.Message):
    new_passwd = message.get_args()
    if new_passwd:
        await db.change_passwd(new_passwd)
        await message.reply("Новый пароль сохранен!")
        await notify_admins(f"Новый пароль: {new_passwd}")
    else:
        await message.reply("Введи новый пароль!")


@dp.message_handler(commands='imadmin')
async def imadmin(message: types.Message):
    passwd = message.get_args()
    result = await db.make_him_admin_magically(message.from_user.id, passwd)

    if result:
        await message.answer("Ты теперь админ!")
        user = await db.select_user(telegram_id=message.from_user.id)
        await notify_admins(
            f"Новый администратор - <a href='tg://user?id={user[-2]}'>{user[1]}</a>, @{user[2]}\n"
            "<b>Самостоятельный доступ!</b>"
        )
    else:
        await notify_admins(
            f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.full_name}</a>, @{message.from_user.username}\n" +\
            "Пытался стать админом!"
        )


@dp.message_handler(IsAdminFilter(is_admin=True), commands='adminadd')
async def add_admin(message: types.Message):
    if message.get_args():

        try:
            telegram_id = int(message.get_args())
            await dp.bot.send_message(telegram_id, "Вам был предоставлен администорский доступ!")
            await db.make_him_admin(telegram_id)
            await message.reply("Теперь он новый администратор!")
        except Exception as exception:
            await message.reply(
                f"<b>{str(exception)}</b>\n\n"
                "Ошибка возможно в том что вы неправильно ввели телеграм id, или такого пользователя в базе нет!"
            )
    else:
        await message.reply("Напииши телеграм id пользователя которого хочешь сделать админом вместе с командой!")


@dp.message_handler(IsAdminFilter(is_admin=True), commands='adminremove')
async def remove_admin(message: types.Message):
    if message.get_args():

        try:
            telegram_id = int(message.get_args())
            await dp.bot.send_message(telegram_id, "Вы были разжалованы с позиции администратора!")
            await db.remove_admin(telegram_id)
            await message.reply("Администратор разжалован с позиции!")
        except Exception as exception:
            await message.reply(
                f"<b>{str(exception)}</b>\n\n"
                "Ошибка возможно в том что вы неправильно ввели телеграм id, или такого пользователя в базе нет!"
            )
    else:
        await message.reply("Напииши телеграм id админа которого хочешь разжаловать с должности вместе с командой!")
