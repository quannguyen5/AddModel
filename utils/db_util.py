import mysql.connector
from mysql.connector import pooling
import logging
from config.config import Config


class DatabaseUtil:
    _instance = None
    _pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseUtil, cls).__new__(cls)
            try:
                # Khởi tạo pool connection
                cls._pool = pooling.MySQLConnectionPool(
                    pool_name="mysql_pool",
                    pool_size=5,
                    host=Config.DB_HOST,
                    port=Config.DB_PORT,
                    user=Config.DB_USER,
                    password=Config.DB_PASSWORD,
                    database=Config.DB_NAME
                )
                logging.info(f"Database connection pool created successfully")
            except Exception as e:
                logging.error(f"Error creating connection pool: {str(e)}")
                raise
        return cls._instance

    def get_connection(self):
        """Lấy connection từ pool"""
        try:
            conn = self._pool.get_connection()
            return conn
        except Exception as e:
            logging.error(f"Error getting connection from pool: {str(e)}")
            raise

    def execute_query(self, query, params=None, fetchone=False, fetchall=False, commit=False):
        """
        Thực thi truy vấn và trả về kết quả

        Args:
            query (str): Câu truy vấn SQL
            params (tuple|dict, optional): Tham số cho truy vấn
            fetchone (bool, optional): Trả về một bản ghi duy nhất
            fetchall (bool, optional): Trả về tất cả bản ghi
            commit (bool, optional): Commit thay đổi vào database

        Returns:
            Kết quả của truy vấn hoặc None nếu lỗi
        """
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
            logging.error(f"Database error: {str(e)}")
            if commit and conn:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def execute_many(self, query, params_list):
        """
        Thực thi nhiều truy vấn cùng một lúc

        Args:
            query (str): Câu truy vấn SQL
            params_list (list): Danh sách các tham số

        Returns:
            Số bản ghi bị ảnh hưởng hoặc None nếu lỗi
        """
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            logging.error(f"Database error in execute_many: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def initialize_database(self, schema_file='schema.sql'):
        """
        Khởi tạo cơ sở dữ liệu từ file schema

        Args:
            schema_file (str): Đường dẫn tới file schema
        """
        conn = None
        cursor = None
        try:
            # Đọc file schema với encoding UTF-8
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema = f.read()

            # Tách các câu lệnh SQL
            statements = schema.split(';')

            conn = self.get_connection()
            cursor = conn.cursor()

            # Thực thi từng câu lệnh
            for statement in statements:
                if statement.strip():
                    cursor.execute(statement)

            conn.commit()
            logging.info("Database initialized successfully")
        except Exception as e:
            logging.error(f"Error initializing database: {str(e)}")
            if conn:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()