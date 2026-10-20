"""Account roles and email OTP tests use disposable SQLite and a fake mail transport."""
import io
import sqlite3

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from auth import service, email_codes, mailer
from auth.admin import grant_admin
from auth.models import database
from auth.router import router as auth_router
from gallery.router import router as gallery_router
from listening.router import router as listening_router


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setenv('AUTH_DB_PATH', str(tmp_path / 'accounts.db'))
    monkeypatch.setenv('GALLERY_UPLOAD_DIR', str(tmp_path / 'gallery'))
    monkeypatch.setenv('AUTH_JWT_SECRET', 'isolated-admin-email-test-secret-' * 2)
    monkeypatch.setenv('AUTH_COOKIE_SECURE', 'true')
    monkeypatch.setenv('AUTH_ALLOW_LEGACY_TEACHER_TOKEN', 'true')
    monkeypatch.setenv('AUTH_EMAIL_VERIFICATION_REQUIRED', 'false')
    monkeypatch.setenv('AUTH_MAIL_DAILY_LIMIT', '200')
    monkeypatch.setenv('TEACHER_TOKEN', 'legacy-test-only')
    monkeypatch.setattr(mailer, 'configured', lambda: True)
    sent = []
    monkeypatch.setattr(mailer, 'send_code', lambda email, code, purpose: sent.append((email, code, purpose)))
    app = FastAPI()
    for router in (auth_router, gallery_router, listening_router):
        app.include_router(router)
    with TestClient(app, base_url='https://testserver', headers={'X-Auth-Request': '1'}) as client:
        yield client, sent


def account(client, email='303528771@qq.com'):
    credentials = {'email': email, 'password': 'Password-123'}
    created = client.post('/api/auth/register', json={**credentials, 'role': 'admin'})
    assert created.status_code == 201, created.text
    assert created.json()['role'] == 'user'  # Including the specified owner's email.
    assert client.post('/api/auth/login', json=credentials).status_code == 200
    return created.json()


def request_code(client, email='new@example.com', purpose='register'):
    return client.post('/api/auth/email-code', json={'email': email, 'purpose': purpose})


def test_admin_live_role_checks_and_legacy_disable(setup, monkeypatch):
    client, _ = setup
    user = account(client)
    assert client.get('/api/admin/gallery').status_code == 403
    grant_admin(user['id'], user['email'])
    # The pre-grant login token picks up the current database role immediately.
    assert client.get('/api/auth/me').json()['role'] == 'admin'
    monkeypatch.delenv('TEACHER_TOKEN')
    assert client.get('/api/admin/gallery').status_code == 200
    assert client.get('/api/listening/teacher/expressions').status_code == 200
    assert client.get('/api/listening/teacher/corpus/assets').status_code == 200
    # Guard executes before business logic even for a nonexistent object.
    denied = client.put('/api/listening/teacher/expressions/nonexistent', json={}, headers={'X-Auth-Request': ''})
    assert denied.status_code == 403
    with database() as db:
        db.execute("UPDATE users SET role='user' WHERE id=?", (user['id'],))
    monkeypatch.setenv('TEACHER_TOKEN', 'legacy-test-only')
    assert client.get('/api/admin/gallery').status_code == 403
    assert client.get('/api/admin/gallery', headers={'X-Teacher-Token': 'legacy-test-only'}).status_code == 200
    monkeypatch.setenv('AUTH_ALLOW_LEGACY_TEACHER_TOKEN', 'false')
    assert client.get('/api/admin/gallery', headers={'X-Teacher-Token': 'legacy-test-only'}).status_code == 403
    assert client.get('/api/listening/teacher/expressions', headers={'X-Teacher-Token': 'legacy-test-only'}).status_code == 403


def test_admin_private_image_and_review_without_teacher(setup):
    client, _ = setup
    user = account(client, 'student@example.com')
    image = io.BytesIO(); Image.new('RGB', (20, 20)).save(image, 'PNG')
    record = client.post('/api/gallery/upload', files={'file': ('x.png', image.getvalue(), 'image/png')}).json()['data']
    admin = account(client, 'owner@example.com')
    assert client.get(record['image_url']).status_code == 404
    grant_admin(admin['id'], admin['email'])
    assert client.get(record['image_url']).status_code == 200
    assert client.get(record['thumbnail_url']).status_code == 200
    assert client.post(f"/api/admin/gallery/{record['id']}/approve").status_code == 200
    assert client.post(f"/api/admin/gallery/{record['id']}/reject", json={'reject_reason': 'test'}).status_code == 200
    assert client.delete(f"/api/admin/gallery/{record['id']}").status_code == 200


def test_grant_checks_existing_uuid_email_and_audits(setup):
    client, _ = setup
    user = account(client)
    with pytest.raises(ValueError):
        grant_admin('missing', user['email'])
    with pytest.raises(ValueError):
        grant_admin(user['id'], 'someone-else@example.com')
    assert client.get('/api/auth/me').json()['role'] == 'user'
    grant_admin(user['id'], user['email'])
    with database() as db:
        assert db.execute('SELECT user_id FROM auth_role_audit').fetchone()[0] == user['id']


