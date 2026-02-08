import os
from pathlib import Path

_ENV_PATH = Path(__file__).resolve().parent / ".env"
if _ENV_PATH.exists():
    for raw_line in _ENV_PATH.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value

class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-env")
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
