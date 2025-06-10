import mysql.connector
from mysql.connector import pooling
import logging
from config import Config


class DatabaseUtil:
    _instance = None
    _pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            try:
                cls._pool = pooling.MySQLConnectionPool(
                    pool_name="model_pool",
                    pool_size=5,
                    host=Config.DB_HOST,
                    port=Config.DB_PORT,
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD,
                    database=Config.DB_NAME
                )
                print("Model DB connection pool created")
            except Exception as e:
                print(f"Error creating model DB pool: {e}")
                raise
        return cls._instance

    def get_connection(self):
        try:
            return self._pool.get_connection()
        except Exception as e:
            print(f"Error getting connection: {e}")
            raise

    def execute_query(self, query, params=None, fetchone=False, fetchall=False, commit=False):
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params)

            if fetchone:
                return cursor.fetchone()
            elif fetchall:
                return cursor.fetchall()
            elif commit:
                conn.commit()
                return cursor.lastrowid
            return None
        except Exception as e:
            print(f"Database error: {e}")
            if commit and conn:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