def test_verified_registration_and_code_not_exposed(setup, monkeypatch):
    client, sent = setup
    monkeypatch.setenv('AUTH_EMAIL_VERIFICATION_REQUIRED', 'true')
    body = {'email': 'new@example.com', 'password': 'Password-123'}
    assert client.post('/api/auth/register', json=body).status_code == 400
    response = request_code(client)
    assert response.status_code == 200
    code = sent[-1][1]
    assert code not in response.text
    with database() as db:
        row = db.execute('SELECT * FROM auth_email_codes').fetchone()
        assert row['code_hash'] != code and len(row['code_hash']) == 64
    result = client.post('/api/auth/register', json={**body, 'code': code, 'role': 'admin'})
    assert result.status_code == 201
    assert result.json()['email_verified'] is True and result.json()['role'] == 'user'
    assert client.post('/api/auth/register', json={**body, 'code': code}).status_code == 400


def test_wrong_codes_lock_after_five_attempts(setup, monkeypatch):
    client, sent = setup
    monkeypatch.setenv('AUTH_EMAIL_VERIFICATION_REQUIRED', 'true')
    request_code(client)
    code = sent[-1][1]
    wrong = '000000' if code != '000000' else '111111'
    body = {'email': 'new@example.com', 'password': 'Password-123'}
    for _ in range(5):
        assert client.post('/api/auth/register', json={**body, 'code': wrong}).status_code == 400
    assert client.post('/api/auth/register', json={**body, 'code': code}).status_code == 400
    with database() as db:
        assert db.execute('SELECT attempts FROM auth_email_codes').fetchone()[0] == 5


def test_expired_wrong_purpose_and_wrong_email(setup, monkeypatch):
    client, sent = setup
    monkeypatch.setenv('AUTH_EMAIL_VERIFICATION_REQUIRED', 'true')
    request_code(client)
    code = sent[-1][1]
    assert client.post('/api/auth/reset-password', json={'email': 'new@example.com', 'password': 'Password-123', 'code': code}).status_code == 400
    assert client.post('/api/auth/register', json={'email': 'other@example.com', 'password': 'Password-123', 'code': code}).status_code == 400
    with database() as db:
        db.execute('UPDATE auth_email_codes SET expires_at=0')
    assert client.post('/api/auth/register', json={'email': 'new@example.com', 'password': 'Password-123', 'code': code}).status_code == 400


def test_reset_revokes_existing_tokens_and_retains_role(setup):
    client, sent = setup
    user = account(client)
    grant_admin(user['id'], user['email'])
    old_token = client.cookies['token']
    assert request_code(client, user['email'], 'reset').status_code == 200
    body = {'email': user['email'], 'password': 'Changed-password-456', 'code': sent[-1][1]}
    assert client.post('/api/auth/reset-password', json=body).status_code == 200
    assert client.get('/api/auth/me', headers={'Cookie': f'token={old_token}'}).status_code == 401
    assert client.get('/api/admin/gallery', headers={'Cookie': f'token={old_token}'}).status_code == 401
    assert client.post('/api/auth/login', json={'email': user['email'], 'password': 'Password-123'}).status_code == 401
    assert client.post('/api/auth/login', json=body).status_code == 200
    assert client.get('/api/auth/me').json()['role'] == 'admin'
    assert client.post('/api/auth/reset-password', json=body).status_code == 400


def test_send_limits_and_unknown_reset_account(setup, monkeypatch):
    client, sent = setup
    assert request_code(client, 'absent@example.com', 'reset').status_code == 200
    assert sent == []
    assert request_code(client, 'absent@example.com', 'reset').status_code == 429
    monkeypatch.setenv('AUTH_MAIL_DAILY_LIMIT', '1')
    assert request_code(client).status_code == 429


def test_missing_smtp_and_delivery_failure(setup, monkeypatch):
    client, sent = setup
    monkeypatch.setattr(mailer, 'configured', lambda: False)
    assert client.get('/api/auth/capabilities').json()['email_available'] is False
    assert request_code(client).status_code == 503
    monkeypatch.setattr(mailer, 'configured', lambda: True)
    def fail(*args):
        raise OSError('secret-smtp-details')
    monkeypatch.setattr(mailer, 'send_code', fail)
    response = request_code(client)
    assert response.status_code == 503 and 'secret-smtp-details' not in response.text
    with database() as db:
        assert db.execute('SELECT used FROM auth_email_codes').fetchone()[0] == 1


def test_old_schema_migration_is_idempotent(tmp_path, monkeypatch):
    path = tmp_path / 'old.db'
    monkeypatch.setenv('AUTH_DB_PATH', str(path))
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE users(id TEXT PRIMARY KEY,email TEXT UNIQUE,password_hash TEXT,created_at TEXT,is_active INTEGER)')
        db.execute("INSERT INTO users VALUES('existing','303528771@qq.com','hash','old',1)")
    for _ in range(2):
        with database() as db:
            row = db.execute('SELECT * FROM users').fetchone()
            assert row['role'] == 'user' and row['token_version'] == 0
            assert row['password_hash'] == 'hash' and row['email_verified'] == 0
