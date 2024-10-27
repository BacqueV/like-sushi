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

#  confirmation buttons
accept = InlineKeyboardButton(text='Подтвердить', callback_data='accept')
deny = InlineKeyboardButton(text='Отменить', callback_data='deny')

#  confirmation keyboard
confirmation = InlineKeyboardMarkup()
confirmation.row(accept, deny)

"""
Continue or save
"""

#  continue or save buttons
btn_continue = InlineKeyboardButton(text='Продолжить', callback_data='continue')
btn_save = InlineKeyboardButton(text='Сохранить', callback_data='save')

#  continue or save keyboard
continue_or_save = InlineKeyboardMarkup()
continue_or_save.row(btn_continue, btn_save)

"""
Quit Anything
"""

#  quit anything buttons
just_deny = InlineKeyboardButton(text='Отменить', callback_data='quit_anything')

#  quit anything keyboard
quit_anything = InlineKeyboardMarkup()
quit_anything.row(just_deny)
