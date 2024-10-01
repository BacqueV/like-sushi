from aiogram import types
from loader import dp, db, bot


@dp.message_handler(text=['🛍 Заказать'])
async def order(message: types.Message):
    await message.answer('Скоро!')


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
    await message.answer('Скоро!')
