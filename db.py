import os
from urllib.parse import urlparse

from config import Config


def _mysql_kwargs_from_url(url):
    parsed = urlparse(url)
    return {
        "host": parsed.hostname or "localhost",
        "user": parsed.username or "",
        "password": parsed.password or "",
        "database": (parsed.path or "").lstrip("/") or None,
        "port": parsed.port or 3306,
    }


def get_db_connection():
    engine = (Config.DB_ENGINE or "mysql").lower()
    if Config.DATABASE_URL:
        if engine.startswith("post"):
            import psycopg2
            from psycopg2.extras import RealDictCursor

            return psycopg2.connect(
                Config.DATABASE_URL,
                cursor_factory=RealDictCursor,
                sslmode=Config.DB_SSLMODE
            )
        if engine.startswith("mysql"):
            import pymysql

            return pymysql.connect(
                **_mysql_kwargs_from_url(Config.DATABASE_URL),
                cursorclass=pymysql.cursors.DictCursor
            )

    if engine.startswith("post"):
        import psycopg2
        from psycopg2.extras import RealDictCursor

        return psycopg2.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            dbname=Config.DB_NAME,
            port=Config.DB_PORT or 5432,
            cursor_factory=RealDictCursor,
            sslmode=Config.DB_SSLMODE
        )

    import pymysql
    return pymysql.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        port=Config.DB_PORT or 3306,
        cursorclass=pymysql.cursors.DictCursor
    )
