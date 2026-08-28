# -*- coding: utf-8 -*-
"""V2.1 Exam Mode 回归测试(无 pytest 依赖):

    venv/Scripts/python.exe -m tests.test_v21_exam

覆盖验收指令第 15 条:
  A. Payload Leakage Test        — exam DTO 无禁止字段(递归)
  B. Question Grouping Test      — 7 units / 25 questions / [4,4,3,4,3,3,4] / 每题 ABCD
  C. Chinese Leakage Test        — 可见选项与标题无中文
  D. Question Stem Leakage Test  — payload JSON 不出现任何题干文本
  E. Answer Leakage Test         — payload 无 correct_answer, 提交前无法获得答案
  F. State Test                  — 作答保存→刷新恢复→提交判分(TestClient 全流程)
  G. No Current-Question Cue Test — 无 audio time → question 映射字段
"""
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# V2.1 release gate: 测试环境显式允许未发布内容(开发预览)
os.environ["ALLOW_UNRELEASED_LISTENING_V2"] = "true"

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from listening import router as listening_router_mod  # noqa: E402
from listening import service, v2_exam_service  # noqa: E402
from listening.repository import StudentRepository  # noqa: E402

V2_IDS = ["cet6_202606_set1_v2", "cet6_202606_set2_v2"]
EXPECTED_UNIT_COUNTS = [4, 4, 3, 4, 3, 3, 4]
CJK_RE = re.compile(r"[一-鿿]")


def _paper(exam_id: str) -> dict:
    dto = v2_exam_service.paper_dto(exam_id)
    assert dto is not None
    return dto


class PayloadLeakageTest(unittest.TestCase):
    """A. 白名单 DTO 递归断言。"""

    def test_no_forbidden_keys(self):
        for eid in V2_IDS:
            dto = _paper(eid)
            v2_exam_service.assert_no_forbidden(dto)  # 内部已断言, 再显式跑一次

    def test_whitelist_shape(self):
        allowed_q = {"question_id", "number", "options"}
        allowed_o = {"label", "text_en"}
        allowed_u = {"unit_id", "section", "unit_type", "display_title",
                     "question_range", "questions"}
        for eid in V2_IDS:
            dto = _paper(eid)
            for u in dto["units"]:
                self.assertLessEqual(set(u), allowed_u)
                for q in u["questions"]:
                    self.assertLessEqual(set(q), allowed_q)
                    for o in q["options"]:
                        self.assertEqual(set(o), allowed_o)


class GroupingTest(unittest.TestCase):
    """B. 7 units / 25 questions / 题组大小 / ABCD 选项。"""

    def test_grouping(self):
        for eid in V2_IDS:
            dto = _paper(eid)
            units = dto["units"]
            self.assertEqual(len(units), 7)
            counts = [len(u["questions"]) for u in units]
            self.assertEqual(counts, EXPECTED_UNIT_COUNTS)
            all_q = [q for u in units for q in u["questions"]]
            self.assertEqual(len(all_q), 25)
            self.assertEqual([q["number"] for q in all_q], list(range(1, 26)))
            for q in all_q:
                self.assertEqual([o["label"] for o in q["options"]],
                                 ["A", "B", "C", "D"])
                for o in q["options"]:
                    self.assertTrue(o["text_en"].strip())


class ChineseLeakageTest(unittest.TestCase):
    """C. 可见文本无中文。"""

    def test_no_cjk(self):
        for eid in V2_IDS:
            dto = _paper(eid)
            v2_exam_service.assert_no_cjk_in_options(dto)
            for u in dto["units"]:
                self.assertFalse(CJK_RE.search(u["display_title"]),
                                 f"CJK in title {u['display_title']}")


class StemLeakageTest(unittest.TestCase):
    """D. payload JSON 中不出现任何题干文本(逐条核对 50 个 stem)。"""

    def test_no_stem_text(self):
        for eid in V2_IDS:
            dto = _paper(eid)
            blob = json.dumps(dto, ensure_ascii=False)
            cand = v2_exam_service.v2_registry.get(eid)
            for q in cand["questions"]:
                stem = q["question_text"]
                if stem and len(stem) > 8:
                    self.assertNotIn(stem, blob, f"stem leaked: {stem[:50]}")
                    self.assertNotIn(q.get("question_text_zh", "")[:12], blob)


