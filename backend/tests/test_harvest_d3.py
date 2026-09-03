# -*- coding: utf-8 -*-
"""D3 红线契约测试 (Work Order E).

覆盖：
  A. exam_attempt 门：已提交 → 允许；未提交 → 403
  B. cp_session 门：result_final → 允许；first_pass → 403
  C. 幂等：同一词条两次采集 → 第二次 already_tracked=True
  D. 响应字段白名单：无 ability 结论
  E. API 端点同步测试
  F. 无效 gate_type → 422
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["ALLOW_UNRELEASED_LISTENING_V2"] = "true"

from fastapi import FastAPI
from fastapi.testclient import TestClient

from listening import router as listening_router_mod
from listening import aural_lexicon_service as svc
from listening.repository import StudentRepository


# ── 夹具 ───────────────────────────────────────────────────────────────

SAMPLE_ITEM = {
    "item_id": "lex_L1_harvest01",
    "layer": "L1",
    "surface": "atmosphere",
    "gloss": None,
    "source_set": 2,
    "source_status": "machine",
    "provenance": "test",
    "sealed_source": 0,
}

SAMPLE_ITEM_2 = {
    "item_id": "lex_L1_harvest02",
    "layer": "L1",
    "surface": "innovative",
    "gloss": None,
    "source_set": 2,
    "source_status": "machine",
    "provenance": "test",
    "sealed_source": 0,
}


def _insert_lex_item(repo, item):
    now = datetime.now(timezone.utc).isoformat()
    repo._conn().execute(
        """INSERT OR IGNORE INTO lex_items
           (item_id,layer,surface,gloss,source_set,source_status,
            provenance,sealed_source,created_at)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (item["item_id"], item["layer"], item["surface"], item.get("gloss"),
         item["source_set"], item["source_status"],
         item.get("provenance", ""), item.get("sealed_source", 0), now),
    )
    repo._conn().commit()


def _make_submitted_attempt(repo, student_id="stu1", exam_id="exam_set2"):
    """在 DB 中创建并提交一个答题记录，返回 attempt_id。"""
    attempt = repo.create_attempt(student_id, exam_id, "exam")
    repo.submit_attempt(attempt["id"], score=20)
    return attempt["id"]


def _make_unsubmitted_attempt(repo, student_id="stu2", exam_id="exam_set2"):
    attempt = repo.create_attempt(student_id, exam_id, "exam")
    return attempt["id"]


def _make_cp_session(repo, stage, student_id="stu3"):
    """创建 cp_session 并将 stage 设置为指定值。"""
    session = repo.create_cp_session(
        student_id=student_id,
        material_id="mat_set2_01",
        manifest={"unit_ids": []},
        round2_order={},
    )
    repo.update_cp_session(session["id"], {"stage": stage})
    return session["id"]


class HarvestD3TestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.repo = StudentRepository(Path(self._tmp.name) / "test.db")
        self._orig_repo = svc.student_repo
        svc.student_repo = self.repo

        app = FastAPI()
        app.include_router(listening_router_mod.router)
        self.client = TestClient(app)

        _insert_lex_item(self.repo, SAMPLE_ITEM)
        _insert_lex_item(self.repo, SAMPLE_ITEM_2)
        self.addCleanup(self._restore)

    def _restore(self):
        conn = getattr(self.repo._local, "conn", None)
        if conn:
            conn.close()
            self.repo._local.conn = None
        svc.student_repo = self._orig_repo
        self._tmp.cleanup()


# ── A. exam_attempt 门 ─────────────────────────────────────────────────

