from aiogram.dispatcher.filters.state import State, StatesGroup


class UserOrders(StatesGroup):
    list = State()
    certain_order = State()
