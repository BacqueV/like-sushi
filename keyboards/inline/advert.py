from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

add_btn = InlineKeyboardButton(text='Добавить кнопку', callback_data='add_btn')
no_btn = InlineKeyboardButton(text='Продолжить без кнопки', callback_data='no_btn')

keyboard_builder = InlineKeyboardMarkup().insert(add_btn).insert(no_btn)
