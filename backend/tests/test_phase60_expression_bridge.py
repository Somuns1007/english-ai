# -*- coding: utf-8 -*-
"""Phase 6 Expression Bridge 回归测试(无 pytest 依赖):

    venv/Scripts/python.exe -m tests.test_phase60_expression_bridge

覆盖验收底线:
1. 数据完整性(走 validate_expressions.validate 全量规则)
2. submit 服务端判分正确, expression_attempts 落库字段齐全
3. cross-context 行为不回流画像(build_profile 结果前后一致)
4. 严禁冒充: 场景全部 ai_generated, 音频全部 ai_generated_tts
5. 揭示后复听计数可累加
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import listening.repository as repo_mod  # noqa: E402
from listening import expression_service, profile_service  # noqa: E402
from listening.repository import StudentRepository  # noqa: E402
from listening.tools import validate_expressions  # noqa: E402

SCENARIO_ID = "scn_fully_booked_hotel"
EXPRESSION_ID = "exp_fully_booked"


class ExpressionBridgeTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = StudentRepository(Path(self._tmp.name) / "test.db")
        self._patches = []
        for mod in (expression_service, profile_service):
            self._patches.append((mod, "student_repo", mod.student_repo))
            mod.student_repo = self.repo
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

    # 1. 数据完整性
    def test_data_integrity(self):
        errors = validate_expressions.validate()
        self.assertEqual(errors, [], f"数据校验失败: {errors[:5]}")

    # 2. submit 判分 + 落库字段
    def test_submit_grading_and_persistence(self):
        result = expression_service.submit_scenario(
            SCENARIO_ID, "s1",
            answers={"scene": "B", "meaning": "C", "key_info": "A"},
            listen_count_before_submit=3,
            reveal_used=False,
            duration_ms=45000,
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["correct"], {
            "scene": True, "meaning": True, "key_info": False, "all": False,
        })
        # 揭示内容随提交返回
        self.assertIn("fully booked", result["text"])
        self.assertEqual(result["target_surface"], "fully booked")
        self.assertEqual(result["source_type"], "ai_generated")

        rows = self.repo.list_expression_attempts("s1", EXPRESSION_ID)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["scenario_id"], SCENARIO_ID)
        self.assertEqual(row["scenario_category"], "hotel")
        self.assertEqual(row["source_type"], "ai_generated")
        self.assertEqual(row["listen_count_before_submit"], 3)
        self.assertEqual(row["reveal_used"], 0)
        self.assertEqual(row["replay_after_reveal"], 0)
        self.assertEqual(row["answer_scene"], "B")
        self.assertEqual(row["answer_meaning"], "C")
        self.assertEqual(row["answer_key_info"], "A")
        self.assertEqual(row["scene_correct"], 1)
        self.assertEqual(row["meaning_correct"], 1)
        self.assertEqual(row["key_info_correct"], 0)
        self.assertEqual(row["all_correct"], 0)
        self.assertEqual(row["duration_ms"], 45000)
        self.assertTrue(row["created_at"])

    # 3. cross-context 行为不回流 cross-question 画像(causes/skills/recommendations)
    def test_expression_attempts_do_not_leak_into_profile(self):
        def core(p: dict) -> str:
            return json.dumps(
                {k: p[k] for k in ("causes", "skills", "recommendations", "attempts_count")},
                sort_keys=True, ensure_ascii=False,
            )

        before = profile_service.build_profile("s1")
        # 做两次场景训练, 一错一对
        expression_service.submit_scenario(
            SCENARIO_ID, "s1",
            answers={"scene": "A", "meaning": "A", "key_info": "A"},
            listen_count_before_submit=5, reveal_used=True, duration_ms=90000,
        )
        expression_service.submit_scenario(
            "scn_fully_booked_restaurant", "s1",
            answers={"scene": "A", "meaning": "B", "key_info": "C"},
            listen_count_before_submit=1, reveal_used=False, duration_ms=20000,
        )
        # 确认两次训练确实落库(否则本测试形同虚设)
        self.assertEqual(len(self.repo.list_expression_attempts("s1")), 2)
        after = profile_service.build_profile("s1")
        self.assertEqual(
            core(before), core(after),
            "expression_attempts 影响了 cross-question 画像, 违反纪律",
        )
        # cross-context 段存在且独立更新(6.1 起允许出现在画像里, 但必须独立成段)
        self.assertIn("cross_context", after)
        self.assertEqual(after["cross_context"]["summary"]["total_expressions_trained"], 1)

    # 4. 严禁冒充真实语料
    def test_no_authentic_masquerading(self):
        scenarios = expression_service.expression_repo.list_expressions()
        for e in scenarios:
            self.assertEqual(e["source_type"], "official_exam")
        doc = json.loads(
            validate_expressions.SCENARIOS_PATH.read_text(encoding="utf-8")
        )
        for s in doc["scenarios"]:
            self.assertEqual(s["source_type"], "ai_generated")
            self.assertEqual(s["generation_status"], "generated")
        audio_index = json.loads(
            expression_service.AUDIO_INDEX_PATH.read_text(encoding="utf-8")
        )
        self.assertEqual(len(audio_index), len(doc["scenarios"]))
        for sid, meta in audio_index.items():
            self.assertEqual(meta["source_type"], "ai_generated_tts", sid)
            self.assertTrue(meta["voice_id"], sid)
            self.assertTrue(meta["provider"], sid)
            self.assertTrue(meta["generated_at"], sid)

    # 5. 揭示后复听计数
    def test_replay_after_reveal_increments(self):
        result = expression_service.submit_scenario(
            SCENARIO_ID, "s1",
            answers={"scene": "B", "meaning": "C", "key_info": "B"},
            listen_count_before_submit=2, reveal_used=False, duration_ms=30000,
        )
        self.assertTrue(result["correct"]["all"])
        att_id = result["attempt_id"]
        self.assertTrue(expression_service.record_replay_after_reveal(att_id))
        self.assertTrue(expression_service.record_replay_after_reveal(att_id))
        row = self.repo.get_expression_attempt(att_id)
        self.assertEqual(row["replay_after_reveal"], 2)
        self.assertEqual(row["all_correct"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