class AnswerLeakageTest(unittest.TestCase):
    """E. 提交前无法获得 correct_answer。"""

    def test_no_answer(self):
        for eid in V2_IDS:
            blob = json.dumps(_paper(eid), ensure_ascii=False).lower()
            self.assertNotIn("correct_answer", blob)
            self.assertNotIn('"answer"', blob)


class NoCueTest(unittest.TestCase):
    """G. 无 audio time → question 映射。"""

    def test_no_timing_fields(self):
        for eid in V2_IDS:
            dto = _paper(eid)
            blob = json.dumps(dto).lower()
            for bad in ("start_ms", "end_ms", "position", "timestamp",
                        "current_question", "time_ms"):
                self.assertNotIn(bad, blob)


class StateFlowTest(unittest.TestCase):
    """F. TestClient 全流程: 创建 attempt→保存答案→模拟刷新恢复→提交判分。"""

    def setUp(self):
        # TestClient 在 worker 线程执行请求, SQLite 连接是 thread-local,
        # Windows 下无法在主线程关闭 worker 连接 -> 允许清理残留临时文件。
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        repo = StudentRepository(Path(self._tmp.name) / "test.db")
        self.repo = repo
        self._patches = []
        for mod in (listening_router_mod, service):
            self._patches.append((mod, mod.student_repo))
            mod.student_repo = repo
        self.addCleanup(self._restore)
        app = FastAPI()
        app.include_router(listening_router_mod.router)
        self.client = TestClient(app)

    def _restore(self):
        conn = getattr(self.repo._local, "conn", None)
        if conn is not None:
            conn.close()
            self.repo._local.conn = None
        for mod, orig in self._patches:
            mod.student_repo = orig
        self._tmp.cleanup()

    def test_full_flow(self):
        eid = "cet6_202606_set1_v2"
        # 试卷端点
        r = self.client.get(f"/api/listening/v2/exams/{eid}/paper")
        self.assertEqual(r.status_code, 200)
        dto = r.json()["data"]
        first_q = dto["units"][0]["questions"][0]

        # 创建 attempt
        r = self.client.post("/api/listening/attempts", json={
            "student_id": "v2test_student", "exam_id": eid, "mode": "exam_mode"})
        self.assertEqual(r.status_code, 200)
        attempt_id = r.json()["data"]["id"]

        # 保存两题答案(含一次改答)
        self.client.put(
            f"/api/listening/attempts/{attempt_id}/answers/{first_q['question_id']}",
            json={"first_answer": "A", "final_answer": "B",
                  "first_answer_at": "2026-08-28T10:00:00Z",
                  "last_answer_at": "2026-08-28T10:01:00Z",
                  "change_count": 1, "dwell_ms": 60000})
        q5 = dto["units"][1]["questions"][0]
        self.client.put(
            f"/api/listening/attempts/{attempt_id}/answers/{q5['question_id']}",
            json={"first_answer": "C", "final_answer": "C",
                  "first_answer_at": "2026-08-28T10:02:00Z",
                  "last_answer_at": "2026-08-28T10:02:00Z",
                  "change_count": 0, "dwell_ms": 30000})

        # 行为事件
        r = self.client.post(f"/api/listening/attempts/{attempt_id}/events", json={
            "student_id": "v2test_student",
            "events": [
                {"event_type": "unit_enter", "payload": {"unit_id": dto["units"][0]["unit_id"]}},
                {"event_type": "audio_play", "payload": {"position_ms": 0}},
                {"event_type": "answer_select", "question_id": first_q["question_id"],
                 "payload": {"value": "A"}},
            ]})
        self.assertEqual(r.json()["data"]["saved"], 3)

        # 模拟刷新: in-progress 恢复
        r = self.client.get("/api/listening/attempts/in-progress",
                            params={"exam_id": eid, "mode": "exam_mode",
                                    "student_id": "v2test_student"})
        restored = r.json()["data"]
        self.assertIsNotNone(restored)
        saved = {a["question_id"]: a for a in restored["answers"]}
        self.assertEqual(saved[first_q["question_id"]]["final_answer"], "B")
        self.assertEqual(saved[first_q["question_id"]]["change_count"], 1)
        self.assertEqual(saved[q5["question_id"]]["final_answer"], "C")

        # 提交判分(Q1 B 为正确答案, Q5 C 故意错)
        r = self.client.post(f"/api/listening/attempts/{attempt_id}/submit")
        self.assertEqual(r.status_code, 200)
        result = r.json()["data"]
        self.assertEqual(result["question_count"], 25)
        self.assertEqual(result["score"], 1)
        # 提交响应不含答案明细
        self.assertNotIn("correct_answer", json.dumps(result))

        # 提交后不可再改
        r = self.client.put(
            f"/api/listening/attempts/{attempt_id}/answers/{first_q['question_id']}",
            json={"final_answer": "A"})
        self.assertEqual(r.status_code, 409)

    def test_v2_exam_list_and_audio(self):
        r = self.client.get("/api/listening/v2/exams")
        self.assertEqual(r.status_code, 200)
        exams = r.json()["data"]
        self.assertEqual(len(exams), 2)
        for e in exams:
            self.assertEqual(e["question_count"], 25)
            self.assertTrue(e["has_audio"])
            self.assertEqual(e["data_status"], "machine_prechecked")
            self.assertFalse(e["student_release_allowed"])
        r = self.client.get(f"/api/listening/v2/exams/{V2_IDS[0]}/audio")
        self.assertEqual(r.status_code, 200)
        self.assertIn("audio", r.headers["content-type"])

    def test_legacy_exam_untouched(self):
        """legacy exam_repo 的判分路径未被 V2 影响。"""
        from listening.repository import exam_repo
        self.assertIsNotNone(exam_repo.get("cet6_202606_set1"))
        self.assertIsNone(exam_repo.get("cet6_202606_set1_v2"))


