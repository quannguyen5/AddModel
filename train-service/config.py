import os
from dotenv import load_dotenv
load_dotenv()


class Config:
    # Services URLs
    TEMPLATE_SERVICE_URL = os.getenv(
        "TEMPLATE_SERVICE_URL", "http://localhost:8003")
    MODEL_SERVICE_URL = os.getenv("MODEL_SERVICE_URL", "http://localhost:8001")

    # Shared Model Directory
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    SHARED_MODEL_DIR = os.path.join(BASE_DIR, "shared_model")

    # Training parameters
    DEFAULT_EPOCH = int(os.getenv("DEFAULT_EPOCH", "100"))
    DEFAULT_BATCH_SIZE = int(os.getenv("DEFAULT_BATCH_SIZE", "16"))
    DEFAULT_LEARNING_RATE = float(os.getenv("DEFAULT_LEARNING_RATE", "0.001"))

    DEBUG = os.getenv("DEBUG", "True").lower() in ('true', '1', 't')

    @staticmethod
    def init_directories():
        """Tạo thư mục shared_model"""
        if not os.path.exists(Config.SHARED_MODEL_DIR):
            os.makedirs(Config.SHARED_MODEL_DIR)
            print(f"Created: {Config.SHARED_MODEL_DIR}")
