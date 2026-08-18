# -*- coding: utf-8 -*-
"""Phase 5A 画像引擎回归测试(无 pytest 依赖):

    venv/Scripts/python.exe -m tests.test_phase50_profile

覆盖验收底线:
1. 同题反复操作不虚增跨题证据(distinct question 计)
2. generated_unverified 证据不单独形成强弱项
3. question mastered 不直接推出 cause mastered
4. 历史弱项可被新题反证修正(current_risk 降级)
5. 每条推荐带 why + evidence_refs 可反查
6. 能力维度只经显式 CAUSE_TO_SKILL 映射聚合
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import listening.repository as repo_mod  # noqa: E402
from listening import (  # noqa: E402
    profile_service,
    review_service,
    training_service,
)
from listening.repository import StudentRepository, exam_repo  # noqa: E402

EXAM_ID = "cet6_202606_set2"
Q3, Q9, Q10 = (f"cet6_202606_set2_q{n}" for n in (3, 9, 10))
CORRECT = {Q3: "B", Q9: "A", Q10: "C"}


class ProfileEngineTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = StudentRepository(Path(self._tmp.name) / "test.db")
        self._patches = []
        for mod in (profile_service, review_service, training_service):
            self._patches.append((mod, "student_repo", mod.student_repo))
            mod.student_repo = self.repo
        # 可控时钟: 保证事件严格递增(Windows 时间戳精度低)
        self._clock = [0]
        orig_now = repo_mod._now

        def fake_now():
            self._clock[0] += 1
            n = self._clock[0]
            return f"2026-08-19T{n // 3600:02d}:{(n // 60) % 60:02d}:{n % 60:02d}+00:00"

        repo_mod._now = fake_now
        self._patches.append((repo_mod, "_now", orig_now))
        self.addCleanup(self._restore)

    def _restore(self):
        conn = getattr(self.repo._local, "conn", None)
        if conn is not None:
            conn.close()
            self.repo._local.conn = None
        for mod, attr, orig in self._patches:
            setattr(mod, attr, orig)
        self._tmp.cleanup()

    # ----- 数据构造辅助 -----

    def _attempt(self, answers: dict, student="s1") -> str:
        """answers: {qid: (first, final)}"""
        att = self.repo.create_attempt(student, EXAM_ID, "practice_mode")
        for qid, (first, final) in answers.items():
            self.repo.upsert_answer(att["id"], qid, {
                "first_answer": first,
                "final_answer": final,
                "is_first_correct": int(first == CORRECT.get(qid)),
            })
        self.repo.submit_attempt(att["id"], 0)
        return att["id"]

    def _diagnose(self, attempt_id: str, qid: str, tag: str):
        return self.repo.upsert_diagnosis(
            "s1", attempt_id, qid,
            student_tags=[tag], ai_tags=[], final_tags=[tag],
        )

    def _train(self, attempt_id: str, qid: str, tag: str, passed: bool,
               provenance: str = "teacher_calibrated"):
        return self.repo.add_training_result(
            "s1", qid, "distractor",
            attempt_id=attempt_id,
            diagnosis_id=(self.repo.get_diagnosis(attempt_id, qid) or {}).get("id"),
            provenance=provenance,
            trigger_tags=[tag],
            input={}, result=passed, score=1.0 if passed else 0.3,
            error_details=[], hints_used=0, duration_ms=1000,
        )

    def _cause(self, tag: str, student="s1") -> dict:
        causes = profile_service.build_cause_profile(student)
        for c in causes:
            if c["cause_tag"] == tag:
                return c
        return {}

    # ----- 1. 同题反复不虚增跨题证据 -----

    def test_same_question_twice_counts_once(self):
        a1 = self._attempt({Q10: ("B", "B")})  # B 命中 scope_shift 陷阱
        self._diagnose(a1, Q10, "scope_shift")
        a2 = self._attempt({Q10: ("B", "B")})  # 同题第二次作答再错
        self._diagnose(a2, Q10, "scope_shift")

        c = self._cause("scope_shift")
        self.assertEqual(c["evidence_questions"], 1)
        self.assertEqual(c["confirmed_questions"], 1)
        self.assertEqual(c["evidence_confidence"], 0.30)
        rules = [r["rule"] for r in c["reason"]]
        self.assertEqual(rules, ["confirmed_diagnosis"])

    def test_three_distinct_questions_high_confidence(self):
        for qid in (Q10, Q3, Q9):
            wrong = {"B" if CORRECT[qid] != "B" else "A"}
            a = self._attempt({qid: (wrong.pop(), wrong and "A" or "A")})
            self._diagnose(a, qid, "scope_shift")
        c = self._cause("scope_shift")
        self.assertEqual(c["evidence_questions"], 3)
        self.assertEqual(c["evidence_confidence"], 0.90)
        self.assertEqual(c["confidence_level"], "high")
        self.assertEqual(c["current_risk"], "high")

    # ----- 2. generated_unverified 不单独形成结论 -----

    def test_unverified_evidence_alone_is_observe_only(self):
        q2 = "cet6_202606_set2_q2"  # 无教师标注
        a = self._attempt({q2: ("B", "B")})  # 错(correct=A)
        self.repo.add_training_result(
            "s1", q2, "dictation", attempt_id=a,
            provenance="generated_unverified",
            trigger_tags=["vocabulary_unknown"],
            input={}, result=False, score=0.3, error_details=[],
        )
        c = self._cause("vocabulary_unknown")
        self.assertEqual(c["evidence_confidence"], 0.0)
        self.assertEqual(c["confidence_level"], "insufficient")
        self.assertTrue(c["only_unverified_evidence"])
        profile = profile_service.build_profile("s1")
        rec = [r for r in profile["recommendations"]
               if r["target_cause"] == "vocabulary_unknown"]
        self.assertEqual(len(rec), 1)
        self.assertEqual(rec[0]["priority"], "observe")

    # ----- 3. question mastered ≠ cause mastered -----

    def test_question_mastered_does_not_make_cause_stable(self):
        a1 = self._attempt({Q10: ("B", "B")})
        self._diagnose(a1, Q10, "scope_shift")
        self._train(a1, Q10, "scope_shift", passed=True)
        training_service.blind_retest(a1, Q10, "C")  # 裸听复测答对

        # 题目层: Q10 已 mastered
        ans = [x for x in self.repo.list_answers(a1) if x["question_id"] == Q10][0]
        events = [e for e in self.repo.list_behavior_events(a1)
                  if e["question_id"] == Q10]
        trainings = self.repo.list_training_results("s1", Q10)
        self.assertEqual(
            training_service.question_mastery(ans, events, trainings), "mastered"
        )

        # 跨题迁移: 训练后新题 Q3(含 scope_shift 陷阱)首答即对 → improving
        self._attempt({Q3: ("B", "B")})
        c = self._cause("scope_shift")
        self.assertEqual(c["trend"]["cross_question_transfer"]["transferred"], 1)
        self.assertEqual(c["cause_mastery"], "improving")
        self.assertNotEqual(c["cause_mastery"], "stable")
        # 同题救回与跨题迁移分开报告
        self.assertEqual(
            c["trend"]["within_question_recovery"], {"recovered": 1, "total": 1}
        )

    # ----- 4. 历史弱项可被新题反证修正 -----

    def test_counter_evidence_lowers_current_risk(self):
        # 三道不同题确认 scope_shift → 高置信高风险
        for qid in (Q10, Q3, Q9):
            wrong = "B" if CORRECT[qid] != "B" else "A"
            a = self._attempt({qid: (wrong, wrong)})
            self._diagnose(a, qid, "scope_shift")
        c = self._cause("scope_shift")
        self.assertEqual(c["current_risk"], "high")

        # 之后一套题里, 含 scope_shift 陷阱的 Q3 首答即对(新证据更晚)
        self._attempt({Q3: ("B", "B")})
        c2 = self._cause("scope_shift")
        self.assertTrue(c2["counter_evidence"])
        self.assertEqual(c2["confidence_level"], "high")  # 历史置信度不抹掉
        self.assertEqual(c2["current_risk"], "medium")    # 但当前风险被修正

    # ----- 5. 推荐必须可反查 -----

    def test_recommendations_carry_why_and_evidence_refs(self):
        for qid in (Q10, Q3, Q9):
            wrong = "B" if CORRECT[qid] != "B" else "A"
            a = self._attempt({qid: (wrong, wrong)})
            self._diagnose(a, qid, "scope_shift")
        profile = profile_service.build_profile("s1")
        recs = profile["recommendations"]
        self.assertTrue(recs)
        for r in recs:
            self.assertTrue(r["why"], f"{r['target_cause']} 缺 why")
            self.assertTrue(r["evidence_refs"], f"{r['target_cause']} 缺证据引用")
            self.assertTrue(r["target_skill"])
        top = recs[0]
        self.assertEqual(top["target_cause"], "scope_shift")
        self.assertEqual(top["priority"], "high")
        self.assertIn("干扰项辨析", top["recommendation"])

    # ----- 6. 能力维度显式映射 -----

    def test_skill_aggregation_uses_fixed_mapping(self):
        for qid in (Q10, Q3):
            wrong = "B" if CORRECT[qid] != "B" else "A"
            a = self._attempt({qid: (wrong, wrong)})
            self._diagnose(a, qid, "scope_shift")
        causes = profile_service.build_cause_profile("s1")
        skills = profile_service.build_skill_profile(causes)
        di = next(s for s in skills if s["skill"] == "distractor_inhibition")
        self.assertEqual(di["score"], 0.60)  # 2 题确认 = 0.6, 权重 0.7 归一
        self.assertEqual(di["from_causes"][0]["weight"], 0.7)
        self.assertEqual(di["from_causes"][0]["cause_tag"], "scope_shift")
        pr = next(s for s in skills if s["skill"] == "paraphrase_recognition")
        self.assertEqual(pr["score"], 0.60)  # 权重 0.3 归一后同为 0.6
        # 无证据维度不得编造分数
        st = next(s for s in skills if s["skill"] == "sound_text_mapping")
        self.assertIsNone(st["score"])
        self.assertEqual(st["level"], "insufficient")


if __name__ == "__main__":
    unittest.main(verbosity=2)
