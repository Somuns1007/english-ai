"""One-time local operator CLI: grant an EXISTING account by UUID plus matching email."""
import argparse
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .models import database


def grant_admin(user_id: str, expected_email: str):
    with database() as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT id,email,is_active FROM users WHERE id=?', (user_id,)).fetchone()
        if not row or not row['is_active'] or row['email'].lower() != expected_email.strip().lower():
            raise ValueError('账号 ID、邮箱不匹配或账号未启用，未授权')
        db.execute("UPDATE users SET role='admin' WHERE id=?", (user_id,))
        db.execute('INSERT INTO auth_role_audit(user_id,role,changed_at,source) VALUES(?,?,?,?)',
                   (user_id, 'admin', datetime.now(timezone.utc).isoformat(), 'operator-cli'))


def main():
    import os
    from dotenv import load_dotenv
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--email', required=True)
    parser.add_argument('--user-id', help='Omit to inspect only; supply the inspected UUID to grant.')
    args = parser.parse_args()
    path = Path(os.getenv('AUTH_DB_PATH', str(Path(__file__).parent / 'data' / 'auth.db'))).resolve()
    if not path.is_file():
        parser.error('账户数据库不存在；不要新建账号代替已有线上账号')
    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as db:
        rows = db.execute('SELECT id,email,is_active FROM users WHERE lower(email)=?',
                          (args.email.strip().lower(),)).fetchall()
    if len(rows) != 1 or not rows[0][2]:
        parser.error('没有找到唯一且启用的已有账号')
    if not args.user_id:
        print(f'只读查询：id={rows[0][0]} email={rows[0][1]}；确认本人持有此账号后再加 --user-id 执行授权。')
        return
    if args.user_id != rows[0][0]:
        parser.error('提供的账号 ID 与邮箱不匹配')
    # SQLite online backup includes committed WAL data. Never overwrite an old backup.
    backup = path.with_name(path.name + '.before-admin-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.bak')
    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as source, sqlite3.connect(backup) as destination:
        source.backup(destination)
    backup.chmod(0o600)
    grant_admin(args.user_id, args.email)
    print(f'已授权账号 {args.user_id}；备份：{backup}')


if __name__ == '__main__':
    main()
