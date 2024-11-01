from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from loader import db

# send location
send_location_kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
btn_location = KeyboardButton("Отправить местоположение", request_location=True)
btn_quit_location = KeyboardButton("⬅️ Назад")
send_location_kb.add(btn_location, btn_quit_location)

# handle location
btn_resend = KeyboardButton(text='Отправить снова', request_location=True)
btn_accept = KeyboardButton(text='✅ Подтвердить')
btn_save_location = KeyboardButton(text='Сохранить')
btn_quit = KeyboardButton(text='⬅️ Назад')

manage_location_kb = ReplyKeyboardMarkup(
    resize_keyboard=True,
    row_width=2,
    one_time_keyboard=True
).add(
    btn_accept, btn_quit, btn_save_location, btn_resend
)

# handle phone number
phone_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
phone_button = KeyboardButton("Отправить номер телефона", request_contact=True)
btn_quit_phone = KeyboardButton("⬅️ Назад")
phone_keyboard.add(phone_button, btn_quit_phone)

# location buttons
async def list_locations(telegram_id):
    locations = await db.list_locations(telegram_id)

    btn_send_location = KeyboardButton(text='Отправить локацию', request_location=True)
    locations_kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True).add(btn_send_location)
    
    for location in locations:
        new_location = KeyboardButton(text=location['address'])
        locations_kb.insert(new_location)

    btn_quit = KeyboardButton(text='⬅️ Назад')
    locations_kb.insert(btn_quit)

    return locations_kb
