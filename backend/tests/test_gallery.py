"""Isolated gallery regression tests: never touch real accounts, listening DB or uploads."""
import io

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from auth import service
from gallery.router import router
from gallery.limits import GalleryBodyLimit
from gallery.storage import gallery_database, image_path


@pytest.fixture
def gallery(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "auth.db"))
    monkeypatch.setenv("GALLERY_UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("AUTH_JWT_SECRET", "gallery-test-secret-only-" * 3)
    monkeypatch.setenv("TEACHER_TOKEN", "gallery-teacher-test")
    accounts = {}
    for name in ('alice', 'bob', 'admin'):
        user = service.register(f'{name}@example.com', 'password123')
        _, token = service.login(user.email, 'password123')
        accounts[name] = (user, token)
    app = FastAPI()
    app.include_router(router)
    app.add_middleware(GalleryBodyLimit)
    with TestClient(app) as client:
        yield client, accounts


def headers(gallery, name='alice', teacher=False):
    _, accounts = gallery
    result = {'X-Auth-Request': '1'}
    if name:
        result['Cookie'] = f'token={accounts[name][1]}'
    if teacher:
        result['X-Teacher-Token'] = 'gallery-teacher-test'
    return result


def picture(fmt='PNG', size=(40, 30), exif=False):
    output = io.BytesIO()
    metadata = Image.Exif()
    metadata[271] = 'PRIVATE_DEVICE'
    Image.new('RGB', size, '#c3aadd').save(output, format=fmt, **({'exif': metadata} if exif else {}))
    return output.getvalue()


def upload(gallery, name='alice', content=None, filename='cat.png', mime='image/png'):
    return gallery[0].post('/api/gallery/upload', headers=headers(gallery, name),
        files={'file': (filename, picture() if content is None else content, mime)}, data={'caption': '校园小猫'})


def test_pending_is_private_and_cannot_be_enumerated(gallery):
    client, accounts = gallery
    result = upload(gallery)
    assert result.status_code == 201, result.text
    row = result.json()['data']
    assert row['status'] == 'pending'
    assert client.get('/api/gallery/public').json()['data'] == []
    assert client.get('/api/gallery/mine', headers=headers(gallery, 'bob'),
                      params={'user_id': accounts['alice'][0].id}).json()['data'] == []
    for url in (row['image_url'], row['thumbnail_url']):
        assert client.get(url).status_code == 404
        assert client.get(url, headers=headers(gallery, 'bob')).status_code == 404
        assert client.get(url, headers=headers(gallery)).status_code == 200
        assert client.get(url, headers=headers(gallery, 'admin', True)).status_code == 200
        assert client.get(url, params={'token': 'gallery-teacher-test'}, headers=headers(gallery, 'bob')).status_code == 404
    assert client.get('/api/gallery/mine').status_code == 401
    assert upload(gallery, name=None).status_code == 401


def test_admin_required_for_every_operation(gallery):
    client, _ = gallery
    row = upload(gallery).json()['data']
    for name in ('alice', 'bob', None):
        expected = 403 if name else 401
        auth = headers(gallery, name)
        assert client.get('/api/admin/gallery', headers=auth).status_code == expected
        assert client.post(f"/api/admin/gallery/{row['id']}/approve", headers=auth).status_code == expected
        assert client.post(f"/api/admin/gallery/{row['id']}/reject", headers=auth,
                           json={'reject_reason': ''}).status_code == expected
        assert client.delete(f"/api/admin/gallery/{row['id']}", headers=auth).status_code == expected


def test_approve_reject_revoke_delete_and_audit(gallery):
    client, accounts = gallery
    row = upload(gallery).json()['data']
    admin = headers(gallery, 'admin', True)
    assert client.post(f"/api/admin/gallery/{row['id']}/approve", headers=admin).status_code == 200
    public = client.get('/api/gallery/public').json()['data']
    assert len(public) == 1
    assert not {'user_id', 'user_email', 'original_filename', 'reviewed_by', 'reject_reason'} & public[0].keys()
    response = client.get(row['image_url'])
    assert response.status_code == 200 and response.headers['cache-control'] == 'private, no-store'
    assert client.post(f"/api/admin/gallery/{row['id']}/reject", headers=admin,
                       json={'reject_reason': '请避免拍到同学的个人信息'}).status_code == 200
    assert client.get('/api/gallery/public').json()['total'] == 0
    assert client.get(row['image_url']).status_code == 404
    mine = client.get('/api/gallery/mine', headers=headers(gallery)).json()['data'][0]
    assert mine['reject_reason'] == '请避免拍到同学的个人信息'
    image_path(row['id'], True).unlink()  # Missing files must not break deletion.
    assert client.delete(f"/api/admin/gallery/{row['id']}", headers=admin).status_code == 200
    assert not image_path(row['id']).exists()
    assert client.get(row['image_url'], headers=admin).status_code == 404
    assert client.get('/api/gallery/mine', headers=headers(gallery)).json()['total'] == 0
    with gallery_database() as db:
        audit = db.execute('SELECT * FROM gallery_audit ORDER BY id').fetchall()
        assert [r['action'] for r in audit] == ['approved', 'rejected', 'delete']
        assert all(r['reviewed_by'] == accounts['admin'][0].id for r in audit)


@pytest.mark.parametrize('filename,mime,content', [
    ('cat.svg', 'image/svg+xml', b'<svg/>'), ('cat.jpg', 'image/jpeg', b'<html>evil</html>'),
    ('cat.png', 'image/png', b'PK\x03\x04zip'), ('cat.exe', 'image/png', None),
    ('cat.png', 'application/octet-stream', None), ('cat.jpg', 'image/jpeg', None),
    ('cat.gif', 'image/gif', b'GIF89a'),
])
def test_invalid_images(gallery, filename, mime, content):
    assert upload(gallery, content=content, filename=filename, mime=mime).status_code in (415, 422)


def test_size_limits_and_request_body_limit(gallery):
    assert upload(gallery, content=b'x' * (10 * 1024 * 1024 + 1)).status_code == 413
    assert upload(gallery, content=b'x' * (11 * 1024 * 1024 + 1)).status_code == 413
    assert upload(gallery, content=picture(size=(8001, 1))).status_code == 422
    assert upload(gallery, content=picture(size=(4001, 4000))).status_code == 422


def test_sanitization_thumbnail_filename_and_metadata(gallery):
    client, _ = gallery
    row = upload(gallery, filename='../../cat.jpg', mime='image/jpeg',
                 content=picture('JPEG', (1200, 800), exif=True)).json()['data']
    with Image.open(image_path(row['id'])) as img:
        assert img.format == 'WEBP' and not img.getexif()
        assert 'exif' not in img.info and 'xmp' not in img.info
    with Image.open(image_path(row['id'], True)) as img:
        assert max(img.size) == 600 and not img.getexif()
    assert client.get('/api/gallery/images/not-an-id', headers=headers(gallery)).status_code == 404


def test_csrf_protection(gallery):
    client, accounts = gallery
    auth = headers(gallery)
    auth.pop('X-Auth-Request')
    assert client.post('/api/gallery/upload', headers=auth,
                       files={'file': ('cat.png', picture(), 'image/png')}).status_code == 403
    auth = headers(gallery); auth['Origin'] = 'https://evil.example'
    assert client.post('/api/gallery/upload', headers=auth,
                       files={'file': ('cat.png', picture(), 'image/png')}).status_code == 403


def test_no_upload_limit(gallery):
    # Rate limit has been removed; many uploads in sequence should all succeed.
    for _ in range(5):
        assert upload(gallery).status_code == 201


def test_pagination_filter_and_safe_caption(gallery):
    client, _ = gallery
    upload(gallery); upload(gallery)
    auth = headers(gallery, 'admin', True)
    result = client.get('/api/admin/gallery?page_size=1', headers=auth).json()
    assert result['total'] == 2 and len(result['data']) == 1
    page2 = client.get('/api/admin/gallery?page_size=1&page=2', headers=auth).json()
    assert result['data'][0]['id'] != page2['data'][0]['id']
    assert client.get('/api/admin/gallery?status=approved', headers=auth).json()['total'] == 0
    assert client.get('/api/gallery/public?page_size=99999').status_code == 422


def test_animated_and_decompression_bomb_rejected(gallery, monkeypatch):
    frames = [Image.new('RGB', (30, 30), color) for color in ('red', 'blue')]
    animated = io.BytesIO()
    frames[0].save(animated, 'PNG', save_all=True, append_images=frames[1:], duration=100)
    assert upload(gallery, content=animated.getvalue()).status_code == 415
    data = picture()
    monkeypatch.setattr(Image, 'MAX_IMAGE_PIXELS', 100)
    assert upload(gallery, content=data).status_code == 422


def test_chunked_body_is_bounded_without_content_length(gallery):
    def chunks():
        for _ in range(12):
            yield b'x' * (1024 * 1024)
    response = gallery[0].post('/api/gallery/upload', headers={**headers(gallery),
        'Content-Type': 'multipart/form-data; boundary=test'}, content=chunks())
    assert response.status_code == 413


def test_delete_failure_hides_image_and_can_retry(gallery, monkeypatch):
    from pathlib import Path
    client, _ = gallery
    row = upload(gallery).json()['data']
    admin = headers(gallery, 'admin', True)
    client.post(f"/api/admin/gallery/{row['id']}/approve", headers=admin)
    original = Path.unlink
    with monkeypatch.context() as patch:
        def fail(path, *args, **kwargs):
            if path == image_path(row['id']):
                raise PermissionError('test-only failure')
            return original(path, *args, **kwargs)
        patch.setattr(Path, 'unlink', fail)
        assert client.delete(f"/api/admin/gallery/{row['id']}", headers=admin).status_code == 503
        assert client.get(row['image_url']).status_code == 404
        assert client.get('/api/gallery/public').json()['total'] == 0
    assert client.delete(f"/api/admin/gallery/{row['id']}", headers=admin).status_code == 200
    assert not image_path(row['id']).exists()


def test_like_toggle_and_sort(gallery):
    client, accounts = gallery
    admin = headers(gallery, 'admin', True)
    r1 = upload(gallery).json()['data']
    r2 = upload(gallery).json()['data']
    client.post(f"/api/admin/gallery/{r1['id']}/approve", headers=admin)
    client.post(f"/api/admin/gallery/{r2['id']}/approve", headers=admin)
    # Public listing includes like_count and liked fields.
    public = client.get('/api/gallery/public').json()['data']
    assert all(p['like_count'] == 0 and p['liked'] is False for p in public)
    # Like requires login — CSRF protection fires before auth, so expect 403.
    assert client.post(f"/api/gallery/images/{r1['id']}/like").status_code in (401, 403)
    # Alice likes image 1.
    result = client.post(f"/api/gallery/images/{r1['id']}/like", headers=headers(gallery)).json()
    assert result['liked'] is True and result['like_count'] == 1
    # Bob also likes image 1.
    result = client.post(f"/api/gallery/images/{r1['id']}/like", headers=headers(gallery, 'bob')).json()
    assert result['liked'] is True and result['like_count'] == 2
    # Alice likes image 2 (1 like).
    client.post(f"/api/gallery/images/{r2['id']}/like", headers=headers(gallery))
    # Sort by popular: image 1 (2 likes) should come first.
    popular = client.get('/api/gallery/public?sort=popular', headers=headers(gallery)).json()['data']
    assert popular[0]['id'] == r1['id'] and popular[0]['like_count'] == 2
    assert popular[1]['id'] == r2['id'] and popular[1]['like_count'] == 1
    # Alice's liked flag.
    assert popular[0]['liked'] is True and popular[1]['liked'] is True
    # Bob sees his own liked state.
    bob_popular = client.get('/api/gallery/public?sort=popular', headers=headers(gallery, 'bob')).json()['data']
    assert bob_popular[0]['liked'] is True  # Bob liked r1
    assert bob_popular[1]['liked'] is False  # Bob didn't like r2
    # Toggle off: Alice unlikes image 1.
    result = client.post(f"/api/gallery/images/{r1['id']}/like", headers=headers(gallery)).json()
    assert result['liked'] is False and result['like_count'] == 1
    # Cannot like a pending image.
    r3 = upload(gallery).json()['data']
    assert client.post(f"/api/gallery/images/{r3['id']}/like", headers=headers(gallery)).status_code == 404


def test_page_size_default_30(gallery):
    client, _ = gallery
    result = client.get('/api/gallery/public').json()
    assert result['page_size'] == 30
