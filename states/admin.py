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

    # await ID
    await_id_delete = State()
    await_id_delete_meal = State()
    await_id_manage = State()
    await_id_manage_meal = State()
    await_id_meal = State()

    # await NAME
    await_name_category = State()
    await_name_meal = State()

    # await description
    await_description_category = State()
    await_description_meal = State()

    # await DATA for MEAL
    await_price = State()
    await_sale_price = State()  
    await_category = State()

    # confirmation
    confirmation_add_category = State()
    confirmation_add_meal = State()

    confirmation_delete_category = State()
    confirmation_delete_meal = State()

    # EDIT category
    manage_menu = State()
    manage_menu_meal = State()
    edit_category = State()
    edit_meal = State()
    confirm_category = State()
    confirm_meal = State()


class ManageLocationState(StatesGroup):
    await_location = State()
