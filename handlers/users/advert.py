import asyncio
from aiogram import types
from data.config import ADMINS
from loader import dp, db, bot
from states.admin import AdminState
from aiogram.dispatcher import FSMContext
from keyboards.inline.advert import keyboard_builder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


@dp.message_handler(commands=["advert"], user_id=ADMINS)
async def wait_msg(message: types.Message, state: FSMContext):
    cmd_args = message.get_args()
    if not cmd_args:
        await message.reply('Для создания рекламной компании введи команду /advert и имя рассылки')
        return
    
    await message.answer(
        f"Приступаем к созданию рассылки. Имя рекламной компании - {cmd_args}\n" +
        "Теперь отправь само рекламное собщение."
    )
    await state.update_data(ad_name=cmd_args)
    await AdminState.wait_msg.set()


@dp.message_handler(state=AdminState.wait_msg)
async def get_message(message: types.Message, state: FSMContext):
    await message.answer(
        'Хорошо, я запомнил сообщение, которое ты хочешь разослать.\n' + 
        'Хочешь добавить кнопку со ссылкой на рекламируемый ресурс?',
        reply_markup=keyboard_builder
    )
    await state.update_data(message_id=message.message_id, chat_id=message.from_user.id)
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
        "Вот сообщение, которое будет отправлено. Проверь.",
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
    ad_name = data.get('ad_name')

    if call.data == 'confirm':
        await call.message.edit_text('Начинаю рассылку', reply_markup=None)

        if not await db.check_table(ad_name):
            await db.create_table_ad_company(ad_name)

        await call.message.answer(f"Успешно разослали рекламное сообщение!")
        await db.delete_ad_copmany(ad_name)

    elif call.data == 'deny':
        await call.message.edit_text('Отменяю рассылку', reply_markup=None)

    await state.finish()
