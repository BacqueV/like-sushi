from aiogram import types
import asyncio
from loader import dp, db, bot
from aiogram.dispatcher import FSMContext
from keyboards.inline import ordering
from states.ordering import OrderingState


@dp.callback_query_handler(text='open_basket', state='*')
async def open_basket(call: types.CallbackQuery, state: FSMContext):
    data = await db.orders_meals(call.from_user.id)

    if data:
        response = "Данные по блюдам:\n"
        for row in data:
            meal = await db.select_meal(meal_id=row['meal_id'])
            name = meal['name']

            response += f"<b>ID:</b> {row['meal_id']}\n" + \
            f"<b>Имя:</b> {name}\n" + \
            f"<b>Количество:</b> {row['amount_sum']}\n" + \
            f"<b>Цена блюда за штуку:</b> {row['real_price']}\n" + \
            f"<b>Общая стоимость:</b> {row['total_cost_sum']} {row['info']}\n\n"
    else:
        response = "Нет данных."

    await call.message.edit_text(response, reply_markup=None)
