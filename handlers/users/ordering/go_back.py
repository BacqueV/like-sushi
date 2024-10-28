from aiogram import types
from loader import dp, db, bot
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