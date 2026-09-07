# -*- coding: utf-8 -*-
"""Work Order G/H — stem_bank_service + dashboard_service 合约测试。

测试组：
  A. 浏览接口 — _correct_answer 不出现在任何响应中
  B. 练习会话 — count 上限 / 过滤 / 无答案
  C. 预测提交 — 唯一返回正确答案的出口 / source_set=1 拒绝
  D. 统计接口 — 空学生 None accuracy / 有记录时计算正确
  E. Dashboard — 字段白名单（无 ability 结论）/ phase0 字段完整
  F. API 路由  — GET /stem-bank/stems 无答案 / POST /stem-bank/predict 有答案

运行：
  cd backend
  venv\\Scripts\\python.exe -m pytest tests/test_stem_bank_dashboard.py -v
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

# ── FastAPI app import ─────────────────────────────────────────────────
from fastapi import FastAPI
from fastapi.testclient import TestClient

from listening import router as listening_router_mod
from listening import stem_bank_service as stem_svc
from listening import dashboard_service as dash_svc
from listening import aural_lexicon_service as lex_svc
from listening.repository import StudentRepository

# ── 禁止出现在学生端的字段 ─────────────────────────────────────────────
FORBIDDEN_KEYS = {
    "_correct_answer", "transcript", "correct_answer",
    "understanding_stable", "ability_improved", "diagnosis",
    "material_mastered",
}


def _has_forbidden(obj: Any) -> bool:
    """递归检查 obj 是否包含 FORBIDDEN_KEYS 中的任意 key。"""
    if isinstance(obj, dict):
        if any(k in FORBIDDEN_KEYS for k in obj):
            return True
        return any(_has_forbidden(v) for v in obj.values())
    if isinstance(obj, (list, tuple)):
        return any(_has_forbidden(v) for v in obj)
    return False


# ── 公共测试基类 ──────────────────────────────────────────────────────

class StemDashTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.repo = StudentRepository(Path(self._tmp.name) / "test.db")

        # 替换所有服务中的 repo
        self._orig_lex  = lex_svc.student_repo
        self._orig_stem = stem_svc.student_repo
        self._orig_dash = dash_svc.student_repo
        lex_svc.student_repo  = self.repo
        stem_svc.student_repo = self.repo
        dash_svc.student_repo = self.repo

        app = FastAPI()
        app.include_router(listening_router_mod.router)
        self.client = TestClient(app)
        self.student = "test_student_01"
        self.addCleanup(self._restore)

    def _restore(self):
        conn = getattr(self.repo._local, "conn", None)
        if conn:
            conn.close()
            self.repo._local.conn = None
        lex_svc.student_repo  = self._orig_lex
        stem_svc.student_repo = self._orig_stem
        dash_svc.student_repo = self._orig_dash
        self._tmp.cleanup()


# ── A. 浏览接口 ───────────────────────────────────────────────────────

class TestStemBrowse(StemDashTestBase):
    def test_get_stems_no_answer_key(self):
        stems = stem_svc.get_stems()
        self.assertIsInstance(stems, list)
        for s in stems:
            self.assertNotIn("_correct_answer", s, "浏览接口不得含 _correct_answer")

    def test_get_stems_filter_by_type(self):
        for qt in stem_svc.QUESTION_TYPES:
            stems = stem_svc.get_stems(question_type=qt)
            for s in stems:
                self.assertEqual(s["question_type"], qt)

    def test_get_stems_no_forbidden_keys(self):
        stems = stem_svc.get_stems()
        self.assertFalse(_has_forbidden(stems), "浏览接口含受限字段")

    def test_api_stems_no_answer(self):
        r = self.client.get("/api/listening/stem-bank/stems")
        self.assertEqual(r.status_code, 200)
        data = r.json()["data"]
        self.assertIsInstance(data, list)
        self.assertFalse(_has_forbidden(data))


# ── B. 练习会话 ───────────────────────────────────────────────────────

class TestPracticeSession(StemDashTestBase):
    def test_session_count_capped(self):
        session = stem_svc.get_practice_session(count=999)
        self.assertLessEqual(len(session["items"]), 25, "count 不得超过题库大小")

    def test_session_items_no_answer(self):
        session = stem_svc.get_practice_session(count=3)
        self.assertFalse(_has_forbidden(session))

    def test_session_count_zero_if_no_match(self):
        # attitude 题在 Set 2 不存在
        session = stem_svc.get_practice_session(count=5, question_type="attitude")
        self.assertEqual(session["count"], 0)
        self.assertEqual(session["items"], [])

    def test_api_session_returns_items(self):
        r = self.client.get("/api/listening/stem-bank/session?count=3")
        self.assertEqual(r.status_code, 200)
        items = r.json()["data"]["items"]
        self.assertLessEqual(len(items), 3)
        self.assertFalse(_has_forbidden(items))


# ── C. 预测提交 ───────────────────────────────────────────────────────

class TestPrediction(StemDashTestBase):
    def _first_q(self):
        bank = stem_svc._load_bank()
        if not bank:
            self.skipTest("stem_bank.json not found")
        return bank[0]

    def test_prediction_returns_correct_answer(self):
        """两阶段协议：
        阶段1 (selected_answer=None) → 只有 correct_type / is_type_correct，无 correct_answer。
        阶段2 (selected_answer 已知) → 含 correct_answer / is_answer_correct。
        """
        q = self._first_q()
        # 阶段1：无 correct_answer，无 DB 写入
        phase1 = stem_svc.record_prediction(
            self.student, q["question_no"], q["question_type"], None, self.repo
        )
        self.assertIn("is_type_correct", phase1)
        self.assertNotIn("correct_answer", phase1)   # 不应提前泄题

        # 阶段2：selected_answer 提供后才返回 correct_answer，且 DB 有写入
        phase2 = stem_svc.record_prediction(
            self.student, q["question_no"], q["question_type"], "A", self.repo
        )
        self.assertIn("correct_answer", phase2)
        self.assertIn("is_answer_correct", phase2)

    def test_prediction_no_ability_conclusions(self):
        q = self._first_q()
        result = stem_svc.record_prediction(
            self.student, q["question_no"], None, None, self.repo
        )
        for key in {"understanding_stable", "ability_improved", "diagnosis"}:
            self.assertNotIn(key, result)

    def test_wrong_question_no_raises(self):
        with self.assertRaises(ValueError):
            stem_svc.record_prediction(self.student, 99999, None, None, self.repo)

    def test_api_predict_returns_correct_answer(self):
        """两阶段 API 协议验证：
        阶段1 (selected_answer=null) → 无 correct_answer；
        阶段2 (selected_answer 已知) → 含 correct_answer，且绝不含 _correct_answer。
        """
        q = self._first_q()
        # 阶段1：类型预测，不泄露答案
        r1 = self.client.post("/api/listening/stem-bank/predict", json={
            "student_id": self.student,
            "question_no": q["question_no"],
            "predicted_type": q["question_type"],
            "selected_answer": None,
        })
        self.assertEqual(r1.status_code, 200)
        d1 = r1.json()["data"]
        self.assertNotIn("correct_answer", d1)    # 阶段1不应泄题
        self.assertNotIn("_correct_answer", d1)

        # 阶段2：提交答案，返回正确答案
        r2 = self.client.post("/api/listening/stem-bank/predict", json={
            "student_id": self.student,
            "question_no": q["question_no"],
            "predicted_type": q["question_type"],
            "selected_answer": "A",
        })
        self.assertEqual(r2.status_code, 200)
        d2 = r2.json()["data"]
        self.assertIn("correct_answer", d2)       # 阶段2才返回正确答案
        self.assertNotIn("_correct_answer", d2)


# ── D. 统计接口 ───────────────────────────────────────────────────────

class TestStemStats(StemDashTestBase):
    def test_empty_student_accuracy_is_none(self):
        stats = stem_svc.get_student_stats("no_one", self.repo)
        self.assertIsNone(stats["answer_accuracy"])
        self.assertEqual(stats["total_predictions"], 0)

    def test_accuracy_computed_correctly(self):
        q = stem_svc._load_bank()
        if not q:
            self.skipTest("stem_bank.json not found")
        q0 = q[0]
        # 提交 2 次：1 正确 1 错误
        stem_svc.record_prediction(
            self.student, q0["question_no"], q0["question_type"],
            q0["_correct_answer"], self.repo           # 正确
        )
        stem_svc.record_prediction(
            self.student, q0["question_no"], q0["question_type"],
            "Z",                                        # 错误
            self.repo
        )
        stats = stem_svc.get_student_stats(self.student, self.repo)
        self.assertEqual(stats["total_predictions"], 2)
        self.assertAlmostEqual(stats["answer_accuracy"], 0.5, places=2)

    def test_stats_no_ability_fields(self):
        stats = stem_svc.get_student_stats(self.student, self.repo)
        self.assertFalse(_has_forbidden(stats))

    def test_api_stats_200(self):
        r = self.client.get(f"/api/listening/stem-bank/stats?student_id={self.student}")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(_has_forbidden(r.json()["data"]))


# ── E. Dashboard 字段合约 ─────────────────────────────────────────────

class TestDashboard(StemDashTestBase):
    def _get_dashboard(self):
        # 先种词库
        with patch.object(lex_svc, "student_repo", self.repo):
            lex_svc.seed_lexicon(self.repo)
        return dash_svc.get_dashboard(self.student, self.repo)

    def test_dashboard_required_top_keys(self):
        dash = self._get_dashboard()
        for key in ("student_id", "generated_at", "phase0", "vocab", "stem_bank", "recent_attempts"):
            self.assertIn(key, dash, f"dashboard 缺少字段 {key}")

    def test_dashboard_phase0_keys(self):
        dash = self._get_dashboard()
        p = dash["phase0"]
        for key in ("status", "phase0_active", "exam_practice_allowed", "entry_score", "cap_days"):
            self.assertIn(key, p)

    def test_dashboard_vocab_keys(self):
        dash = self._get_dashboard()
        v = dash["vocab"]
        for key in ("due_count", "total_in_srs", "total_lex_items", "daily_minutes_cap"):
            self.assertIn(key, v)

    def test_dashboard_no_ability_fields(self):
        dash = self._get_dashboard()
        self.assertFalse(_has_forbidden(dash), "dashboard 含受限字段")

    def test_dashboard_recent_attempts_empty_for_new_student(self):
        dash = self._get_dashboard()
        self.assertIsInstance(dash["recent_attempts"], list)
        self.assertEqual(len(dash["recent_attempts"]), 0)

    def test_api_dashboard_200(self):
        with patch.object(lex_svc, "student_repo", self.repo):
            lex_svc.seed_lexicon(self.repo)
        r = self.client.get(f"/api/listening/dashboard?student_id={self.student}")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(_has_forbidden(r.json()["data"]))


if __name__ == "__main__":
    unittest.main()
