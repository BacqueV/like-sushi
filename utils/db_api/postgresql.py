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
        CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        full_name VARCHAR(255) NOT NULL,
        username VARCHAR(255) NULL,
        telegram_id BIGINT NOT NULL UNIQUE,
        is_admin BOOLEAN DEFAULT FALSE NOT NULL
        );
        """
        await self.execute(sql, execute=True)

    # then create table with phone number and saved locations for every user + language settings

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
        sql = "INSERT INTO users (full_name, username, telegram_id) VALUES($1, $2, $3) returning *"
        return await self.execute(sql, full_name, username, telegram_id, fetchrow=True)

    async def select_all_users(self):
        sql = "SELECT * FROM users"
        return await self.execute(sql, fetch=True)

    async def select_user(self, **kwargs):
        sql = "SELECT * FROM users WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    async def count_users(self):
        sql = "SELECT COUNT(*) FROM users"
        return await self.execute(sql, fetchval=True)

    async def update_user_username(self, username, telegram_id):
        sql = "UPDATE users SET username=$1 WHERE telegram_id=$2"
        return await self.execute(sql, username, telegram_id, execute=True)

    async def delete_users(self):
        await self.execute("DELETE FROM users WHERE TRUE", execute=True)

    async def drop_users(self):
        await self.execute("DROP TABLE users", execute=True)

    """
    Broadcasting
    """

    async def create_table_broadcasting(self):
        sql = "CREATE TABLE IF NOT EXISTS broadcasting (telegram_id bigint NOT NULL, status text, description text, PRIMARY KEY (telegram_id));"
        await self.execute(sql)
        
    async def fill_broadcasting_table(self):
        sql = "INSERT INTO broadcasting (telegram_id, status, description) SELECT telegram_id, 'waiting', null FROM users;"
        await self.execute(sql, execute=True)

    async def clean_broadcasting_table(self):
        await self.execute("DELETE FROM broadcasting WHERE TRUE;", execute=True)


    """
    Admin Panel
    """

    async def create_passwd_table(self):
        await self.execute("CREATE TABLE IF NOT EXISTS admin_passwd (passwd text);", execute=True)

    async def force_delete_passwd(self):
        await self.execute("DELETE FROM admin_passwd WHERE TRUE", execute=True)

    async def change_passwd(self, new_passwd):
        await self.force_delete_passwd()
        sql = f"INSERT INTO admin_passwd (passwd) VALUES($1)"
        return await self.execute(sql, new_passwd, execute=True, fetchrow=True)

    async def get_passwd(self):
        passwd = await self.execute("SELECT * from admin_passwd WHERE TRUE;", fetchval=True)
        return passwd

    async def check_passwd(self, passwd):
        real_passwd = await self.get_passwd()
        return True if passwd == real_passwd else False

    async def make_him_admin(self, telegram_id):
        sql = "UPDATE users SET is_admin = true WHERE telegram_id=$1;"
        return await self.execute(sql, telegram_id, execute=True)

    async def remove_admin(self, telegram_id):
        sql = "UPDATE users SET is_admin = false WHERE telegram_id=$1;"
        return await self.execute(sql, telegram_id, execute=True)
    
    async def make_him_admin_magically(self, telegram_id, passwd):
        if passwd == await self.get_passwd():
            await self.make_him_admin(telegram_id)
            return 1
        return 0

    async def admin_list(self):
        sql = "SELECT * FROM users WHERE is_admin = TRUE;"
        return await self.execute(sql, fetch=True)

    """
    Control meal categories
    """

    async def create_table_categories(self):
        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
            category_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT
            );
            """, execute=True)

    async def add_category(self, name, description):
        sql = "INSERT INTO categories (name, description) VALUES($1, $2) returning *"
        return await self.execute(sql, name, description, fetchrow=True)

    async def delete_category(self, category_id):
        return await self.execute("DELETE FROM categories WHERE category_id = $1", category_id, execute=True)

    async def list_categories(self):
        sql = "SELECT * FROM categories"
        return await self.execute(sql, fetch=True)

    async def select_category(self, **kwargs):
        sql = "SELECT * FROM categories WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)
    
    async def update_category_data(self, name, description, category_id):
        sql = "UPDATE categories SET name=$1, description=$2 WHERE category_id=$3"
        return await self.execute(sql, name, description, category_id, execute=True)

    async def create_table_meals(self):
        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS meals (
            meal_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            category VARCHAR(100) NOT NULL,
            description TEXT NULL,
            price DECIMAL NOT NULL,
            sale BOOLEAN DEFAULT FALSE,
            sale_price DECIMAL NULL,
            included BOOLEAN DEFAULT TRUE
            );
            """, execute=True)

    async def add_meal(self, name, category, description, price):
        sql = "INSERT INTO categories (name, category, description, price) VALUES($1, $2, $3, $4) returning *"
        return await self.execute(sql, name, category, description, price, fetchrow=True)
    
    async def delete_meal(self, category_id):
        return await self.execute("DELETE FROM categories WHERE category_id = $1", category_id, execute=True)

    async def list_meals(self):
        sql = "SELECT * FROM meals"
        return await self.execute(sql, fetch=True)

    async def select_meal(self, **kwargs):
        sql = "SELECT * FROM meals WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)
    