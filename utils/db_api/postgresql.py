from typing import Union

import asyncpg
from asyncpg import Connection
from asyncpg.pool import Pool

from data import config


class Database:
    def __init__(self):
        self.pool: Union[Pool, None] = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            user=config.DB_USER,
            password=config.DB_PASS,
            host=config.DB_HOST,
            database=config.DB_NAME,
        )

    async def execute(
        self,
        command,
        *args,
        fetch: bool = False,
        fetchval: bool = False,
        fetchrow: bool = False,
        execute: bool = False,
    ):
        async with self.pool.acquire() as connection:

            result = None

            connection: Connection
            async with connection.transaction():
                if fetch:
                    result = await connection.fetch(command, *args)
                elif fetchval:
                    result = await connection.fetchval(command, *args)
                elif fetchrow:
                    result = await connection.fetchrow(command, *args)
                elif execute:
                    result = await connection.execute(command, *args)
            return result

    async def create_table_users(self):
        sql = """
        CREATE TABLE IF NOT EXISTS Users (
        id SERIAL PRIMARY KEY,
        full_name VARCHAR(255) NOT NULL,
        username varchar(255) NULL,
        telegram_id BIGINT NOT NULL UNIQUE
        );
        """
        await self.execute(sql, execute=True)

    @staticmethod
    def format_args(sql, parameters: dict):
        sql += " AND ".join(
            [f"{item} = ${num}" for num, item in enumerate(parameters.keys(), start=1)]
        )
        return sql, tuple(parameters.values())

    """
    Base
    """

    async def add_user(self, full_name, username, telegram_id):
        sql = "INSERT INTO Users (full_name, username, telegram_id) VALUES($1, $2, $3) returning *"
        return await self.execute(sql, full_name, username, telegram_id, fetchrow=True)

    async def select_all_users(self):
        sql = "SELECT * FROM Users"
        return await self.execute(sql, fetch=True)

    async def select_user(self, **kwargs):
        sql = "SELECT * FROM Users WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    async def count_users(self):
        sql = "SELECT COUNT(*) FROM Users"
        return await self.execute(sql, fetchval=True)

    async def update_user_username(self, username, telegram_id):
        sql = "UPDATE Users SET username=$1 WHERE telegram_id=$2"
        return await self.execute(sql, username, telegram_id, execute=True)

    async def delete_users(self):
        await self.execute("DELETE FROM Users WHERE TRUE", execute=True)

    async def drop_users(self):
        await self.execute("DROP TABLE Users", execute=True)

    """
    Advert
    """

    async def check_table(self, table_name):
        sql = f"SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = '{table_name}');"
        return await self.execute(sql, fetchval=True)
    
    async def create_table_ad_company(self, table_name):
        sql = f"CREATE TABLE IF NOT EXISTS {table_name} (telegram_id bigint NOT NULL, status text, description text, PRIMARY KEY (telegram_id));"
        await self.execute(sql)
        
        sql = f"INSERT INTO {table_name} (telegram_id, status, description) SELECT telegram_id, 'waiting', null FROM Users;"
        await self.execute(sql)

    async def delete_ad_copmany(self, table_name):
        sql = f"DROP TABLE {table_name};"
        await self.execute(sql)

    """
    Broadcasting
    """

    async def list_broadcasting_users(self, ad_name):
        sql = f"SELECT telegram_id FROM {ad_name} WHERE status = 'waiting'"
        self.execute(sql, fetch=True)

    async def update_status(self, ad_name, telegram_id, status, description):
        sql = f"UPDATE {ad_name}, SET status='status', description='{description}' WHERE telegram_id={telegram_id}"
        
