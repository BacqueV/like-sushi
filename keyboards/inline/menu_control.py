from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

"""
Main menu
"""

#  mainmenu buttons
list_categories = InlineKeyboardButton(text='Список категорий', callback_data='list_categories')

add_category = InlineKeyboardButton(text='Добавить категорию', callback_data='add_category')
delete_category = InlineKeyboardButton(text='Удалить категорию', callback_data='delete_category')

manage_category = InlineKeyboardButton(text='Править категорию', callback_data='manage_category')

add_meal = InlineKeyboardButton(text='Добавить Блюдо', callback_data='add_meal')
delete_meal = InlineKeyboardButton(text='Удалить блюдо', callback_data='delete_meal')

manage_meal = InlineKeyboardButton(text='Править блюдо', callback_data='manage_meal')

quit_menu = InlineKeyboardButton(text='Покинуть меню', callback_data='quit')

#  main_menu keyboard
main_menu = InlineKeyboardMarkup()
main_menu.row(list_categories)
main_menu.add(add_category, delete_category)
main_menu.row(manage_category)
main_menu.add(add_meal, delete_meal)
main_menu.row(manage_meal)
main_menu.row(quit_menu)

"""
Confirmation
"""

accept = InlineKeyboardButton(text='Подтвердить', callback_data='accept')
deny = InlineKeyboardButton(text='Отменить', callback_data='deny')

confirmation = InlineKeyboardMarkup().row(accept, deny)

"""
Continue or save
"""

btn_continue = InlineKeyboardButton(text='Сохранить и продолжить', callback_data='continue')
btn_save = InlineKeyboardButton(text='Сохранить и выйти', callback_data='save')
continue_or_save = InlineKeyboardMarkup(row_width=1).add(btn_continue, btn_save)

"""
Quit Anything
"""

just_deny = InlineKeyboardButton(text='Отменить', callback_data='quit_anything')
quit_anything = InlineKeyboardMarkup().row(just_deny)

"""
Skip
"""

skip = InlineKeyboardButton(text='Пропустить', callback_data='skip')
skip_kb = InlineKeyboardMarkup().row(skip)

"""
Image managing
"""

button_delete_image = InlineKeyboardButton(text='Удалить', callback_data='delete')
image_control = InlineKeyboardMarkup(row_width=1).add(button_delete_image, just_deny)
