from aiogram import types
from loader import dp, db
from aiogram.dispatcher import FSMContext
from keyboards.inline import ordering
from states.ordering import OrderingState


@dp.callback_query_handler(text='quit', state=OrderingState.choose_category)
async def quit_choosing_category(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await call.message.edit_text(
        "<i>Вы прекратили просмотр меню</i>",
        reply_markup=None
    )


@dp.callback_query_handler(text='quit', state=OrderingState.choose_meal)
async def quit_choosing_meal(call: types.CallbackQuery):
    categories = await db.list_categories()
    categories_kb = await ordering.list_categories(categories)

    await OrderingState.choose_category.set()
    await call.message.edit_text(
        "<b>Выберите категорию</b>",
        reply_markup=categories_kb
    )


@dp.callback_query_handler(text='quit', state=OrderingState.meal_menu)
async def quit_meal_deal(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    category_id = data.get('category_id')
    
    meals = await db.open_category(category_id)

    category = await db.select_category(category_id=category_id)

    meals_kb = await ordering.list_meals(meals)

    await state.finish()
    await OrderingState.choose_meal.set()
    await call.message.edit_text(
        f"<b>{category[1]}</b>",
        reply_markup=meals_kb
    )
