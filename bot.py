from aiogram import executor

from loader import dp, db
import asyncpg
from data import config
from utils.notify_admins import on_startup_notify
from utils.set_bot_commands import set_default_commands

# don't delete this unused imports, without them nothing will work
import middlewares, filters, handlers


async def start(dispatcher):
    await db.connect()
    await db.create_table_users()
    await db.create_table_broadcasting()
    await set_default_commands(dispatcher)
    await on_startup_notify(dispatcher)


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=start)