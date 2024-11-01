from aiogram import types
from loader import dp, db, bot
from aiogram.dispatcher import FSMContext
from keyboards.default import userdata, main_menu
from keyboards.inline import ordering
from states.ordering import OrderingState
import aiohttp
import asyncio
from datetime import datetime


async def get_address_from_coordinates(latitude, longitude, fsm: FSMContext):
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={latitude}&lon={longitude}&accept-language=ru"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                address_data = data.get("address", {})
                
                # Форматируем адрес вручную
                country = address_data.get("country", "")
                state = address_data.get("state", "")
                city = address_data.get("city", address_data.get("town", address_data.get("village", "")))
                street = address_data.get("road", "")
                house_number = address_data.get("house_number", "")

                # Сохраняем данные в машину состояний
                await fsm.update_data(latitude=latitude)
                await fsm.update_data(longitude=longitude)

                # Убираем пустые значения и составляем адрес в нужном формате
                address_parts = [country, state, city, street]
                if house_number:
                    address_parts.append(house_number)
                
                # Соединяем адресные части
                formatted_address = ", ".join(part for part in address_parts if part)
                await fsm.update_data(address=formatted_address)
                return formatted_address
            return None


async def pre_check(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    telegram_id = data.get('telegram_id')
    address = data.get('address')
    phone = data.get('phone')

    basket = await db.order_meals(telegram_id)

    event_time = datetime.now().replace(second=0, microsecond=0)
    response = f"<b>Проверьте заказ</b>:\n\n<b>Дата:</b> {event_time}\n<b>Доставка:</b> 20000\n"
    total_cost = 0

    for record in basket:
        meal = await db.select_meal(meal_id=record['meal_id'])
        name = meal[2]
        
        total_cost += record['total_cost_sum']
        
        response += f"<b>{name}</b> x {record['amount_sum']} = {record['total_cost_sum']}" + \
        (f"\n{record['info']}\n" if record['info'] else '\n')
    
    await state.update_data(total_cost=total_cost)
    await OrderingState.order.set()

    response += f'\n<b>Адрес доставки: </b>{address}\n<b>Номер телефона:</b> {phone}\n\n<b>Итого:</b> {int(total_cost) + 20000}'

    await state.update_data(info=response[25:])
    await message.answer(response, reply_markup=ordering.order_kb)


# START
@dp.callback_query_handler(text='pre_check', state=OrderingState.basket)
async def check_order_info(call: types.CallbackQuery, state: FSMContext):
    await OrderingState.pre_check.set()

    telegram_id = call.from_user.id
    phone = await db.check_number(telegram_id)

    await state.update_data(telegram_id=telegram_id)


    await call.message.edit_text('<i>Проверяем данные для доставки...</i>', reply_markup=None)
    
    if phone:
        await state.update_data(phone=phone)
        locations = await db.check_locations(telegram_id)

        if locations == 0:
            await call.message.answer(
                "<b>Отправьте ваш адрес или напишите в виде текста</b>",
                reply_markup=userdata.send_location_kb
            )
        else:
            locations_kb = await userdata.list_locations(telegram_id)
            await call.message.answer(
                "<b>Отправьте ваш адрес или напишите в виде текста</b>",
                reply_markup=locations_kb
            )
    else:
        await call.message.answer("Нам нужно знать, как с вами связаться!", reply_markup=userdata.phone_keyboard)


@dp.message_handler(content_types=types.ContentType.CONTACT, state=OrderingState.pre_check)
async def handle_phone_number(message: types.Message, state: FSMContext):
    phone_number = message.contact.phone_number
    telegram_id = message.from_user.id

    # Сохранение номер телефона в базе данных и машине состояний
    await db.save_phone_number(telegram_id, phone_number, message.from_user.full_name)
    await state.update_data(phone_number=phone_number)

    await state.update_data(phone=phone_number)
    await message.answer("<i>Ваш номер телефона сохранен</i>", reply_markup=types.ReplyKeyboardRemove())

    locations = await db.check_locations(telegram_id)
    if locations == 0:
        await message.answer(
            "<b>Отправьте ваш адрес или напишите в виде текста</b>",
            reply_markup=userdata.send_location_kb
        )
    else:
        locations_kb = await userdata.list_locations(telegram_id)
        await message.answer(
            "<b>Отправьте ваш адрес или напишите в виде текста</b>",
            reply_markup=locations_kb
        )


@dp.message_handler(content_types=types.ContentType.LOCATION, state=OrderingState.pre_check)
async def find_location(message: types.Message, state: FSMContext):
    latitude = message.location.latitude
    longitude = message.location.longitude
    
    # Получение адреса по координатам
    address = await get_address_from_coordinates(latitude, longitude, state)
    
    if address:
        await message.answer(
            f"Ваш адрес:\n" + \
            f"📍 <b>{address}</b>\n" + \
            "Проверьте адрес!",
            reply_markup=userdata.manage_location_kb
        )
    else:
        await state.update_data(address='Менеджер уточнит')
        await message.answer(
            "Не удалось определить адрес.\n" + \
            "С вами свяжется наш менеджер и запишет адрес сам"
        )
        await pre_check(message, state)


@dp.message_handler(text='⬅️ Назад', state=OrderingState.pre_check)
async def quit_location_managment(message: types.Message):
    data = await db.order_meals(message.from_user.id)

    response = "<b>Корзина</b>\n\n"
    for row in data:
        meal = await db.select_meal(meal_id=row['meal_id'])
        name = meal[2]

        response += f"<b>ID:</b> {row['meal_id']}\n" + \
        f"<b>Имя:</b> {name}\n" + \
        f"<b>Количество:</b> {row['amount_sum']}\n" + \
        f"<b>Цена блюда за штуку:</b> {row['real_price']}\n" + \
        f"<b>Общая стоимость:</b> {row['total_cost_sum']} {row['info']}\n\n"

    await OrderingState.basket.set()
    await message.reply("Возвращаемся к корзине", reply_markup=types.ReplyKeyboardRemove())
    await message.answer(response, reply_markup=ordering.basket_kb)


@dp.message_handler(text='Сохранить', state=OrderingState.pre_check)
async def save_location(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    address = data.get('address')

    # Сохранение геолокации в базе данных
    await db.save_location(message.from_user.id, address, latitude, longitude)

    await pre_check(message, state)


@dp.message_handler(text='✅ Подтвердить', state=OrderingState.pre_check)
async def confirm_location(message: types.Message, state: FSMContext):
    await message.answer(
        "<b>Последний шаг.</b>"
        "\nОтправить заказ менеджеру?", reply_markup=types.ReplyKeyboardRemove()
    )    
    await pre_check(message, state)


@dp.message_handler(state=OrderingState.pre_check)
async def location_as_text(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    await message.answer(
        "<b>Последний шаг.</b>"
        "\nОтправить заказ менеджеру?", reply_markup=types.ReplyKeyboardRemove()
    )    
    await pre_check(message, state)


@dp.callback_query_handler(text='accept', state=OrderingState.order)
async def order(call: types.CallbackQuery, state: FSMContext):

    data = await state.get_data()
    info = data.get('info')
    total_cost = data.get('total_cost')
    telegram_id = data.get('telegram_id')
    
    order = await db.create_order(info, (total_cost + 20000), telegram_id)
    await state.update_data(order_id=order[0])
    await db.clean_basket(telegram_id)

    managers = await db.manager_id_list()

    if managers:
        await call.message.edit_text(
            "<b>Заказ принят, ожидайте звонка нашего менеджера для подтверждения!</b>",
            reply_markup=None
        )
        await asyncio.sleep(1)
        await call.message.answer(
            "Благодарим за ожидание ❤️",
            reply_markup=main_menu.kb
        )

        process_order_kb = await ordering.enter_order_processing(order[0])

        try:
            for manager in managers:
                await bot.send_message(
                    chat_id=manager['telegram_id'],
                    text="🤑 <b>Поступил новый заказ!</b>",
                    reply_markup=process_order_kb
                )
                await asyncio.sleep(.05)
        except Exception:
            pass
    else:
        admins = await db.admin_id_list()
        try:
            for admin in admins:
                await bot.send_message(
                    chat_id=admin['telegram_id'],
                    text="<b>В системе нет менеджеров. Клиенты не могут оформить заказ!</b>"
                )
                await asyncio.sleep(.05)
        except Exception:
            pass

    await state.finish()