class TestExamAttemptGate(HarvestD3TestBase):

    def test_submitted_attempt_allows_harvest(self):
        """已提交答卷 → harvest 成功。"""
        attempt_id = _make_submitted_attempt(self.repo)
        result = svc.harvest_word(
            student_id="stu1",
            item_id=SAMPLE_ITEM["item_id"],
            gate_type="exam_attempt",
            gate_id=attempt_id,
            repo=self.repo,
        )
        self.assertTrue(result["harvested"])
        self.assertFalse(result["already_tracked"])
        self.assertEqual(result["surface"], "atmosphere")

    def test_unsubmitted_attempt_blocks_harvest(self):
        """未提交答卷 → ValueError D3_GATE_BLOCKED。"""
        attempt_id = _make_unsubmitted_attempt(self.repo)
        with self.assertRaises(ValueError) as ctx:
            svc.harvest_word(
                student_id="stu2",
                item_id=SAMPLE_ITEM["item_id"],
                gate_type="exam_attempt",
                gate_id=attempt_id,
                repo=self.repo,
            )
        self.assertIn("D3_GATE_BLOCKED", str(ctx.exception))

    def test_nonexistent_attempt_blocks(self):
        """attempt_id 不存在 → D3_GATE_BLOCKED。"""
        with self.assertRaises(ValueError) as ctx:
            svc.harvest_word(
                student_id="stu1",
                item_id=SAMPLE_ITEM["item_id"],
                gate_type="exam_attempt",
                gate_id="nonexistent_id",
                repo=self.repo,
            )
        self.assertIn("D3_GATE_BLOCKED", str(ctx.exception))


# ── B. cp_session 门 ───────────────────────────────────────────────────

class TestCpSessionGate(HarvestD3TestBase):

    def test_result_final_allows_harvest(self):
        """cp_session.stage = result_final → harvest 成功。"""
        session_id = _make_cp_session(self.repo, stage="result_final")
        result = svc.harvest_word(
            student_id="stu3",
            item_id=SAMPLE_ITEM["item_id"],
            gate_type="cp_session",
            gate_id=session_id,
            repo=self.repo,
        )
        self.assertTrue(result["harvested"])

    def test_first_pass_blocks_harvest(self):
        """cp_session.stage = first_pass → D3_GATE_BLOCKED。"""
        session_id = _make_cp_session(self.repo, stage="first_pass",
                                      student_id="stu4")
        with self.assertRaises(ValueError) as ctx:
            svc.harvest_word(
                student_id="stu4",
                item_id=SAMPLE_ITEM["item_id"],
                gate_type="cp_session",
                gate_id=session_id,
                repo=self.repo,
            )
        self.assertIn("D3_GATE_BLOCKED", str(ctx.exception))

    def test_intro_blocks_harvest(self):
        """cp_session.stage = intro（默认）→ D3_GATE_BLOCKED。"""
        session_id = _make_cp_session(self.repo, stage="intro",
                                      student_id="stu5")
        with self.assertRaises(ValueError):
            svc.harvest_word(
                student_id="stu5",
                item_id=SAMPLE_ITEM["item_id"],
                gate_type="cp_session",
                gate_id=session_id,
                repo=self.repo,
            )


# ── C. 幂等 ─────────────────────────────────────────────────────────────

class TestHarvestIdempotent(HarvestD3TestBase):

    def test_second_harvest_returns_already_tracked(self):
        """同一词条两次采集：第二次 harvested=False, already_tracked=True。"""
        attempt_id = _make_submitted_attempt(self.repo)
        svc.harvest_word("stu1", SAMPLE_ITEM["item_id"],
                         "exam_attempt", attempt_id, repo=self.repo)
        r2 = svc.harvest_word("stu1", SAMPLE_ITEM["item_id"],
                               "exam_attempt", attempt_id, repo=self.repo)
        self.assertFalse(r2["harvested"])
        self.assertTrue(r2["already_tracked"])

    def test_harvest_adds_to_srs_once(self):
        """重复采集后 lex_srs 里只有一条记录。"""
        attempt_id = _make_submitted_attempt(self.repo, student_id="stu6")
        for _ in range(3):
            svc.harvest_word("stu6", SAMPLE_ITEM["item_id"],
                             "exam_attempt", attempt_id, repo=self.repo)
        count = self.repo._conn().execute(
            "SELECT count(*) as c FROM lex_srs WHERE student_id='stu6' AND item_id=?",
            (SAMPLE_ITEM["item_id"],)
        ).fetchone()["c"]
        self.assertEqual(count, 1)


