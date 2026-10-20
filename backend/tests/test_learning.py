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
    for module in (repository, api, api.service, svc.v2_practice_service):
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


def test_cet4_submitted_attempt_unlocks_eight_learning_units(env):
    client, _, _, _ = env
    exam_id = "cet4_202606_set2_v2"
    response = client.post("/api/listening/attempts", json={
        "exam_id": exam_id, "student_id": "spoofed", "mode": "exam_mode"})
    assert response.status_code == 200, response.text
    gate = response.json()["data"]["id"]
    submitted = client.post(f"/api/listening/attempts/{gate}/submit")
    assert submitted.status_code == 200, submitted.text
    query = {"gate_type": "exam_attempt", "gate_id": gate}
    materials = client.get(BASE + "/materials", params=query)
    assert materials.status_code == 200, materials.text
    assert len(materials.json()["data"]) == 8
    unit_id = "cet4_202606_set2_u1"
    session = client.post(BASE + "/sessions", json={**query, "material_id": unit_id}, headers=HEADERS)
    assert session.status_code == 200, session.text
    audio = session.json()["data"]["audio"]
    candidate = json.loads((svc.v2_exam_service.DATA_DIR / "v2_full" / "cet4_202606_set2.candidate.json").read_text(encoding="utf-8"))
    bounds = candidate["units"][0]["learning_audio_bounds"]
    assert audio["scope"] == "whole_unit"
    assert (audio["start_ms"], audio["end_ms"]) == (bounds["start_ms"], bounds["end_ms"])
    practice = client.get("/api/listening/v2/practice/materials")
    assert practice.status_code == 200
    assert all(not item["material_id"].startswith("cet4") for item in practice.json()["data"])


def test_cet4_set1_exam_explanations_and_sentence_learning(env):
    client, _, _, _ = env
    exam_id = "cet4_202606_set1_v2"
    summaries = client.get("/api/listening/v2/exams").json()["data"]
    summary = next(item for item in summaries if item["id"] == exam_id)
    assert summary["exam_type"] == "cet4"
    assert (summary["question_count"], summary["unit_count"], summary["has_audio"]) == (25, 8, True)
    paper = client.get(f"/api/listening/v2/exams/{exam_id}/paper").json()["data"]
    assert [len(u["questions"]) for u in paper["units"]] == [2, 2, 3, 4, 4, 3, 3, 4]
    assert "correct_answer" not in json.dumps(paper)
    response = client.post("/api/listening/attempts", json={
        "exam_id": exam_id, "student_id": "spoofed", "mode": "exam_mode"})
    assert response.status_code == 200, response.text
    attempt_id = response.json()["data"]["id"]
    explanation_path = f"/api/listening/v2/attempts/{attempt_id}/explanations"
    assert client.get(explanation_path).status_code == 409
    submitted = client.post(f"/api/listening/attempts/{attempt_id}/submit")
    assert submitted.status_code == 200, submitted.text
    explanations = client.get(explanation_path)
    assert explanations.status_code == 200, explanations.text
    explanation_rows = explanations.json()["data"]
    assert len(explanation_rows) == 25
    assert all("【录音原句】" in row["source_explanation"] for row in explanation_rows)
    assert all("🎧【发音提示】" in row["source_explanation"] for row in explanation_rows)
    query = {"gate_type": "exam_attempt", "gate_id": attempt_id}
    materials = client.get(BASE + "/materials", params=query)
    assert materials.status_code == 200, materials.text
    assert len(materials.json()["data"]) == 8
    session = client.post(BASE + "/sessions", json={**query,
        "material_id": "cet4_202606_set1_u1"}, headers=HEADERS)
    assert session.status_code == 200, session.text
    state = session.json()["data"]
    assert len(state["segments"]) == 9
    assert all("text" not in item for item in state["segments"])
    segment_id = state["segments"][0]["id"]
    endpoint = BASE + "/sessions/" + state["session_id"]
    assert client.post(endpoint + "/attempts", json={"request_id": "c4s1-attempt",
        "segment_id": segment_id, "text": "A man was left"}, headers=HEADERS).status_code == 200
    reveal = client.post(endpoint + "/reveal", json={"request_id": "c4s1-reveal",
        "segment_id": segment_id}, headers=HEADERS)
    assert reveal.status_code == 200, reveal.text
    assert reveal.json()["data"]["segments"][0]["text"].startswith("A man was left")


