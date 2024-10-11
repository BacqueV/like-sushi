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
  
    await_id_delete = State()
    await_id_manage = State()

    await_name = State()
    await_description = State()
  
    await_price = State()
    await_sale_price = State()
  
    await_category = State()
  
    confirmation_add = State()
    confirmation_delete = State()

    manage_menu = State()
    edit_category = State()
    confirm_category = State()
