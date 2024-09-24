from environs import Env
from asyncpg import Record
from typing import List
import asyncpg
import asyncio

env = Env()
env.read_env()

ADMINS = []
BOT_TOKEN = env.str("BOT_TOKEN")

DB_USER = env.str("DB_USER")
DB_PASS = env.str("DB_PASS")
DB_NAME = env.str("DB_NAME")
DB_HOST = env.str("DB_HOST")


async def get_adminlist():
    connection = await asyncpg.create_pool(
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST,
        database=DB_NAME,
    )
    sql = f"SELECT * FROM users WHERE is_admin = true;"
    
    results_query: List[Record] = await connection.fetch(sql)
    await connection.close()

    global ADMINS
    ADMINS = [result.get('telegram_id') for result in results_query]
    
    return [result.get('telegram_id') for result in results_query]


ADMINS = asyncio.run(get_adminlist())


async def refresh_adminlist(interval):
    while True:
        await get_adminlist()
        await asyncio.sleep(interval)


loop = asyncio.get_event_loop()
loop.create_task(refresh_adminlist(60))
