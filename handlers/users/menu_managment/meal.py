import asyncio
from aiogram import types
from loader import dp, db, bot
from aiogram.dispatcher import FSMContext
from keyboards.inline import menu_control
from states.admin import MControlState
from handlers.users.admin.panel import notify_admins
from io import BytesIO
from aiogram.utils.exceptions import BadRequest


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
        await call.answer("Для начала вам нужно добавить хотя бы одну категорию блюд", show_alert=True)
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
        reply_markup=menu_control.skip_kb
    )


# continue without description
@dp.callback_query_handler(text='skip', state=MControlState.await_description_meal)
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

            await MControlState.await_image.set()
            await message.answer(
                "Будем добавлять фотографию к еде?",
                reply_markup=menu_control.skip_kb
            )
        else:
            await message.reply(
                "Цена обычно хранится в положительных значениях :|"
            )
    except ValueError:
        await message.reply("<b>Введенное значение должно быть числом!</b>")


# continue without image
@dp.callback_query_handler(text='skip', state=MControlState.await_image)
async def no_meal_description(call: types.CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "<i>Фотография не потребовалась</i>",
        reply_markup=None
    )

    await MControlState.confirmation_add_meal.set()
    data = await state.get_data()

    price = data.get('price')
    name = data.get('name')
    description = data.get('description')

    category_id = data.get('category_id')
    category = await db.select_category(category_id=int(category_id))

    await call.message.answer(
        (f"<b>Сохраняем?</b>\n\n"
        f"<b>Имя:</b> {name}\n") + \
        (f"<b>Описание:</b> {description}\n" if description else "") + \
        (f"<b>Цена:</b> {price}\n"
        f"<b>Категория:</b> {category[1]}"),
        reply_markup=menu_control.confirmation
    )


# continue with image
@dp.message_handler(state=MControlState.await_image, content_types=types.ContentType.ANY)
async def save_image(message: types.Message, state: FSMContext):
    # Получаем файл фотографии
    try:
        photo = message.photo[-1]  # Берем последнее фото, т.к. оно максимального размера
    except IndexError:
        await message.reply("Отправьте мне фотографию блюда!")
        return
    file = await bot.get_file(photo.file_id)
    file_path = file.file_path

    # Скачиваем файл
    downloaded_file = await bot.download_file(file_path)

    # Конвертируем фото в байты
    photo_data = BytesIO(downloaded_file.getvalue()).getvalue()

    await MControlState.confirmation_add_meal.set()
    data = await state.get_data()

    price = data.get('price')
    name = data.get('name')
    description = data.get('description')

    category_id = data.get('category_id')
    category = await db.select_category(category_id=int(category_id))
    
    msg = (f"<b>Сохраняем?</b>\n\n"
        f"<b>Имя:</b> {name}\n") + \
        (f"<b>Описание:</b> {description}\n" if description else "") + \
        (f"<b>Цена:</b> {price}\n"
        f"<b>Категория:</b> {category[1]}")

    await state.update_data(photo=photo_data)
    await message.reply_photo(
        photo=photo_data,
        caption=msg,
        reply_markup=menu_control.confirmation
    )

