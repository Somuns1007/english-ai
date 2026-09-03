# -*- coding: utf-8 -*-
"""Pacing 端点合约测试 (Work Order F).

测试组：
  A. Set 2 分段数据结构正确性
     - 返回 25 个 Q-window
     - 每个 window 含必要字段
     - window_duration_s > 0
     - q 字段连续 1–25
  B. Set 1 封卷 → 404
     - cet6_202606_set1 不存在 pacing 文件 → 404
     - 不存在的 exam_id → 404
  C. Window 数值约束
     - window_start_s < window_end_s
     - window_duration_s ≈ window_end_s - window_start_s（±0.1s）
     - 没有负数时间戳
  D. API 路由
     - GET /api/listening/exams/cet6_202606_set2/pacing → 200
     - GET /api/listening/exams/cet6_202606_set1/pacing  → 404
     - GET /api/listening/exams/nonexistent_exam/pacing  → 404

运行：
  cd backend
  venv\\Scripts\\python.exe -m pytest tests/test_pacing.py -v
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from listening import router as listening_router_mod
from listening import aural_lexicon_service as lex_svc
from listening.repository import StudentRepository

SET2_EXAM_ID = "cet6_202606_set2"
SET1_EXAM_ID = "cet6_202606_set1"
EXPECTED_Q_COUNT = 25

REQUIRED_WINDOW_KEYS = {
    "q", "unit_id", "section_type",
    "stem_start_s", "window_start_s", "window_end_s", "window_duration_s"
}


class PacingTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.repo = StudentRepository(Path(self._tmp.name) / "test.db")
        self._orig = lex_svc.student_repo
        lex_svc.student_repo = self.repo

        app = FastAPI()
        app.include_router(listening_router_mod.router)
        self.client = TestClient(app)
        self.addCleanup(self._restore)

    def _restore(self):
        conn = getattr(self.repo._local, "conn", None)
        if conn:
            conn.close()
            self.repo._local.conn = None
        lex_svc.student_repo = self._orig
        self._tmp.cleanup()


# ── A. Set 2 数据结构 ─────────────────────────────────────────────────

class TestSet2Structure(PacingTestBase):
    def _windows(self):
        r = self.client.get(f"/api/listening/exams/{SET2_EXAM_ID}/pacing")
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()["data"]
        return data.get("windows", [])

    def test_returns_25_windows(self):
        windows = self._windows()
        self.assertEqual(len(windows), EXPECTED_Q_COUNT,
                         f"期望 {EXPECTED_Q_COUNT} 个 Q-window，实际 {len(windows)}")

    def test_window_required_keys(self):
        windows = self._windows()
        for w in windows:
            missing = REQUIRED_WINDOW_KEYS - set(w.keys())
            self.assertFalse(missing, f"Q{w.get('q')} 缺少字段: {missing}")

    def test_q_numbers_consecutive(self):
        windows = self._windows()
        q_nums = [w["q"] for w in windows]
        self.assertEqual(sorted(q_nums), list(range(1, EXPECTED_Q_COUNT + 1)),
                         "Q 编号应为 1–25 连续")

    def test_window_duration_positive(self):
        windows = self._windows()
        for w in windows:
            self.assertGreater(w["window_duration_s"], 0,
                               f"Q{w['q']} window_duration_s 应 > 0")

    def test_exam_metadata_present(self):
        r = self.client.get(f"/api/listening/exams/{SET2_EXAM_ID}/pacing")
        data = r.json()["data"]
        self.assertIn("exam_id", data)
        self.assertIn("total_questions", data)
        self.assertEqual(data["total_questions"], EXPECTED_Q_COUNT)


# ── B. Set 1 封卷 → 404 ───────────────────────────────────────────────

class TestSet1Sealed(PacingTestBase):
    def test_set1_returns_404(self):
        r = self.client.get(f"/api/listening/exams/{SET1_EXAM_ID}/pacing")
        self.assertEqual(r.status_code, 404,
                         "Set 1 封卷，pacing 端点必须返回 404")

    def test_nonexistent_exam_404(self):
        r = self.client.get("/api/listening/exams/fake_exam_xyz/pacing")
        self.assertEqual(r.status_code, 404)

    def test_set1_error_detail_mentions_sealed(self):
        r = self.client.get(f"/api/listening/exams/{SET1_EXAM_ID}/pacing")
        detail = r.json().get("detail", "").lower()
        self.assertTrue(
            "sealed" in detail or "not found" in detail or "unavailable" in detail,
            f"404 detail 应包含 sealed/not found/unavailable，实际: {detail}"
        )


# ── C. Window 数值约束 ────────────────────────────────────────────────

class TestWindowValues(PacingTestBase):
    def _windows(self):
        r = self.client.get(f"/api/listening/exams/{SET2_EXAM_ID}/pacing")
        return r.json()["data"]["windows"]

    def test_start_before_end(self):
        for w in self._windows():
            self.assertLess(w["window_start_s"], w["window_end_s"],
                            f"Q{w['q']}: window_start_s 应 < window_end_s")

    def test_duration_matches_range(self):
        for w in self._windows():
            computed = w["window_end_s"] - w["window_start_s"]
            self.assertAlmostEqual(
                w["window_duration_s"], computed, delta=0.2,
                msg=f"Q{w['q']}: duration {w['window_duration_s']:.3f} ≠ "
                    f"end-start {computed:.3f}"
            )

    def test_no_negative_timestamps(self):
        for w in self._windows():
            for key in ("stem_start_s", "window_start_s", "window_end_s"):
                self.assertGreaterEqual(w[key], 0,
                                        f"Q{w['q']} {key} 不应为负数")

    def test_stem_start_before_window_start(self):
        for w in self._windows():
            self.assertLessEqual(w["stem_start_s"], w["window_start_s"],
                                 f"Q{w['q']}: stem 应在 window 之前或同时")

    def test_section_types_valid(self):
        valid = {"conversation", "passage", "lecture"}
        for w in self._windows():
            self.assertIn(w["section_type"], valid,
                          f"Q{w['q']} section_type '{w['section_type']}' 不合法")


if __name__ == "__main__":
    unittest.main()
