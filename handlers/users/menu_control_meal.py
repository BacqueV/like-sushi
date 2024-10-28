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
    await call.message.edit_text("<i>Вы отменили добавление блюда</i>", reply_markup=None)
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

    await call.message.edit_text(f"Выбрана категория: <i>{category[1]}</i>")
    
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
        reply_markup=None
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
        
        if price > 0:
            await state.update_data(price=price)

            data = await state.get_data()

            name = data.get('name')
            description = data.get('description')

            category_id = data.get('category_id')
            category = await db.select_category(category_id=int(category_id))

            await MControlState.confirmation_add_meal.set()
            await message.answer(
                (f"<b>Сохраняем?</b>\n\n"
                f"Имя: {name}\n") + \
                (f"Описание: {description}\n" if description else "") + \
                (f"Цена: {price}\n"
                f"Категория: {category[1]}"),
                reply_markup=menu_control.confirmation
            )
        else:
            await message.reply(
                "Цена обычно хранится в положительных значениях :|"
            )
    except ValueError:
        await message.reply("<b>Введенное значение должно быть числом!</b>")


@dp.callback_query_handler(state=MControlState.confirmation_add_meal)
async def meal_add_confirmation(call: types.CallbackQuery, state: FSMContext):
    if call.data == "accept":
        data = await state.get_data()

        name = data.get('name')
        category_id = data.get('category_id')
        description = data.get('description')
        price = data.get('price')

        await db.add_meal(int(category_id), name, description, float(price))
        
        await call.message.edit_text(
            "<i>Вы добавили новое блюдо</i>\n\n",
            reply_markup=None
        )
        await notify_admins(
            f"Добавлено новое блюдо - <b>{name}</b> ({description})"
        )
    else:
        await call.message.edit_text(
            "<i>Вы отменили добавление новой категории</i>",
            reply_markup=None
        )
    await back_to_menu(call)

"""
Delete meal
"""

@dp.callback_query_handler(text='delete_meal', state=MControlState.main_menu)
async def delete_meal(call: types.CallbackQuery):
    meals = await db.list_meals()
    if len(meals) == 0:
        await call.answer("Нет блюд для удаления!")
        return
    
    await MControlState.await_id_delete_meal.set()
    await call.message.edit_text(
        "<b>Введите ID блюда для удаления</b>\n\n"
        "Это вы можете узнать открыв меню!",
        reply_markup=menu_control.quit_anything
    )


# quit deleting category
@dp.callback_query_handler(text='quit_anything', state=MControlState.await_id_delete_meal)
async def quit_deleting(call: types.CallbackQuery):
    await call.message.edit_text("<i>Вы отменили удаление блюда</i>", reply_markup=None)
    await back_to_menu(call)


# continue deleting
@dp.message_handler(state=MControlState.await_id_delete_meal)
async def await_id_delete_meal(message: types.Message, state: FSMContext):
    try:
        meal = await db.select_meal(meal_id=int(message.text))
        category = await db.select_category(category_id=meal[1])
        
        if meal:
            await state.update_data(meal_id=int(message.text))
            await MControlState.confirmation_delete_meal.set()
            await message.reply(
                "<b>Подтвердите удаление блюда!</b>\n\n" + \
                (f"<b>ID:</b> {meal[0]}\n"
                f"<b>Есть в меню:</b> {meal[-1]}\n"
                f"<b>Имя:</b> {meal[2]}\n") + \
                f"<b>Цена:</b> {meal[4]}\n" +\
                (f"<b>Описание:</b> {meal[3]}\n") + \
                (f"<b>Категория:</b> {category[1]}\n" if category else "<b>Категория:</b> Была удалена}\n") + \
                (f"<b>Скидка:</b> {meal[5]}\n") + \
                (f"<b>Величина скидки</b>: {meal[6]}%" if meal[5] else ""),
                reply_markup=menu_control.confirmation
            )
        else:
             await message.reply("Такого блюда нет!")
    except ValueError:
        await message.reply("<b>ID</b> хранится в числовых значениях!")


@dp.callback_query_handler(state=MControlState.confirmation_delete_meal)
async def meal_delete_confirmation(call: types.CallbackQuery, state: FSMContext):
    if call.data == "accept":
        data = await state.get_data()
        meal_id = data.get("meal_id")
        meal = await db.select_meal(meal_id=meal_id)
        meal_name = meal[2]

        await db.delete_meal(meal_id)
        await call.message.edit_text(
            f"Блюдо {meal_name} было удалено!",
            reply_markup=None
        )

        await notify_admins(
            f"Блюда <b>{meal_name}</b> было удалено!"
        )
    else:
        await call.message.edit_text("<i>Вы отменили удаление блюда!</i>", reply_markup=None)
    await back_to_menu(call)

"""
Manage meal
"""

