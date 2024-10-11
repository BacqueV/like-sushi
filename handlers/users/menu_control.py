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
        await message.answer(
            "Вы открыли интерфейс управления меню",
            reply_markup=menu_control.main_menu
        )


@dp.callback_query_handler(text="list_categories", state=MControlState.main_menu)
async def list_categories(call: types.CallbackQuery):
    users = await db.list_categories()
    category_id = []
    name = []
    description = []
    for user in users:
        category_id.append(user[0])
        name.append(user[1])
        description.append(user[2])
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
    await call.message.edit_text(
        text="<i>Вы вышли из интерфейса управления меню!</i>",
        reply_markup=types.InlineKeyboardMarkup()
    )


async def back_to_menu(call: types.CallbackQuery):
    await asyncio.sleep(1)
    await MControlState.main_menu.set()
    await call.message.answer(
        "Вы открыли интерфейс управления меню",
        reply_markup=menu_control.main_menu
    )

"""
Add category
"""

@dp.callback_query_handler(text="add_category", state=MControlState.main_menu)
async def add_category(call: types.CallbackQuery):
    await MControlState.await_name.set()
    await call.message.edit_text(
        "<b>Вы добавляете новую категорию</b>\n\n" "Введите имя категории",
        reply_markup=menu_control.quit_anything
    )


@dp.callback_query_handler(text='quit_anything', state=MControlState.await_name)
async def no_category(call: types.CallbackQuery):
    await call.message.edit_text("<i>Вы отменили добавление категории</i>", reply_markup=types.InlineKeyboardMarkup())
    await MControlState.main_menu.set()
    await asyncio.sleep(1)
    await call.message.answer(
        "Вы открыли интерфейс управления меню",
        reply_markup=menu_control.main_menu
    )

@dp.message_handler(state=MControlState.await_name)
async def save_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await MControlState.await_description.set()
    await message.reply(
        "Сохранил! Теперь введи описание, если требуется",
        reply_markup=menu_control.quit_anything
    )


