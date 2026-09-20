"""Gallery API: login-bound uploads, teacher-authorized reviews and guarded media."""
import io
import logging
import warnings
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, Request, Response, UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import BaseModel, Field

from auth.models import User
from auth.router import protect_request
from auth.service import get_user_by_token
from listening.router import require_teacher
from .storage import gallery_database, image_path, root

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["gallery"], dependencies=[Depends(protect_request)])
MAX_FILE = 10 * 1024 * 1024
FORMATS = {"jpg": ("image/jpeg", "JPEG"), "jpeg": ("image/jpeg", "JPEG"),
           "png": ("image/png", "PNG"), "webp": ("image/webp", "WEBP")}


def current_user(request: Request):
    return get_user_by_token(request.cookies.get("token"))


def administrator(user: User = Depends(current_user), x_teacher_token: str | None = Header(None)):
    # Reuse existing teacher authorization, but never accept secrets in URLs.
    try:
        require_teacher(x_teacher_token=x_teacher_token, token=None)
    except HTTPException as exc:
        if exc.status_code == 401:
            raise HTTPException(403, "仅管理员可以操作") from None
        raise
    return user


def now():
    return datetime.now(timezone.utc).isoformat()


def public_record(row):
    # Explicit DTO: never expose account ID, email, filename or rejection notes.
    data = {key: row[key] for key in (
        "id", "image_url", "thumbnail_url", "caption", "created_at", "reviewed_at", "status")}
    data["like_count"] = row["like_count"] if "like_count" in row.keys() else 0
    data["liked"] = bool(row["liked"]) if "liked" in row.keys() else False
    return data


def own_record(row):
    return {**public_record(row), "reject_reason": row["reject_reason"]}


def sanitize(file: UploadFile):
    filename = PurePosixPath((file.filename or "").replace("\\", "/")).name
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in FORMATS or file.content_type != FORMATS[ext][0]:
        raise HTTPException(415, "仅支持 JPG、PNG 和 WebP 图片。")
    raw = file.file.read(MAX_FILE + 1)
    if len(raw) > MAX_FILE:
        raise HTTPException(413, "图片不能超过 10MB。")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as source:
                width, height = source.size
                if source.format != FORMATS[ext][1]:
                    raise HTTPException(415, "文件内容与图片格式不一致。")
                if width * height > 16_000_000 or max(width, height) > 8000:
                    raise HTTPException(422, "图片尺寸过大，请缩小到 1600 万像素、边长 8000px 以内。")
                if getattr(source, "n_frames", 1) != 1:
                    raise HTTPException(415, "暂不支持动态图片。")
                source.verify()
            with Image.open(io.BytesIO(raw)) as source:
                oriented = ImageOps.exif_transpose(source).convert("RGB")
                # Reconstruct pixels rather than copying metadata (EXIF/GPS/ICC/XMP).
                clean = Image.frombytes("RGB", oriented.size, oriented.tobytes())
            full = io.BytesIO()
            clean.save(full, format="WEBP", quality=88)
            clean.thumbnail((600, 600))
            thumb = io.BytesIO()
            clean.save(thumb, format="WEBP", quality=82)
            if full.tell() > MAX_FILE:
                raise HTTPException(413, "图片处理后过大，请缩小后重新上传。")
            return filename[:255], full.getvalue(), thumb.getvalue()
    except HTTPException:
        raise
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError,
            Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise HTTPException(422, "图片文件无法识别或尺寸异常，请重新选择。") from None


@router.post("/gallery/upload", status_code=201)
def upload(file: UploadFile = File(...), caption: str = Form("", max_length=200),
           user: User = Depends(current_user)):
    filename, full, thumb = sanitize(file)
    image_id = uuid4().hex
    created = now()
    paths = []
    try:
        with gallery_database() as db:
            root().mkdir(parents=True, exist_ok=True, mode=0o750)
            for thumbnail, content in ((False, full), (True, thumb)):
                path = image_path(image_id, thumbnail)
                with path.open("xb") as output:
                    paths.append(path)
                    output.write(content)
                path.chmod(0o640)
            db.execute("""INSERT INTO gallery_images
                (id,user_id,image_url,thumbnail_url,original_filename,mime_type,file_size,caption,created_at)
                VALUES (?,?,?,?,?,?,?,?,?)""", (image_id, user.id,
                f"/api/gallery/images/{image_id}", f"/api/gallery/images/{image_id}/thumbnail",
                filename, "image/webp", len(full), caption.strip(), created))
            row = db.execute("SELECT * FROM gallery_images WHERE id=?", (image_id,)).fetchone()
        return {"data": own_record(row)}
    except Exception as exc:
        for path in paths:
            path.unlink(missing_ok=True)
        if isinstance(exc, HTTPException):
            raise
        logger.error("gallery upload failed (%s)", type(exc).__name__)
        raise HTTPException(503, "上传失败，请稍后重试。") from None


