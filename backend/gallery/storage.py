"""Reuse account SQLite connections; keep sanitized image files outside web roots."""
import os
from contextlib import contextmanager
from pathlib import Path

from auth.models import database


@contextmanager
def gallery_database():
    # Idempotent additive migration, using the existing account database/transaction.
    with database() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS gallery_images (
            id TEXT PRIMARY KEY, user_id TEXT NOT NULL,
            image_url TEXT NOT NULL, thumbnail_url TEXT NOT NULL,
            original_filename TEXT NOT NULL, mime_type TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK(status IN ('pending','approved','rejected')),
            caption TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL,
            reviewed_at TEXT, reviewed_by TEXT, reject_reason TEXT,
            deleted_at TEXT
        )""")
        db.execute("CREATE INDEX IF NOT EXISTS gallery_owner ON gallery_images(user_id, created_at)")
        db.execute("CREATE INDEX IF NOT EXISTS gallery_status ON gallery_images(status, reviewed_at)")
        db.execute("""CREATE TABLE IF NOT EXISTS gallery_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT, image_id TEXT NOT NULL,
            reviewed_by TEXT NOT NULL, reviewed_at TEXT NOT NULL, action TEXT NOT NULL
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS gallery_likes (
            image_id TEXT NOT NULL, user_id TEXT NOT NULL, created_at TEXT NOT NULL,
            PRIMARY KEY (image_id, user_id)
        )""")
        db.execute("CREATE INDEX IF NOT EXISTS gallery_likes_image ON gallery_likes(image_id)")
        yield db


def root():
    return Path(os.getenv("GALLERY_UPLOAD_DIR", str(
        Path(__file__).resolve().parents[2] / "uploads" / "gallery"))).resolve()


def image_path(image_id: str, thumbnail: bool = False):
    # No user filenames or database URLs ever participate in path resolution.
    import re
    if not re.fullmatch(r"[0-9a-f]{32}", image_id):
        from fastapi import HTTPException
        raise HTTPException(404, "图片不存在")
    directory = root()
    path = directory / f"{image_id}{'.thumb' if thumbnail else ''}.webp"
    if path.is_symlink() or not path.resolve().is_relative_to(directory):
        from fastapi import HTTPException
        raise HTTPException(404, "图片不存在")
    return path
