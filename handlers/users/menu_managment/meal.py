import asyncio
from data import config
from aiogram import types
from loader import dp, db, bot
from aiogram.dispatcher import FSMContext
from keyboards.inline import menu_control
from states.admin import MControlState
from handlers.users.admin.panel import notify_admins


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
async def save_meals_category(call: types.CallbackQuery, state: FSMContext):
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

        await db.add_meal(int(category_id), name, description, int(price))
        
        await call.message.edit_text(
            "<i>Вы добавили новое блюдо</i>\n\n",
            reply_markup=None
        )
        await notify_admins(
            f"Добавлено новое блюдо - <b>{name}</b> ({description})"
        )
    else:
        await call.message.edit_text(
            "<i>Вы отменили добавление нового блюда</i>",
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


# quit deleting meal
@dp.callback_query_handler(text='quit_anything', state=MControlState.await_id_delete_meal)
async def quit_deleting(call: types.CallbackQuery):
    await call.message.edit_text("<i>Вы отменили удаление блюда</i>", reply_markup=None)
    await back_to_menu(call)


# continue deleting
@dp.message_handler(state=MControlState.await_id_delete_meal)
async def await_id_delete_meal(message: types.Message, state: FSMContext):
    try:
        meal = await db.select_meal(meal_id=int(message.text))
        
        if meal:
            category = await db.select_category(category_id=meal[1])
    
            await state.update_data(meal_id=int(message.text))
            await MControlState.confirmation_delete_meal.set()
            await message.reply(
                "<b>Подтвердите удаление блюда!</b>\n\n" + \
                (f"<b>ID:</b> {meal[0]}\n"
                f"<b>Есть в наличии:</b> {meal[-1]}\n"
                f"<b>Имя:</b> {meal[2]}\n") + \
                f"<b>Цена:</b> {meal[4]}\n" +\
                (f"<b>Описание:</b> {meal[3]}\n") + \
                (f"<b>Категория:</b> {category[1]}\n" if category else "<b>Категория:</b> Была удалена\n") + \
                (f"<b>Скидка:</b> {meal[5]}\n") + \
                (f"<b>Величина скидки</b>: {meal[6]}%" if meal[5] else ""),
                reply_markup=menu_control.confirmation
            )
        else:
             await message.reply("Такого блюда нет!", reply_markup=menu_control.quit_anything)
    except ValueError:
        await message.reply("<b>ID</b> хранится в числовых значениях!", reply_markup=menu_control.quit_anything)


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

    await MControlState.await_id_manage_meal.set()
    await call.message.edit_text(
        "Введите <b>ID</b> блюда для правки\n\n"
        "Узнать вы это можете открыв меню\n\n"
        "<b>ID</b> будет являться колонка слева",
        reply_markup=menu_control.quit_anything
    )


# quit managing meal
@dp.callback_query_handler(text='quit_anything', state=MControlState.await_id_manage_meal)
async def quit_managing(call: types.CallbackQuery):
    await call.message.edit_text("<i>Вы отменили правки в параметрах блюд</i>", reply_markup=None)
    await back_to_menu(call)


# continue managing
@dp.message_handler(state=MControlState.await_id_manage_meal)
async def await_id_manage_meal(message: types.Message, state: FSMContext):
    try:
        meal = await db.select_meal(meal_id=int(message.text))

        if meal:
            category = await db.select_category(category_id=meal[1])

            await state.update_data(
                meal_id=meal[0],
                category_id=meal[1],
                name=meal[2],
                description=meal[3],
                price=meal[4],
                meal_sale=meal[5],
                meal_sale_percent=meal[6],
                included=meal[-1]
            )

            await MControlState.manage_menu_meal.set()

            await message.reply(
                "<b>Подтвердите удаление блюда!</b>\n\n" + \
                (f"<b>ID:</b> {meal[0]}\n"
                f"<b>Есть в наличии:</b> {meal[-1]}\n"
                f"<b>Имя:</b> {meal[2]}\n") + \
                f"<b>Цена:</b> {meal[4]}\n" +\
                (f"<b>Описание:</b> {meal[3]}\n") + \
                (f"<b>Категория:</b> {category[1]}\n" if category else "<b>Категория:</b> Была удалена\n") + \
                (f"<b>Скидка:</b> {meal[5]}\n") + \
                (f"<b>Величина скидки</b>: {meal[6]}%" if meal[5] else ""),
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
                                callback_data='meal_sale'
                            )
                        ],
                        [
                            types.InlineKeyboardButton(
                                text="В наличии",
                                callback_data='included'
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
             await message.reply("Такого блюда нет!", reply_markup=menu_control.quit_anything)
    except ValueError:
        await message.reply("<b>ID</b> хранится в числовых значениях!", reply_markup=menu_control.quit_anything)


# editing
@dp.callback_query_handler(state=MControlState.manage_menu_meal)
async def save_or_not(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
        
    meal_id = data.get('meal_id')
    category_id = data.get('category_id')
    
    name = data.get('name')
    description = data.get('description')

    price = data.get('price')
    meal_sale = data.get('meal_sale')
    meal_sale_percent = data.get('meal_sale_percent')

    included = data.get('included')

    if call.data == "saveit":
        await db.update_meal_data(int(category_id), name, description, int(price), meal_sale, int(meal_sale_percent), included, int(meal_id))

        await call.message.edit_text(
            "<i>Данные для блюда сохранены!</i>",
            reply_markup=None
        )
        await state.finish()
        await back_to_menu(call)

    elif call.data == "back":
        await call.message.edit_text(
            "<i>Отменяем правки в блюдах!</i>",
            reply_markup=None
        )
        await back_to_menu(call)

    else:
        if call.data == "name":
            edit_data = "имя"
            await state.update_data(edit=call.data)
        elif call.data == "included":
            category = await db.select_category(category_id=category_id)

            meal = await db.select_meal(meal_id=meal_id)

            included = meal[-1]
            new_state = not included
            await state.update_data(included=new_state)

            await db.update_included(new_state, meal_id)
            meal_new = await db.select_meal(meal_id=meal_id)
            
            await MControlState.manage_menu_meal.set()
            await call.message.edit_text(
                        "<b>Подтвердите удаление блюда!</b>\n\n" + \
                        (f"<b>ID:</b> {meal_id}\n"
                        f"<b>Есть в наличии:</b> {meal_new[-1]}\n"
                        f"<b>Имя:</b> {name}\n") + \
                        f"<b>Цена:</b> {price}\n" +\
                        (f"<b>Описание:</b> {description}\n") + \
                        (f"<b>Категория:</b> {category[1]}\n" if category else "<b>Категория:</b> Была удалена\n") + \
                        (f"<b>Скидка:</b> {meal_sale}\n") + \
                        (f"<b>Величина скидки</b>: {meal_sale_percent}%" if meal_sale else ""),
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
                                        callback_data='meal_sale'
                                    )
                                ],
                                [
                                    types.InlineKeyboardButton(
                                        text="В наличии",
                                        callback_data='included'
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
        elif call.data == "description":
            edit_data = "описание"
            await state.update_data(edit=call.data)

            await MControlState.edit_meal.set()

            await call.message.edit_text(
                f"Редактируем {edit_data} блюда. Введите новое значение",
                reply_markup=menu_control.quit_anything
            )
        elif call.data == "meal_sale":
            category = await db.select_category(category_id=category_id)
            if category[-2]:
                await call.answer(
                    "Для категории включена скидка. "
                    "Установить скидку отдельно для каждого из блюд в этой "
                    "категории теперь нельзя.\n"
                    "Чтобы это стало доступным - отключите скидку "
                    "для всей категории, выставив ее значение = 0",
                    show_alert=True
                )
                return

            edit_data = "скидку"
            await state.update_data(edit=call.data)

            await MControlState.edit_meal.set()

            await call.message.edit_text(
                f"Редактируем {edit_data} блюда. Введите новое значение",
                reply_markup=menu_control.quit_anything
            )


# quit editing
@dp.callback_query_handler(text='quit_anything', state=MControlState.edit_meal)
async def quit_managing_meal(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    category = await db.select_category(category_id=int(data.get('category_id')))

    meal_id = data.get('meal_id')

    name = data.get('name')
    description = data.get('description')

    price = data.get('price')
    meal_sale = data.get('meal_sale')
    meal_sale_percent = data.get('meal_sale_percent')

    included = data.get('included')

    await MControlState.manage_menu_meal.set()
    await call.message.edit_text(
                "<b>Подтвердите удаление блюда!</b>\n\n" + \
                (f"<b>ID:</b> {meal_id}\n"
                f"<b>Есть в наличии:</b> {included}\n"
                f"<b>Имя:</b> {name}\n") + \
                f"<b>Цена:</b> {price}\n" +\
                (f"<b>Описание:</b> {description}\n") + \
                (f"<b>Категория:</b> {category[1]}\n" if category else "<b>Категория:</b> Была удалена\n") + \
                (f"<b>Скидка:</b> {meal_sale}\n") + \
                (f"<b>Величина скидки</b>: {meal_sale_percent}%" if meal_sale else ""),
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
                                callback_data='meal_sale'
                            )
                        ],
                        [
                            types.InlineKeyboardButton(
                                text="В наличии",
                                callback_data='included'
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
@dp.message_handler(state=MControlState.edit_meal)
async def await_data_manage(message: types.Message, state: FSMContext):    
    data = await state.get_data()
    edit = data.get('edit')

    if edit == "name":
        await state.update_data(name=message.text)
    elif edit == "description":
        await state.update_data(description=message.text)
    elif edit == "meal_sale":
        try:
            percent = int(message.text)
            if percent in range(0, 100):
                if percent != 0:
                    await state.update_data(meal_sale=True)
                    await state.update_data(meal_sale_percent=percent)
                else:
                    await state.update_data(meal_sale=False)
                    await state.update_data(meal_sale_percent=0)
            else:
                await message.reply("В допустимых значениях!")
                return
        except ValueError:
                await message.reply("% скидки это числовое значение!")
                return

    await MControlState.confirm_meal.set()
    await message.reply(
        "Запомнил. Продолжаем?",
        reply_markup=menu_control.continue_or_save
    )


@dp.callback_query_handler(state=MControlState.confirm_meal)
async def continue_or_save(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    category = await db.select_category(category_id=int(data.get('category_id')))

    meal_id = data.get('meal_id')
    category_id = data.get('category_id')
    
    name = data.get('name')
    description = data.get('description')
    
    price = data.get('price')
    meal_sale = data.get('meal_sale')
    meal_sale_percent = data.get('meal_sale_percent')

    included = data.get('included')

    if call.data == "continue":
        await MControlState.manage_menu_meal.set()
        await call.message.edit_text(
                "<b>Подтвердите удаление блюда!</b>\n\n" + \
                (f"<b>ID:</b> {meal_id}\n"
                f"<b>Есть в наличии:</b> {included}\n"
                f"<b>Имя:</b> {name}\n") + \
                f"<b>Цена:</b> {price}\n" +\
                (f"<b>Описание:</b> {description}\n") + \
                (f"<b>Категория:</b> {category[1]}\n" if category else "<b>Категория:</b> Была удалена\n") + \
                (f"<b>Скидка:</b> {meal_sale}\n") + \
                (f"<b>Величина скидки</b>: {meal_sale_percent}%" if meal_sale else ""),
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
                                callback_data='meal_sale'
                            )
                        ],
                        [
                            types.InlineKeyboardButton(
                                text="В наличии",
                                callback_data='included'
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
        await db.update_meal_data(int(category_id), name, description, price, meal_sale, int(meal_sale_percent), included, int(meal_id))

        await call.message.edit_text(f"<i>Вы обновили категорию {name}!</i>", reply_markup=None)
        await state.finish()
        await back_to_menu(call)


@dp.callback_query_handler(state=MControlState.confirm_meal)
async def confirm_meal(call: types.CallbackQuery, state=FSMContext):
    data = await state.get_data()
    category = await db.select_category(category_id=int(data.get('category_id')))

    meal_id = data.get('meal_id')
    category_id = data.get('category_id')
    
    name = data.get('name')
    description = data.get('description')
    
    price = data.get('price')
    meal_sale = data.get('meal_sale')
    meal_sale_percent = data.get('meal_sale_percent')

    included = data.get('included')

    if call.data == "accept":

        await db.update_meal_data(int(category_id), name, description, meal_sale, int(meal_sale_percent), included, int(meal_id))

        await call.message.edit_text(f"<i>Вы обновили категорию {name}!</i>", reply_markup=None)
        await state.finish()
        await back_to_menu(call)
    else:
        await MControlState.manage_menu_meal.set()
        await call.message.edit_text(
            "<b>Подтвердите удаление блюда!</b>\n\n" + \
                (f"<b>ID:</b> {meal_id}\n"
                f"<b>Есть в наличии:</b> {included}\n"
                f"<b>Имя:</b> {name}\n") + \
                f"<b>Цена:</b> {price}\n" +\
                (f"<b>Описание:</b> {description}\n") + \
                (f"<b>Категория:</b> {category[1]}\n" if category else "<b>Категория:</b> Была удалена\n") + \
                (f"<b>Скидка:</b> {meal_sale}\n") + \
                (f"<b>Величина скидки</b>: {meal_sale_percent}%" if meal_sale else ""),
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
                            callback_data='meal_sale'
                        )
                    ],
                    [
                        types.InlineKeyboardButton(
                            text="В наличии",
                            callback_data='included'
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