SORT_ORDERS = {
    "latest": "COALESCE(g.reviewed_at, g.created_at) DESC, g.id DESC",
    "popular": "like_count DESC, COALESCE(g.reviewed_at, g.created_at) DESC, g.id DESC",
}


def listing(where, parameters, page, page_size, kind, sort="latest", viewer_id=None):
    order = SORT_ORDERS.get(sort, SORT_ORDERS["latest"])
    if kind == "admin":
        order = f"CASE WHEN g.status='pending' THEN 0 ELSE 1 END, {order}"
    with gallery_database() as db:
        predicate = f"g.deleted_at IS NULL AND ({where})"
        total = db.execute(f"SELECT COUNT(*) FROM gallery_images g WHERE {predicate}", parameters).fetchone()[0]
        rows = db.execute(f"""SELECT g.*, u.email AS user_email,
            COALESCE(lc.cnt, 0) AS like_count,
            COALESCE(ml.liked, 0) AS liked
            FROM gallery_images g
            LEFT JOIN users u ON u.id=g.user_id
            LEFT JOIN (SELECT image_id, COUNT(*) AS cnt FROM gallery_likes GROUP BY image_id) lc ON lc.image_id=g.id
            LEFT JOIN (SELECT image_id, 1 AS liked FROM gallery_likes WHERE user_id=?) ml ON ml.image_id=g.id
            WHERE {predicate}
            ORDER BY {order} LIMIT ? OFFSET ?""",
            (viewer_id or "", *parameters, page_size, (page - 1) * page_size)).fetchall()
    items = []
    for row in rows:
        data = public_record(row) if kind == "public" else own_record(row)
        if kind == "admin":
            data.update({key: row[key] for key in ("user_email", "file_size", "reviewed_by")})
        items.append(data)
    return {"data": items, "total": total, "page": page, "page_size": page_size}


def _optional_user(request: Request):
    if request.cookies.get("token"):
        try:
            return get_user_by_token(request.cookies.get("token"))
        except HTTPException:
            pass
    return None


@router.get("/gallery/public")
def public(request: Request, page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=60),
           sort: Literal['latest', 'popular'] = 'latest'):
    viewer = _optional_user(request)
    return listing("g.status='approved'", (), page, page_size, "public", sort, viewer.id if viewer else None)


@router.get("/gallery/mine")
def mine(user: User = Depends(current_user), page: int = Query(1, ge=1),
         page_size: int = Query(30, ge=1, le=60)):
    return listing("g.user_id=?", (user.id,), page, page_size, "mine", viewer_id=user.id)


@router.get("/admin/gallery")
def admin_list(user: User = Depends(administrator), status: Literal['pending', 'approved', 'rejected', 'all'] = 'pending',
               page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=60)):
    return listing("1=1" if status == 'all' else "g.status=?", () if status == 'all' else (status,),
                   page, page_size, "admin", viewer_id=user.id)


@router.get("/gallery/images/{image_id}")
@router.get("/gallery/images/{image_id}/{variant}")
def media(image_id: str, request: Request, variant: Literal['thumbnail'] | None = None):
    user = None
    if request.cookies.get("token"):
        try:
            user = get_user_by_token(request.cookies.get("token"))
        except HTTPException as exc:
            if exc.status_code != 401:
                raise
    with gallery_database() as db:
        row = db.execute("SELECT * FROM gallery_images WHERE id=? AND deleted_at IS NULL", (image_id,)).fetchone()
        if not row:
            raise HTTPException(404, "图片不存在")
        if row["status"] != "approved" and (not user or row["user_id"] != user.id):
            try:
                if not user:
                    raise HTTPException(403)
                administrator(user, request.headers.get("X-Teacher-Token"))
            except HTTPException:
                raise HTTPException(404, "图片不存在") from None
        try:
            data = image_path(image_id, variant == 'thumbnail').read_bytes()
        except OSError:
            raise HTTPException(404, "图片不存在") from None
    return Response(data, media_type="image/webp", headers={
        "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff",
        "Content-Security-Policy": "default-src 'none'", "Vary": "Cookie, X-Teacher-Token",
        "Content-Disposition": 'inline; filename="gallery.webp"'})


