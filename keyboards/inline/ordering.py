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

    categories_kb.add(
        InlineKeyboardButton(
            text='Покинуть меню',
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

    meals_kb.add(
        InlineKeyboardButton(
            text='Покинуть меню',
            callback_data='quit'
        )
    )
    return meals_kb