# ── D. 响应字段白名单 ──────────────────────────────────────────────────

class TestHarvestDTOContract(HarvestD3TestBase):

    def test_no_ability_fields_in_response(self):
        """harvest_word 响应不含 ability 结论字段。"""
        attempt_id = _make_submitted_attempt(self.repo, student_id="stu7")
        result = svc.harvest_word(
            "stu7", SAMPLE_ITEM["item_id"],
            "exam_attempt", attempt_id, repo=self.repo,
        )
        forbidden = {"understanding_stable", "ability_improved",
                     "diagnosis", "material_mastered"}
        self.assertFalse(forbidden & set(result.keys()))

    def test_response_contains_required_fields(self):
        """harvest_word 响应包含必要字段。"""
        attempt_id = _make_submitted_attempt(self.repo, student_id="stu8")
        result = svc.harvest_word(
            "stu8", SAMPLE_ITEM["item_id"],
            "exam_attempt", attempt_id, repo=self.repo,
        )
        for key in ("harvested", "already_tracked", "item_id", "surface"):
            self.assertIn(key, result)


# ── E. API 端点同步测试 ────────────────────────────────────────────────

class TestHarvestAPI(HarvestD3TestBase):

    def test_api_submitted_attempt_200(self):
        """API POST /lexicon/harvest：已提交 → 200。"""
        attempt_id = _make_submitted_attempt(self.repo, student_id="stu9")
        r = self.client.post("/api/listening/lexicon/harvest", json={
            "student_id": "stu9",
            "item_id": SAMPLE_ITEM["item_id"],
            "gate_type": "exam_attempt",
            "gate_id": attempt_id,
        })
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["data"]["harvested"])

    def test_api_unsubmitted_attempt_403(self):
        """API POST /lexicon/harvest：未提交 → 403。"""
        attempt_id = _make_unsubmitted_attempt(self.repo, student_id="stu10")
        r = self.client.post("/api/listening/lexicon/harvest", json={
            "student_id": "stu10",
            "item_id": SAMPLE_ITEM["item_id"],
            "gate_type": "exam_attempt",
            "gate_id": attempt_id,
        })
        self.assertEqual(r.status_code, 403)

    def test_api_result_final_session_200(self):
        """API POST /lexicon/harvest：cp result_final → 200。"""
        session_id = _make_cp_session(self.repo, stage="result_final",
                                      student_id="stu11")
        r = self.client.post("/api/listening/lexicon/harvest", json={
            "student_id": "stu11",
            "item_id": SAMPLE_ITEM_2["item_id"],
            "gate_type": "cp_session",
            "gate_id": session_id,
        })
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["data"]["harvested"])

    def test_api_get_all_items(self):
        """GET /lexicon/items 返回 lex_items 列表。"""
        r = self.client.get("/api/listening/lexicon/items")
        self.assertEqual(r.status_code, 200)
        items = r.json()["data"]
        self.assertIsInstance(items, list)
        surfaces = [it["surface"] for it in items]
        self.assertIn("atmosphere", surfaces)


# ── F. 无效 gate_type → 422 ──────────────────────────────────────────

class TestInvalidGateType(HarvestD3TestBase):

    def test_invalid_gate_type_raises(self):
        """无效 gate_type → ValueError。"""
        with self.assertRaises(ValueError):
            svc.harvest_word(
                "stu1", SAMPLE_ITEM["item_id"],
                gate_type="bad_type", gate_id="any",
                repo=self.repo,
            )

    def test_api_invalid_gate_type_422(self):
        """API POST /lexicon/harvest：无效 gate_type → 422。"""
        r = self.client.post("/api/listening/lexicon/harvest", json={
            "student_id": "stu1",
            "item_id": SAMPLE_ITEM["item_id"],
            "gate_type": "bad_type",
            "gate_id": "any",
        })
        self.assertEqual(r.status_code, 422)


if __name__ == "__main__":
    unittest.main(verbosity=2)
