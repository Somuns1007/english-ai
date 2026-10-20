"""User schema and isolated SQLite storage (never uses listening.db)."""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

from pydantic import BaseModel


class User(BaseModel):
    id: str
    email: str
    created_at: str
    is_active: bool
    role: Literal['user', 'admin'] = 'user'
    email_verified: bool = False


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
            # Serialize additive migrations across workers; never grant roles by email.
            connection.execute('BEGIN IMMEDIATE')
            columns = {row['name'] for row in connection.execute('PRAGMA table_info(users)')}
            for name, declaration in (
                ('role', "TEXT NOT NULL DEFAULT 'user' CHECK(role IN ('user','admin'))"),
                ('email_verified', 'INTEGER NOT NULL DEFAULT 0'),
                ('token_version', 'INTEGER NOT NULL DEFAULT 0'),
            ):
                if name not in columns:
                    connection.execute(f'ALTER TABLE users ADD COLUMN {name} {declaration}')
            connection.execute('''CREATE TABLE IF NOT EXISTS auth_email_codes (
                id TEXT PRIMARY KEY, email TEXT NOT NULL, purpose TEXT NOT NULL,
                code_hash TEXT NOT NULL, created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0, used INTEGER NOT NULL DEFAULT 1,
                client_key TEXT NOT NULL
            )''')
            connection.execute('CREATE INDEX IF NOT EXISTS auth_codes_email ON auth_email_codes(email,created_at)')
            connection.execute('CREATE INDEX IF NOT EXISTS auth_codes_time ON auth_email_codes(created_at)')
            connection.execute('CREATE INDEX IF NOT EXISTS auth_codes_client ON auth_email_codes(client_key,created_at)')
            connection.execute('''CREATE TABLE IF NOT EXISTS auth_role_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT NOT NULL,
                role TEXT NOT NULL, changed_at TEXT NOT NULL, source TEXT NOT NULL
            )''')
        with connection:
            yield connection
    finally:
        connection.close()
