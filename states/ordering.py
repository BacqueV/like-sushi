from aiogram.dispatcher.filters.state import State, StatesGroup


class OrderingState(StatesGroup):
    basket = State()

    choose_category = State()
    choose_meal = State()

    meal_menu = State()
    basket = State()

    pre_check = State()
    order = State()

class OrderProcessingState(StatesGroup):
    processing = State()
