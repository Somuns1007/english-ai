"""Listening identity integration: real JWT/cookie checks with isolated account/student stores."""
import ast
from pathlib import Path
import inspect
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth.router import router as auth_router
from listening import router as api
from listening.repository import StudentRepository


@pytest.fixture(scope="module")
def app():
    application = FastAPI()
    application.include_router(auth_router)
    application.include_router(api.router)
    return application


@pytest.fixture
def setup(tmp_path, monkeypatch, app):
    monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "auth.db"))
    monkeypatch.setenv("AUTH_JWT_SECRET", "isolated-student-auth-test-secret-32-bytes")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "true")
    repo = StudentRepository(tmp_path / "listening.db")
    monkeypatch.setattr(api, "student_repo", repo)
    with TestClient(app, base_url="https://testserver") as client:
        yield client, repo, app
    app.dependency_overrides.clear()


def sign_in(client):
    data = {"email": "identity@example.com", "password": "test-password-123"}
    headers = {"X-Auth-Request": "1"}
    created = client.post("/api/auth/register", json=data, headers=headers)
    assert created.status_code == 201
    assert client.post("/api/auth/login", json=data, headers=headers).status_code == 200
    return created.json()["id"]


def test_anonymous_and_authenticated_persistence(setup, monkeypatch):
    client, repo, app = setup
    # Only availability is stubbed; attempt creation and JWT verification are real.
    monkeypatch.setattr(api.exam_repo, "get", lambda _: object())
    monkeypatch.setattr(api.v2_exam_service, "is_v2_exam", lambda _: False)
    payload = {"student_id": "alice", "exam_id": "identity-fixture", "mode": "exam_mode"}
    anonymous = client.post("/api/listening/attempts", json=payload).json()["data"]
    assert repo.get_attempt(anonymous["id"])["student_id"] == "alice"
    user_id = sign_in(client)
    owned = client.post("/api/listening/attempts", json=payload).json()["data"]
    assert repo.get_attempt(owned["id"])["student_id"] == user_id
    # Simulated second device: separate cookie jar, same account login.
    with TestClient(app, base_url="https://testserver") as device2:
        assert device2.post("/api/auth/login", json={"email": "identity@example.com", "password": "test-password-123"},
                            headers={"X-Auth-Request": "1"}).status_code == 200
        found = device2.get("/api/listening/attempts/in-progress", params={
            "student_id": "some-other-device", "exam_id": "identity-fixture", "mode": "exam_mode"})
        assert found.json()["data"]["attempt"]["id"] == owned["id"]
    assert client.post("/api/auth/logout", headers={"X-Auth-Request": "1"}).status_code == 204
    assert client.post("/api/listening/attempts", json=payload).json()["data"]["student_id"] == "alice"


@pytest.mark.parametrize("failure", [None, "broken-token", "backend-error"])
def test_optional_auth_fallback(setup, monkeypatch, failure):
    client, _, _ = setup
    if failure:
        client.cookies.set("token", failure)
    if failure == "backend-error":
        monkeypatch.setattr(api, "_auth_get_user", Mock(side_effect=RuntimeError("unavailable")))
    spy = Mock(return_value={})
    monkeypatch.setattr(api.dashboard_service, "get_dashboard", spy)
    assert client.get("/api/listening/dashboard?student_id=alice").status_code == 200
    spy.assert_called_once_with("alice")


QUERY_CASES = [
    ("/exams", "service", "exam_summaries", [], 0),
    ("/attempts/in-progress?exam_id=x", "student_repo", "find_in_progress_attempt", None, 0),
    ("/mistakes", "service", "list_mistakes", [], 0),
    ("/profile", "profile_service", "build_profile", {}, 0),
    ("/profile/causes", "profile_service", "build_cause_profile", {}, 0),
    ("/profile/skills", "profile_service", "build_cause_profile", [], 0),
    ("/expressions", "expression_service", "list_expressions", [], 0),
    ("/expressions/x", "expression_service", "expression_detail", {"id": "x"}, 1),
    ("/v2/practice/sessions/find?material_id=x", "v2_practice_service", "find_session", None, 0),
    ("/lexicon/session", "aural_lexicon_service", "get_daily_session", {}, 0),
    ("/lexicon/phase0/status", "aural_lexicon_service", "get_phase0_status", {}, 0),
    ("/lexicon/phase0/entry-test", "aural_lexicon_service", "start_entry_test", {}, 0),
    ("/stem-bank/stats", "stem_bank_service", "get_student_stats", {}, 0),
    ("/dashboard", "dashboard_service", "get_dashboard", {}, 0),
]


