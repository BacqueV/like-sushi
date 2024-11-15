from aiogram import types
from loader import dp, db
from keyboards.inline import ordering
from keyboards.default import main_menu
from aiogram.dispatcher import FSMContext
from states.orders import UserOrders
from states.ordering import OrderingState
from states.settings import SettingsState
import asyncio


@dp.message_handler(text=['🛍 Заказать'])
async def order(message: types.Message):
    categories = await db.list_categories()

    if len(categories) == 0:
        await message.answer(
            "Меню пусто 😕\n"
            "Это значит, что либо мы готовим новое меню, либо вам стоит обратиться в тех. поддержку 😌\n\n"
            "Осуществить заказ вы можете через Uzum Tezkor или же Яндекс.Еда!\n\n"
            "<b><a href='https://www.uzumtezkor.uz/ru/restaurants/94b3642e-5147-4afb-a026-c7f54c80a108'>Uzum Tezkor</a></b>\n"
            "<b><a href='https://eda.yandex.ru/restaurant/like_2kzq8?utm_campaign=superapp_taxi_web&utm_medium=referral&utm_source=rst_shared_link'>Яндекс.Еда</a></b>\n\n",
            disable_web_page_preview=True
        )
        return

    categories_kb = await ordering.list_categories(categories)

    await OrderingState.choose_category.set()
    await message.answer(
        "<b>Выберите категорию</b>",
        reply_markup=categories_kb
    )


@dp.message_handler(text=['🎉 Акции'])
async def shares(message: types.Message):
    categories_onsale = await db.select_onsale_categories()
    meals_onsale = await db.select_all_onsale_meals()

    response = "<b>Скидки на целые категории блюд</b>\n\n"
    for category in categories_onsale:
        response += f"{category['name']}\n"

    response += '\n<b>Скидки на отдельные блюда</b>\n\n'
    for meal in meals_onsale:
        response += f"{meal['name']}\n"

    await message.answer(response)


@dp.message_handler(text=['🏘 Филиалы'])
async def branches(message: types.Message):
    branches = await db.branchlist()

    for branch in branches:
        await message.answer(f"<b>№{branch[0]} - {branch[1]}</b>")
        await message.answer_location(branch[2], branch[3])
        await asyncio.sleep(.05)


@dp.message_handler(text=['⚙️ Настройки'])
async def settings(message: types.Message):
    await SettingsState.menu.set()
    user = await db.select_user(telegram_id=message.from_user.id)
    await message.answer(
        "<b>Выберите настройку</b>\n\n"
        f"Номер телефона: <code>{user[-1]}</code>",
        reply_markup=main_menu.settings_kb
    )


@dp.message_handler(text=['⬅️ Назад'], state=SettingsState.menu)
async def quit_settings(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer(
        "<i>Вы покинули меню настроек</i>",
        reply_markup=main_menu.kb
    )


@dp.message_handler(content_types=types.ContentType.CONTACT, state=SettingsState.menu)
async def change_phone_number(message: types.Message, state: FSMContext):
    phone_number = message.contact.phone_number
    # Здесь сохраняем номер в базу данных или выполняем другие действия
    await db.save_phone_number(
        message.from_user.id,
        phone_number,
        message.from_user.full_name
    )
    await message.answer(
        f"<b>Новый номер телефона сохранен!</b>\n{phone_number}",
        reply_markup=main_menu.settings_kb    
    )


@dp.message_handler(text=['📋 Мои заказы'])
async def my_orders(message: types.Message):
    telegram_id = message.from_user.id
    orders = await db.list_user_orders(telegram_id)
    
    msg = '<b>Ваши заказы</b>'
    orders_kb = types.InlineKeyboardMarkup(row_width=2)

    for order in orders:
        orders_kb.insert(
            types.InlineKeyboardButton(
                text=f"№{order[0]} - {order[-1]} сум",
                callback_data=str(order[0])
            )
        )

    btn_quit = types.InlineKeyboardButton(
        text='Закрыть',
        callback_data='quit'
    )
    orders_kb.row(btn_quit)

    await message.answer(text=msg, reply_markup=orders_kb)
    await UserOrders.list.set()


@dp.callback_query_handler(text='quit', state=UserOrders.list)
async def quit_order_menu(call: types.CallbackQuery):
    await call.message.edit_text(
        "<i>Вы завершили просмотр ваших заказов</i>",
        reply_markup=None
    )


@dp.callback_query_handler(state=UserOrders.list)
async def open_order(call: types.CallbackQuery):
    order_id = int(call.data)
    order = await db.select_order(order_id=order_id)

    btn_quit = types.InlineKeyboardButton(
        text='Назад ⬅️',
        callback_data='quit'
    )
    order_kb = types.InlineKeyboardMarkup(row_width=2)
    order_kb.row(btn_quit)

    await call.message.edit_text(order[1], reply_markup=order_kb)
    await UserOrders.certain_order.set()


@dp.callback_query_handler(text='quit', state=UserOrders.certain_order)
async def quit_order_menu(call: types.CallbackQuery):
    telegram_id = call.from_user.id
    orders = await db.list_user_orders(telegram_id)
    
    msg = '<b>Ваши заказы</b>'
    orders_kb = types.InlineKeyboardMarkup(row_width=2)

    for order in orders:
        orders_kb.insert(
            types.InlineKeyboardButton(
                text=f"№{order[0]} - {order[-1]} сум",
                callback_data=str(order[0])
            )
        )

    btn_quit = types.InlineKeyboardButton(
        text='Закрыть',
        callback_data='quit'
    )
    orders_kb.row(btn_quit)

    await call.message.edit_text(text=msg, reply_markup=orders_kb)
    await UserOrders.list.set()

@dp.message_handler(text=['ℹ️ О нас'])
async def about_us(message: types.Message):
    await message.answer(
        '<b>Like Sushi</b> — это сочетание свежих ингредиентов, авторских рецептов и японских традиций.\n\n'
        'Наши суши и роллы созданы с любовью к деталям, чтобы каждый кусочек приносил удовольствие.\n\n'
        'Закажите ваши любимые блюда через нашего Telegram-бота и наслаждайтесь вкусом востока!'
    )
