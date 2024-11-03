from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# creating buttons
btn_order = KeyboardButton('🛍 Заказать')
btn_review = KeyboardButton('✍️ Оставить отзыв')
btn_promotions = KeyboardButton('🎉 Акции')
btn_all_branches = KeyboardButton('🏘 Филиалы')
btn_settings = KeyboardButton('⚙️ Настройки')
btn_my_orders = KeyboardButton('📋 Мои заказы')
btn_about_us = KeyboardButton('ℹ️ О нас')

# creating keyboard
kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
kb.row(btn_order)
kb.add(btn_promotions, btn_all_branches)
kb.add(btn_settings, btn_my_orders)
kb.row(btn_about_us)