@pytest.mark.parametrize("case", QUERY_CASES, ids=[c[0] for c in QUERY_CASES])
@pytest.mark.parametrize("authenticated", [False, True])
def test_all_query_endpoints(setup, monkeypatch, case, authenticated):
    client, _, app = setup
    app.dependency_overrides[api._optional_student_id] = lambda: "USER-UUID-123" if authenticated else None
    monkeypatch.setattr(api.v2_exam_service, "gate_allows", lambda: True)
    monkeypatch.setattr(api.profile_service, "build_skill_profile", lambda _: {})
    path, module, method, result, index = case
    spy = Mock(return_value=result)
    monkeypatch.setattr(getattr(api, module), method, spy)
    response = client.get("/api/listening" + path + ("&" if "?" in path else "?") + "student_id=alice")
    assert response.status_code == 200, response.text
    assert spy.call_args.args[index] == ("USER-UUID-123" if authenticated else "alice")


BODY_CASES = [
    ("/attempts", {"exam_id": "x"}, "student_repo", "create_attempt", {}, 0),
    ("/attempts/a/events", {"events": []}, "student_repo", "add_behavior_events", 0, 0),
    ("/diagnoses", {"attempt_id": "a", "question_id": "q"}, "student_repo", "upsert_diagnosis", {}, 0),
    ("/training-results", {"question_id": "q", "training_type": "dictation"}, "student_repo", "add_training_result", {}, 0),
    ("/expressions/scenarios/x/submit", {}, "expression_service", "submit_scenario", {}, 1),
    ("/v2/practice/sessions", {"material_id": "x"}, "v2_practice_service", "create_session", {"id": "s", "stage": "first_pass"}, 0),
    ("/v2/practice/sessions/s/events", {"events": []}, "v2_practice_service", "record_events", {}, 1),
    ("/lexicon/phase0/entry-test/complete", {"results": []}, "aural_lexicon_service", "complete_entry_test", {}, 0),
    ("/lexicon/phase0/complete", {"retest_score": 1}, "aural_lexicon_service", "complete_phase0", {}, 0),
    ("/lexicon/attempt", {"item_id": "x", "task_type": "hear_identify", "is_correct": True}, "aural_lexicon_service", "record_attempt", {}, "student_id"),
    ("/lexicon/harvest", {"item_id": "x", "gate_type": "exam_attempt", "gate_id": "a"}, "aural_lexicon_service", "harvest_word", {}, "student_id"),
    ("/stem-bank/predict", {"question_no": 1}, "stem_bank_service", "record_prediction", {}, "student_id"),
]


@pytest.mark.parametrize("case", BODY_CASES, ids=[c[0] for c in BODY_CASES])
@pytest.mark.parametrize("authenticated", [False, True])
def test_all_body_endpoints(setup, monkeypatch, case, authenticated):
    client, _, app = setup
    app.dependency_overrides[api._optional_student_id] = lambda: "USER-UUID-123" if authenticated else None
    monkeypatch.setattr(api.v2_exam_service, "gate_allows", lambda: True)
    monkeypatch.setattr(api.v2_exam_service, "is_v2_exam", lambda _: False)
    monkeypatch.setattr(api.exam_repo, "get", lambda _: object())
    monkeypatch.setattr(api.student_repo, "get_attempt", lambda _: {"exam_id": "x"})
    path, payload, module, method, result, index = case
    spy = Mock(return_value=result)
    monkeypatch.setattr(getattr(api, module), method, spy)
    response = client.post("/api/listening" + path, json={**payload, "student_id": "alice"})
    assert response.status_code == 200, response.text
    args = spy.call_args.kwargs if isinstance(index, str) else spy.call_args.args
    assert args[index] == ("USER-UUID-123" if authenticated else "alice")


