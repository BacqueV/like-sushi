from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from loader import db, bot
from asyncpg import Record
from typing import List
from aiogram.utils.exceptions import RetryAfter
import asyncio

class Broadcast:
    async def create_keyboard(self, btn_txt, btn_url):
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


    async def get_userlist(self, ad_name):
        results_query = List[Record] = await db.list_broadcasting_users(ad_name)
        return [result.get('telegram_id') for result in results_query]


    async def send_message(
            self, telegram_id: int, from_chat_id: int, message_id: int,
            ad_name: str, keyboard: InlineKeyboardMarkup = None
        ):
        try:
            await bot.copy_message(telegram_id, from_chat_id, message_id, reply_markup=keyboard)
        except RetryAfter as e:
            await asyncio.sleep(e.timeout)
            return await self.send_message(
                telegram_id, from_chat_id, message_id, ad_name, keyboard
            )
        except Exception as e:
            await db.update_status(ad_name, telegram_id, 'unsuccessful', f'{e}')
        else:
            await db.update_status(ad_name, telegram_id, 'successful', "No errors")
            return True
        
        return False


    async def broadcaster(
        self, ad_name, from_chat_id: int, message: int,
        btn_txt: str = None, btn_url: str = None
    ):
        keyboard = None

        if btn_txt and btn_url:
            keyboard = await self.create_keyboard(btn_txt, btn_url)

        userlist = await self.get_userlist(ad_name)
        count = 0
        try:
            for telegram_d in userlist:
                pass
        finally:
            pass
