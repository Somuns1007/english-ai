"""Post-listening regression: real cookie auth, disposable DBs, no production writes."""
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth.router import router as auth_router
from listening import repository, router as api, learning_service as svc
from listening.learning_router import router as learning_router

BASE = "/api/listening/learning"
EXAM = "cet6_202606_set2_v2"
UNIT = "cet6_202606_set2_u1"
HEADERS = {"X-Auth-Request": "1"}


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "auth.db"))
    monkeypatch.setenv("AUTH_JWT_SECRET", "isolated-learning-test-secret-over-32-characters")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "true")
    monkeypatch.setattr(svc.v2_exam_service, "gate_allows", lambda: True)
    repo = repository.StudentRepository(tmp_path / "learning.db")
    for module in (repository, api, svc.v2_practice_service):
        monkeypatch.setattr(module, "student_repo", repo)
    app = FastAPI()
    for router in (auth_router, api.router, learning_router):
        app.include_router(router)
    with TestClient(app, base_url="https://testserver") as client:
        account = {"email": "learning@example.com", "password": "learning-test-password-123"}
        response = client.post("/api/auth/register", json=account, headers=HEADERS)
        assert response.status_code == 201, response.text
        user = response.json()["id"]
        assert client.post("/api/auth/login", json=account, headers=HEADERS).status_code == 200
        yield client, repo, user, app


def create_source(env, completed=True):
    client, repo, _, _ = env
    response = client.post("/api/listening/attempts", json={
        "exam_id": EXAM, "student_id": "spoofed", "mode": "exam_mode"})
    assert response.status_code == 200, response.text
    gate = response.json()["data"]["id"]
    if completed:
        with repo._conn() as conn:
            conn.execute("UPDATE attempts SET submitted_at=? WHERE id=?", (repository._now(), gate))
    return gate


def start(env, gate=None):
    client, _, _, _ = env
    response = client.post(BASE + "/sessions", json={"gate_type": "exam_attempt",
        "gate_id": gate or create_source(env), "material_id": UNIT}, headers=HEADERS)
    assert response.status_code == 200, response.text
    return response.json()["data"]


def reveal_first(client, data):
    path = BASE + "/sessions/" + data["session_id"]
    segment = data["segments"][0]["id"]
    body = {"request_id": "attempt-first-001", "segment_id": segment, "text": "I heard a trip", "difficulty": "sound"}
    assert client.post(path + "/attempts", json=body, headers=HEADERS).status_code == 200
    result = client.post(path + "/reveal", json={"request_id": "reveal-first-001", "segment_id": segment}, headers=HEADERS)
    assert result.status_code == 200, result.text
    return path, result.json()["data"]


def test_terminal_gate_and_payload_whitelist(env):
    client, _, _, _ = env
    gate = create_source(env, False)
    assert client.get(BASE + "/materials", params={"gate_type": "exam_attempt", "gate_id": gate}).status_code == 409
    data = start(env)
    assert data["profile_eligible"] is False
    assert all("text" not in s and "vocabulary" not in s for s in data["segments"])
    path = BASE + "/sessions/" + data["session_id"]
    payload = {"request_id": "early-reveal-001", "segment_id": data["segments"][0]["id"]}
    assert client.post(path + "/reveal", json=payload, headers=HEADERS).status_code == 409
    assert client.post(path + "/attempts", json={**payload, "content_hash": "forged"}, headers=HEADERS).status_code == 422
    assert client.post(path + "/attempts", json=payload).status_code == 403
    assert client.get(path + "/compare", params={"segment_id": payload["segment_id"]}).status_code == 403


def test_attempt_reveal_resume_and_finish(env):
    client, repo, _, _ = env
    data = start(env)
    path, revealed = reveal_first(client, data)
    assert revealed["segments"][0]["text"]
    assert all("text" not in s for s in revealed["segments"][1:])
    assert revealed["exposure_status"] == "text_exposed"
    assert client.get(path).json()["data"] == revealed
    assert client.get(path + "/compare", params={"segment_id": data["segments"][0]["id"]}).status_code == 200
    assert client.post(path + "/finish", json={"request_id": "finish-test-001"}, headers=HEADERS).json()["data"]["finished"]
    assert client.post(path + "/attempts", json={"request_id": "after-finish-001", "segment_id": data["segments"][0]["id"]}, headers=HEADERS).status_code == 409
    history = svc.events(repo, data["session_id"])
    assert all(json.loads(e["payload"]).get("profile_eligible") is not True for e in history)