class RejectBody(BaseModel):
    reject_reason: str = Field("", max_length=300)


def review(image_id, user, status, reason=""):
    image_path(image_id)  # Validate identifier before any changes.
    reviewed = now()
    with gallery_database() as db:
        result = db.execute("""UPDATE gallery_images SET status=?,reviewed_at=?,reviewed_by=?,reject_reason=?
            WHERE id=? AND deleted_at IS NULL""", (status, reviewed, user.id, reason.strip(), image_id))
        if not result.rowcount:
            raise HTTPException(404, "图片不存在")
        db.execute("INSERT INTO gallery_audit(image_id,reviewed_by,reviewed_at,action) VALUES(?,?,?,?)",
                   (image_id, user.id, reviewed, status))
    logger.info("gallery review image_id=%s reviewed_by=%s reviewed_at=%s action=%s",
                image_id, user.id, reviewed, status)
    return {"message": "已通过审核" if status == 'approved' else "已拒绝"}


@router.post("/admin/gallery/{image_id}/approve")
def approve(image_id: str, user: User = Depends(administrator)):
    return review(image_id, user, "approved")


@router.post("/admin/gallery/{image_id}/reject")
def reject(image_id: str, body: RejectBody, user: User = Depends(administrator)):
    return review(image_id, user, "rejected", body.reject_reason)


@router.delete("/admin/gallery/{image_id}")
def delete(image_id: str, user: User = Depends(administrator)):
    paths = [image_path(image_id), image_path(image_id, True)]
    deleted = now()
    with gallery_database() as db:
        result = db.execute("UPDATE gallery_images SET deleted_at=? WHERE id=?", (deleted, image_id))
        if not result.rowcount:
            raise HTTPException(404, "图片不存在")
        db.execute("INSERT INTO gallery_audit(image_id,reviewed_by,reviewed_at,action) VALUES(?,?,?,?)",
                   (image_id, user.id, deleted, "delete"))
    # Commit invisibility first. Retry DELETE can finish cleanup after a filesystem error.
    try:
        for path in paths:
            path.unlink(missing_ok=True)
    except OSError:
        logger.error("gallery cleanup failed image_id=%s", image_id)
        raise HTTPException(503, "图片已隐藏，文件清理失败，请重试删除。") from None
    logger.info("gallery review image_id=%s reviewed_by=%s reviewed_at=%s action=delete", image_id, user.id, deleted)
    return {"message": "已删除"}


@router.post("/gallery/images/{image_id}/like")
def toggle_like(image_id: str, user: User = Depends(current_user)):
    """点赞/取消点赞。只能赞已通过审核的图片。"""
    image_path(image_id)  # Validate identifier format.
    with gallery_database() as db:
        row = db.execute("SELECT status FROM gallery_images WHERE id=? AND deleted_at IS NULL",
                         (image_id,)).fetchone()
        if not row or row["status"] != "approved":
            raise HTTPException(404, "图片不存在")
        existing = db.execute("SELECT 1 FROM gallery_likes WHERE image_id=? AND user_id=?",
                              (image_id, user.id)).fetchone()
        if existing:
            db.execute("DELETE FROM gallery_likes WHERE image_id=? AND user_id=?", (image_id, user.id))
            liked = False
        else:
            db.execute("INSERT INTO gallery_likes(image_id,user_id,created_at) VALUES(?,?,?)",
                       (image_id, user.id, now()))
            liked = True
        count = db.execute("SELECT COUNT(*) FROM gallery_likes WHERE image_id=?",
                           (image_id,)).fetchone()[0]
    return {"liked": liked, "like_count": count}
