import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

_ENV_PATH = Path(__file__).resolve().parent / ".env"
if load_dotenv and _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)

class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "replace-me")
    DB_ENGINE = os.getenv("DB_ENGINE", "mysql").lower()
    DATABASE_URL = os.getenv("DATABASE_URL", "")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "5432" if DB_ENGINE.startswith("post") else "3306"))
    DB_NAME = os.getenv("DB_NAME", "mini_erp")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_SSLMODE = os.getenv("DB_SSLMODE", "require")


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False


Config = ProductionConfig if os.getenv("FLASK_ENV") == "production" else DevelopmentConfig
