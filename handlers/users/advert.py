import asyncio
from aiogram import types
from data.config import ADMINS
from loader import dp, db, bot
from states.admin import AdminState
from aiogram.dispatcher import FSMContext
from keyboards.inline.advert import keyboard_builder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from utils.broadcast import broadcaster


@dp.message_handler(text='/advert', user_id=ADMINS)
async def wait_msg(message: types.Message):
    await message.answer("Приступаем к созданию рассылки!\n" + "<b>Отправь сообщение для рассылки</b>")
    await AdminState.wait_msg.set()


@dp.message_handler(state=AdminState.wait_msg)
async def get_message(message: types.Message, state: FSMContext):
    await state.update_data(message_id=message.message_id, chat_id=message.from_user.id)
    await message.answer(
        'Хорошо, я запомнил сообщение, которое ты хочешь разослать\n' + 
        'Хочешь добавить кнопку со ссылкой на рекламируемый ресурс?',
        reply_markup=keyboard_builder
    )
    await AdminState.build_kb.set()


@dp.callback_query_handler(state=AdminState.build_kb)
async def build_kb(call: types.CallbackQuery, state: FSMContext):
    if call.data == 'add_btn':
        await call.message.answer("Отправь текст для кнопки", reply_markup=None)
        await AdminState.get_btn_txt.set()
    
    elif call.data == 'no_btn':
        await call.message.edit_reply_markup(reply_markup=None)
    
        data = await state.get_data()
    
        message_id = int(data.get('message_id'))
        chat_id = int(data.get('chat_id'))
    
        await confirm(call.message, message_id, chat_id)
        await AdminState.confirmation.set()

    await call.answer()


@dp.message_handler(state=AdminState.get_btn_txt)
async def get_btn_txt(message: types.Message, state: FSMContext):
    await state.update_data(btn_txt=message.text)
    await message.answer('Теперь отправь ссылку')
    await AdminState.get_btn_url.set()


@dp.message_handler(state=AdminState.get_btn_url)
async def get_btn_url(message: types.Message, state: FSMContext):
    await state.update_data(btn_url=message.text)
    data = await state.get_data()
    btn_txt = data.get('btn_txt')
    confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=(btn_txt),
                url=f'{message.text}'
            )
        ]
    ])
    data = await state.get_data()
    message_id = int(data.get('message_id'))
    chat_id = int(data.get('chat_id'))
    await confirm(message, message_id, chat_id, confirm_keyboard)


@dp.message_handler(state=AdminState.get_btn_url)
async def confirm(message: types.Message, message_id: int, chat_id: int, reply_markup: InlineKeyboardMarkup = None):
    await bot.copy_message(chat_id, chat_id, message_id, reply_markup=reply_markup)
    await message.answer(
        "Вот сообщение, которое будет отправлено. Проверь!",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text='Подтвердить',
                        callback_data='confirm'
                    )
                ],
                [
                    InlineKeyboardButton(
                        text='Отменить',
                        callback_data='deny'
                    )
                ]
            ]
        )
    )
    await AdminState.confirmation.set()


@dp.callback_query_handler(state=AdminState.confirmation)
async def decide_confirmation(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    message_id = data.get('message_id')
    chat_id = data.get('chat_id')
    btn_txt = data.get('btn_txt')
    btn_url = data.get('btn_url')

    if call.data == 'confirm':
        await call.message.edit_text('Начинаю рассылку', reply_markup=None)

        await db.fill_broadcasting_table()  # in
        
        count = await broadcaster(bot, chat_id, message_id, btn_txt, btn_url)
        await call.message.answer(f"Успешно разослали сообщение [{count}] пользователям!")
        
        await db.clean_broadcasting_table()  # out

    elif call.data == 'deny':
        await call.message.edit_text('Отменяю рассылку', reply_markup=None)

    await state.finish()
