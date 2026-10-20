"""Expiring, purpose-bound OTPs with hashed storage and atomic shared SQLite quotas."""
import hashlib
import hmac
import os
import secrets
import time
from uuid import uuid4

from fastapi import HTTPException

from .models import database
from . import mailer


def required():
    return os.getenv('AUTH_EMAIL_VERIFICATION_REQUIRED', 'false').lower() == 'true'


def digest(value):
    from .service import jwt_secret
    return hmac.new(jwt_secret().encode(), value.encode(), hashlib.sha256).hexdigest()


def send(email: str, purpose: str, client_host: str):
    from .service import credentials
    email, _ = credentials(email, 'validation-only')
    if purpose not in ('register', 'reset'):
        raise HTTPException(422, '验证码用途无效')
    if not mailer.configured():
        raise HTTPException(503, '邮件服务尚未配置，请联系管理员')
    stamp = int(time.time())
    code_id, code = uuid4().hex, f'{secrets.randbelow(1_000_000):06d}'
    client_key = digest('client:' + client_host)
    try:
        daily_limit = max(1, min(10000, int(os.getenv('AUTH_MAIL_DAILY_LIMIT', '200'))))
    except ValueError:
        raise HTTPException(503, '邮件服务配置有误，请联系管理员') from None
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        # Keep 48h for rolling-day quotas, not a permanent history of addresses/IPs.
        db.execute('DELETE FROM auth_email_codes WHERE created_at<?', (stamp - 172800,))
        latest = db.execute('SELECT MAX(created_at) FROM auth_email_codes WHERE email=?', (email,)).fetchone()[0]
        email_count = db.execute('SELECT COUNT(*) FROM auth_email_codes WHERE email=? AND created_at>?',
                                (email, stamp - 3600)).fetchone()[0]
        ip_count = db.execute('SELECT COUNT(*) FROM auth_email_codes WHERE client_key=? AND created_at>?',
                             (client_key, stamp - 3600)).fetchone()[0]
        total = db.execute('SELECT COUNT(*) FROM auth_email_codes WHERE created_at>?', (stamp - 86400,)).fetchone()[0]
        if (latest is not None and stamp - latest < 60) or email_count >= 5 or ip_count >= 20 or total >= daily_limit:
            raise HTTPException(429, '发送过于频繁或今日额度已用完，请稍后再试')
        db.execute('UPDATE auth_email_codes SET used=1 WHERE email=? AND purpose=?', (email, purpose))
        db.execute('''INSERT INTO auth_email_codes
            (id,email,purpose,code_hash,created_at,expires_at,client_key) VALUES(?,?,?,?,?,?,?)''',
            (code_id, email, purpose, digest(code_id + ':' + code), stamp, stamp + 600, client_key))
        existing = db.execute('SELECT is_active FROM users WHERE email=?', (email,)).fetchone()
        deliver = (purpose == 'register' and not existing) or (purpose == 'reset' and existing and existing['is_active'])
    # Unknown/inactive reset accounts and existing registration accounts get the same response.
    if not deliver:
        return
    try:
        mailer.send_code(email, code, purpose)
    except Exception:
        raise HTTPException(503, '验证码发送失败，请稍后重试') from None
    with database() as db:
        # A slow earlier SMTP operation must not reactivate an OTP superseded by a later request.
        db.execute('''UPDATE auth_email_codes SET used=0 WHERE id=? AND NOT EXISTS (
            SELECT 1 FROM auth_email_codes newer WHERE newer.email=? AND newer.purpose=? AND newer.created_at>?)''',
            (code_id, email, purpose, stamp))


def consume(db, email: str, purpose: str, code: str | None):
    """Caller must commit failed-attempt increments too; return false instead of raising."""
    row = db.execute('''SELECT * FROM auth_email_codes WHERE email=? AND purpose=? AND used=0
        ORDER BY created_at DESC LIMIT 1''', (email, purpose)).fetchone()
    if not row or row['expires_at'] <= int(time.time()) or row['attempts'] >= 5:
        return False
    db.execute('UPDATE auth_email_codes SET attempts=attempts+1 WHERE id=?', (row['id'],))
    if not isinstance(code, str) or not hmac.compare_digest(row['code_hash'], digest(row['id'] + ':' + code)):
        return False
    db.execute('UPDATE auth_email_codes SET used=1 WHERE id=?', (row['id'],))
    return True


def reset_password(email: str, password: str, code: str):
    import bcrypt
    from .service import credentials
    email, encoded = credentials(email, password)
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        valid = consume(db, email, 'reset', code)
        if valid:
            # Invalid OTP requests must not trigger expensive password hashing.
            hashed = bcrypt.hashpw(encoded, bcrypt.gensalt()).decode('ascii')
            result = db.execute('''UPDATE users SET password_hash=?,email_verified=1,token_version=token_version+1
                WHERE email=? AND is_active=1''', (hashed, email))
            valid = result.rowcount == 1
            db.execute('UPDATE auth_email_codes SET used=1 WHERE email=?', (email,))
    if not valid:
        raise HTTPException(400, '验证码无效、已过期或尝试次数过多，请重新获取')
