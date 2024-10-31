from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


async def list_categories(categories: list) -> InlineKeyboardMarkup:
    categories_kb = InlineKeyboardMarkup(row_width=2)

    for category in categories:
        categories_kb.insert(
            InlineKeyboardButton(
                text=category[1],
                callback_data=category[0]
            )
        )

    btn_basket = InlineKeyboardButton(text='Корзина 🧺', callback_data='open_basket')
    categories_kb.row(btn_basket)
    categories_kb.add(
        InlineKeyboardButton(
            text='Покинуть меню ⬅️',
            callback_data='quit'
        )
    )
    return categories_kb


async def list_meals(meals: list) -> InlineKeyboardMarkup:
    meals_kb = InlineKeyboardMarkup(row_width=2)

    for meal in meals:
        meals_kb.insert(
            InlineKeyboardButton(
                text=meal[2],
                callback_data=meal[0]
            )
        )

    btn_basket = InlineKeyboardButton(text='Корзина 🧺', callback_data='open_basket')
    meals_kb.row(btn_basket)
    meals_kb.add(
        InlineKeyboardButton(
            text='Назад ⬅️',
            callback_data='quit'
        )
    )
    return meals_kb


async def meal_menu_markup(amount: int) -> InlineKeyboardMarkup:
    btn_decrease = InlineKeyboardButton(text='➖', callback_data='decrease')
    btn_amount = InlineKeyboardButton(text=f'{amount}', callback_data=f'{amount}')
    btn_increase = InlineKeyboardButton(text='➕', callback_data='increase')

    btn_basket = InlineKeyboardButton(text='Добавить в корзину 🧺', callback_data='basket')
    btn_back = InlineKeyboardButton(text='Назад ⬅️', callback_data='quit')

    meal_menu_kb = InlineKeyboardMarkup()
    meal_menu_kb.add(btn_decrease, btn_amount, btn_increase)
    meal_menu_kb.row(btn_basket)
    meal_menu_kb.row(btn_back)

    return meal_menu_kb


# basket buttons
btn_order = InlineKeyboardButton(text='Заказать ⚡️', callback_data='pre_check')
btn_empty = InlineKeyboardButton(text='Очистить корзину 🧹', callback_data='empty')
btn_quit_meal_deal = InlineKeyboardButton(text='Назад ⬅️', callback_data='quit')

basket_kb = InlineKeyboardMarkup().row(btn_order)
basket_kb.add(btn_quit_meal_deal, btn_empty)

# order check buttons
btn_accept = InlineKeyboardButton(text='Подтвердить ✅', callback_data='accept')
btn_deny = InlineKeyboardButton(text='Отменить ❌', callback_data='back')

order_kb = InlineKeyboardMarkup(row_width=2).add(btn_accept, btn_deny)