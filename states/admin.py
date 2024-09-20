from aiogram.dispatcher.filters.state import State, StatesGroup


class AdminState(StatesGroup):
    wait_msg = State()
    check_ad = State()