@dp.callback_query_handler(state=MControlState.confirmation_add_meal)
async def meal_add_confirmation(call: types.CallbackQuery, state: FSMContext):
    if call.data == "accept":
        data = await state.get_data()

        name = data.get('name')
        category_id = data.get('category_id')
        description = data.get('description')
        price = data.get('price')
        photo = data.get('photo')

        await db.add_meal(int(category_id), name, description, int(price), photo)
        
        await call.message.delete()
        await call.message.answer(
            "<i>Вы добавили новое блюдо</i>\n\n",
        )
        await notify_admins(
            f"Добавлено новое блюдо - <b>{name}</b> ({description})"
        )
    else:
        await call.message.delete()
        await state.finish()
        await call.message.answer(
            "<i>Вы отменили добавление блюда</i>\n\n",
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

            msg = "<b>Подтвердите удаление блюда!</b>\n\n" + \
                (f"<b>ID:</b> {meal[0]}\n"
                f"<b>Есть в наличии:</b> {meal[-2]}\n"
                f"<b>Имя:</b> {meal[2]}\n") + \
                f"<b>Цена:</b> {meal[4]}\n" +\
                (f"<b>Описание:</b> {meal[3]}\n") + \
                (f"<b>Категория:</b> {category[1]}\n" if category else "<b>Категория:</b> Была удалена\n") + \
                (f"<b>Скидка:</b> {meal[5]}\n") + \
                (f"<b>Величина скидки:</b> {meal[6]}%" if meal[5] else "")

            if meal[-1]:
                await message.reply_photo(
                    photo=meal[-1],
                    caption=msg,
                    reply_markup=menu_control.confirmation
                )
            else:
                await message.answer(
                    text=msg,
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

        await call.message.delete()
        await call.message.answer(
            f"Блюдо {meal_name} было удалено!",
            reply_markup=None
        )

        await notify_admins(
            f"Блюда <b>{meal_name}</b> было удалено!"
        )
    else:
        await call.message.delete()
        await call.message.answer("<i>Вы отменили удаление блюда!</i>", reply_markup=None)
    await back_to_menu(call)

"""
Manage meal
"""
manage_kb = types.InlineKeyboardMarkup(
                    row_width=2,
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text="Имя",
                                callback_data='name'
                            ),
                            types.InlineKeyboardButton(
                                text="Описание",
                                callback_data='description'
                            )
                        ],
                        [
                            types.InlineKeyboardButton(
                                text="Скидка",
                                callback_data='meal_sale'
                            ),
                            types.InlineKeyboardButton(
                                text="В наличии",
                                callback_data='included'
                            )
                        ],
                        [
                            types.InlineKeyboardButton(
                                text='Фотография',
                                callback_data='image'
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
                photo=meal[-1],
                meal_id=meal[0],
                category_id=meal[1],
                name=meal[2],
                description=meal[3],
                price=meal[4],
                meal_sale=meal[5],
                meal_sale_percent=meal[6],
                included=meal[-2]
            )

            await MControlState.manage_menu_meal.set()

            msg = "<b>Подтвердите правки в данных блюда!</b>\n\n" + \
                (f"<b>ID:</b> {meal[0]}\n"
                f"<b>Есть в наличии:</b> {meal[-2]}\n"
                f"<b>Имя:</b> {meal[2]}\n") + \
                f"<b>Цена:</b> {meal[4]}\n" +\
                (f"<b>Описание:</b> {meal[3]}\n") + \
                (f"<b>Категория:</b> {category[1]}\n" if category else "<b>Категория:</b> Была удалена\n") + \
                (f"<b>Скидка:</b> {meal[5]}\n") + \
                (f"<b>Величина скидки:</b> {meal[6]}%" if meal[5] else "")

            if meal[-1]:
                await message.reply_photo(
                    photo=meal[-1],
                    caption=msg,
                    reply_markup=manage_kb
                    
                )
            else:
                await message.reply(
                    msg,
                    reply_markup=manage_kb
                )
        else:
             await message.reply("Такого блюда нет!", reply_markup=menu_control.quit_anything)
    except ValueError:
        await message.reply("<b>ID</b> хранится в числовых значениях!", reply_markup=menu_control.quit_anything)


# editing
@dp.callback_query_handler(state=MControlState.manage_menu_meal)
async def save_or_not(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    
    photo = data.get('photo')
    meal_id = data.get('meal_id')
    category_id = data.get('category_id')
    
    name = data.get('name')
    description = data.get('description')

    price = data.get('price')
    meal_sale = data.get('meal_sale')
    meal_sale_percent = data.get('meal_sale_percent')

    included = data.get('included')

    if call.data == "saveit":
        await db.update_meal_data(
            int(category_id),
            name,
            description,
            int(price),
            meal_sale,
            int(meal_sale_percent),
            included,
            photo,
            int(meal_id)
        )

        await call.message.delete()
        await call.message.answer(
            "<i>Данные для блюда сохранены!</i>",
            reply_markup=None
        )
        await state.finish()
        await back_to_menu(call)
    elif call.data == "back":
        await call.message.delete()
        await call.message.answer(
            "<i>Отменяем правки в блюдах!</i>",
            reply_markup=None
        )
        await back_to_menu(call)
    else:
        if call.data == "name":
            edit_data = "имя"
            await state.update_data(edit=call.data)
            await MControlState.edit_meal.set()

            await call.message.delete()
            await call.message.answer(
                f"Редактируем {edit_data} блюда. Введите новое значение",
                reply_markup=menu_control.quit_anything
            )
        elif call.data == "included":
            category = await db.select_category(category_id=category_id)

            meal = await db.select_meal(meal_id=meal_id)

            included = meal[-2]
            new_state = not included
            await state.update_data(included=new_state)

            await db.update_included(new_state, meal_id)
            meal_new = await db.select_meal(meal_id=meal_id)
            
            await MControlState.manage_menu_meal.set()

            msg = "<b>Подтвердите правки в данных блюда!</b>\n\n" + \
                (f"<b>ID:</b> {meal_id}\n"
                f"<b>Есть в наличии:</b> {meal_new[-2]}\n"
                f"<b>Имя:</b> {name}\n") + \
                f"<b>Цена:</b> {price}\n" +\
                (f"<b>Описание:</b> {description}\n") + \
                (f"<b>Категория:</b> {category[1]}\n" if category else "<b>Категория:</b> Была удалена\n") + \
                (f"<b>Скидка:</b> {meal_sale}\n") + \
                (f"<b>Величина скидки</b>: {meal_sale_percent}%" if meal_sale else "")

            if photo:
                await call.message.edit_caption(
                    caption=msg,
                    reply_markup=manage_kb
                )
            else:
                await call.message.edit_text(
                    text=msg,
                    reply_markup=manage_kb
                )
        elif call.data == "description":
            edit_data = "описание"
            await state.update_data(edit=call.data)

            await MControlState.edit_meal.set()

            await call.message.delete()
            await call.message.answer(
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
                    "для всей категории, выставив ee значение = 0",
                    show_alert=True
                )
                return

            edit_data = "скидку"
            await state.update_data(edit=call.data)

            await MControlState.edit_meal.set()

            await call.message.delete()
            await call.message.answer(
                f"Редактируем {edit_data} блюда. Введите новое значение",
                reply_markup=menu_control.quit_anything
            )
        elif call.data == 'image':
            edit_data = "фотографию"
            await state.update_data(edit=call.data)

            await MControlState.edit_meal.set()

            if photo:
                await call.message.delete()
                await call.message.answer_photo(
                    photo=photo,
                    caption="Чтобы добавить / изменить фотографию, просто отправьте ее сюда, "
                    "если хотите удалить просто нажмите кнопку снизу",
                    reply_markup=menu_control.image_control
                )
            else:
                await call.message.edit_text(
                    text="Чтобы добавить / изменить фотографию, просто отправьте ее сюда, "
                    "если хотите удалить просто нажмите кнопку снизу",
                    reply_markup=menu_control.image_control
                )


# quit editing
@dp.callback_query_handler(text='quit_anything', state=MControlState.edit_meal)
async def quit_managing_meal(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    category = await db.select_category(category_id=int(data.get('category_id')))
    photo = data.get('photo')

    meal_id = data.get('meal_id')

    name = data.get('name')
    description = data.get('description')

    price = data.get('price')
    meal_sale = data.get('meal_sale')
    meal_sale_percent = data.get('meal_sale_percent')

    included = data.get('included')

    await MControlState.manage_menu_meal.set()

    msg = "<b>Подтвердите правки в данных блюда!</b>\n\n" + \
        (f"<b>ID:</b> {meal_id}\n"
        f"<b>Есть в наличии:</b> {included}\n"
        f"<b>Имя:</b> {name}\n") + \
        f"<b>Цена:</b> {price}\n" +\
        (f"<b>Описание:</b> {description}\n") + \
        (f"<b>Категория:</b> {category[1]}\n" if category else "<b>Категория:</b> Была удалена\n") + \
        (f"<b>Скидка:</b> {meal_sale}\n") + \
        (f"<b>Величина скидки:</b> {meal_sale_percent}%" if meal_sale else "")

    if photo:
        await call.message.delete()
        await call.message.answer_photo(
                    photo=photo,
                    caption= msg,
                    reply_markup=manage_kb
        )
    else:
        await call.message.edit_text(
            msg,
            reply_markup=manage_kb
        )


# deleting image of the meal
@dp.callback_query_handler(text='delete', state=MControlState.edit_meal)
async def delete_meal_image(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    photo = data.get("photo")
    meal_id = data.get("meal_id")
    name = data.get("name")

    included = data.get("included")
    price = data.get("price")
    meal_sale = data.get("meal_sale")
    meal_sale_percent = data.get("meal_sale_percent")
    description = data.get("description")
    
    category_id = data.get("category_id")
    category = await db.select_category(category_id=category_id)

    if not photo:
        await call.answer("Фото и так нет!")
    else:
        await db.delete_image(meal_id)
        await state.update_data(photo=None)

        await call.message.delete()
        await call.message.answer(f"Фотография <i>{name}</i> была успешно удалена!")

        await asyncio.sleep(.5)
        msg = "<b>Подтвердите правки в данных блюда!</b>\n\n" + \
        (f"<b>ID:</b> {meal_id}\n"
        f"<b>Есть в наличии:</b> {included}\n"
        f"<b>Имя:</b> {name}\n") + \
        f"<b>Цена:</b> {price}\n" +\
        (f"<b>Описание:</b> {description}\n") + \
        (f"<b>Категория:</b> {category[1]}\n" if category else "<b>Категория:</b> Была удалена\n") + \
        (f"<b>Скидка:</b> {meal_sale}\n") + \
        (f"<b>Величина скидки:</b> {meal_sale_percent}%" if meal_sale else "")
        await MControlState.manage_menu_meal.set()
        await call.message.answer(
            msg,
            reply_markup=manage_kb
        )


# save new photo
@dp.message_handler(content_types=types.ContentType.ANY, state=MControlState.edit_meal)
async def save_new_photo(message: types.Message, state: FSMContext):
    # Получаем файл фотографии
    try:
        photo = message.photo[-1]  # Берем последнее фото, т.к. оно максимального размера
    except IndexError:
        await message.reply("Отправьте мне фотографию блюда!")
        return
    file = await bot.get_file(photo.file_id)
    file_path = file.file_path

    # Скачиваем файл
    downloaded_file = await bot.download_file(file_path)

    # Конвертируем фото в байты
    photo_data = BytesIO(downloaded_file.getvalue()).getvalue()

    await MControlState.manage_menu_meal.set()
    data = await state.get_data()

    price = data.get('price')
    name = data.get('name')
    description = data.get('description')
    meal_id = data.get('meal_id')
    included = data.get('included')
    meal_sale = data.get('meal_sale')
    meal_sale_percent = data.get('meal_sale_percent')


    category_id = data.get('category_id')
    category = await db.select_category(category_id=int(category_id))
    
    msg = "<b>Подтвердите правки в данных блюда!</b>\n\n" + \
        (f"<b>ID:</b> {meal_id}\n"
        f"<b>Есть в наличии:</b> {included}\n"
        f"<b>Имя:</b> {name}\n") + \
        f"<b>Цена:</b> {price}\n" +\
        (f"<b>Описание:</b> {description}\n") + \
        (f"<b>Категория:</b> {category[1]}\n" if category else "<b>Категория:</b> Была удалена\n") + \
        (f"<b>Скидка:</b> {meal_sale}\n") + \
        (f"<b>Величина скидки:</b> {meal_sale_percent}%" if meal_sale else "")

    await state.update_data(photo=photo_data)
    await message.reply_photo(
        photo=photo_data,
        caption=msg,
        reply_markup=manage_kb
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
    elif edit == "image":
        await message.reply("<b>Отправьте фотографию блюда, или нажмите на одну из кнопок</b> 👆")
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
    photo = data.get('photo')

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

        msg = "<b>Подтвердите правки в данных блюда!</b>\n\n" + \
            (f"<b>ID:</b> {meal_id}\n"
            f"<b>Есть в наличии:</b> {included}\n"
            f"<b>Имя:</b> {name}\n") + \
            f"<b>Цена:</b> {price}\n" +\
            (f"<b>Описание:</b> {description}\n") + \
            (f"<b>Категория:</b> {category[1]}\n" if category else "<b>Категория:</b> Была удалена\n") + \
            (f"<b>Скидка:</b> {meal_sale}\n") + \
            (f"<b>Величина скидки:</b> {meal_sale_percent}%" if meal_sale else "")
        
        if photo:
            await call.message.delete()
            await call.message.answer_photo(
                photo=photo,
                caption=msg,
                reply_markup=manage_kb
            )
        else:
            await call.message.edit_text(
                    msg,
                    reply_markup=manage_kb
                )
    else:
        await db.update_meal_data(
            int(category_id),
            name,
            description,
            price,
            meal_sale,
            int(meal_sale_percent),
            included,
            photo,
            int(meal_id)
        )

        await call.message.delete()
        await call.message.answer(f"<i>Вы обновили блюдо №{name}!</i>", reply_markup=None)
        await state.finish()
        await back_to_menu(call)


@dp.callback_query_handler(state=MControlState.confirm_meal)
async def confirm_meal(call: types.CallbackQuery, state=FSMContext):
    data = await state.get_data()
    category = await db.select_category(category_id=int(data.get('category_id')))
    photo = data.get('photo')

    meal_id = data.get('meal_id')
    category_id = data.get('category_id')
    
    name = data.get('name')
    description = data.get('description')
    
    price = data.get('price')
    meal_sale = data.get('meal_sale')
    meal_sale_percent = data.get('meal_sale_percent')

    included = data.get('included')

    if call.data == "accept":

        await db.update_meal_data(
            int(category_id),
            name,
            description,
            meal_sale,
            int(meal_sale_percent),
            included,
            photo,
            int(meal_id)
        )

        await call.message.edit_text(f"<i>Вы обновили блюдо №{name}!</i>", reply_markup=None)
        await state.finish()
        await back_to_menu(call)
    else:
        await MControlState.manage_menu_meal.set()
        
        await call.message.delete()
        await call.message.answer(
            "<b>Подтвердите правки в данных блюда!</b>\n\n" + \
            (f"<b>ID:</b> {meal_id}\n"
            f"<b>Есть в наличии:</b> {included}\n"
            f"<b>Имя:</b> {name}\n") + \
            f"<b>Цена:</b> {price}\n" +\
            (f"<b>Описание:</b> {description}\n") + \
            (f"<b>Категория:</b> {category[1]}\n" if category else "<b>Категория:</b> Была удалена\n") + \
            (f"<b>Скидка:</b> {meal_sale}\n") + \
            (f"<b>Величина скидки:</b> {meal_sale_percent}%" if meal_sale else ""),
            reply_markup=types.InlineKeyboardMarkup(
                row_width=2,
                inline_keyboard=[
                    [
                        types.InlineKeyboardButton(
                            text="Имя",
                            callback_data='name'
                        ),
                        types.InlineKeyboardButton(
                            text="Описание",
                            callback_data='description'
                        )
                    ],
                    [
                        types.InlineKeyboardButton(
                            text="Скидка",
                            callback_data='meal_sale'
                        ),
                        types.InlineKeyboardButton(
                            text="В наличии",
                            callback_data='included'
                        )
                    ],
                    [
                        types.InlineKeyboardButton(
                            text='Фотография',
                            callback_data='image'
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
