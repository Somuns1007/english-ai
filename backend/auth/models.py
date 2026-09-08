"""User schema and isolated SQLite storage (never uses listening.db)."""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from pydantic import BaseModel


class User(BaseModel):
    id: str
    email: str
    created_at: str
    is_active: bool


@contextmanager
def database():
    path = Path(os.getenv("AUTH_DB_PATH", str(Path(__file__).parent / "data" / "auth.db"))).resolve()
    listening = Path(__file__).resolve().parents[1] / "listening"
    if path.is_relative_to(listening):
        raise RuntimeError("认证数据库不能位于 listening 目录")
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("""CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            is_active INTEGER DEFAULT 1
        )""")
        with connection:
            yield connection
    finally:
        connection.close()