def test_cross_account_and_anonymous_access(env):
    client, _, _, app = env
    gate = create_source(env)
    data = start(env, gate)
    path = BASE + "/sessions/" + data["session_id"]
    with TestClient(app, base_url="https://testserver") as other:
        assert other.get(path).status_code == 401
        assert other.post(f"/api/listening/attempts/{gate}/events", json={"events": []}).status_code == 403
        account = {"email": "other@example.com", "password": "learning-test-password-456"}
        assert other.post("/api/auth/register", json=account, headers=HEADERS).status_code == 201
        assert other.post("/api/auth/login", json=account, headers=HEADERS).status_code == 200
        assert other.get(path).status_code == 404
        assert other.get(path + "/audio").status_code == 404
        assert other.get(BASE + "/materials", params={"gate_type": "exam_attempt", "gate_id": gate}).status_code == 403
        assert other.get(BASE + "/sessions").json()["data"] == []
    assert client.get(path).status_code == 200


def test_unbound_history_and_set1_not_claimable(env):
    client, repo, user, _ = env
    old = repo.create_attempt(user, EXAM, "exam_mode", owner_id=user)
    assert client.get(BASE + "/materials", params={"gate_type": "exam_attempt", "gate_id": old["id"]}).status_code == 403
    gate = create_source(env)
    for material in ("cet6_202606_set1_u1", "invented"):
        assert client.post(BASE + "/sessions", json={"gate_type": "exam_attempt", "gate_id": gate,
            "material_id": material}, headers=HEADERS).status_code == 403


@pytest.mark.parametrize("method,suffix,body", [
    ("get", "/events", None), ("get", "/review", None),
    ("post", "/submit", None), ("put", "/answers/q1", {}),
    ("get", "/questions/q1/candidates", None),
])
def test_bound_source_legacy_routes_require_owner(env, method, suffix, body):
    _, _, _, app = env
    gate = create_source(env, False)
    with TestClient(app, base_url="https://testserver") as anonymous:
        response = anonymous.request(method, f"/api/listening/attempts/{gate}{suffix}",
                                     **({"json": body} if body is not None else {}))
        assert response.status_code == 403, response.text


def test_cp_only_unlocks_its_unit(env):
    client, repo, _, _ = env
    response = client.post("/api/listening/v2/practice/sessions", json={"material_id": UNIT, "student_id": "spoofed"})
    assert response.status_code == 200, response.text
    gate = response.json()["data"]["session_id"]
    # Fixture terminal state; the existing CP suite tests all actual stage transitions.
    repo.update_cp_session(gate, {"stage": "result_final"})
    query = {"gate_type": "cp_session", "gate_id": gate}
    assert [x["material_id"] for x in client.get(BASE + "/materials", params=query).json()["data"]] == [UNIT]
    assert client.post(BASE + "/sessions", json={**query, "material_id": "cet6_202606_set2_u2"}, headers=HEADERS).status_code == 403
    assert client.post(BASE + "/sessions", json={**query, "material_id": UNIT}, headers=HEADERS).status_code == 200


def test_pinned_content_and_release_revocation(env, monkeypatch):
    client, _, _, _ = env
    gate = create_source(env)
    original = start(env, gate)
    monkeypatch.setitem(svc.CONTENT[UNIT], "title", "Changed future title")
    restored = start(env, gate)
    assert restored == original
    path = BASE + "/sessions/" + restored["session_id"]
    monkeypatch.setattr(svc, "media_identity", lambda: {"sha256": "changed"})
    assert client.get(path + "/audio").status_code == 409
    monkeypatch.setattr(svc.v2_exam_service, "gate_allows", lambda: False)
    assert client.get(path).status_code == 403
    assert client.get(BASE + "/cards").status_code == 403


def test_owned_audio_supports_range_without_public_cache(env):
    client, _, _, _ = env
    data = start(env)
    response = client.get(data["audio"]["url"], headers={"Range": "bytes=0-127"})
    assert response.status_code == 206
    assert len(response.content) == 128
    assert response.headers["cache-control"] == "private, no-store"


