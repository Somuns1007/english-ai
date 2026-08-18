# -*- coding: utf-8 -*-
"""Phase 4.1 证据链加固回归测试(无 pytest 依赖, 直接运行):

    venv/Scripts/python.exe -m tests.test_phase41_evidence_chain

覆盖验收要求第 5 条:
  同一道题产生第二次 diagnosis 后, 新训练必须绑定"当前有效诊断"
  (id + revision), 旧 training_result 保留原 revision 快照不被重写;
以及:
  - is_training_passed 规则层(per-type 可扩展, 不再写死 score>=0.8)
  - training_provenance 服务端分级(teacher_calibrated / generated_unverified)
  - question_mastery 为题目层概念(旧名 mastery_with_training 已移除)
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from listening import review_service, router, training_service  # noqa: E402
from listening.models import TrainingResultIn  # noqa: E402
from listening.repository import StudentRepository, exam_repo  # noqa: E402

EXAM_ID = "cet6_202606_set2"
QUESTION_ID = "cet6_202606_set2_q10"  # 有教师标注的验收案例题


class EvidenceChainTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        repo = StudentRepository(Path(self._tmp.name) / "test.db")
        self.repo = repo
        # 各模块持有的 student_repo 引用全部替换为临时库
        self._patches = []
        for mod in (training_service, review_service, router):
            self._patches.append((mod, mod.student_repo))
            mod.student_repo = repo
        self.addCleanup(self._restore)

    def _restore(self):
        # 先关闭临时库的 SQLite 连接(Windows 下占用文件无法删除)
        conn = getattr(self.repo._local, "conn", None)
        if conn is not None:
            conn.close()
            self.repo._local.conn = None
        for mod, orig in self._patches:
            mod.student_repo = orig
        self._tmp.cleanup()

    def _make_submitted_attempt(self) -> str:
        att = self.repo.create_attempt("test_student", EXAM_ID, "practice_mode")
        self.repo.submit_attempt(att["id"], 0)
        return att["id"]

    def _save_training_via_router(self, attempt_id: str, training_type: str,
                                  score: float, result: bool) -> dict:
        body = TrainingResultIn(
            student_id="test_student",
            question_id=QUESTION_ID,
            training_type=training_type,
            attempt_id=attempt_id,
            input={"simulated": True},
            result=result,
            score=score,
            error_details=[],
            hints_used=0,
            duration_ms=1000,
        )
        out = router.save_training_result(body)
        rid = out["data"]["id"]
        rows = [t for t in self.repo.list_training_results("test_student",
                                                           QUESTION_ID)
                if t["id"] == rid]
        self.assertEqual(len(rows), 1)
        return rows[0]

    # ----- 核心回归: 二次诊断后的绑定 -----

    def test_retraining_binds_current_diagnosis_old_snapshot_kept(self):
        attempt_id = self._make_submitted_attempt()

        d1 = self.repo.upsert_diagnosis(
            "test_student", attempt_id, QUESTION_ID,
            student_tags=["scope_shift"], ai_tags=[], final_tags=["scope_shift"],
        )
        self.assertEqual(d1["revision"], 1)

        plan1 = training_service.training_plan(attempt_id, QUESTION_ID)
        self.assertTrue(plan1["available"])
        self.assertEqual(plan1["diagnosis_id"], d1["id"])
        self.assertEqual(plan1["diagnosis_revision"], 1)
        self.assertIn("scope_shift", [t["tag"] for t in plan1["triggers"]])

        train1 = self._save_training_via_router(attempt_id, "distractor", 1.0, True)
        self.assertEqual(train1["diagnosis_id"], d1["id"])
        self.assertEqual(train1["diagnosis_revision"], 1)
        self.assertEqual(train1["trigger_tags"], ["scope_shift"])
        self.assertEqual(train1["provenance"], "teacher_calibrated")

        # 第二次诊断: 同一题, id 稳定, revision 递增, 结论变化
        d2 = self.repo.upsert_diagnosis(
            "test_student", attempt_id, QUESTION_ID,
            student_tags=["speaker_confusion"], ai_tags=[],
            final_tags=["speaker_confusion"],
        )
        self.assertEqual(d2["id"], d1["id"])
        self.assertEqual(d2["revision"], 2)

        plan2 = training_service.training_plan(attempt_id, QUESTION_ID)
        self.assertEqual(plan2["diagnosis_revision"], 2)
        self.assertIn("speaker_confusion", [t["tag"] for t in plan2["triggers"]])

        train2 = self._save_training_via_router(attempt_id, "distractor", 1.0, True)
        # 新训练绑定当前有效诊断(rev 2)
        self.assertEqual(train2["diagnosis_id"], d2["id"])
        self.assertEqual(train2["diagnosis_revision"], 2)
        self.assertEqual(train2["trigger_tags"], ["speaker_confusion"])

        # 旧训练快照不被重写
        train1_after = [t for t in self.repo.list_training_results(
            "test_student", QUESTION_ID) if t["id"] == train1["id"]][0]
        self.assertEqual(train1_after["diagnosis_revision"], 1)
        self.assertEqual(train1_after["trigger_tags"], ["scope_shift"])

    def test_training_without_diagnosis_binds_none_and_snapshots_candidates(self):
        attempt_id = self._make_submitted_attempt()
        # 无诊断时: 高置信候选驱动的训练, diagnosis_id 为空但 trigger_tags
        # 仍快照候选错因
        train = self._save_training_via_router(attempt_id, "distractor", 1.0, True)
        self.assertIsNone(train["diagnosis_id"])
        self.assertIsNone(train["diagnosis_revision"])
        # Q10 题目层陷阱含 scope_shift 等, 候选是否高置信取决于行为数据;
        # 这里只要求字段存在且为列表(不硬猜)
        self.assertIsInstance(train["trigger_tags"], list)

    # ----- 达标规则层 -----

    def test_pass_rule_extensible_per_type(self):
        ip = training_service.is_training_passed
        # default: result 且 score>=0.8
        self.assertTrue(ip("dictation", 0.8, True))
        self.assertFalse(ip("dictation", 0.79, True))
        self.assertFalse(ip("dictation", 0.95, False))
        # distractor / paraphrase 要求全对(与判分端一致)
        self.assertTrue(ip("distractor", 1.0, True))
        self.assertFalse(ip("distractor", 0.9, True))
        self.assertTrue(ip("paraphrase", 1.0, True))
        self.assertFalse(ip("paraphrase", 0.75, True))
        # 未知类型走 default
        self.assertTrue(ip("future_type", 0.85, True))

    # ----- 内容来源分级 -----

    def test_provenance_grading(self):
        exam = exam_repo.get(EXAM_ID)
        q10 = training_service._find_question(exam, QUESTION_ID)
        # Q10 有教师标注: distractor 内容 = teacher_calibrated
        self.assertEqual(
            training_service.training_provenance(q10, "distractor"),
            "teacher_calibrated",
        )
        self.assertEqual(
            training_service.distractor_content(q10)["provenance"],
            "teacher_calibrated",
        )
        # Q10 的 dictation 文本来自教师校准 evidence_text
        self.assertEqual(
            training_service.training_provenance(q10, "dictation"),
            "teacher_calibrated",
        )
        # 无教师标注的题: dictation/chunk 只能是 generated_unverified
        q2 = training_service._find_question(exam, "cet6_202606_set2_q2")
        self.assertEqual(
            training_service.training_provenance(q2, "dictation"),
            "generated_unverified",
        )

    # ----- 题目层 / 错因层掌握度分离 -----

    def test_question_mastery_is_question_layer_only(self):
        # 旧名必须移除, 防止 Phase 5 误用为错因层掌握度
        self.assertFalse(hasattr(training_service, "mastery_with_training"))
        self.assertTrue(callable(training_service.question_mastery))
        self.assertIn("题目层", training_service.question_mastery.__doc__)


if __name__ == "__main__":
    unittest.main(verbosity=2)
