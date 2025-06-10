import os
from dotenv import load_dotenv
load_dotenv()


class Config:
    # Template Service Database
    DB_HOST = os.getenv("TEMPLATE_DB_HOST", "localhost")
    DB_PORT = int(os.getenv("TEMPLATE_DB_PORT", "3306"))
    DB_NAME = os.getenv("TEMPLATE_DB_NAME", "template_db")
    DB_USER = os.getenv("TEMPLATE_DB_USER", "root")
    DB_PASSWORD = os.getenv("TEMPLATE_DB_PASSWORD", "")

    DEBUG = os.getenv("DEBUG", "True").lower() in ('true', '1', 't')
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
