# -*- coding: utf-8 -*-
"""Phase 7 Corpus Ingestion 回归测试(无 pytest 依赖):

    venv/Scripts/python.exe -m tests.test_phase70_corpus

覆盖验收底线:
1. content_revision 保护: 实质修改文本后旧 attempt 不计入新内容 demonstrated
2. 切分规则: 按停顿/长度切, 保留上下文, 不按固定秒数
3. Expression 规则匹配: exact/target_surface/related/normalized, 命中为 candidate
4. 许可门控: unverified 素材不可批准
5. clip 编辑: revision+1, 实质修改回落 pending, revisions_log 记录, 原始 ASR 不被覆盖
6. 教师鉴权: 无 token 401, 错 token 401, 对 token 放行
"""
import io
import json
import os
import sys
import tempfile
import unittest
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import listening.repository as repo_mod  # noqa: E402
from listening import corpus_service, expression_service, profile_service  # noqa: E402
from listening.repository import StudentRepository  # noqa: E402

SCN_HOTEL = "scn_fully_booked_hotel"
SCN_RESTAURANT = "scn_fully_booked_restaurant"
EXPRESSION_ID = "exp_fully_booked"
HOTEL_ANSWERS = {"scene": "B", "meaning": "C", "key_info": "B"}


def _tiny_wav_bytes(seconds: float = 0.5) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00\x00" * int(16000 * seconds))
    return buf.getvalue()


def _fake_segments():
    """模拟 ASR 段: 两个停顿点, 验证按停顿切分。"""
    return [
        {"start_ms": 0, "end_ms": 4000, "text": "Hello, I'd like to book a room.", "avg_logprob": -0.2, "no_speech_prob": 0.01},
        {"start_ms": 4200, "end_ms": 8000, "text": "Let me check for you.", "avg_logprob": -0.2, "no_speech_prob": 0.01},
        # 停顿 1500ms → 切
        {"start_ms": 9500, "end_ms": 14000, "text": "I'm afraid we're fully booked on Friday.", "avg_logprob": -0.2, "no_speech_prob": 0.01},
        {"start_ms": 14200, "end_ms": 18000, "text": "We only have rooms on Saturday.", "avg_logprob": -0.2, "no_speech_prob": 0.01},
        # 停顿 1500ms → 切
        {"start_ms": 19500, "end_ms": 24000, "text": "Shall I book that for you?", "avg_logprob": -0.2, "no_speech_prob": 0.01},
    ]


class CorpusTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = StudentRepository(Path(self._tmp.name) / "test.db")
        self._patches = []
        for mod in (corpus_service, expression_service, profile_service):
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
        # corpus_service 写文件到 DATA_DIR: 重定向到临时目录
        for attr, new_val in (
            ("DATA_DIR", Path(self._tmp.name)),
            ("CORPUS_DIR", Path(self._tmp.name) / "corpus"),
            ("CORPUS_AUDIO_DIR", Path(self._tmp.name) / "corpus" / "audio"),
        ):
            self._patches.append((corpus_service, attr, getattr(corpus_service, attr)))
            setattr(corpus_service, attr, new_val)
        # 教师审核会改真实 scenarios.json / 作废音频索引: 备份恢复;
        # 文本编辑会物理删除 mp3, 二进制同样备份恢复
        self._scenarios_backup = expression_service.SCENARIOS_PATH.read_text(encoding="utf-8")
        self._audio_index_backup = expression_service.AUDIO_INDEX_PATH.read_text(encoding="utf-8")
        self._bin_backups = {}
        for sid in (SCN_HOTEL, SCN_RESTAURANT):
            meta = expression_service.expression_repo.audio_meta(sid)
            if meta:
                mp3 = expression_service.EXPRESSIONS_DIR / meta["file"]
                if mp3.exists():
                    self._bin_backups[mp3] = mp3.read_bytes()
        self.addCleanup(self._restore)

    def _restore(self):
        conn = getattr(self.repo._local, "conn", None)
        if conn is not None:
            conn.close()
            self.repo._local.conn = None
        for mod, attr, orig in self._patches:
            setattr(mod, attr, orig)
        expression_service.SCENARIOS_PATH.write_text(self._scenarios_backup, encoding="utf-8")
        expression_service.AUDIO_INDEX_PATH.write_text(self._audio_index_backup, encoding="utf-8")
        for path, content in self._bin_backups.items():
            path.write_bytes(content)
        expression_service.expression_repo.reload()
        self._tmp.cleanup()

    def _make_asset(self, permission="verified_open_license") -> dict:
        asset = corpus_service.create_asset(
            _tiny_wav_bytes(), "test.wav", "测试素材", "UnitTest",
            "https://example.com", "CC BY 4.0", permission,
        )
        self.assertTrue((Path(self._tmp.name) / asset["file_path"]).exists())
        return asset

    # 1. content_revision 保护
    def test_content_revision_protection(self):
        for sid in (SCN_HOTEL, SCN_RESTAURANT):
            answers = {
                k: expression_service.expression_repo.get_scenario(sid)["questions"][k]["answer"]
                for k in ("scene", "meaning", "key_info")
            }
            expression_service.submit_scenario(
                sid, "s1", answers=answers,
                listen_count_before_submit=1, reveal_used=False, duration_ms=30000,
            )
        expression_service.review_scenario(SCN_HOTEL, "approve")
        expression_service.review_scenario(SCN_RESTAURANT, "approve")
        st = expression_service.expression_transfer_state("s1", EXPRESSION_ID)
        self.assertEqual(st["transfer_state"], "demonstrated")

        # 教师实质修改 restaurant 场景文本 → rev 2 → 旧 attempt 失效
        s = expression_service.expression_repo.get_scenario(SCN_RESTAURANT)
        new_text = s["text"] + "\nA: Perfect, see you then."
        expression_service.update_scenario(SCN_RESTAURANT, {"text": new_text})
        st2 = expression_service.expression_transfer_state("s1", EXPRESSION_ID)
        # restaurant 旧 attempt 不再计入: 只剩 hotel 一个 strong_blind_approved
        self.assertEqual(st2["strong_blind_approved_scenarios"], 1)
        self.assertNotEqual(st2["transfer_state"], "demonstrated")
        stale = next(e for e in st2["scenario_evidence"] if e["scenario_id"] == SCN_RESTAURANT)
        self.assertFalse(stale["revision_current"])

        # 教师重新审核批准修订版 + 学生在新内容上重新作答 → 恢复资格
        expression_service.review_scenario(SCN_RESTAURANT, "approve")
        answers = {
            k: expression_service.expression_repo.get_scenario(SCN_RESTAURANT)["questions"][k]["answer"]
            for k in ("scene", "meaning", "key_info")
        }
        expression_service.submit_scenario(
            SCN_RESTAURANT, "s1", answers=answers,
            listen_count_before_submit=1, reveal_used=False, duration_ms=30000,
        )
        st3 = expression_service.expression_transfer_state("s1", EXPRESSION_ID)
        self.assertEqual(st3["transfer_state"], "demonstrated")

    # 2. 切分规则
    def test_segmentation_with_context(self):
        asset = self._make_asset()
        self.repo.update_corpus_asset(asset["asset_id"], {
            "asr_segments": _fake_segments(),
            "raw_asr_text": " ".join(s["text"] for s in _fake_segments()),
            "transcript_status": "asr_raw",
            "pipeline_status": "asr_done",
        })
        result = corpus_service.run_segmentation(asset["asset_id"])
        self.assertEqual(result["clips_created"], 3)  # 两个 ≥0.8s 停顿 → 3 段
        clips = self.repo.list_corpus_clips(asset["asset_id"])
        self.assertEqual(clips[0]["start_ms"], 0)
        self.assertEqual(clips[0]["end_ms"], 8000)
        self.assertEqual(clips[1]["start_ms"], 9500)
        # 上下文保留
        self.assertIn("Let me check", clips[1]["context_before"])
        self.assertIn("Shall I book", clips[1]["context_after"])
        # 重跑清除旧候选
        result2 = corpus_service.run_segmentation(asset["asset_id"])
        self.assertEqual(result2["clips_created"], 3)
        self.assertEqual(len(self.repo.list_corpus_clips(asset["asset_id"])), 3)

    # 3. Expression 匹配(规则, candidate)
    def test_expression_matching(self):
        asset = self._make_asset()
        segs = [
            {"start_ms": 0, "end_ms": 6000, "text": "Sorry, we're fully booked tonight.", "avg_logprob": -0.2, "no_speech_prob": 0.01},
            {"start_ms": 7500, "end_ms": 13500, "text": "No vacancies at all, I'm afraid.", "avg_logprob": -0.2, "no_speech_prob": 0.01},
        ]
        self.repo.update_corpus_asset(asset["asset_id"], {
            "asr_segments": segs,
            "raw_asr_text": "x",
            "transcript_status": "asr_raw",
            "pipeline_status": "asr_done",
        })
        corpus_service.run_segmentation(asset["asset_id"])
        r = corpus_service.run_matching(asset["asset_id"])
        self.assertGreaterEqual(r["matches"], 1)
        clips = self.repo.list_corpus_clips(asset["asset_id"])
        all_matches = [m for c in clips for m in c["expression_matches"]]
        fb = next(m for m in all_matches if m["expression_id"] == "exp_fully_booked")
        self.assertEqual(fb["match_type"], "exact_expression")
        self.assertEqual(fb["match_method"], "verbatim")  # 原文逐字命中
        self.assertEqual(fb["confidence"], 1.0)
        self.assertEqual(fb["status"], "candidate")  # 命中只是候选
        # related_expression 命中(help out 的 related)
        rel = next(m for m in all_matches if m["match_type"] == "related_expression")
        self.assertIn(rel["match_method"], ("verbatim", "normalized"))
        self.assertLess(rel["confidence"], fb["confidence"])  # related 置信度低于 exact
        # 每条 match 都必须带匹配方式与置信度
        for m in all_matches:
            self.assertIn(m["match_type"],
                          ("exact_expression", "target_surface", "related_expression"))
            self.assertIn(m["match_method"], ("verbatim", "normalized"))
            self.assertGreater(m["confidence"], 0)
        self.assertEqual(
            self.repo.get_corpus_asset(asset["asset_id"])["pipeline_status"], "matched"
        )

    # 4. 许可门控
    def test_permission_gate(self):
        asset = self._make_asset(permission="unverified")
        r = corpus_service.review_asset(asset["asset_id"], "approve")
        self.assertEqual(r["error"], "permission")
        # 教师补许可元数据后可批准
        corpus_service.update_asset_metadata(asset["asset_id"], {
            "permission_status": "verified_open_license",
        })
        r2 = corpus_service.review_asset(asset["asset_id"], "approve")
        self.assertEqual(r2["review_status"], "approved")
        self.assertTrue(r2["reviewed_at"])

    # 5. clip 编辑版本链
    def test_clip_revision_chain(self):
        asset = self._make_asset()
        self.repo.update_corpus_asset(asset["asset_id"], {
            "asr_segments": _fake_segments(),
            "raw_asr_text": "ORIGINAL_ASR",
            "transcript_status": "asr_raw",
            "pipeline_status": "asr_done",
        })
        corpus_service.run_segmentation(asset["asset_id"])
        clip = self.repo.list_corpus_clips(asset["asset_id"])[1]
        corpus_service.review_clip(clip["clip_id"], "approve")
        # 实质修改 transcript → content_revision+1, 回落 pending
        updated = corpus_service.update_clip(clip["clip_id"], {"transcript": "I'm afraid we're fully booked on Friday. We only have rooms on Saturday."})
        self.assertEqual(updated["revision"], 2)
        self.assertEqual(updated["content_revision"], 2)
        self.assertEqual(updated["review_status"], "pending_teacher")
        self.assertEqual(len(updated["revisions_log"]), 1)
        self.assertEqual(updated["revisions_log"][0]["bump"], "content")
        # 原始 ASR 不被覆盖
        self.assertEqual(
            self.repo.get_corpus_asset(asset["asset_id"])["raw_asr_text"], "ORIGINAL_ASR"
        )
        # 教师改过 transcript 后: asset 联动 teacher_edited, cleaned_text 按 clip 时间序重组
        asset_after = self.repo.get_corpus_asset(asset["asset_id"])
        self.assertEqual(asset_after["transcript_status"], "teacher_edited")
        clips = self.repo.list_corpus_clips(asset["asset_id"])
        expected = " ".join(
            (c["transcript"] or "").strip()
            for c in sorted(clips, key=lambda c: c["start_ms"])
            if (c["transcript"] or "").strip()
        )
        self.assertEqual(asset_after["cleaned_text"], expected)
        self.assertIn("fully booked on Friday", asset_after["cleaned_text"])
        # 非法区间
        bad = corpus_service.update_clip(clip["clip_id"], {"start_ms": 9000, "end_ms": 8000})
        self.assertEqual(bad["error"], "bad_range")

    # 6. 教师鉴权
    def test_teacher_auth(self):
        os.environ["TEACHER_TOKEN"] = "secret-test-token"
        try:
            from fastapi import FastAPI
            from fastapi.testclient import TestClient
            from listening.router import router

            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)
            r1 = client.get("/api/listening/teacher/expressions")
            self.assertEqual(r1.status_code, 401)
            r2 = client.get("/api/listening/teacher/expressions",
                           headers={"X-Teacher-Token": "wrong"})
            self.assertEqual(r2.status_code, 401)
            r3 = client.get("/api/listening/teacher/expressions",
                            headers={"X-Teacher-Token": "secret-test-token"})
            self.assertEqual(r3.status_code, 200)
            r4 = client.get("/api/listening/teacher/corpus/assets")
            self.assertEqual(r4.status_code, 401)  # corpus 同样受保护
        finally:
            del os.environ["TEACHER_TOKEN"]


if __name__ == "__main__":
    unittest.main(verbosity=2)