@dp.callback_query_handler(text='manage_meal', state=MControlState.main_menu)
async def manage_meal(call: types.CallbackQuery):
    meals = await db.list_meals()
    if len(meals) == 0:
        await call.answer("Нет блюд для правки!", show_alert=False)
        return

    await MControlState.await_id_manage.set()
    await call.message.edit_text(
        "Введите <b>ID</b> категории для правки\n\n"
        "Узнать вы это можете воспользовавшись другой командой из главного меню. "
        "<b>ID</b> будет являться колонка справа",
        reply_markup=menu_control.quit_anything
    )


# quit managing category
@dp.callback_query_handler(text='quit_anything', state=MControlState.await_id_manage)
async def quit_managing(call: types.CallbackQuery):
    await call.message.edit_text("<i>Вы отменили изменения в категориях</i>", reply_markup=None)
    await back_to_menu(call)


# continue managing
@dp.message_handler(state=MControlState.await_id_manage)
async def await_id_manage(message: types.Message, state: FSMContext):
    try:
        category = await db.select_category(category_id=int(message.text))

        if category:

            await state.update_data(
                category_id=category[0],
                name=category[1],
                description=category[2],
                category_sale=category[3],
                category_sale_percent=category[4]
            )

            await MControlState.manage_menu.set()

            await message.reply(
                ("<b>Какие данные будем править?</b>\n\n"
                f"<b>ID</b>: {category[0]}\n"
                f"<b>Имя</b>: {category[1]}\n"
                f"<b>Описание</b>: {category[2]}\n"
                f"<b>Скидка</b>: {category[3]}\n") + \
                (f"<b>Величина скидки</b>: {category[4]}%" if category[3] else ""),
                reply_markup=types.InlineKeyboardMarkup(
                    row_width=1,
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text="Имя",
                                callback_data='name'
                            )
                        ],
                        [
                            types.InlineKeyboardButton(
                                text="Описание",
                                callback_data='description'
                            )
                        ],
                        [
                            types.InlineKeyboardButton(
                                text="Скидка",
                                callback_data='category_sale'
                            )
                        ]
                    ]
                ).row(
                    types.InlineKeyboardButton(
                        text="Сохранить",
                        callback_data='saveit'
                    ),
                    types.InlineKeyboardButton(
                        text="Отменить",
                        callback_data='back'
                    )
                )
            )
        else:
             await message.reply("Такой категории нет!")
    except ValueError:
        await message.reply("<b>ID</b> хранится в числовых значениях!")


# editing
@dp.callback_query_handler(state=MControlState.manage_menu)
async def save_or_not(call: types.CallbackQuery, state: FSMContext):
    if call.data == "saveit":
        data = await state.get_data()
        category_id = data.get('category_id')
        
        name = data.get('name')
        description = data.get('description')
        
        category_sale = data.get('category_sale')
        category_sale_percent = data.get('category_sale_percent')

        if name and description and category_id and category_sale and category_sale_percent:
            await db.update_category_data(name, description, category_sale, category_sale_percent, category_id)
        await call.message.edit_text(
            "<i>Данные для категории сохранены!</i>",
            reply_markup=None
        )
        await state.finish()
        await back_to_menu(call)

    elif call.data == "back":
        await call.message.edit_text(
            "<i>Отменяем правки в категориях!</i>",
            reply_markup=None
        )
        await back_to_menu(call)

    else:
        if call.data == "name":
            edit_data = "имя"
            await state.update_data(edit=call.data)
        elif call.data == "description":
            edit_data = "описание"
            await state.update_data(edit=call.data)
        elif call.data == "category_sale":
            edit_data = "скидку"
            await state.update_data(edit=call.data)

        await MControlState.edit_category.set()

        await call.message.edit_text(
            f"Редактируем {edit_data} категории. Введите новое значение",
            reply_markup=menu_control.quit_anything
        )


# quit editing
@dp.callback_query_handler(text='quit_anything', state=MControlState.edit_category)
async def quit_managing_category(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    name = data.get('name')
    description = data.get('description')
    category_id = data.get('category_id')
    category_sale = data.get('category_sale')
    category_sale_percent = data.get('category_sale_percent')

    await MControlState.manage_menu.set()
    await call.message.edit_text(
                ("<b>Какие данные будем править?</b>\n\n"
                f"<b>ID</b>: {category_id}\n"
                f"<b>Имя</b>: {name}\n"
                f"<b>Описание</b>: {description}\n"
                f"<b>Скидка</b>: {category_sale}\n") + \
                (f"<b>Величина скидки</b>: {category_sale_percent}%" if category_sale else ""),
                reply_markup=types.InlineKeyboardMarkup(
                    row_width=1,
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text="Имя",
                                callback_data='name'
                            )
                        ],
                        [
                            types.InlineKeyboardButton(
                                text="Описание",
                                callback_data='description'
                            )
                        ],
                        [
                            types.InlineKeyboardButton(
                                text="Скидка",
                                callback_data='category_sale'
                            )
                        ]
                    ]
                ).row(
                    types.InlineKeyboardButton(
                        text="Сохранить",
                        callback_data='saveit'
                    ),
                    types.InlineKeyboardButton(
                        text="Отменить",
                        callback_data='back'
                    )
                )
            )