def test_cet4_set1_all_learning_notes_attached():
    exam_id = "cet4_202606_set1_v2"
    candidate = svc.v2_exam_service.v2_registry.get(exam_id)
    snapshots = [svc.material_snapshot(unit, exam_id) for unit in candidate["units"]]
    assert sum(len(s["segments"]) for s in snapshots) == 133
    assert sum(len(seg["vocabulary"]) for s in snapshots for seg in s["segments"]) == 48
    assert sum(len(seg["guidance"]) for s in snapshots for seg in s["segments"]) == 16
    assert sum(len(seg["sound_notes"]) for s in snapshots for seg in s["segments"]) >= 48
    for snapshot in snapshots:
        assert snapshot["audio"]["scope"] == "whole_unit"
        assert all(seg["start_ms"] < seg["end_ms"] for seg in snapshot["segments"])


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
    monkeypatch.setattr(svc, "media_identity", lambda *args, **kwargs: {"sha256": "changed"})
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


def test_learnable_exams_have_ordered_sentence_timing_before_reveal():
    for exam_id in ("cet4_202606_set1_v2", "cet4_202606_set2_v2", "cet6_202606_set1_v2", "cet6_202606_set2_v2"):
        exam = svc.v2_exam_service.v2_registry.get(exam_id)
        assert exam
        for unit in exam["units"]:
            snapshot = svc.material_snapshot(unit, exam_id)
            assert snapshot["audio"]["scope"] == "whole_unit"
            assert snapshot["audio"]["sentence_timing"] == "machine_aligned"
            previous_start = -1
            previous_end = -1
            for segment in snapshot["segments"]:
                start, end = segment["start_ms"], segment["end_ms"]
                assert isinstance(start, int) and isinstance(end, int)
                assert previous_start < start < end
                if exam_id in ("cet4_202606_set1_v2", "cet6_202606_set1_v2"):
                    assert previous_end <= start
                else:
                    assert previous_end < end
                assert segment["timing_status"] in ("machine_aligned", "needs_check")
                previous_start, previous_end = start, end
            # CET6 u1 deliberately keeps its manually reviewed whole-unit bounds.
            assert abs(snapshot["audio"]["start_ms"] - snapshot["segments"][0]["start_ms"]) <= 1000
            assert snapshot["audio"]["end_ms"] >= snapshot["segments"][-1]["end_ms"]


def test_cet4_set1_audio_gap_is_disclosed_without_scoring_missing_words():
    exam = svc.v2_exam_service.v2_registry.get("cet4_202606_set1_v2")
    unit = next(unit for unit in exam["units"] if unit["unit_id"].endswith("_u8"))
    snapshot = svc.material_snapshot(unit, "cet4_202606_set1_v2")
    first = snapshot["segments"][0]
    assert first["audio_warning"]
    assert first["text"].startswith("… as they age")
    assert "People looking" not in first["text"]
    assert first["timing_status"] == "machine_aligned"


