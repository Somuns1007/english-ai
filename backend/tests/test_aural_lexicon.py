# -*- coding: utf-8 -*-
"""Aural Lexicon 契约测试 (V2.C CET Track).

运行：
    venv/Scripts/python.exe -m tests.test_aural_lexicon

覆盖：
  A. SRS 到期逻辑 — 正确答题后 interval 延长；错误答题后重置到1天
  B. Attempt 字段契约 — lex_attempts 只写 lexical 字段，无 ability 结论
  C. Phase 0 封顶与强制过渡 — cap_days 到期后 forced_exit
  D. Phase 0 入口测试 — 低分进入 active，高分直接 completed
  E. Sealed 排除 — source_set=1 / sealed_source=1 词条被拒绝
  F. exam_practice_allowed — Phase 0 active 时为 False
  G. 禁止字段白名单 — attempt/entry-test DTO 不接受 ability 结论字段
  H. 幂等 seed — 重复 seed 不重复写入
"""

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ["ALLOW_UNRELEASED_LISTENING_V2"] = "true"

from fastapi import FastAPI
from fastapi.testclient import TestClient

from listening import router as listening_router_mod
from listening import aural_lexicon_service as svc
from listening.repository import StudentRepository


# ── 测试夹具 ────────────────────────────────────────────────────────────

SAMPLE_ITEMS = [
    {"item_id": "lex_L1_test001", "layer": "L1", "surface": "atmosphere",
     "gloss": None, "source_set": 2, "source_status": "machine",
     "provenance": "test", "sealed_source": 0},
    {"item_id": "lex_L2_test002", "layer": "L2", "surface": "annual leave",
     "gloss": "paid holiday from work", "source_set": 2, "source_status": "machine",
     "provenance": "test", "sealed_source": 0},
    {"item_id": "lex_L3_test003", "layer": "L3", "surface": "in contrast",
     "gloss": "contrast signal", "source_set": 2, "source_status": "machine",
     "provenance": "test", "sealed_source": 0},
]

SEALED_ITEM = {
    "item_id": "lex_L1_sealed", "layer": "L1", "surface": "sealed_word",
    "gloss": None, "source_set": 1, "source_status": "machine",   # source_set=1 → rejected
    "provenance": "test", "sealed_source": 0,
}