class ReleaseGateTest(unittest.TestCase):
    """Hardening A1: release gate 必须可执行, 不能只是 metadata。"""

    def _client(self):
        app = FastAPI()
        app.include_router(listening_router_mod.router)
        return TestClient(app)

    def test_gate_closed_blocks_students(self):
        os.environ.pop("ALLOW_UNRELEASED_LISTENING_V2", None)
        self.addCleanup(lambda: os.environ.__setitem__("ALLOW_UNRELEASED_LISTENING_V2", "true"))
        self.assertFalse(v2_exam_service.gate_allows())
        client = self._client()
        # 学生列表为空
        r = client.get("/api/listening/v2/exams")
        self.assertEqual(r.json()["data"], [])
        # 直接访问 paper/audio/attempt 均被 403
        eid = V2_IDS[0]
        self.assertEqual(client.get(f"/api/listening/v2/exams/{eid}/paper").status_code, 403)
        self.assertEqual(client.get(f"/api/listening/v2/exams/{eid}/audio").status_code, 403)
        r = client.post("/api/listening/attempts", json={
            "student_id": "gate_test", "exam_id": eid, "mode": "exam_mode"})
        self.assertEqual(r.status_code, 403)

    def test_gate_preview_flag_allows(self):
        os.environ["ALLOW_UNRELEASED_LISTENING_V2"] = "true"
        self.assertTrue(v2_exam_service.gate_allows())
        client = self._client()
        r = client.get(f"/api/listening/v2/exams/{V2_IDS[0]}/paper")
        self.assertEqual(r.status_code, 200)

    def test_gate_release_flag_source(self):
        """release 唯一事实来源是 baseline 文件, 当前 student_release_allowed=false。"""
        self.assertFalse(v2_exam_service.student_release_allowed())


if __name__ == "__main__":
    unittest.main(verbosity=2)
