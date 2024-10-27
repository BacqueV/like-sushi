import asyncio
from data import config
from aiogram import types
from loader import dp, db, bot
from aiogram.dispatcher import FSMContext
from keyboards.inline import menu_control
from states.admin import MControlState
from handlers.users.admin_panel import notify_admins


async def back_to_menu(call: types.CallbackQuery):
    await asyncio.sleep(.5)
    await MControlState.main_menu.set()
    await call.message.answer(
        "Вы открыли интерфейс управления меню",
        reply_markup=menu_control.main_menu
    )

"""
Add Meal
"""

@dp.callback_query_handler(text="add_meal", state=MControlState.main_menu)
async def add_meal(call: types.CallbackQuery):
    if len(await db.list_categories()) == 0:
        await call.answer("Для начала вам нужно добавит хотя бы одну категорию блюд", show_alert=True)
        return

    await MControlState.await_name_meal.set()
    await call.message.edit_text(
        "<b>Вы добавляете новое блюдо</b>\n\n" "Введите имя блюда",
        reply_markup=menu_control.quit_anything
    )


@dp.callback_query_handler(text='quit_anything', state=MControlState.await_name_meal)
async def no_meal(call: types.CallbackQuery):
    await call.message.edit_text("<i>Вы отменили добавление блюда</i>", reply_markup=types.InlineKeyboardMarkup())
    await MControlState.main_menu.set()
    await asyncio.sleep(1)
    await call.message.answer(
        "Вы открыли интерфейс управления меню",
        reply_markup=menu_control.main_menu
    )


@dp.message_handler(state=MControlState.await_name_meal)
async def save_name_meal(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await MControlState.await_category.set()

    meals_category_kb = types.InlineKeyboardMarkup(row_width=2)
    categories = await db.list_categories()

    for category in categories:
        meals_category_kb.insert(
            types.InlineKeyboardButton(
                text=str(category['name']),
                callback_data=str(category['category_id'])
            )
        )

    await message.answer(
        "Сохранил! Теперь выберите категорию к которй будет принадлежать блюдо",
        reply_markup=meals_category_kb
    )


@dp.callback_query_handler(state=MControlState.await_category)
async def save_meal_category(call: types.CallbackQuery, state: FSMContext):
    await state.update_data(category_id=call.data)
    category = await db.select_category(category_id=int(call.data))

    await call.message.edit_text(f"<i>Выбрана категория: {category[1]}</i>")
    
    await MControlState.await_description_meal.set()
    await call.message.reply(
        "Сохранил! Теперь введи описание, если требуется",
        reply_markup=menu_control.quit_anything
    )


# continue without description
@dp.callback_query_handler(text='quit_anything', state=MControlState.await_description_meal)
async def no_meal_description(call: types.CallbackQuery):
    await call.message.edit_text(
        "<i>Описание не потребовалось</i>",
        reply_markup=types.InlineKeyboardMarkup()
    )
    
    await MControlState.await_price.set()
    await call.message.answer(
        "Отлично, теперь введите цену блюда!"
    )


# continue with description
@dp.message_handler(state=MControlState.await_description_meal)
async def save_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)

    await MControlState.await_price.set()
    await message.answer(
        "Отлично, теперь введите цену блюда!"
    )


# PRICE
@dp.message_handler(state=MControlState.await_price)
async def save_price(message: types.Message, state: FSMContext):
    try:
        price = int(message.text)
        await state.update_data(price=price)
    except ValueError:
        await message.reply("<b>Введенное значение должно быть числом!</b>")


@dp.callback_query_handler(state=MControlState.confirmation_add_meal)
async def category_add_confirmation(call: types.CallbackQuery, state: FSMContext):
    if call.data == "accept":
        data = await state.get_data()
        name = data.get("name")
        description = data.get("description")
        await db.add_meal(name, description)
        
        await call.message.edit_text(
            "<i>Вы добавили новую категорию блюд</i>",
            reply_markup=types.InlineKeyboardMarkup()
        )
        await notify_admins(
            f"Добавлена новая категория - <b>{name} ({description})</b>"
        )
    else:
        await call.message.edit_text(
            "<i>Вы отменили добавление новой категории</i>",
            reply_markup=types.InlineKeyboardMarkup()
        )
    await back_to_menu(call)
