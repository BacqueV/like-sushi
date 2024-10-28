from aiogram import types
import asyncio
from loader import dp, db, bot
from aiogram.dispatcher import FSMContext
from keyboards.inline import ordering
from states.ordering import OrderingState


@dp.callback_query_handler(state=OrderingState.choose_category)
async def open_category(call: types.CallbackQuery):
    meals = await db.open_category(int(call.data))

    category = await db.select_category(category_id=int(call.data))

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
        "<b>Выберите блюдо</b>",
        reply_markup=meals_kb
    )


@dp.callback_query_handler(state=OrderingState.choose_meal)
async def open_meal(call: types.CallbackQuery, state: FSMContext):
    meal = await db.select_meal(meal_id=int(call.data))
    category = await db.select_category(category_id=int(meal[1]))

    await state.update_data(meal_id=int(call.data))
    await OrderingState.meal_menu.set()

    await call.message.reply(
        (f"<b>ID:</b> {meal[0]}\n"
        f"<b>Есть в наличии:</b> {'Есть' if meal[-1] else 'Отсутствует'}\n"
        f"<b>Имя:</b> {meal[2]}\n") + \
        f"<b>Цена:</b> {meal[4]}\n" +\
        (f"<b>Описание:</b> {meal[3]}\n") + \
        (f"<b>Категория:</b> {category[1]}\n" if category else "<b>Категория:</b> Была удалена\n") + \
        (f"<b>Скидка:</b> {'Есть' if meal[5] else 'Отсутствует'}\n") + \
        (f"<b>Величина скидки</b>: {meal[6]}%" if meal[5] else "")
    )
