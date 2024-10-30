from aiogram import types
import asyncio
from loader import dp, db, bot
from aiogram.dispatcher import FSMContext
from keyboards.inline import ordering
from states.ordering import OrderingState
from . import go_back


@dp.callback_query_handler(state=OrderingState.choose_category)
async def open_category(call: types.CallbackQuery, state: FSMContext):
    meals = await db.open_category(int(call.data))

    category = await db.select_category(category_id=int(call.data))
    await state.update_data(category_id=int(call.data))

    if len(meals) == 0:
        await call.message.edit_text(
            f"Вы открыли категорию: <i>{category[1]}</i>",
            reply_markup=None
        )

        await call.message.answer(
            "Меню пусто 😕\n"
            "Это значит, что либо мы готовим новое меню, либо вам стоит обратиться в тех. поддержку 😌\n\n"
            "Осуществить заказ вы можете через Uzum Tezkor или же Яндекс.Еда!\n\n"
            "<b><a href='https://www.uzumtezkor.uz/ru/restaurants/94b3642e-5147-4afb-a026-c7f54c80a108'>Uzum Tezkor</a></b>\n"
            "<b><a href='https://eda.yandex.ru/restaurant/like_2kzq8?utm_campaign=superapp_taxi_web&utm_medium=referral&utm_source=rst_shared_link'>Яндекс.Еда</a></b>\n\n",
            disable_web_page_preview=True
        )
        await asyncio.sleep(.5)
        
        categories = await db.list_categories()
        categories_kb = await ordering.list_categories(categories)

        await OrderingState.choose_category.set()
        await call.message.answer(
            "<b>Выберите категорию</b>",
            reply_markup=categories_kb
        )

        return

    meals_kb = await ordering.list_meals(meals)

    await OrderingState.choose_meal.set()
    await call.message.edit_text(
        f"<b>{category[1]}</b>",
        reply_markup=meals_kb
    )


@dp.callback_query_handler(state=OrderingState.choose_meal)
async def open_meal(call: types.CallbackQuery, state: FSMContext):
    meal = await db.select_meal(meal_id=int(call.data))
    category = await db.select_category(category_id=int(meal[1]))

    if meal[5]:
        price = meal[4] * (1 - meal[6] / 100)
        discount_state = meal[5]
        discount = meal[6]
        info = f"(Со скидкой в {meal[6]}% на единицу блюда)"
    else:
        price = meal[4]
        discount_state = False
        discount = 0
        info = ''
        if category[-2]:
            price = meal[4] * (1 - category[-1] / 100)
            discount_state = category[-2]
            discount = category[-1]
            info = f"(Со скидкой в {category[-1]}% на единицу блюда)"

    await state.update_data(
        meal_id=int(call.data), category_id=meal[1], amount=1,
        price=price, real_price = meal[4], total_cost=price,
        discount_state=discount_state, discount=discount,
        info=info
    )
    await OrderingState.meal_menu.set()

    meal_menu_kb = await ordering.meal_menu_markup(1)

    await call.message.edit_text(
        f"{1} x {meal[4]} = <b>{price}</b> {info}\n\n"
        f"<b>ID:</b> {meal[0]}\n"
        f"<b>Имя:</b> {meal[2]}\n"
        f"<b>Категория:</b> {category[1]}\n"
        f"<b>Цена:</b> {meal[4]}\n"
        f"<b>Описание:</b> {meal[3]}\n" + \
        (f"<b>Скидка:</b> {'Есть' if discount_state else 'Отсутствует'}\n") + \
        (f"<b>Величина скидки</b>: {discount}%" if discount_state else ""),
        reply_markup=meal_menu_kb
    )


@dp.callback_query_handler(state=OrderingState.meal_menu)
async def meal_deal(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    category = await db.select_category(category_id=data.get('category_id'))
    meal_id = data.get('meal_id')
    real_price = data.get('real_price')
    amount = data.get('amount')
    meal = await db.select_meal(meal_id=data.get('meal_id'))
    price = data.get('price')
    discount_state = data.get('discount_state')
    discount = data.get('discount')
    total_cost = data.get('total_cost')
    info = data.get('info')

    if call.data == 'decrease':
        if amount == 1:
            await call.answer(":D")
        else:
            await state.update_data(amount=amount-1)
            
            meal_menu_kb = await ordering.meal_menu_markup(amount-1)
            
            total_cost = (amount-1) * price
            await state.update_data(total_cost=total_cost)

            await call.message.edit_text(
                f"{amount-1} x {meal[4]} = <b>{total_cost}</b> {info}\n\n"
                f"<b>ID:</b> {meal[0]}\n"
                f"<b>Имя:</b> {meal[2]}\n"
                f"<b>Категория:</b> {category[1]}\n"
                f"<b>Цена:</b> {meal[4]}\n"
                f"<b>Описание:</b> {meal[3]}\n" + \
                (f"<b>Скидка:</b> {'Есть' if discount_state else 'Отсутствует'}\n") + \
                (f"<b>Величина скидки</b>: {discount}%" if discount_state else ""),
                reply_markup=meal_menu_kb
            )
    elif call.data == 'increase':
        await state.update_data(amount=amount+1)

        meal_menu_kb = await ordering.meal_menu_markup(amount+1)

        total_cost = (amount+1) * price
        await state.update_data(total_cost=total_cost)

        await call.message.edit_text(
            f"{amount+1} x {meal[4]} = <b>{total_cost}</b> {info}\n\n"
            f"<b>ID:</b> {meal[0]}\n"
            f"<b>Имя:</b> {meal[2]}\n"
            f"<b>Категория:</b> {category[1]}\n"
            f"<b>Цена:</b> {meal[4]}\n"
            f"<b>Описание:</b> {meal[3]}\n" + \
            (f"<b>Скидка:</b> {'Есть' if discount_state else 'Отсутствует'}\n") + \
            (f"<b>Величина скидки</b>: {discount}%" if discount_state else ""),
            reply_markup=meal_menu_kb
        )
    elif call.data == 'basket':
        data = await state.get_data()
        total_cost = data.get('total_cost')
        await db.add_meal_into_basket(
            call.message.from_user.id, meal_id, real_price,
            amount, price, total_cost, info, discount
        )
        await call.answer("Добавлено!")
        await go_back.quit_meal_deal(call, state)