def test_v2_explanations_are_owner_only_and_post_submit(env):
    client, repo, _, app = env
    path = "/api/listening/v2/attempts/"
    for exam_id in ("cet4_202606_set2_v2", "cet6_202606_set1_v2", "cet6_202606_set2_v2"):
        created = client.post("/api/listening/attempts", json={
            "exam_id": exam_id, "student_id": "spoofed", "mode": "exam_mode"})
        assert created.status_code == 200, created.text
        attempt_id = created.json()["data"]["id"]
        endpoint = path + attempt_id + "/explanations"
        assert client.get(endpoint).status_code == 409
        with TestClient(app, base_url="https://testserver") as other:
            assert other.get(endpoint).status_code == 403
            account = {"email": f"other-{exam_id}@example.com", "password": "other-test-password-123"}
            assert other.post("/api/auth/register", json=account, headers=HEADERS).status_code == 201
            assert other.post("/api/auth/login", json=account, headers=HEADERS).status_code == 200
            assert other.get(endpoint).status_code == 403
        first = svc.v2_exam_service.v2_registry.get(exam_id)["questions"][0]
        repo.upsert_answer(attempt_id, first["question_id"], {"final_answer": "B"})
        with repo._conn() as conn:
            conn.execute("UPDATE attempts SET submitted_at=? WHERE id=?", (repository._now(), attempt_id))
        response = client.get(endpoint)
        assert response.status_code == 200, response.text
        rows = response.json()["data"]
        assert len(rows) == 25
        assert [item["number"] for item in rows] == list(range(1, 26))
        assert rows[0]["your_answer"] == "B"
        assert rows[1]["your_answer"] is None
        assert all(item["source_explanation"] and item["distractor_analysis"] for item in rows)
        assert all("🎧【连读提醒】" in item["source_explanation"] for item in rows)


def test_cet6_set1_sentence_cards_cover_every_unit():
    exam_id = "cet6_202606_set1_v2"
    exam = svc.v2_exam_service.v2_registry.get(exam_id)
    assert len(exam["questions"]) == 25
    assert len(exam["units"]) == 7
    for unit in exam["units"]:
        snapshot = svc.material_snapshot(unit, exam_id)
        words = [word["id"] for segment in snapshot["segments"] for word in segment["vocabulary"]]
        guidance = [note for segment in snapshot["segments"] for note in segment["guidance"]]
        assert len(words) == 6
        assert len(set(words)) == 6
        assert len(guidance) == 2
        assert all(segment["start_ms"] < segment["end_ms"] for segment in snapshot["segments"])


def test_cet6_v2_legacy_explanation_keys_match():
    from listening import v2_explanation_service
    exam = svc.v2_exam_service.v2_registry.get("cet6_202606_set2_v2")
    result = v2_explanation_service.explanations_for({"exam_id": "cet6_202606_set2_v2"}, [])
    assert len(result) == 25
    assert [(x["number"], x["correct_answer"]) for x in result] == [
        (q["number"], q["correct_answer"]) for q in exam["questions"]]


def test_cet4_explanation_source_and_sound_note_match():
    import re
    from listening.learning_content import SOUND_NOTES
    path = svc.v2_exam_service.V2_DIR / "cet4_202606_set2.explanations.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    candidate = svc.v2_exam_service.v2_registry.get("cet4_202606_set2_v2")
    segments = {s["segment_id"]: s["text"] for u in candidate["units"]
                for s in u["transcript"]["segments"]}
    for q, row in zip(candidate["questions"], data["questions"], strict=True):
        assert row["correct_answer"] == q["correct_answer"]
        source = segments[row["source_segment_id"]]
        assert source
        cleaned = re.sub(r"\[\d+(?:-\d+)?\]", "", source).strip()
        cleaned = re.sub(r"\s{2,}", " ", cleaned)
        assert cleaned in row["source_explanation"]
        unit = row["source_segment_id"].rsplit("_seg", 1)[0]
        sound = next(n for n in SOUND_NOTES[unit] if n["id"] == row["sound_note_id"])
        assert sound["segment_id"] == row["source_segment_id"]
        assert sound["note"] in row["source_explanation"]


def test_sound_pair_does_not_skip_spoken_numbers():
    from listening.tools.check_learning_notes import pair_in_anchor
    assert not pair_in_anchor(["spent", "years"], "spent 102 years")
    assert pair_in_anchor(["months", "after"], "months after")
    assert pair_in_anchor(["turned", "off"], "[12-2]turned off")
