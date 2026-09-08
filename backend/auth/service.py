"""Password validation, bcrypt hashing and 30-day signed JWT authentication."""
import os
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import bcrypt
from fastapi import HTTPException
from jose import JWTError, jwt

from .models import User, database

TOKEN_SECONDS = 30 * 24 * 60 * 60
ISSUER = "english-ai-auth"
# Equal-cost password check for nonexistent accounts.
_DUMMY_HASH = bcrypt.hashpw(b"not-a-real-password", bcrypt.gensalt())


def jwt_secret():
    secret = os.getenv("AUTH_JWT_SECRET", "")
    if len(secret.encode()) < 32:
        raise HTTPException(503, "认证服务尚未配置，请联系管理员")
    return secret


def credentials(email: str, password: str):
    email = email.strip().lower()
    if len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@.]+(?:\.[^\s@.]+)+", email):
        raise HTTPException(422, "请输入有效邮箱")
    if len(password) < 8 or len(password.encode("utf-8")) > 72:
        raise HTTPException(422, "密码至少 8 个字符，且 UTF-8 长度不超过 72 字节")
    return email, password.encode("utf-8")


def public_user(row):
    return User(**{key: row[key] for key in User.model_fields})


def register(email: str, password: str):
    jwt_secret()  # Fail before creating an account if login cannot work.
    email, encoded = credentials(email, password)
    user = User(id=str(uuid4()), email=email, created_at=datetime.now(timezone.utc).isoformat(), is_active=True)
    password_hash = bcrypt.hashpw(encoded, bcrypt.gensalt()).decode("ascii")
    try:
        with database() as db:
            db.execute("INSERT INTO users (id,email,password_hash,created_at) VALUES (?,?,?,?)",
                       (user.id, user.email, password_hash, user.created_at))
    except sqlite3.IntegrityError:
        raise HTTPException(409, "该邮箱已注册，请直接登录")
    return user


def login(email: str, password: str):
    secret = jwt_secret()
    email, encoded = credentials(email, password)
    with database() as db:
        row = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    valid = bcrypt.checkpw(encoded, row["password_hash"].encode("ascii") if row else _DUMMY_HASH)
    if not valid or not row or not row["is_active"]:
        raise HTTPException(401, "邮箱或密码错误")
    now = datetime.now(timezone.utc)
    token = jwt.encode({"sub": row["id"], "iat": now, "exp": now + timedelta(seconds=TOKEN_SECONDS),
                        "iss": ISSUER, "aud": ISSUER}, secret, algorithm="HS256")
    return public_user(row), token


def get_user_by_token(token: str | None):
    if not token:
        raise HTTPException(401, "请先登录")
    try:
        claims = jwt.decode(token, jwt_secret(), algorithms=["HS256"], issuer=ISSUER, audience=ISSUER,
                            options={"require_exp": True, "require_sub": True, "require_iat": True})
    except JWTError:
        raise HTTPException(401, "登录已失效，请重新登录")
    with database() as db:
        row = db.execute("SELECT * FROM users WHERE id = ? AND is_active = 1", (claims["sub"],)).fetchone()
    if not row:
        raise HTTPException(401, "登录已失效，请重新登录")
    return public_user(row)
