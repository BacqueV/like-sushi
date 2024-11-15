from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


"""
Main Menu
"""

btn_order = KeyboardButton('🛍 Заказать')
btn_review = KeyboardButton('✍️ Оставить отзыв')
btn_promotions = KeyboardButton('🎉 Акции')
btn_all_branches = KeyboardButton('🏘 Филиалы')
btn_settings = KeyboardButton('⚙️ Настройки')
btn_my_orders = KeyboardButton('📋 Мои заказы')
btn_about_us = KeyboardButton('ℹ️ О нас')

kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
kb.row(btn_order)
kb.add(btn_promotions, btn_all_branches)
kb.add(btn_settings, btn_my_orders)
kb.row(btn_about_us)

"""
Settings
"""

btn_send_number = KeyboardButton('📞 Номер телефона', request_contact=True)
btn_quit = KeyboardButton("⬅️ Назад")

settings_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
settings_kb.row(btn_send_number)
settings_kb.row(btn_quit)
