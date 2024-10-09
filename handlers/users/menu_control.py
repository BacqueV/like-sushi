import asyncio
import pandas as pd
from data import config
from aiogram import types
from loader import dp, db, bot
from aiogram.dispatcher import FSMContext
from keyboards.inline import menu_control
from states.admin import MControlState
from handlers.users.admin_panel import notify_admins


@dp.message_handler(text="/mcontrol")
async def open_menu(message: types.Message):
    if message.from_user.id in config.admins:
        await MControlState.main_menu.set()
        await message.answer("Вы открыли интерфейс управления меню", reply_markup=menu_control.main_menu)


@dp.callback_query_handler(text="list_categories", state=MControlState.main_menu)
async def list_categories(call: types.CallbackQuery):
    users = await db.list_categories()
    category_id = []
    name = []
    description = []
    for user in users:
        category_id.append(user[-2])
        name.append(user[1])
        description.append(user[-1])
    data = {
        "Category ID": category_id,
        "Name": name,
        "Description": description
    }
    pd.options.display.max_rows = 10000
    df = pd.DataFrame(data)

    await call.message.edit_text("<i>Открываем список категорий</i>", reply_markup=types.InlineKeyboardMarkup())

    if len(df) > 50:
        for x in range(0, len(df), 50):
            await bot.send_message(call.message.chat.id, df[x:x + 50])

    else:
        await bot.send_message(call.message.chat.id, df)
    await asyncio.sleep(1)
    await call.message.answer("Вы открыли меню работы с категориями и блюдами", reply_markup=menu_control.main_menu)


@dp.callback_query_handler(text="quit", state=MControlState.main_menu)
async def quit_menu(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.message.edit_text(text="<i>Вы вышли из интерфейса управления меню!</i>", reply_markup=types.InlineKeyboardMarkup())

"""
Add category
"""

@dp.callback_query_handler(text="add_category", state=MControlState.main_menu)
async def add_category(call: types.CallbackQuery):
    await MControlState.await_name.set()
    await call.message.edit_text(
        "<b>Вы добавляете новую категорию</b>\n\n" + "Введите имя категории",
        reply_markup=types.InlineKeyboardMarkup()
    )


@dp.message_handler(state=MControlState.await_name)
async def save_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await MControlState.await_description.set()
    await message.reply("Сохранил! Теперь введи описание, если требуется", reply_markup=menu_control.quit_anything)


@dp.callback_query_handler(text='quit_anything', state=MControlState.await_description)
async def no_category_description(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    name = data.get('name')

    await call.message.edit_text("<i>Описание не потребовалось</i>", reply_markup=types.InlineKeyboardMarkup())
    
    await MControlState.confirmation.set()
    await call.message.answer(f"<b>Сохраняем?</b>\n\n" + f"Имя: {name}", reply_markup=menu_control.confirmation)
    

@dp.message_handler(state=MControlState.await_description)
async def save_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data.get('name')
    await state.update_data(description=message.text)
    await MControlState.confirmation.set()
    await message.answer(f"<b>Сохраняем?</b>\n\n" + f"Имя: {name}\n" + f"Описание: {message.text}", reply_markup=menu_control.confirmation)


@dp.callback_query_handler(state=MControlState.confirmation)
async def confirmation(call: types.CallbackQuery, state: FSMContext):
    if call.data == "accept":
        data = await state.get_data()
        name = data.get("name")
        description = data.get("description")
        await db.add_category(name, description)
        
        await call.message.edit_text("<i>Вы добавили новую категорию блюд</i>", reply_markup=types.InlineKeyboardMarkup())
        await notify_admins(f"Добавлена новая категория - <b>{name} ({description})</b>")
    else:
        await call.message.edit_text("<i>Вы отменили добавление новой категории</i>", reply_markup=types.InlineKeyboardMarkup())
    
    await MControlState.main_menu.set()
    await asyncio.sleep(1)
    await call.message.answer("Вы открыли интерфейс управления меню", reply_markup=menu_control.main_menu)

"""
Delete category
"""

@dp.callback_query_handler(text='delete_category', state=MControlState.main_menu)
async def delete_category(call: types.CallbackQuery):
    await MControlState.await_name.set()
    await call.message.edit_text(
        "<b>Введите название или ID категории.</b>\n\n" + "Это вы можете узнать вернувшись в главное меню интерфейса!",
        reply_markup=menu_control.quit_deleting
    )


@dp.callback_query_handler(text='quit_deleting', state=MControlState.await_name)
async def quit_deleting(call: types.CallbackQuery):
    await MControlState.main_menu.set()
    await call.message.edit_text("<i>Вы отменили удаление категории</i>")
    await asyncio.sleep(1)
    await call.message.answer("Вы открыли интерфейс управления меню", reply_markup=menu_control.main_menu)
