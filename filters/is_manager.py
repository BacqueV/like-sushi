from aiogram import types
from aiogram.dispatcher.filters import Filter
from aiogram.utils.exceptions import Unauthorized
from aiogram.dispatcher.handler import CancelHandler
import asyncpg
from data import config


class IsManagerFilter(Filter):
    key = 'is_manager'
    
    def __init__(self, is_manager: bool):
        self.is_manager = is_manager

    async def check(self, message: types.Message) -> bool:
        conn = await asyncpg.connect(
            user=config.DB_USER, 
            password=config.DB_PASS,
            database=config.DB_NAME,
            host=config.DB_HOST
        )
        
        try:
            result = await conn.fetchval(
                'SELECT is_manager FROM users WHERE telegram_id = $1',
                message.from_user.id
            )
            return result == self.is_manager
        except Unauthorized:
            raise CancelHandler()
        finally:
            await conn.close()
