from aiogram.fsm.state import StatesGroup, State


class MainGroup(StatesGroup):
    common = State()
    main_menu = State()
    choosing_companion = State()