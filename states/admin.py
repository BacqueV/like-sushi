from aiogram.dispatcher.filters.state import State, StatesGroup


class BroadcastingState(StatesGroup):
    wait_msg = State()
    build_kb = State()
    get_btn_txt = State()
    get_btn_url = State()
    confirmation = State()


class AdminPanelState(StatesGroup):
    mainmenu = State()
