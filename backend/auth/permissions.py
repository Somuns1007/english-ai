"""Database-backed admin checks, with an explicit legacy-token retirement switch."""
import os
import secrets

from fastapi import HTTPException

from .service import get_user_by_token


def cookie_admin(token: str | None):
    if not isinstance(token, str) or not token:
        return None
    try:
        user = get_user_by_token(token)
    except HTTPException as exc:
        if exc.status_code == 401:
            return None
        raise
    return user if user.role == 'admin' else None


def require_legacy_teacher(provided: str | None):
    if os.getenv('AUTH_ALLOW_LEGACY_TEACHER_TOKEN', 'true').lower() != 'true':
        raise HTTPException(403, '请使用管理员账号登录')
    expected = os.getenv('TEACHER_TOKEN')
    if not expected:
        raise HTTPException(503, '教师口令入口未配置，请使用管理员账号登录')
    if not isinstance(provided, str) or not secrets.compare_digest(provided.encode(), expected.encode()):
        raise HTTPException(401, '教师口令无效或未提供')
