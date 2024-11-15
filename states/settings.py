from aiogram.dispatcher.filters.state import State, StatesGroup


class SettingsState(StatesGroup):
    menu = State()
