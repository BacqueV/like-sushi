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

    @staticmethod
    def format_args(sql, parameters: dict):
        sql += " AND ".join(
            [f"{item} = ${num}" for num, item in enumerate(parameters.keys(), start=1)]
        )
        return sql, tuple(parameters.values())

    """
    Base
    """

    async def create_table_users(self):
        sql = """
        CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        full_name VARCHAR(255) NOT NULL,
        username VARCHAR(255) NULL,
        telegram_id BIGINT NOT NULL UNIQUE,
        is_admin BOOLEAN DEFAULT FALSE NOT NULL,
        is_manager BOOLEAN DEFAULT FALSE,
        language VARCHAR(50) DEFAULT 'ru',
        phone_number VARCHAR(50)
        );
        """
        await self.execute(sql, execute=True)

    async def check_number(self, telegram_id):
        sql = "SELECT phone_number FROM users WHERE telegram_id=$1"
        return await self.execute(sql, telegram_id, fetchval=True)

    async def save_phone_number(self, telegram_id, phone_number, full_name):
        sql = """
        INSERT INTO users (telegram_id, phone_number, full_name) 
        VALUES ($1, $2, $3) 
        ON CONFLICT (telegram_id) DO UPDATE SET phone_number = $2, full_name = COALESCE($3, users.full_name)
        """
        return await self.execute(sql, telegram_id, phone_number, full_name, execute=True)

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

    async def delete_user(self, telegram_id):
        await self.execute("DELETE FROM users WHERE telegram_id = $1", telegram_id, execute=True)

    async def drop_users(self):
        await self.execute("DROP TABLE users", execute=True)

    """
    Managers
    """
    
    async def manager_list(self):
        sql = "SELECT * FROM users WHERE is_manager = true;"
        return await self.execute(sql, fetch=True)

    async def manager_id_list(self):
        sql = "SELECT telegram_id FROM users WHERE is_manager = true;"
        return await self.execute(sql, fetchrow=True)

    async def add_manager(self, telegram_id):
        sql = "UPDATE users SET is_manager = true WHERE telegram_id = $1;"
        return await self.execute(sql, telegram_id, execute=True)

    async def remove_manager(self, telegram_id):
        sql = "UPDATE users SET is_manager = false WHERE telegram_id = $1;"
        return await self.execute(sql, telegram_id, execute=True)

    """
    Admins
    """
    async def admin_list(self):
        sql = "SELECT * FROM users WHERE is_admin = true;"
        return await self.execute(sql, fetch=True)

    async def admin_id_list(self):
        sql = "SELECT telegram_id FROM users WHERE is_admin = true;"
        return await self.execute(sql, fetchrow=True)

    async def remove_admin(self, telegram_id):
        sql = "UPDATE users SET is_admin = false WHERE telegram_id=$1;"
        return await self.execute(sql, telegram_id, execute=True)

    """
    Locations
    """

    async def create_table_locations (self):
        sql = """
        CREATE TABLE IF NOT EXISTS locations (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT NOT NULL,
        address TEXT,
        lattitude DOUBLE PRECISION,
        longitude DOUBLE PRECISION
        );
        """
        return await self.execute(sql, execute=True)
    
    async def list_locations(self, telegram_id):
        sql = "SELECT *  FROM locations WHERE telegram_id=$1"
        return await self.execute(sql, telegram_id, fetch=True)
    
    async def check_locations(self, telegram_id):
        sql = "SELECT COUNT(*) FROM locations WHERE telegram_id = $1"
        return await self.execute(sql, telegram_id, fetchval=True)
    
    async def save_location(self, telegram_id, address, lattitude, longitude):
        sql = "INSERT INTO locations (telegram_id, address, lattitude, longitude) VALUES($1, $2, $3, $4)"
        return await self.execute(sql, telegram_id, address, lattitude, longitude, execute=True)

    """
    Broadcasting
    """

    async def create_table_broadcasting(self):
        sql = "CREATE TABLE IF NOT EXISTS broadcasting (telegram_id bigint NOT NULL, status text, description text, PRIMARY KEY (telegram_id));"
        await self.execute(sql, execute=True)
        
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
    
    async def make_him_admin_magically(self, telegram_id, passwd):
        if passwd == await self.get_passwd():
            await self.make_him_admin(telegram_id)
            return True
        return False

    """
    Control categories
    """

    async def create_table_categories(self):
        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
            category_id SERIAL PRIMARY KEY,
            
            name VARCHAR(100) NOT NULL,
            description TEXT,
            
            sale BOOLEAN DEFAULT FALSE,
            sale_percent SMALLINT DEFAULT 0
            );
            """, execute=True)

    async def list_categories(self):
        sql = "SELECT * FROM categories"
        return await self.execute(sql, fetch=True)

    async def add_category(self, name, description):
        sql = "INSERT INTO categories (name, description) VALUES($1, $2) returning *"
        return await self.execute(sql, name, description, fetchrow=True)

    async def delete_category(self, category_id):
        return await self.execute("DELETE FROM categories WHERE category_id = $1", category_id, execute=True)

    async def cascade_deleting(self, category_id):
        return await self.execute("DELETE FROM meals where category_id = $1", category_id, execute=True)

    async def select_category(self, **kwargs):
        sql = "SELECT * FROM categories WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    async def update_category_data(self, name, description, sale, sale_percent, category_id):
        sql = "UPDATE categories SET name=$1, description=$2, sale=$3, sale_percent=$4 WHERE category_id=$5"
        return await self.execute(sql, name, description, sale, sale_percent, category_id, execute=True)

    async def open_category(self, category_id):
        sql = "SELECT * FROM meals WHERE category_id=$1 AND included=true"
        return await self.execute(sql, category_id, fetch=True)

    """
    Control meals
    """

    async def create_table_meals(self):
        await self.execute(
            """
            CREATE TABLE IF NOT EXISTS meals (
            meal_id SERIAL PRIMARY KEY,
            
            category_id BIGINT DEFAULT NULL,
            
            name VARCHAR(100) NOT NULL,
            description TEXT NULL,
            
            price INTEGER NOT NULL,
            sale BOOLEAN DEFAULT FALSE,
            sale_percent SMALLINT DEFAULT 0,
            
            included BOOLEAN DEFAULT TRUE
            );
            """, execute=True)

    async def list_meals(self):
        sql = "SELECT * FROM meals"
        return await self.execute(sql, fetch=True)

    async def add_meal(self, category_id, name, description, price):
        sql = "INSERT INTO meals (category_id, name, description, price) VALUES($1, $2, $3, $4) returning *"
        return await self.execute(sql, category_id, name, description, price, fetchrow=True)

    async def delete_meal(self, meal_id):
        return await self.execute("DELETE FROM meals WHERE meal_id = $1", meal_id, execute=True)

    async def select_onsale_ones(self, category_id):
        sql = "SELECT name FROM meals WHERE sale=true AND category_id=$1"
        return await self.execute(sql, category_id, fetch=True)

    async def update_meal_data(self, category_id, name, description, price, sale, sale_percent, included, meal_id):
        sql = "UPDATE meals SET category_id=$1, name=$2, description=$3, price=$4, sale=$5, sale_percent=$6, included=$7 WHERE meal_id=$8"
        return await self.execute(sql, category_id, name, description, price, sale, sale_percent, included, meal_id, execute=True)

    async def update_included(self, new_state, meal_id):
        sql = "UPDATE meals SET included=$1 WHERE meal_id=$2"
        return await self.execute(sql, new_state, meal_id, execute=True)

    async def select_meal(self, **kwargs):
        sql = "SELECT * FROM meals WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    """
    Basket
    """

    async def create_table_basket(self):
        sql = """
        CREATE TABLE IF NOT EXISTS basket (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT NOT NULL,
        meal_id INTEGER NOT NULL,
        real_price INTEGER NOT NULL,
        discount SMALLINT DEFAULT 0,
        amount SMALLINT DEFAULT 1,
        price INTEGER NOT NULL,
        total_cost INTEGER NOT NULL,
        info VARCHAR(100)
        );
        """
        await self.execute(sql, execute=True)

    async def add_meal_into_basket(
            self, telegram_id, meal_id, real_price, amount, price, total_cost, info, discount
        ):
        sql = "INSERT INTO basket " + \
        "(telegram_id, meal_id, real_price, amount, price, total_cost, info, discount) " + \
        "VALUES ($1, $2, $3, $4, $5, $6, $7, $8)"
        
        return await self.execute(
            sql, telegram_id, meal_id, real_price, amount, price, total_cost, info, discount,
            execute=True
        )

    async def order_meals(self, telegram_id):
        sql = """
        SELECT 
            meal_id,
            SUM(total_cost) AS total_cost_sum,
            SUM(amount) AS amount_sum,
            real_price,
            info
        FROM 
            basket
        WHERE 
            telegram_id = $1
        GROUP BY 
            meal_id, real_price, info
        ORDER BY 
            meal_id;
        """
        return await self.execute(sql, telegram_id, fetch=True)

    async def open_basket(self, telegram_id):
        sql = "SELECT * FROM basket WHERE telegram_id=$1"
        return await self.execute(sql, telegram_id, fetch=True)

    async def clean_basket(self, telegram_id):
        sql = "DELETE FROM basket WHERE telegram_id=$1"
        return await self.execute(sql, telegram_id, execute=True)

    async def delete_meal_from_basket(self, meal_id):
        sql = "DELETE * FROM basket WHERE meal_id=$1"
        return await self.execute(sql, meal_id, execute=True)

    """
    Orders
    """

    async def create_table_orders(self):
        sql = """
        CREATE TABLE IF NOT EXISTS orders (
            order_id SERIAL PRIMARY KEY,
            info TEXT,
            processing BOOLEAN DEFAULT FALSE,
            processed BOOLEAN DEFAULT FALSE,
            total_cost INTEGER NOT NULL,
            telegram_id BIGINT NOT NULL
        );"""
        await self.execute(sql, execute=True)

    async def create_order(self, info, total_cost, telegram_id):
        sql = """
        INSERT INTO orders (info, total_cost, telegram_id)
        VALUES ($1, $2, $3)
        RETURNING order_id, info, processed, total_cost, telegram_id
        """
        return await self.execute(sql, info, total_cost, telegram_id, fetchrow=True)

    async def select_order(self, **kwargs):
        sql = "SELECT * FROM orders WHERE "
        sql, parameters = self.format_args(sql, parameters=kwargs)
        return await self.execute(sql, *parameters, fetchrow=True)

    async def change_processing(self, order_id):
        sql = "UPDATE orders SET processing = NOT processing WHERE order_id=$1"
        return await self.execute(sql, order_id, execute=True)

    async def set_processed(self, order_id):
        sql = "UPDATE orders SET processed = true WHERE order_id=$1"
        return await self.execute(sql, order_id, execute=True)

    async def list_all_orders(self):
        sql = "SELECT * FROM orders ORDER BY order_id"
        return await self.execute(sql, fetch=True)
    
    async def list_user_orders(self, telegram_id):
        sql = "SELECT * FROM orders WHERE telegram_id=$1 ORDER BY order_id"
        return await self.execute(sql, telegram_id, fetch=True)
