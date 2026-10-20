"""Disposable account-admin/email UI preview; simulated mail, NEVER a production server."""
import os
import sys
import tempfile
from pathlib import Path


if __name__ == '__main__':
    with tempfile.TemporaryDirectory(prefix='admin-email-preview-', ignore_cleanup_errors=True) as folder:
        os.environ.update(
            LISTENING_DB_PATH=str(Path(folder) / 'listening.db'), AUTH_DB_PATH=str(Path(folder) / 'auth.db'),
            GALLERY_UPLOAD_DIR=str(Path(folder) / 'gallery'),
            AUTH_JWT_SECRET='isolated-preview-admin-email-secret-12345678', AUTH_COOKIE_SECURE='false',
            AUTH_ALLOW_LEGACY_TEACHER_TOKEN='false', AUTH_EMAIL_VERIFICATION_REQUIRED='false',
            AUTH_ALLOWED_ORIGINS='http://127.0.0.1:5173,http://localhost:5173',
            DEEPSEEK_API_KEY='preview-no-external-model-call')
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from auth import service, mailer
        from auth.admin import grant_admin
        user = service.register('admin-preview@example.com', 'Preview-only-123')
        grant_admin(user.id, user.email)
        os.environ['AUTH_EMAIL_VERIFICATION_REQUIRED'] = 'true'
        # No SMTP delivery, production credentials, or real recipient addresses are used.
        mailer.configured = lambda: True
        mailer.send_code = lambda *args: None
        from main import app
        import uvicorn
        print('Local simulated preview only: admin-preview@example.com / Preview-only-123', flush=True)
        uvicorn.run(app, host='127.0.0.1', port=8000)
