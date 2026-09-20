"""Local-only manual QA server with disposable accounts/data; never run in production.

Run from the repository with a working backend Python, then start Vite on 5173.
Fixture terminal states bypass practice only in this isolated developer server.
"""
import os
import sys
import tempfile
from pathlib import Path


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="listening-preview-", ignore_cleanup_errors=True) as folder:
        os.environ.update(LISTENING_DB_PATH=str(Path(folder) / "listening.db"),
                          AUTH_DB_PATH=str(Path(folder) / "auth.db"),
                          AUTH_JWT_SECRET="local-preview-only-not-a-production-secret-123",
                          AUTH_COOKIE_SECURE="false", ALLOW_UNRELEASED_LISTENING_V2="true",
                          AUTH_ALLOWED_ORIGINS="http://127.0.0.1:5173,http://localhost:5173")
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from fastapi import FastAPI
        import uvicorn
        from auth import service as auth_service
        from auth.router import router as auth_router
        from listening import repository, learning_service, v2_exam_service
        from listening.router import router as listening_router
        from listening.learning_router import router as learning_router

        user = auth_service.register("preview@example.com", "Preview-only-123")
        repo = repository.student_repo
        exam = "cet6_202606_set2_v2"
        attempt = repo.create_attempt(user.id, exam, "exam_mode", owner_id=user.id)
        learning_service.bind_source(repo, "exam_attempt", attempt["id"], user.id, exam)
        with repo._conn() as conn:
            conn.execute("UPDATE attempts SET submitted_at=? WHERE id=?", (repository._now(), attempt["id"]))
        for unit in v2_exam_service.v2_registry.get(exam)["units"]:
            learning_service.create(repo, user.id, "exam_attempt", attempt["id"], unit["unit_id"])
        app = FastAPI()
        for router in (auth_router, listening_router, learning_router):
            app.include_router(router)
        print("Disposable preview: preview@example.com / Preview-only-123", flush=True)
        uvicorn.run(app, host="127.0.0.1", port=8000)
