from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# creating buttons
btn_order = KeyboardButton('🛍 Заказать')
btn_review = KeyboardButton('✍️ Оставить отзыв')
btn_nearest_branch = KeyboardButton('🏠 Ближайший филиал')
btn_promotions = KeyboardButton('🎉 Акция')
btn_all_branches = KeyboardButton('🏘 Филиалы')
btn_settings = KeyboardButton('⚙️ Настройки')
btn_my_orders = KeyboardButton('📋 Мои заказы')
btn_about_us = KeyboardButton('ℹ️ О нас')

# creating keyboard
main_menu_kb = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu_kb.row(btn_order)
main_menu_kb.add(btn_review, btn_nearest_branch)
main_menu_kb.add(btn_promotions, btn_all_branches)
main_menu_kb.add(btn_settings, btn_my_orders)
main_menu_kb.row(btn_about_us)
