import os
from .sqlite_storage import storage as sqlite_storage


def get_storage():
    database_url = os.getenv("DATABASE_URL")
    if database_url and database_url.startswith("postgresql"):
        from .postgres_storage import PostgresStorage
        return PostgresStorage(database_url)
    return sqlite_storage


# Global storage instance
storage = get_storage()