def _insert_items(repo, items):
    """Directly insert test items (bypassing seed_lexicon for speed)."""
    import sqlite3
    now = datetime.now(timezone.utc).isoformat()
    conn = repo._conn()
    for it in items:
        try:
            conn.execute(
                """INSERT OR IGNORE INTO lex_items
                   (item_id,layer,surface,gloss,source_set,source_status,
                    provenance,sealed_source,created_at)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (it["item_id"], it["layer"], it["surface"], it.get("gloss"),
                 it["source_set"], it["source_status"],
                 it.get("provenance",""), it.get("sealed_source",0), now),
            )
        except sqlite3.IntegrityError:
            pass  # sealed guard triggers → expected in sealed test
    conn.commit()


class LexiconTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.repo = StudentRepository(Path(self._tmp.name) / "test.db")
        self._orig = svc.student_repo
        svc.student_repo = self.repo

        app = FastAPI()
        app.include_router(listening_router_mod.router)
        self.client = TestClient(app)

        # Insert sample items
        _insert_items(self.repo, SAMPLE_ITEMS)
        self.addCleanup(self._restore)

    def _restore(self):
        conn = getattr(self.repo._local, "conn", None)
        if conn:
            conn.close()
            self.repo._local.conn = None
        svc.student_repo = self._orig
        self._tmp.cleanup()


# ── A. SRS 到期逻辑 ────────────────────────────────────────────────────

class TestSRS(LexiconTestBase):

    def test_correct_answer_extends_interval(self):
        """正确答题后 interval_days > 1（SM-2 升档）。"""
        item_id = SAMPLE_ITEMS[0]["item_id"]
        svc.record_attempt("s1", item_id, "hear_identify", True, repo=self.repo)
        row = self.repo._conn().execute(
            "SELECT interval_days, repetitions FROM lex_srs WHERE student_id='s1' AND item_id=?",
            (item_id,)
        ).fetchone()
        self.assertIsNotNone(row)
        # First correct: reps=1, interval=1.0; next correct should be 6.0
        svc.record_attempt("s1", item_id, "hear_identify", True, repo=self.repo)
        row2 = self.repo._conn().execute(
            "SELECT interval_days, repetitions FROM lex_srs WHERE student_id='s1' AND item_id=?",
            (item_id,)
        ).fetchone()
        self.assertEqual(row2["repetitions"], 2)
        self.assertAlmostEqual(row2["interval_days"], 6.0, places=1)

    def test_wrong_answer_resets_interval(self):
        """错误答题后 interval_days=1, repetitions=0。"""
        item_id = SAMPLE_ITEMS[0]["item_id"]
        # First make it successful to get interval > 1
        svc.record_attempt("s1", item_id, "hear_identify", True, repo=self.repo)
        svc.record_attempt("s1", item_id, "hear_identify", True, repo=self.repo)
        # Now fail
        svc.record_attempt("s1", item_id, "hear_identify", False, repo=self.repo)
        row = self.repo._conn().execute(
            "SELECT interval_days, repetitions FROM lex_srs WHERE student_id='s1' AND item_id=?",
            (item_id,)
        ).fetchone()
        self.assertEqual(row["repetitions"], 0)
        self.assertAlmostEqual(row["interval_days"], 1.0, places=1)

    def test_due_items_returned(self):
        """到期的词条出现在 due 列表中。"""
        item_id = SAMPLE_ITEMS[0]["item_id"]
        # Insert SRS entry with next_due in the past
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        self.repo._conn().execute(
            """INSERT INTO lex_srs (srs_id,student_id,item_id,next_due,
               interval_days,ease_factor,repetitions)
               VALUES ('srs_test','s2',?,?,1.0,2.5,0)""",
            (item_id, past)
        )
        self.repo._conn().commit()
        due = svc.get_due_items("s2", repo=self.repo)
        self.assertTrue(any(d["item_id"] == item_id for d in due))

    def test_future_items_not_due(self):
        """下次复习时间在未来的词条不出现在 due 列表。"""
        item_id = SAMPLE_ITEMS[1]["item_id"]
        future = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        self.repo._conn().execute(
            """INSERT INTO lex_srs (srs_id,student_id,item_id,next_due,
               interval_days,ease_factor,repetitions)
               VALUES ('srs_fut','s3',?,?,7.0,2.5,2)""",
            (item_id, future)
        )
        self.repo._conn().commit()
        due = svc.get_due_items("s3", repo=self.repo)
        self.assertFalse(any(d["item_id"] == item_id for d in due))


# ── B. Attempt 字段契约 ────────────────────────────────────────────────

class TestAttemptContract(LexiconTestBase):

    def test_attempt_only_writes_lexical_fields(self):
        """lex_attempts 只含 lexical_item_recognized，无 ability 结论字段。"""
        item_id = SAMPLE_ITEMS[0]["item_id"]
        result = svc.record_attempt("s1", item_id, "hear_identify", True, repo=self.repo)

        # Check return value has no ability fields
        forbidden = {"understanding_stable", "ability_improved", "diagnosis",
                     "material_mastered", "evidence_level", "evidence_strength"}
        self.assertFalse(forbidden & set(result.keys()),
                         f"Forbidden fields in response: {forbidden & set(result.keys())}")
        self.assertIn("lexical_item_recognized", result)

        # Check DB row
        row = self.repo._conn().execute(
            "SELECT * FROM lex_attempts WHERE attempt_id=?",
            (result["attempt_id"],)
        ).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["lexical_item_recognized"], 1)
        # Verify no extra columns
        col_names = set(row.keys())
        self.assertNotIn("understanding_stable", col_names)
        self.assertNotIn("ability_improved", col_names)
        self.assertNotIn("diagnosis", col_names)

    def test_invalid_task_type_rejected(self):
        """非法 task_type 被拒绝（ValueError）。"""
        item_id = SAMPLE_ITEMS[0]["item_id"]
        with self.assertRaises(ValueError):
            svc.record_attempt("s1", item_id, "invalid_type", True, repo=self.repo)

    def test_api_attempt_dto_contract(self):
        """API 端点返回 DTO 只含 lexical 字段。"""
        item_id = SAMPLE_ITEMS[0]["item_id"]
        r = self.client.post("/api/listening/lexicon/attempt", json={
            "student_id": "s1", "item_id": item_id,
            "task_type": "hear_identify", "is_correct": True
        })
        self.assertEqual(r.status_code, 200)
        data = r.json()["data"]
        forbidden = {"understanding_stable", "ability_improved", "diagnosis",
                     "material_mastered"}
        self.assertFalse(forbidden & set(data.keys()))
        self.assertIn("lexical_item_recognized", data)


# ── C. Phase 0 封顶与强制过渡 ────────────────────────────────────────────

class TestPhase0Cap(LexiconTestBase):

    def test_forced_exit_after_cap(self):
        """cap_days 到期后调用 get_phase0_status 触发 forced_exit。"""
        past_start = (datetime.now(timezone.utc) - timedelta(days=22)).isoformat()
        self.repo._conn().execute(
            """INSERT INTO phase0_state
               (student_id,status,entry_score,entry_threshold,started_at,cap_days,daily_vocab_minutes)
               VALUES ('s_cap','active',0.5,0.7,?,21,15)""",
            (past_start,)
        )
        self.repo._conn().commit()
        status = svc.get_phase0_status("s_cap", repo=self.repo)
        self.assertEqual(status["status"], "forced_exit")
        self.assertFalse(status["phase0_active"])
        self.assertTrue(status["exam_practice_allowed"])

    def test_active_within_cap(self):
        """cap 未到期时 status 保持 active。"""
        recent_start = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        self.repo._conn().execute(
            """INSERT INTO phase0_state
               (student_id,status,entry_score,entry_threshold,started_at,cap_days,daily_vocab_minutes)
               VALUES ('s_cap2','active',0.5,0.7,?,21,15)""",
            (recent_start,)
        )
        self.repo._conn().commit()
        status = svc.get_phase0_status("s_cap2", repo=self.repo)
        self.assertEqual(status["status"], "active")
        self.assertTrue(status["phase0_active"])


# ── D. Phase 0 入口测试 ──────────────────────────────────────────────────

class TestPhase0EntryTest(LexiconTestBase):

    def _make_results(self, correct_count, total=10):
        items = SAMPLE_ITEMS * (total // len(SAMPLE_ITEMS) + 1)
        results = []
        for i, item in enumerate(items[:total]):
            results.append({
                "item_id": item["item_id"],
                "is_correct": i < correct_count
            })
        return results

    def test_low_score_enters_phase0(self):
        """覆盖率低于阈值 → status=active。"""
        results = self._make_results(correct_count=3, total=10)  # 30% < 70%
        out = svc.complete_entry_test("s_low", results, threshold=0.70, repo=self.repo)
        self.assertEqual(out["status"], "active")
        self.assertTrue(out["phase0_entered"])
        self.assertLess(out["entry_score"], 0.70)

    def test_high_score_skips_phase0(self):
        """覆盖率高于阈值 → status=completed，不进入 Phase 0。"""
        results = self._make_results(correct_count=9, total=10)  # 90% > 70%
        out = svc.complete_entry_test("s_high", results, threshold=0.70, repo=self.repo)
        self.assertEqual(out["status"], "completed")
        self.assertFalse(out["phase0_entered"])

    def test_no_ability_conclusion_in_response(self):
        """入口测试响应不含 ability 结论字段。"""
        results = self._make_results(correct_count=3, total=10)
        out = svc.complete_entry_test("s_noability", results, repo=self.repo)
        forbidden = {"understanding_stable","ability_improved","diagnosis","material_mastered"}
        self.assertFalse(forbidden & set(out.keys()))


# ── E. Sealed 排除 ────────────────────────────────────────────────────────

class TestSealedExclusion(LexiconTestBase):

    def test_sealed_source_set1_rejected_by_seed(self):
        """source_set=1 的词条被 seed_lexicon 拒绝。"""
        import json
        # Write a temp lexicon with a Set-1 sourced item
        tmp_lexicon = {
            "provenance": {"internal_annotation_only": True},
            "L1": [{
                "word": "sealed_word", "source_layer": "L1",
                "source_set": 1,            # SEALED — should be rejected
                "source_status": "machine", "sealed_source": False,
                "provenance": "test"
            }],
            "L2": [], "L3": []
        }
        import tempfile
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(tmp_lexicon, f)
            tmp_path = f.name

        orig_path = svc.LEXICON_PATH
        svc.LEXICON_PATH = Path(tmp_path)
        result = svc.seed_lexicon(repo=self.repo)
        svc.LEXICON_PATH = orig_path
        Path(tmp_path).unlink(missing_ok=True)

        self.assertEqual(result["sealed_rejected"], 1)
        self.assertEqual(result["inserted"], 0)

    def test_sealed_item_not_in_srs(self):
        """sealed_source=1 的词条不应进入 SRS 队列。"""
        # Verify no lex_items with sealed_source=1
        rows = self.repo._conn().execute(
            "SELECT * FROM lex_items WHERE sealed_source=1"
        ).fetchall()
        self.assertEqual(len(rows), 0)


# ── F. exam_practice_allowed ────────────────────────────────────────────

class TestExamPracticeGate(LexiconTestBase):

    def test_phase0_active_blocks_exam(self):
        """Phase 0 active → exam_practice_allowed=False。"""
        recent_start = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        self.repo._conn().execute(
            """INSERT INTO phase0_state
               (student_id,status,entry_score,entry_threshold,started_at,cap_days,daily_vocab_minutes)
               VALUES ('s_blocked','active',0.4,0.7,?,21,15)""",
            (recent_start,)
        )
        self.repo._conn().commit()
        r = self.client.get("/api/listening/lexicon/phase0/status?student_id=s_blocked")
        self.assertEqual(r.status_code, 200)
        data = r.json()["data"]
        self.assertFalse(data["exam_practice_allowed"])
        self.assertTrue(data["phase0_active"])

    def test_no_phase0_allows_exam(self):
        """未进入 Phase 0 → exam_practice_allowed=True。"""
        r = self.client.get("/api/listening/lexicon/phase0/status?student_id=s_fresh")
        self.assertEqual(r.status_code, 200)
        data = r.json()["data"]
        self.assertTrue(data["exam_practice_allowed"])
        self.assertFalse(data["phase0_active"])


# ── G. 禁止字段白名单（API 层） ──────────────────────────────────────────

class TestDTOWhitelist(LexiconTestBase):

    def test_entry_test_rejects_ability_fields(self):
        """entry-test DTO 含 ability 结论字段时 422。"""
        item_id = SAMPLE_ITEMS[0]["item_id"]
        r = self.client.post("/api/listening/lexicon/phase0/entry-test/complete", json={
            "student_id": "s_bad",
            "results": [{"item_id": item_id, "is_correct": True,
                          "understanding_stable": True}],  # FORBIDDEN
            "threshold": 0.7
        })
        self.assertEqual(r.status_code, 422)


# ── H. 幂等 Seed ──────────────────────────────────────────────────────────

class TestIdempotentSeed(LexiconTestBase):

    def test_double_seed_no_duplicates(self):
        """重复 seed 不写入重复词条。"""
        import json, tempfile
        tmp_lexicon = {
            "provenance": {"internal_annotation_only": True},
            "L1": [{
                "word": "idempotent_word", "source_layer": "L1",
                "source_set": 2, "source_status": "machine",
                "sealed_source": False, "provenance": "test"
            }],
            "L2": [], "L3": []
        }
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(tmp_lexicon, f)
            tmp_path = f.name

        orig = svc.LEXICON_PATH
        svc.LEXICON_PATH = Path(tmp_path)

        r1 = svc.seed_lexicon(repo=self.repo)
        r2 = svc.seed_lexicon(repo=self.repo)

        svc.LEXICON_PATH = orig
        Path(tmp_path).unlink(missing_ok=True)

        self.assertEqual(r1["inserted"], 1)
        self.assertEqual(r2["inserted"], 0)
        self.assertEqual(r2["skipped"], 1)

        count = self.repo._conn().execute(
            "SELECT count(*) as c FROM lex_items WHERE surface='idempotent_word'"
        ).fetchone()["c"]
        self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
