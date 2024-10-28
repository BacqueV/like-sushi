from aiogram import types
from loader import dp, db, bot
from keyboards.inline import ordering
from states.ordering import OrderingState


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


@dp.message_handler(text=['✍️ Оставить отзыв'])
async def order(message: types.Message):
    await message.answer('Скоро!')


@dp.message_handler(text=['🏠 Ближайший филиал'])
async def order(message: types.Message):
    await message.answer('Скоро!')


@dp.message_handler(text=['🎉 Акция'])
async def order(message: types.Message):
    await message.answer('Скоро!')


@dp.message_handler(text=['🏘 Филиалы'])
async def order(message: types.Message):
    await message.answer('Скоро!')


@dp.message_handler(text=['⚙️ Настройки'])
async def order(message: types.Message):
    await message.answer('Скоро!')


@dp.message_handler(text=['📋 Мои заказы'])
async def order(message: types.Message):
    await message.answer('Скоро!')


@dp.message_handler(text=['ℹ️ О нас'])
async def order(message: types.Message):
    await message.answer(
        '<b>Like Sushi</b> в Ташкенте — это сочетание свежих ингредиентов, авторских рецептов и японских традиций.\n\n'
        'Наши суши и роллы созданы с любовью к деталям, чтобы каждый кусочек приносил удовольствие.\n\n'
        'Закажите ваши любимые блюда через нашего Telegram-бота и наслаждайтесь вкусом востока, где бы вы ни были!'
    )
