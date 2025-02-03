# database/db_handler.py
import logging
import psycopg2
from config.db_config import DB_CONFIG
from datetime import datetime

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('database.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
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

    def add_payment(self, telegram_id, amount):
        self.cur.execute(
            """
            INSERT INTO pay (telegram_id, amount) 
            VALUES (%s, %s) 
            RETURNING payment_id
            """,
            (telegram_id, amount)
        )
        payment_id = self.cur.fetchone()[0]
        self.conn.commit()
        return payment_id

    def update_payment(self, payment_id, payment_uid):
        self.cur.execute(
            """
            UPDATE pay 
            SET payment_uid = %s 
            WHERE payment_id = %s
            """,
            (payment_uid, payment_id)
        )
        self.conn.commit()

    def delete_payment(self, payment_id):
        self.cur.execute(
            """
            DELETE FROM pay 
            WHERE payment_id = %s
            """,
            (payment_id,)
        )
        self.conn.commit()

    def get_payment_by_uid(self, payment_uid):
        try:
            self.cur.execute(
                """
                SELECT payment_id, amount, telegram_id 
                FROM pay 
                WHERE payment_uid = %s
                """,
                (payment_uid,)
            )
            result = self.cur.fetchone()
            logger.info(f"Payment info for UID {payment_uid}: {result}")
            return result
        except Exception as e:
            logger.error(f"Ошибка получения платежа: {str(e)}")
            return None

    def get_last_payment(self, telegram_id):
        self.cur.execute(
            """
            SELECT payment_id, amount 
            FROM pay 
            WHERE telegram_id = %s 
            ORDER BY payment_id DESC 
            LIMIT 1
            """,
            (telegram_id,)
        )
        return self.cur.fetchone()

    def update_payment_status(self, payment_id, status):
        try:
            self.cur.execute(
                """
                UPDATE pay 
                SET status = %s 
                WHERE payment_id = %s
                """,
                (status, payment_id)
            )
            self.conn.commit()
            logger.info(f"Статус платежа {payment_id} обновлен на {status}")
        except Exception as e:
            logger.error(f"Ошибка обновления статуса платежа: {str(e)}")
            self.conn.rollback()

    def close(self):
        self.cur.close()
        self.conn.close()
