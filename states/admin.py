from aiogram.dispatcher.filters.state import State, StatesGroup


class AdminState(StatesGroup):
    wait_msg = State()
    build_kb = State()
    get_btn_txt = State()
    get_btn_url = State()
    confirmation = State()
