from aiogram import executor

from loader import dp, db
from utils.set_bot_commands import set_default_commands

# don't delete this unused imports, without them nothing will work
import middlewares, filters, handlers


async def start(dispatcher):
    await db.connect()
    await db.create_table_users()
    await db.create_table_broadcasting()
    await db.create_passwd_table()
    await db.create_table_categories()
    await db.create_table_meals()
    await db.create_table_basket()
    await db.create_table_locations()
    await db.create_table_orders()

    await set_default_commands(dispatcher)


if __name__ == '__main__':
    executor.start_polling(dp, on_startup=start)
