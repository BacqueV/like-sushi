from aiogram.dispatcher.filters.state import State, StatesGroup


class BroadcastingState(StatesGroup):
    wait_msg = State()
    build_kb = State()
    get_btn_txt = State()
    get_btn_url = State()
    confirmation = State()


class AdminPanelState(StatesGroup):
    mainmenu = State()


class MControlState(StatesGroup):
    main_menu = State()
    await_name = State()
    await_description = State()
    await_price = State()
    await_sale_price = State()
    await_category = State()
    confirmation = State()
