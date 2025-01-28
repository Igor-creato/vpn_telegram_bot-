# database/db_handler.py
import psycopg2
from config.db_config import DB_CONFIG
from datetime import datetime

class DatabaseHandler:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cur = self.conn.cursor()

    def get_user(self, telegram_id):
        self.cur.execute("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
        return self.cur.fetchone()

    def update_user(self, telegram_id, username, phone_number, email, name):
        self.cur.execute(
            """
            UPDATE users 
            SET user_name = %s, phone_number = %s, email = %s, name = %s 
            WHERE telegram_id = %s
            """,
            (username, phone_number, email, name, telegram_id)
        )
        self.conn.commit()

    def add_user(self, username, telegram_id, phone_number, email, name):
        self.cur.execute(
            """
            INSERT INTO users (user_name, telegram_id, phone_number, email, name) 
            VALUES (%s, %s, %s, %s, %s)
            """,
            (username, telegram_id, phone_number, email, name)
        )
        self.conn.commit()

    def get_user_keys(self, telegram_id):
        self.cur.execute(
            """
            SELECT link_key, expiration_date 
            FROM keys 
            WHERE telegram_id = %s 
            ORDER BY expiration_date ASC
            """,
            (telegram_id,)
        )
        return self.cur.fetchall()

    def close(self):
        self.cur.close()
        self.conn.close()