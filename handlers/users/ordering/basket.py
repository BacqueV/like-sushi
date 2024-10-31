from aiogram import types
from loader import dp, db
from aiogram.dispatcher import FSMContext
from keyboards.inline import ordering
from keyboards.default import main_menu
from states.ordering import OrderingState


@dp.callback_query_handler(text=['open_basket', 'back'], state=[OrderingState.choose_category, OrderingState.choose_meal, OrderingState.order])
async def open_basket(call: types.CallbackQuery):
    data = await db.order_meals(call.from_user.id)

    if data:
        response = "<b>Корзина:</b>\n\n"
        for row in data:
            meal = await db.select_meal(meal_id=row['meal_id'])
            name = meal[2]

            response += f"<b>ID:</b> {row['meal_id']}\n" + \
            f"<b>Имя:</b> {name}\n" + \
            f"<b>Количество:</b> {row['amount_sum']}\n" + \
            f"<b>Цена блюда за штуку:</b> {row['real_price']}\n" + \
            f"<b>Общая стоимость:</b> {row['total_cost_sum']} {row['info']}\n\n"
    else:
        response = "🍱 Надо выбрать что поесть 😋"
        await call.answer(response)
        return

    await OrderingState.basket.set()
    await call.message.edit_text(response, reply_markup=ordering.basket_kb)


@dp.callback_query_handler(text='empty', state=OrderingState.basket)
async def empty_basket(call: types.CallbackQuery, state: FSMContext):
    await db.clean_busket(int(call.from_user.id))
    await state.finish()

    await call.answer("😎 Чисто")
    await call.message.edit_text(
        "Теперь вы можете заново заполнить эту корзину, "
        "нажав на 🛍 Заказать",
        reply_markup=main_menu.kb
    )