# continue without description
@dp.callback_query_handler(text='quit_anything', state=MControlState.await_description)
async def no_category_description(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    name = data.get('name')

    await call.message.edit_text(
        "<i>Описание не потребовалось</i>",
        reply_markup=types.InlineKeyboardMarkup()
    )
    
    await MControlState.confirmation_add.set()
    await call.message.answer(
        f"<b>Сохраняем?</b>\n\n" f"Имя: {name}",
        reply_markup=menu_control.confirmation
    )


# continue with description
@dp.message_handler(state=MControlState.await_description)
async def save_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data.get('name')
    await state.update_data(description=message.text)
    await MControlState.confirmation_add.set()
    await message.answer(
        f"<b>Сохраняем?</b>\n\n" f"Имя: {name}\n" f"Описание: {message.text}",
        reply_markup=menu_control.confirmation
    )


@dp.callback_query_handler(state=MControlState.confirmation_add)
async def category_add_confirmation(call: types.CallbackQuery, state: FSMContext):
    if call.data == "accept":
        data = await state.get_data()
        name = data.get("name")
        description = data.get("description")
        await db.add_category(name, description)
        
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

"""
Delete category
"""

@dp.callback_query_handler(text='delete_category', state=MControlState.main_menu)
async def delete_category(call: types.CallbackQuery):
    await MControlState.await_id_delete.set()
    await call.message.edit_text(
        "<b>Введите ID категории для удаления</b>\n\n"
        "Это вы можете узнать вернувшись в главное меню интерфейса!",
        reply_markup=menu_control.quit_anything
    )


# quit deleting category
@dp.callback_query_handler(text='quit_anything', state=MControlState.await_id_delete)
async def quit_deleting(call: types.CallbackQuery):
    await call.message.edit_text("<i>Вы отменили удаление категории</i>")
    await back_to_menu(call)


# continue deleting
@dp.message_handler(state=MControlState.await_id_delete)
async def await_id_delete(message: types.Message, state: FSMContext):
    try:
        category = await db.select_category(category_id=int(message.text))
        
        if category:
            await state.update_data(category_id=int(message.text))
            await MControlState.confirmation_delete.set()
            await message.reply(
                "<b>Подтвердите удаление категории!</b>\n"
                "<b>Все блюда принадлежащие этой категории будут удалены!</b>\n\n"
                f"<b>ID</b>: {category[0]}\n"
                f"<b>Имя</b>: {category[1]}\n"
                f"<b>Описание</b>: {category[2]}",
                reply_markup=menu_control.confirmation
            )
        else:
             await message.reply("Такой категории нет!")
    except ValueError:
        await message.reply("<b>ID</b> хранится в числовых значениях!")


@dp.callback_query_handler(state=MControlState.confirmation_delete)
async def category_delete_confirmation(call: types.CallbackQuery, state: FSMContext):
    if call.data == "accept":
        data = await state.get_data()
        category_id = data.get("category_id")
        category = await db.select_category(category_id=category_id)
        category_name = category[1]

        await db.delete_category(category_id)
        await call.message.edit_text(
            f"Категория [{category_name}] и все блюда принадлежащие ей были удалены!",
            reply_markup=types.InlineKeyboardMarkup()
        )

        await notify_admins(
            f"Категория <b>{category_name}</b> и все блюда принадлежащие ей были удалены!"
        )    
    await back_to_menu()

"""
Manage category
"""

@dp.callback_query_handler(text='manage_category', state=MControlState.main_menu)
async def manage_category(call: types.CallbackQuery):
    await MControlState.await_id_manage.set()
    await call.message.edit_text(
        "Введите <b>ID</b> категории для правки\n\n"
        "Узнать вы это можете воспользовавшись другой командой из главного меню. "
        "<b>ID</b> будет являтся колонка справа",
        reply_markup=menu_control.quit_anything
    )


# quit managing category
@dp.callback_query_handler(text='quit_anything', state=MControlState.await_id_manage)
async def quit_managing(call: types.CallbackQuery):
    await call.message.edit_text("<i>Вы отменили изменения в категориях</i>")
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
                description=category[2]
            )

            await MControlState.manage_menu.set()

            await message.reply(
                "<b>Какие данные будем править?</b>\n\n"
                f"<b>ID</b>: {category[0]}\n"
                f"<b>Имя</b>: {category[1]}\n"
                f"<b>Описание</b>: {category[2]}",
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


# editing name
@dp.callback_query_handler(state=MControlState.manage_menu)
async def edit_data(call: types.CallbackQuery, state: FSMContext):
    if call.data == "saveit":
        data = await state.get_data()
        name = data.get('name')
        description = data.get('description')
        category_id = data.get('category_id')

        if name and description and category_id:
            await db.update_category_data(name, description, category_id)
        await call.message.edit_text(
            "<i>Данные для категории сохранены!</i>",
            reply_markup=types.InlineKeyboardMarkup()
        )
        await state.finish()
        await back_to_menu(call)
    elif call.data == "back":
        await call.message.edit_text(
            "<i>Отменяем правки в категориях!</i>",
            reply_markup=types.InlineKeyboardMarkup()
        )
        await back_to_menu(call)

    else:
        if call.data == "name":
            edit_data = "имя"
            await state.update_data(edit=call.data)
        elif call.data == "description":
            edit_data = "описание"
            await state.update_data(edit=call.data)

        await MControlState.edit_category.set()

        await call.message.edit_text(
            f"Редактируем {edit_data} категории. Введи новое значение",
            reply_markup=menu_control.quit_anything
        )


@dp.callback_query_handler(text='quit_anything', state=MControlState.edit_category)
async def quit_managing_category(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    name = data.get('name')
    description = data.get('description')
    category_id = data.get('category_id')

    await MControlState.manage_menu.set()
    await call.message.edit_text(
                "<b>Какие данные будем править?</b>\n\n"
                f"<b>ID</b>: {category_id}\n"
                f"<b>Имя</b>: {name}\n"
                f"<b>Описание</b>: {description}",
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


@dp.message_handler(state=MControlState.edit_category)
async def await_data_manage(message: types.Message, state: FSMContext):
    await MControlState.confirm_category.set()
    
    data = await state.get_data()
    edit = data.get('edit')
    
    if edit == "name":
        await state.update_data(name=message.text)
    else:
        await state.update_data(description=message.text)

    await message.reply(
        "Запомнил. Продолжаем?",
        reply_markup=menu_control.continue_or_save
    )


@dp.callback_query_handler(state=MControlState.confirm_category)
async def continue_or_save(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    name = data.get('name')
    description = data.get('description')
    category_id = data.get('category_id')

    if call.data == "continue":
        await MControlState.manage_menu.set()
        await call.message.edit_text(
                "<b>Какие данные будем править?</b>\n\n"
                f"<b>ID</b>: {category_id}\n"
                f"<b>Имя</b>: {name}\n"
                f"<b>Описание</b>: {description}",
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
        await db.update_category_data(name, description, category_id)

        await call.message.edit_text(f"<i>Вы обновили категорию {name}!</i>", reply_markup=types.InlineKeyboardMarkup())
        await state.finish()
        await back_to_menu(call)


@dp.callback_query_handler(state=MControlState.confirm_category)
async def confirm_category(call: types.CallbackQuery, state=FSMContext):
    data = await state.get_data()

    name = data.get('name')
    description = data.get('description')
    category_id = data.get('category_id')

    if call.data == "accept":

        await db.update_category_data(name, description, category_id)

        await call.message.edit_text(f"<i>Вы обновили категорию {name}!</i>", reply_markup=types.InlineKeyboardMarkup())
        await state.finish()
        await back_to_menu(call)
    else:
        await MControlState.manage_menu.set()
        await call.message.edit_text(
            "<b>Какие данные будем править?</b>\n\n"
            f"<b>ID</b> Категории: {category_id}\n"
            f"<b>Имя</b>: {name}\n"
            f"<b>Описание</b>: {description}",
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