def test_retry_and_foreign_segment_rejected(env):
    client, repo, _, _ = env
    data = start(env)
    path = BASE + "/sessions/" + data["session_id"]
    body = {"request_id": "retry-attempt-001", "segment_id": data["segments"][0]["id"], "text": "test"}
    for _ in range(2):
        assert client.post(path + "/attempts", json=body, headers=HEADERS).status_code == 200
    assert len(svc.events(repo, data["session_id"])) == 1
    assert client.post(path + "/attempts", json={**body, "text": "different"}, headers=HEADERS).status_code == 409
    assert client.post(path + "/attempts", json={**body, "segment_id": "foreign-segment"}, headers=HEADERS).status_code == 404


def test_private_cards_and_exactly_once_srs(env):
    client, repo, user, _ = env
    data = start(env)
    path = BASE + "/sessions/" + data["session_id"]
    _, snapshot = svc.owned(repo, user, data["session_id"])
    segment_id = next(s["id"] for s in snapshot["segments"] if s["vocabulary"])
    body = {"request_id": "card-attempt-001", "segment_id": segment_id}
    assert client.post(path + "/attempts", json=body, headers=HEADERS).status_code == 200
    data = client.post(path + "/reveal", json={**body, "request_id": "card-segment-001"}, headers=HEADERS).json()["data"]
    item = next(s for s in data["segments"] if s["id"] == segment_id)
    assert item["vocabulary"]
    payload = {"segment_id": item["id"], "vocabulary_id": item["vocabulary"][0]["id"]}
    saved = client.post(path + "/cards", json=payload, headers=HEADERS)
    assert saved.status_code == 200, saved.text
    card = saved.json()["data"]["card_id"]
    with pytest.raises(ValueError, match="aural recognition"):
        api.aural_lexicon_service.record_attempt(user, card, "hear_identify", True, repo=repo)
    assert client.post(path + "/cards", json=payload, headers=HEADERS).json()["data"]["card_id"] == card
    due = client.get(BASE + "/cards").json()["data"]
    assert len(due) == 1 and "gloss" not in due[0]
    assert repo._conn().execute("SELECT 1 FROM lex_items WHERE item_id=?", (card,)).fetchone() is None
    grade = {"review_id": "card-reveal-001", "request_id": "card-grade-001", "grade": 5}
    card_path = BASE + "/cards/" + card
    assert client.post(card_path + "/grade", json=grade, headers=HEADERS).status_code == 409
    assert client.post(card_path + "/reveal", json={"request_id": grade["review_id"]}, headers=HEADERS).status_code == 200
    for _ in range(2):
        assert client.post(card_path + "/grade", json=grade, headers=HEADERS).status_code == 200
    assert client.post(card_path + "/grade", json={**grade, "request_id": "card-grade-002"}, headers=HEADERS).status_code == 409
    assert client.get(BASE + "/cards").json()["data"] == []
    assert repo._conn().execute("SELECT repetitions FROM lex_srs WHERE student_id=? AND item_id=?", (user, card)).fetchone()[0] == 1
    with repo._conn() as conn:
        conn.execute("UPDATE lex_srs SET next_due='2000-01-01' WHERE item_id=?", (card,))
    assert client.post(card_path + "/grade", json={**grade, "request_id": "stale-cycle-001"}, headers=HEADERS).status_code == 409


def test_all_42_word_anchors_attached_once():
    exam = svc.v2_exam_service.v2_registry.get(EXAM)
    count = 0
    guidance_count = 0
    for unit in exam["units"]:
        snapshot = svc.material_snapshot(unit)
        words = [w["id"] for s in snapshot["segments"] for w in s["vocabulary"]]
        assert sorted(words) == sorted(w["id"] for w in svc.CONTENT[unit["unit_id"]]["vocabulary"])
        count += len(words)
        guidance = [g for s in snapshot["segments"] for g in s["guidance"]]
        assert len(guidance) == 2
        assert all(g["gloss"] and g["structure"] and g["transfer"] for g in guidance)
        guidance_count += len(guidance)
    assert count == 42
    assert guidance_count == 14
