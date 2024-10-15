from aiogram import types
from loader import dp, db, bot


@dp.message_handler(text=['🛍 Заказать'])
async def order(message: types.Message):
    await message.answer(
        "Осуществить заказ вы можете через Uzum Tezkor или же Яндекс.Еда!\n\n"
        "<b><a href='https://www.uzumtezkor.uz/ru/restaurants/94b3642e-5147-4afb-a026-c7f54c80a108'>Uzum Tezkor</a></b>\n"
        "<b><a href='https://eda.yandex.ru/restaurant/like_2kzq8?utm_campaign=superapp_taxi_web&utm_medium=referral&utm_source=rst_shared_link'>Яндекс.Еда</a></b>\n\n"
        "<i>Доставка через телеграм бота будет доступна скоро!</i>",
        disable_web_page_preview=True
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