def test_no_student_endpoint_missing_dependency():
    tree = ast.parse(Path(api.__file__).read_text(encoding="utf-8"))
    found = 0
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or not node.decorator_list:
            continue
        has_id = any(a.arg == "student_id" for a in node.args.args) or any(
            isinstance(n, ast.Attribute) and n.attr == "student_id" for n in ast.walk(node))
        if has_id:
            found += 1
            assert any(a.arg == "auth_id" for a in node.args.args), node.name
            # Legacy tests call route functions directly, bypassing dependency injection.
            assert inspect.signature(getattr(api, node.name)).parameters["auth_id"].default is None
    assert found == 26


def test_release_gate_remains_closed(setup, monkeypatch):
    client, _, _ = setup
    monkeypatch.delenv("ALLOW_UNRELEASED_LISTENING_V2", raising=False)
    assert api.v2_exam_service.student_release_allowed() is False
    sign_in(client)
    assert client.post("/api/listening/v2/practice/sessions", json={"student_id": "alice", "material_id": "x"}).status_code == 403


# Exercise all three write paths, not only the events acceptance example.
_OWNER_WRITES = [
    ("events", "behavior_events"),
    ("diagnoses", "diagnoses"),
    ("training-results", "training_results"),
]


def _new_owner_attempt(client):
    response = client.post("/api/listening/attempts", json={
        "student_id": "client-claimed-id", "exam_id": "cet6_202606_set2", "mode": "exam_mode",
    })
    assert response.status_code == 200, response.text
    return response.json()["data"]


def _owner_write(client, attempt_id, endpoint):
    if endpoint == "events":
        return client.post(f"/api/listening/attempts/{attempt_id}/events", json={
            "student_id": "forged-id", "events": [{"event_type": "audio_play"}],
        })
    return client.post(f"/api/listening/{endpoint}", json={
        "student_id": "forged-id", "attempt_id": attempt_id,
        "question_id": "cet6_202606_set2_q10", "training_type": "dictation",
    })


@pytest.mark.parametrize("endpoint,table", _OWNER_WRITES)
def test_ownership_blocks_cross_user_write(setup, endpoint, table):
    """A's owned attempt rejects B before any of the three tables are written."""
    client, repo, app = setup
    owner = sign_in(client)
    attempt = _new_owner_attempt(client)
    assert attempt["owner_id"] == owner
    assert repo.get_attempt(attempt["id"])["owner_id"] == owner
    with TestClient(app, base_url="https://testserver") as other:
        body = {"email": "other@example.com", "password": "other-password-123"}
        headers = {"X-Auth-Request": "1"}
        assert other.post("/api/auth/register", json=body, headers=headers).status_code == 201
        assert other.post("/api/auth/login", json=body, headers=headers).status_code == 200
        response = _owner_write(other, attempt["id"], endpoint)
        assert response.status_code == 403
        assert response.json()["detail"] == "无权操作他人记录"
    assert repo._conn().execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0
    # Explicitly retain the requested limitation: invalid/no cookie bypasses ownership.
    with TestClient(app, base_url="https://testserver") as anonymous:
        anonymous.cookies.set("token", "invalid-cookie")
        assert _owner_write(anonymous, attempt["id"], endpoint).status_code == 200


@pytest.mark.parametrize("endpoint,table", _OWNER_WRITES)
def test_ownership_passes_anonymous_attempt(setup, endpoint, table):
    """Anonymous creation stays NULL and permits a subsequently logged-in writer."""
    client, repo, _ = setup
    attempt = _new_owner_attempt(client)
    assert attempt["owner_id"] is None
    # Repeated migration is idempotent and does not backfill an anonymous owner.
    repo._init_schema()
    assert repo.get_attempt(attempt["id"])["owner_id"] is None
    sign_in(client)
    assert _owner_write(client, attempt["id"], endpoint).status_code == 200
    assert repo._conn().execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 1


@pytest.mark.parametrize("endpoint,table", _OWNER_WRITES)
def test_ownership_passes_self_write(setup, endpoint, table):
    """The authenticated owner can still write to their own attempt."""
    client, repo, _ = setup
    owner = sign_in(client)
    attempt = _new_owner_attempt(client)
    assert attempt["owner_id"] == owner
    assert _owner_write(client, attempt["id"], endpoint).status_code == 200
    assert repo._conn().execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 1