# continue editing
@dp.message_handler(state=MControlState.edit_category)
async def await_data_manage(message: types.Message, state: FSMContext):    
    data = await state.get_data()
    edit = data.get('edit')
    category_sale = data.get('category_sale')
    
    if edit == "name":
        await state.update_data(name=message.text)
    elif edit == "description":
        await state.update_data(description=message.text)
    elif edit == "category_sale":
        try:
            percent = int(message.text)
            if percent in range(0, 100):
                if percent != 0:
                    await state.update_data(category_sale=True)
                    await state.update_data(category_sale_percent=percent)
                else:
                    await state.update_data(category_sale=False)
                    await state.update_data(category_sale_percent=None)
            else:
                await message.reply("В допустимых значениях!")
                return
        except ValueError:
                await message.reply("% скидки это числовое значение!")
                return

    await MControlState.confirm_category.set()
    await message.reply(
        "Запомнил. Продолжаем?",
        reply_markup=menu_control.continue_or_save
    )


@dp.callback_query_handler(state=MControlState.confirm_category)
async def continue_or_save(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    category_id = data.get('category_id')
    
    name = data.get('name')
    description = data.get('description')
    
    category_sale = data.get('category_sale')
    category_sale_percent = data.get('category_sale_percent')

    if call.data == "continue":
        await MControlState.manage_menu.set()
        await call.message.edit_text(
                ("<b>Какие данные будем править?</b>\n\n"
                f"<b>ID</b>: {category_id}\n"
                f"<b>Имя</b>: {name}\n"
                f"<b>Описание</b>: {description}\n"
                f"<b>Скидка</b>: {category_sale}\n") + \
                (f"<b>Величина скидки</b>: {category_sale_percent}%" if category_sale else ""),
                reply_markup=types.InlineKeyboardMarkup(
                    row_width=1,
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text="Имя",
                                callback_data='name'
                            )
                        ],
                        [
                            types.InlineKeyboardButton(
                                text="Описание",
                                callback_data='description'
                            )
                        ],
                        [
                            types.InlineKeyboardButton(
                                text="Скидка",
                                callback_data='category_sale'
                            )
                        ]
                    ]
                ).row(
                    types.InlineKeyboardButton(
                        text="Сохранить",
                        callback_data='saveit'
                    ),
                    types.InlineKeyboardButton(
                        text="Отменить",
                        callback_data='back'
                    )
                )
            )
    else:
        await db.update_category_data(name, description, category_sale, category_sale_percent, category_id)

        await call.message.edit_text(f"<i>Вы обновили категорию {name}!</i>", reply_markup=None)
        await state.finish()
        await back_to_menu(call)


@dp.callback_query_handler(state=MControlState.confirm_category)
async def confirm_category(call: types.CallbackQuery, state=FSMContext):
    data = await state.get_data()

    name = data.get('name')
    description = data.get('description')
    category_id = data.get('category_id')
    category_sale = data.get('category_sale')
    category_sale_percent = data.get('category_sale_percent')

    if call.data == "accept":

        await db.update_category_data(name, description, category_sale, category_sale_percent, category_id)

        await call.message.edit_text(f"<i>Вы обновили категорию {name}!</i>", reply_markup=None)
        await state.finish()
        await back_to_menu(call)
    else:
        await MControlState.manage_menu.set()
        await call.message.edit_text(
            ("<b>Какие данные будем править?</b>\n\n"
                f"<b>ID</b>: {category_id}\n"
                f"<b>Имя</b>: {name}\n"
                f"<b>Описание</b>: {description}\n"
                f"<b>Скидка</b>: {category_sale}\n") + \
                (f"<b>Величина скидки</b>: {category_sale_percent}%" if category_sale else ""),
            reply_markup=types.InlineKeyboardMarkup(
                row_width=1,
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(
                            text="Имя",
                            callback_data='name'
                        )
                    ],
                    [
                        types.InlineKeyboardButton(
                            text="Описание",
                            callback_data='description'
                        )
                    ],
                    [
                        types.InlineKeyboardButton(
                            text="Скидка",
                            callback_data='category_sale'
                        )
                    ]
                ]
            ).row(
                types.InlineKeyboardButton(
                    text="Сохранить",
                    callback_data='saveit'
                ),
                types.InlineKeyboardButton(
                    text="Отменить",
                    callback_data='back'
                )
            )
        )
