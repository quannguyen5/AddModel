import os
from dotenv import load_dotenv
load_dotenv()


class Config:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_NAME = os.getenv("DB_NAME", "kttk")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")

    DEFAULT_EPOCH = int(os.getenv("DEFAULT_EPOCH", "100"))
    DEFAULT_BATCH_SIZE = int(os.getenv("DEFAULT_BATCH_SIZE", "16"))
    DEFAULT_LEARNING_RATE = float(os.getenv("DEFAULT_LEARNING_RATE", "0.001"))

    DEBUG = os.getenv("DEBUG", "True").lower() in ('true', '1', 't')
    BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


@staticmethod
def init_app(app):
    upload_path = os.path.join(Config.BASE_DIR, Config.UPLOAD_FOLDER)
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
