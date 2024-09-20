import asyncio
from aiogram import types
from data.config import ADMINS
from loader import dp, db, bot
from states.admin import AdminState
from aiogram.dispatcher import FSMContext


@dp.message_handler(text="/advert", user_id=ADMINS)
async def wait_msg(message: types.Message):
    await message.answer("<i>Что будем рекламировать?</i>")
    await AdminState.wait_msg.set()


@dp.message_handler(user_id=ADMINS, state=AdminState.wait_msg)
async def are_you_sure(message: types.Message, state: FSMContext):
    await state.update_data(ad=message.text)  # setting ad message
    await message.answer("Отправляем?\n" + "<b>Да / Нет</b>\n" + "<b>Yes / No</b>")
    await AdminState.check_ad.set()


@dp.message_handler(user_id=ADMINS, state=AdminState.check_ad)
async def send_ad(message: types.Message, state: FSMContext):
    data = await state.get_data()
    ad = data.get("ad")

    if message.text.lower() in ("да", "д", "yes", "y"):
        
        users = await db.select_all_users()
        for user in users:
            user_id = user[-1]
            try:
                await bot.send_message(chat_id=user_id, text=ad)
            except Exception:
                pass
            await asyncio.sleep(0.05)

        await state.finish()  # CLEARING STATE

    elif message.text.lower() in ("нет", "н", "no", "n"):

        await state.finish()  # CLEARING STATE
        await message.answer("Отменяем рекламу...")

    else:

        await message.answer("Таки да или нет?")
