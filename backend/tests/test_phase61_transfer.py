# -*- coding: utf-8 -*-
"""Phase 6.1 Cross-context Transfer 回归测试(无 pytest 依赖):

    venv/Scripts/python.exe -m tests.test_phase61_transfer

覆盖验收底线:
1. 证据强度区分: 盲听一次全对 > 看文本后全对(同 3/3 不同强度)
2. 去重规则: 同一场景刷多次只算一份证据; demonstrated 要求 distinct 场景
3. 状态机: not_demonstrated → emerging → demonstrated
4. pending_teacher 上限: 未审核内容最多 emerging, approve 后才可 demonstrated
5. 速度护栏: 全对但时长过短被降权
6. 教师审核流: 编辑→revision+1 且回落 pending→approve→reviewed_at;
   text 变更作废旧音频; 可重新生成
7. cross-context 画像段可解释(scenario→blind/reveal→answers→strength→contribution)
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

EXPRESSION_ID = "exp_fully_booked"
SCN_HOTEL = "scn_fully_booked_hotel"
SCN_RESTAURANT = "scn_fully_booked_restaurant"
# scn_fully_booked_hotel 答案: scene=B meaning=C key_info=B
HOTEL_ANSWERS = {"scene": "B", "meaning": "C", "key_info": "B"}


class TransferTest(unittest.TestCase):
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
        # 教师审核会改真实 JSON: 备份原始内容, 测试后恢复
        self._json_backups = {
            p: p.read_text(encoding="utf-8")
            for p in (
                expression_service.EXPRESSIONS_PATH,
                expression_service.SCENARIOS_PATH,
                expression_service.AUDIO_INDEX_PATH,
            )
            if p.exists()
        }
        self.addCleanup(self._restore)

    def _restore(self):
        conn = getattr(self.repo._local, "conn", None)
        if conn is not None:
            conn.close()
            self.repo._local.conn = None
        for mod, attr, orig in self._patches:
            setattr(mod, attr, orig)
        for path, content in self._json_backups.items():
            path.write_text(content, encoding="utf-8")
        expression_service.expression_repo.reload()
        self._tmp.cleanup()

    def _submit(self, scenario_id, answers, listen=1, reveal=False, duration=30000, student="s1"):
        result = expression_service.submit_scenario(
            scenario_id, student, answers=answers,
            listen_count_before_submit=listen, reveal_used=reveal, duration_ms=duration,
        )
        self.assertIsNotNone(result)
        return result

    # 1. 同样 3/3 全对, 盲听一次 vs 看文本, 证据强度必须不同
    def test_strength_blind_vs_revealed(self):
        blind = self._submit(SCN_HOTEL, HOTEL_ANSWERS, listen=1, reveal=False)
        revealed = self._submit(SCN_HOTEL, HOTEL_ANSWERS, listen=1, reveal=True, student="s2")
        self.assertEqual(blind["evidence"]["level"], "strong")
        self.assertGreater(blind["evidence"]["strength"], 0.9)
        self.assertLess(revealed["evidence"]["strength"], 0.35)
        self.assertEqual(revealed["evidence"]["level"], "weak")
        self.assertEqual(revealed["evidence"]["factors"]["blind_factor"], 0.3)

    # 2. 去重: 同场景刷 3 次只保留 best; demonstrated 需要 distinct 场景
    def test_dedup_same_scenario(self):
        for _ in range(3):
            self._submit(SCN_HOTEL, HOTEL_ANSWERS)
        st = expression_service.expression_transfer_state("s1", EXPRESSION_ID)
        self.assertEqual(st["distinct_scenarios_with_evidence"], 1)
        self.assertEqual(len(st["scenario_evidence"]), 1)
        self.assertEqual(st["scenario_evidence"][0]["attempt_count_for_scenario"], 3)
        # 只有一个 distinct 场景, 即使 strong 也只能 emerging(且 pending 上限)
        self.assertEqual(st["transfer_state"], "emerging")

    # 3+4. 状态机 + pending 上限: 两场景 strong 盲听 → emerging(pending);
    #      approve 后 → demonstrated
    def test_state_machine_and_pending_cap(self):
        self._submit(SCN_HOTEL, HOTEL_ANSWERS)
        r2 = expression_service.submit_scenario(
            SCN_RESTAURANT, "s1",
            # 读取真实答案, 避免硬编码漂移
            answers={
                k: expression_service.expression_repo.get_scenario(SCN_RESTAURANT)["questions"][k]["answer"]
                for k in ("scene", "meaning", "key_info")
            },
            listen_count_before_submit=2, reveal_used=False, duration_ms=40000,
        )
        self.assertEqual(r2["evidence"]["level"], "strong")

        st = expression_service.expression_transfer_state("s1", EXPRESSION_ID)
        self.assertEqual(st["distinct_scenarios_with_evidence"], 2)
        self.assertEqual(st["strong_blind_approved_scenarios"], 0)
        self.assertEqual(st["transfer_state"], "emerging")
        self.assertTrue(st["capped_by_pending_teacher"])

        # 教师 approve 两个场景后 → demonstrated
        expression_service.review_scenario(SCN_HOTEL, "approve")
        expression_service.review_scenario(SCN_RESTAURANT, "approve")
        st2 = expression_service.expression_transfer_state("s1", EXPRESSION_ID)
        self.assertEqual(st2["strong_blind_approved_scenarios"], 2)
        self.assertEqual(st2["transfer_state"], "demonstrated")
        self.assertFalse(st2["capped_by_pending_teacher"])

    # 5. 速度护栏
    def test_speed_guard(self):
        r = self._submit(SCN_HOTEL, HOTEL_ANSWERS, listen=1, duration=3000)
        self.assertEqual(r["evidence"]["factors"]["speed_factor"], 0.5)
        self.assertLessEqual(r["evidence"]["strength"], 0.5)

    # 6. 教师审核流
    def test_teacher_review_flow(self):
        # 编辑文本: revision+1, 回落 pending, 旧音频作废
        s0 = expression_service.expression_repo.get_scenario(SCN_HOTEL)
        rev0 = s0.get("revision", 1)
        self.assertIsNotNone(expression_service.expression_repo.audio_meta(SCN_HOTEL))
        updated = expression_service.update_scenario(SCN_HOTEL, {
            "text": s0["text"] + "\nA: Great, I'll take it.",
        })
        self.assertEqual(updated["revision"], rev0 + 1)
        self.assertEqual(updated["review_status"], "pending_teacher")
        self.assertIsNone(expression_service.expression_repo.audio_meta(SCN_HOTEL))

        # 目标表达被删必须拒绝
        bad = expression_service.update_scenario(SCN_HOTEL, {"text": "A: hello\nB: hi"})
        self.assertEqual(bad["error"], "target_missing")

        # approve → approved + reviewed_at
        reviewed = expression_service.review_scenario(SCN_HOTEL, "approve")
        self.assertEqual(reviewed["review_status"], "approved")
        self.assertTrue(reviewed["reviewed_at"])

        # 重新生成音频(教师链的一部分)
        meta = expression_service.regenerate_scenario_audio(SCN_HOTEL)
        self.assertEqual(meta["source_type"], "ai_generated_tts")
        self.assertTrue(meta["voice_id"])
        self.assertTrue(
            (expression_service.EXPRESSIONS_DIR / meta["file"]).exists()
        )

    # 7. 画像 cross-context 段可解释
    def test_cross_context_profile_explainable(self):
        self._submit(SCN_HOTEL, HOTEL_ANSWERS, listen=2, duration=35000)
        p = profile_service.build_profile("s1")
        cc = p["cross_context"]
        self.assertEqual(cc["summary"]["total_expressions_trained"], 1)
        self.assertEqual(cc["summary"]["emerging"], 1)
        expr = cc["expressions"][0]
        self.assertEqual(expr["expression_id"], EXPRESSION_ID)
        ev = expr["scenario_evidence"][0]
        # 钻取链: scenario → blind/reveal → answers → strength → contribution
        for key in ("scenario_id", "blind", "reveal_used", "answers", "correct",
                    "evidence_strength", "evidence_level", "verification_level",
                    "contribution", "attempt_id"):
            self.assertIn(key, ev)
        self.assertEqual(ev["verification_level"], "pending_teacher")
        self.assertEqual(ev["verification_weight"], 0.5)
        self.assertAlmostEqual(ev["contribution"], ev["evidence_strength"] * 0.5, places=3)
        # cross-question 段不受影响
        self.assertIn("causes", p)
        self.assertIn("skills", p)


if __name__ == "__main__":
    unittest.main(verbosity=2)
