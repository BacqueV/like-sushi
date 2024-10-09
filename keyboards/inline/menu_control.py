from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


"""
Main menu
"""

# mainmenu buttons
list_categories = InlineKeyboardButton(text='Список категорий', callback_data='list_categories')

add_category = InlineKeyboardButton(text='Добавить категорию', callback_data='add_category')
delete_category = InlineKeyboardButton(text='Удалить категорию', callback_data='delete_category')

find_category = InlineKeyboardButton(text='Найти категорию', callback_data='find_category')

add_meal = InlineKeyboardButton(text='Добавить Блюдо', callback_data='add_meal')
delete_meal = InlineKeyboardButton(text='Удалить блюдо', callback_data='delete_meal')

find_meal = InlineKeyboardButton(text='Найти блюдо', callback_data='find_meal')

quit_menu = InlineKeyboardButton(text='Покинуть меню', callback_data='quit')

# mainmenu keyboard
main_menu = InlineKeyboardMarkup()
main_menu.row(list_categories)
main_menu.add(add_category, delete_category)
main_menu.row(find_category)
main_menu.add(add_meal, delete_meal)
main_menu.row(find_meal)
main_menu.row(quit_menu)

"""
Confirmation
"""

accept = InlineKeyboardButton(text='Подтвердить', callback_data='accept')
deny = InlineKeyboardButton(text='Отменить', callback_data='deny')

confirmation = InlineKeyboardMarkup()
confirmation.row(accept, deny)

"""
Quit deleting
"""

just_deny = InlineKeyboardButton(text='Отменить', callback_data='quit_anything')

quit_anything = InlineKeyboardMarkup()
quit_anything.row(just_deny)
