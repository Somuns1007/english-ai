"""Disposable full-app gallery QA server; synthetic pictures/accounts, never production data."""
import io
import os
import sys
import tempfile
from pathlib import Path


if __name__ == '__main__':
    with tempfile.TemporaryDirectory(prefix='gallery-preview-', ignore_cleanup_errors=True) as folder:
        os.environ.update(
            LISTENING_DB_PATH=str(Path(folder) / 'listening.db'),
            AUTH_DB_PATH=str(Path(folder) / 'auth.db'),
            GALLERY_UPLOAD_DIR=str(Path(folder) / 'uploads'),
            AUTH_JWT_SECRET='gallery-preview-not-a-real-secret-123456789',
            AUTH_COOKIE_SECURE='false', TEACHER_TOKEN='gallery-preview-teacher',
            DEEPSEEK_API_KEY='local-preview-no-network-requests',
            AUTH_ALLOWED_ORIGINS='http://127.0.0.1:5173,http://localhost:5173')
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from main import app
        from auth import service
        from fastapi.testclient import TestClient
        from PIL import Image, ImageDraw
        import uvicorn

        service.register('gallery@example.com', 'Preview-only-123')
        _, token = service.login('gallery@example.com', 'Preview-only-123')
        with TestClient(app) as client:
            for n, color in enumerate(('#c5b4d9', '#b4d9cf', '#e3c9a0')):
                canvas = Image.new('RGB', (900, 600), color)
                draw = ImageDraw.Draw(canvas)
                draw.ellipse((320, 190, 580, 450), fill='#faf5ed')
                draw.polygon(((340, 230), (350, 120), (420, 210)), fill='#faf5ed')
                draw.polygon(((480, 210), (550, 120), (560, 230)), fill='#faf5ed')
                for x in (395, 495):
                    draw.ellipse((x, 290, x + 14, 305), fill='#423c49')
                data = io.BytesIO(); canvas.save(data, 'PNG')
                headers = {'Cookie': f'token={token}', 'X-Auth-Request': '1'}
                result = client.post('/api/gallery/upload', headers=headers,
                    files={'file': ('cat.png', data.getvalue(), 'image/png')},
                    data={'caption': ('今天也要好好休息', '自习室的小猫', '仅供本地页面测试')[n]})
                result.raise_for_status()
                if n != 1:
                    headers['X-Teacher-Token'] = 'gallery-preview-teacher'
                    action = 'approve' if n == 0 else 'reject'
                    client.post(f"/api/admin/gallery/{result.json()['data']['id']}/{action}",
                                headers=headers, json={'reject_reason': '测试审核结果'}).raise_for_status()
        print('Local QA only: gallery@example.com / Preview-only-123; teacher: gallery-preview-teacher', flush=True)
        uvicorn.run(app, host='127.0.0.1', port=8000)
