import os
from dotenv import load_dotenv
load_dotenv()


class Config:
    # Model Service Database
    DB_HOST = os.getenv("MODEL_DB_HOST", "localhost")
    DB_PORT = int(os.getenv("MODEL_DB_PORT", "3306"))
    DB_NAME = os.getenv("MODEL_DB_NAME", "model_db")
    DB_USER = os.getenv("MODEL_DB_USER", "root")
    DB_PASSWORD = os.getenv("MODEL_DB_PASSWORD", "")

    # Services
    TEMPLATE_SERVICE_URL = os.getenv(
        "TEMPLATE_SERVICE_URL", "http://localhost:8003")

    DEBUG = os.getenv("DEBUG", "True").lower() in ('true', '1', 't')
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
