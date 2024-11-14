from aiogram import types
from loader import dp, db, bot
import pandas as pd
from filters.is_admin import IsAdminFilter
from filters.is_manager import IsManagerFilter
import asyncio
from states.admin import ManageLocationState
from aiogram.dispatcher import FSMContext
from handlers.users.ordering.order import get_address_from_coordinates
from .panel import notify_admins


@dp.message_handler(IsAdminFilter(is_admin=True), text="/userlist")
async def get_all_users(message: types.Message):
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
    if len(df) > 50:
        for x in range(0, len(df), 50):
            await bot.send_message(message.chat.id, df[x:x + 50])
    else:
        await bot.send_message(message.chat.id, df)


@dp.message_handler(IsAdminFilter(is_admin=True), commands='profile')
async def get_user_profile(message: types.Message):
    user_data = message.get_args()
    
    if user_data:
        try:

            user = await db.select_user(telegram_id=int(user_data))
            if user:
                await message.reply(
                    f"<a href='tg://user?id={user_data}'>Ссылка</a> на "
                    f"профиль пользователя: <a href='tg://user?id={user_data}'>{user[1]}</a>"
                )
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


@dp.message_handler(IsAdminFilter(is_admin=True), text="/managerlist")
async def get_managers(message: types.Message):
    users = await db.manager_list()
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


@dp.message_handler(IsAdminFilter(is_admin=True), commands='manageradd')
async def add_manager(message: types.Message):
    if message.get_args():

        try:
            telegram_id = int(message.get_args())
            await dp.bot.send_message(telegram_id, "Вам был предоставлен доступ менеджера!")
            await db.add_manager(telegram_id)
            await message.reply("Теперь он новый менеджер!")
        except Exception as exception:
            await message.reply(
                f"<b>{str(exception)}</b>\n\n"
                "Ошибка возможно в том что вы неправильно ввели телеграм id, или такого пользователя в базе нет!"
            )
    else:
        await message.reply("Напииши телеграм id пользователя которого хочешь сделать менеджером вместе с командой!")


@dp.message_handler(IsAdminFilter(is_admin=True), commands='managerremove')
async def remove_admin(message: types.Message):
    if message.get_args():

        try:
            telegram_id = int(message.get_args())
            await dp.bot.send_message(telegram_id, "Вы были разжалованы с позиции менеджера!")
            await db.remove_manager(telegram_id)
            await message.reply("Менеджер разжалован с позиции!")
        except Exception as exception:
            await message.reply(
                f"<b>{str(exception)}</b>\n\n"
                "Ошибка возможно в том что вы неправильно ввели телеграм id, или такого пользователя в базе нет!"
            )
    else:
        await message.reply("Напииши телеграм id менеджера которого хочешь разжаловать с должности вместе с командой!")


@dp.message_handler(commands='orders')
async def list_orders(message: types.Message):
    is_admin = await IsAdminFilter(is_admin=True).check(message)
    is_manager = await IsManagerFilter(is_manager=True).check(message)
    
    if is_admin or is_manager:

        orders = await db.list_all_orders()

        if len(orders) == 0:
            await message.reply("<b>Пока нет заказов!</b>")
            return

        response = '<b>Завершенные:</b>\n\n'
        unprocessed_orders_kb = types.InlineKeyboardMarkup(row_width=1)

        for order in orders:
            if order[3]:  # has been processed
                response += f"Заказ №{order[0]} — <b>[{order[-1]}]</b> {order[-2]}\n"
            else:  # has not been processed yet
                unprocessed_orders_kb.insert(
                    types.InlineKeyboardButton(
                        text=f"Заказ №{order[0]} — [{order[-1]}] {order[-2]}",
                        callback_data=order[0]
                    )
                )

        num_buttons = sum(len(row) for row in unprocessed_orders_kb.inline_keyboard)
        
        if num_buttons != 0:
            response += "\n<b>Не завершенные:</b>"
            await message.answer(response, reply_markup=unprocessed_orders_kb)
        else:
            await message.answer(response)
            await asyncio.sleep(.5)
            await message.answer("<b>Все заказы обработаны!</b>")


@dp.message_handler(commands='order')
async def list_orders(message: types.Message):
    is_admin = await IsAdminFilter(is_admin=True).check(message)
    is_manager = await IsManagerFilter(is_manager=True).check(message)
    
    if is_admin or is_manager:
        try:
            order_id = int(message.get_args())
            order = await db.select_order(order_id=order_id)
            await message.reply(order[1])
        except (ValueError, TypeError):
            await message.reply("Значение <b>ID</b> не существует, либо вы не знаете что оно хранится в числовых значениях 🤔")


@dp.message_handler(commands='reset', state='*')
async def clean_state(message: types.Message, state: FSMContext):
    await state.finish()
    await message.reply("Вы прервали процесс!")


@dp.message_handler(commands='branchlist')
async def branchlist(message: types.Message):
    branches = await db.branchlist()
    branch_id = []
    address = []

    for branch in branches:
        branch_id.append(branch[0])
        address.append(branch[1])

    data = {
        "Branch ID": branch_id,
        "Address": address
    }

    pd.options.display.max_rows = 10000
    df = pd.DataFrame(data)

    chunk_size = 50
    if len(df) > chunk_size:
        for x in range(0, len(df), chunk_size):
            await bot.send_message(message.chat.id, df[x:x + chunk_size].to_string(index=False))
    else:
        await bot.send_message(message.chat.id, df.to_string(index=False))


# add branch
@dp.message_handler(IsAdminFilter(is_admin=True), text='/branchadd')
async def start_location_saving(message: types.Message):
    await ManageLocationState.await_location.set()
    await message.answer("<b>Отправьте локацию филиала!</b>")


@dp.message_handler(
        IsAdminFilter(is_admin=True),
        content_types=types.ContentType.LOCATION,
        state=ManageLocationState.await_location
    )
async def save_location(message: types.Message, state: FSMContext):
    latitude = message.location.latitude
    longitude = message.location.longitude

    address = await get_address_from_coordinates(latitude, longitude, state)

    await notify_admins(f"Новый адрес: {address}")

    await db.add_branch(address, latitude, longitude)
    await state.finish()
    await message.reply(
        f"Адрес сохранен!\n<b>{address}</b>",
    )


# delete location
@dp.message_handler(IsAdminFilter(is_admin=True), commands='branchdel')
async def start_location_saving(message: types.Message):
    try:
        branch_id = int(message.get_args())

        address = await db.get_branch_address(branch_id)
        if address:
            await db.delete_branch(branch_id)
            await message.reply(f"Адрес филиала был удален!\n<b>{address}</b>")
        else:
            await message.reply("<b>Такого адреса нет в базе данных!</b>")
    except ValueError:
        await message.reply("<b>ID</b> хранится в числовых значениях!")
