"""Content correction regression; reads fixtures, uses isolated DB for HTTP writes.

These checks do not constitute teacher approval or an independent listening audit.
"""
import hashlib
import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from listening import expression_service as es, router as api
from listening.repository import StudentRepository
from listening.tools.validate_expressions import validate

ROOT = Path(__file__).resolve().parents[1] / "listening" / "data" / "expressions"
BEFORE = ROOT / "history" / "20260919_before"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def scenarios(path=ROOT):
    return {s["scenario_id"]: s for s in read(path / "scenarios.json")["scenarios"]}


def test_scope_original_sentences_and_labels_preserved():
    previous = read(BEFORE / "expressions.json")["expressions"]
    current = read(ROOT / "expressions.json")["expressions"]
    assert len(previous) == len(current) == 31
    for old, new in zip(previous, current):
        for key in old:
            if key not in ("meaning", "revision"):
                assert old[key] == new[key], (old["expression_id"], key)
        assert new["review_status"] == "pending_teacher"


def test_structure_and_revision_for_every_corrected_scenario():
    assert validate() == []
    old, new = scenarios(BEFORE), scenarios()
    assert len(new) == 62 and set(old) == set(new)
    changes = 0
    for sid, item in new.items():
        assert item["review_status"] == "pending_teacher"
        if item != old[sid]:
            changes += 1
            assert item["revision"] == old[sid].get("revision", 1) + 1
        for key, question in item["questions"].items():
            assert set(question["options"]) == set("ABCD")
            assert len(set(question["options"].values())) == 4
            # This correction does not shuffle answers underneath existing learners.
            assert question["answer"] == old[sid]["questions"][key]["answer"]
    assert changes == 39


def test_audio_changed_with_text_and_old_recordings_retained():
    old, new = scenarios(BEFORE), scenarios()
    index = read(ROOT / "audio_index.json")
    old_index = read(BEFORE / "audio_index.json")
    changes = 0
    for sid, s in new.items():
        meta = index[sid]
        assert (ROOT / meta["file"]).is_file()
        if old[sid]["text"] != s["text"]:
            changes += 1
            assert meta["file"] != old_index[sid]["file"]
            assert (ROOT / old_index[sid]["file"]).is_file()
            assert meta["content_revision"] == s["revision"]
            assert meta["text_sha256"] == hashlib.sha256(s["text"].encode()).hexdigest()
            audio = (ROOT / meta["file"]).read_bytes()
            assert len(audio) > 1000
            assert meta["audio_sha256"] == hashlib.sha256(audio).hexdigest()
        else:
            assert meta == old_index[sid]
    assert changes == 12


def test_student_report_and_time_role_qualifiers():
    data = scenarios()
    annual = data["scn_annual_leave_colleague"]
    assert "almost all my annual leave" in annual["text"]
    assert "almost all my annual leave" in annual["questions"]["meaning"]["question"]
    assert annual["questions"]["meaning"]["options"]["A"] == "年假快用完了"
    restaurant = data["scn_fully_booked_restaurant"]
    assert "fully booked at seven on Saturday" in restaurant["text"]
    assert "nine fifteen" in restaurant["text"]
    assert "周六七点" in restaurant["questions"]["meaning"]["options"]["B"]
    assert "B 打扫厨房，A 打扫卫生间，每月轮换" == data["scn_fair_chores"]["questions"]["key_info"]["options"]["A"]
    assert "later in the year" in data["scn_useup_hr"]["text"]


def test_no_invented_dosing_in_corrected_dialogues():
    data = scenarios()
    pharmacist = data["scn_interaction_pharmacist"]
    doctor = data["scn_interaction_doctor"]
    assert "take them at least two hours apart" not in pharmacist["text"]
    assert "Only on the days you take the new medicine" not in doctor["text"]
    assert "check the exact medicines" in pharmacist["text"]
    assert "check the exact medicines" in doctor["text"]
    assert "先与开药医生核对" in pharmacist["questions"]["key_info"]["options"]["B"]


@pytest.fixture
def client(tmp_path, monkeypatch):
    repo = StudentRepository(tmp_path / "student.db")
    monkeypatch.setattr(es, "student_repo", repo)
    app = FastAPI()
    app.include_router(api.router)
    with TestClient(app) as c:
        yield c, repo


@pytest.mark.parametrize("revision", [None, 1, 999])
def test_old_question_page_cannot_submit_new_content(client, revision):
    c, repo = client
    payload = {"student_id": "revision-test", "answers": {"scene": "B", "meaning": "C", "key_info": "B"}}
    if revision is not None:
        payload["content_revision"] = revision
    response = c.post("/api/listening/expressions/scenarios/scn_fully_booked_hotel/submit", json=payload)
    assert response.status_code == 409
    assert repo.list_expression_attempts("revision-test") == []
    suffix = "" if revision is None else f"?revision={revision}"
    assert c.get("/api/listening/expressions/scenarios/scn_fully_booked_hotel/audio" + suffix).status_code == 409
    assert c.post("/api/listening/expressions/scenarios/scn_fully_booked_hotel/reveal-early" + suffix).status_code == 409


def test_current_question_page_audio_and_submit(client):
    c, repo = client
    detail = c.get("/api/listening/expressions/exp_fully_booked").json()["data"]
    s = next(s for s in detail["scenarios"] if s["scenario_id"] == "scn_fully_booked_hotel")
    assert s["content_revision"] == 2
    assert "text" not in s and "answer" not in s["questions"]["scene"]
    path = "/api/listening/expressions/scenarios/scn_fully_booked_hotel"
    assert c.get(path + "/audio?revision=2", headers={"Range": "bytes=0-127"}).status_code == 206
    assert c.post(path + "/reveal-early?revision=2").status_code == 200
    response = c.post(path + "/submit", json={"student_id": "revision-test", "content_revision": 2,
        "answers": {"scene": "B", "meaning": "C", "key_info": "B"}})
    assert response.status_code == 200
    assert response.json()["data"]["correct"]["all"] is True
    assert repo.list_expression_attempts("revision-test")[0]["content_revision"] == 2
