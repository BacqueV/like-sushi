from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from asyncpg import Record
from typing import List
from aiogram.utils.exceptions import RetryAfter
import asyncio
import asyncpg
from data import config


async def create_keyboard(btn_txt, btn_url):
    advertising_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=btn_txt,
                    url=btn_url
                )
            ]
        ]
    )
    return advertising_kb


async def get_userlist(ad_name):
    connection = await asyncpg.create_pool(
        user=config.DB_USER,
        password=config.DB_PASS,
        host=config.DB_HOST,
        database=config.DB_NAME,
    )

    sql = f"SELECT telegram_id FROM {ad_name} WHERE status = 'waiting'"
    results_query = List[Record] = await connection.fetch(sql)
    return [result.get('telegram_id') for result in results_query]


async def update_status(ad_name, telegram_id, status, description):
    connection = await asyncpg.create_pool(
        user=config.DB_USER,
        password=config.DB_PASS,
        host=config.DB_HOST,
        database=config.DB_NAME,
    )

    sql = f"UPDATE {ad_name}, SET status='{status}', description='{description}' WHERE telegram_id={telegram_id}"
    await connection.execute(sql)


async def send_message(
        bot,
        telegram_id: int, from_chat_id: int, message_id: int,
        ad_name: str, keyboard: InlineKeyboardMarkup = None
    ):
    try:
        await bot.copy_message(telegram_id, from_chat_id, message_id, reply_markup=keyboard)
    except RetryAfter as e:
        await asyncio.sleep(e.timeout)
        return await send_message(
            telegram_id, from_chat_id, message_id, ad_name, keyboard
        )
    except Exception as e:
        await update_status(ad_name, telegram_id, 'unsuccessful', f'{e}')
    else:
        await update_status(ad_name, telegram_id, 'successful', "No errors")
        return True
    
    return False


async def broadcaster(
    bot,
    ad_name, from_chat_id: int, message_id: int,
    btn_txt: str = None, btn_url: str = None
):
    keyboard = None

    if btn_txt and btn_url:
        keyboard = await create_keyboard(btn_txt, btn_url)

    userlist = await get_userlist(ad_name)
    count = 0
    try:
        for telegram_id in userlist:
            if await send_message(bot, int(telegram_id), from_chat_id, message_id, ad_name, keyboard):
                count += 1
            await asyncio.sleep(.05)
    finally:
        print(f"Разослали сообщение {count} пользователям")

    return count
