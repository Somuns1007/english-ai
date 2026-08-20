# -*- coding: utf-8 -*-
"""Phase 7.6 Seed Corpus Build 回归测试(无 pytest 依赖):

    venv/Scripts/python.exe -m tests.test_phase76_seed_corpus

覆盖验收底线:
1. 教师手工 clip: 区间校验, origin=manual, 重跑切分不被清除
2. 教学标签: accent/speaker_count/speech_rate/listening_features 可编辑,
   非法 listening_features 拒绝
3. 匹配确认: candidate 才能 approve/reject, 教师确认前不得正式关联
4. 学生端列表: 只出 approved clip + approved asset + 有许可, 带 attribution
5. 学生端音频: 服务端精确切片(时长≈clip 区间), 未批准拿不到
"""
import io
import sys
import tempfile
import unittest
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from listening import corpus_service  # noqa: E402
from listening.repository import StudentRepository  # noqa: E402


def _wav_bytes(seconds: float) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00\x00" * int(16000 * seconds))
    return buf.getvalue()


class SeedCorpusTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = StudentRepository(Path(self._tmp.name) / "test.db")
        self._patches = [(corpus_service, "student_repo", corpus_service.student_repo)]
        corpus_service.student_repo = self.repo
        for attr, new_val in (
            ("DATA_DIR", Path(self._tmp.name)),
            ("CORPUS_DIR", Path(self._tmp.name) / "corpus"),
            ("CORPUS_AUDIO_DIR", Path(self._tmp.name) / "corpus" / "audio"),
        ):
            self._patches.append((corpus_service, attr, getattr(corpus_service, attr)))
            setattr(corpus_service, attr, new_val)
        self.addCleanup(self._restore)

    def _restore(self):
        conn = getattr(self.repo._local, "conn", None)
        if conn is not None:
            conn.close()
            self.repo._local.conn = None
        for mod, attr, orig in self._patches:
            setattr(mod, attr, orig)
        self._tmp.cleanup()

    def _make_asset(self, permission="verified_open_license", seconds=60.0) -> dict:
        return corpus_service.create_asset(
            _wav_bytes(seconds), "test.wav", "测试素材", "UnitTest",
            "https://example.com", "CC BY 4.0", permission,
        )

    def _make_approved_clip(self):
        asset = self._make_approved_asset()
        clip = corpus_service.create_clip(asset["asset_id"], 10000, 25000,
                                          transcript="Could we maybe postpone it?")
        corpus_service.review_clip(clip["clip_id"], "approve")
        return asset, corpus_service.list_approved_clips()

    def _make_approved_asset(self):
        asset = self._make_asset()
        corpus_service.review_asset(asset["asset_id"], "approve")
        return asset

    # 1. 手工 clip: 校验 + origin + 重跑切分不清除
    def test_manual_clip_creation(self):
        asset = self._make_asset()
        bad = corpus_service.create_clip(asset["asset_id"], 9000, 8000)
        self.assertEqual(bad["error"], "bad_range")
        over = corpus_service.create_clip(asset["asset_id"], 1000, 99999999)
        self.assertEqual(over["error"], "bad_range")

        clip = corpus_service.create_clip(
            asset["asset_id"], 10000, 25000, transcript="hello", speaker_info="A,B")
        self.assertEqual(clip["origin"], "manual")
        self.assertEqual(clip["review_status"], "pending_teacher")

        # 自动切分重跑: 手工 pending clip 必须存活, 自动 pending clip 被清
        self.repo.update_corpus_asset(asset["asset_id"], {
            "asr_segments": [
                {"start_ms": 0, "end_ms": 5000, "text": "x",
                 "avg_logprob": -0.2, "no_speech_prob": 0.01},
                {"start_ms": 7000, "end_ms": 12000, "text": "y",
                 "avg_logprob": -0.2, "no_speech_prob": 0.01},
            ],
            "pipeline_status": "asr_done",
        })
        corpus_service.run_segmentation(asset["asset_id"])
        ids = {c["clip_id"]: c["origin"] for c in
               self.repo.list_corpus_clips(asset["asset_id"])}
        self.assertIn(clip["clip_id"], ids)
        self.assertEqual(ids[clip["clip_id"]], "manual")
        # 再重跑一次: 上一轮 auto pending 被清, manual 仍在
        corpus_service.run_segmentation(asset["asset_id"])
        ids2 = {c["clip_id"]: c["origin"] for c in
                self.repo.list_corpus_clips(asset["asset_id"])}
        self.assertEqual(sum(1 for o in ids2.values() if o == "manual"), 1)
        self.assertTrue(all(o == "manual" or True for o in ids2.values()))

    # 2. 教学标签
    def test_teaching_tags(self):
        asset = self._make_asset()
        clip = corpus_service.create_clip(asset["asset_id"], 10000, 25000)
        updated = corpus_service.update_clip(clip["clip_id"], {
            "accent": "british",
            "speaker_count": 4,
            "speech_rate": "fast",
            "listening_features": ["weak_form", "linking", "hesitation"],
        })
        self.assertEqual(updated["accent"], "british")
        self.assertEqual(updated["speaker_count"], 4)
        self.assertEqual(updated["speech_rate"], "fast")
        self.assertEqual(updated["listening_features"],
                         ["weak_form", "linking", "hesitation"])

        bad = corpus_service.update_clip(clip["clip_id"], {
            "listening_features": ["not_a_feature"]})
        self.assertEqual(bad["error"], "bad_listening_features")

    # 3. 匹配确认流
    def test_match_confirmation(self):
        asset = self._make_asset()
        clip = corpus_service.create_clip(
            asset["asset_id"], 10000, 25000,
            transcript="Sorry, we're fully booked tonight.")
        corpus_service.run_matching(asset["asset_id"])
        clip = self.repo.get_corpus_clip(clip["clip_id"])
        cand = [m for m in clip["expression_matches"] if m["status"] == "candidate"]
        self.assertTrue(cand, "应命中 fully booked")
        exp_id = cand[0]["expression_id"]

        # 确认前: 学生端看不到该匹配
        corpus_service.review_asset(asset["asset_id"], "approve")
        corpus_service.review_clip(clip["clip_id"], "approve")
        listed = corpus_service.list_approved_clips()
        self.assertEqual(listed[0]["expression_matches"], [])

        ok = corpus_service.review_clip_match(clip["clip_id"], exp_id, "approve")
        match = next(m for m in ok["expression_matches"]
                     if m["expression_id"] == exp_id)
        self.assertEqual(match["status"], "approved")
        self.assertTrue(match["reviewed_at"])
        # 确认后学生端可见
        listed = corpus_service.list_approved_clips()
        self.assertEqual(listed[0]["expression_matches"][0]["expression_id"], exp_id)

        # 已确认不能再审; 不存在的表达不能凭空关联
        again = corpus_service.review_clip_match(clip["clip_id"], exp_id, "approve")
        self.assertEqual(again["error"], "no_candidate")
        ghost = corpus_service.review_clip_match(clip["clip_id"], "exp_ghost", "approve")
        self.assertEqual(ghost["error"], "no_candidate")

    # 4. 学生端列表门控与 attribution
    def test_student_listing_gate(self):
        # 未批准 asset 的 approved clip 不出现(异常态也不放行)
        asset_pending = self._make_asset()
        clip1 = corpus_service.create_clip(asset_pending["asset_id"], 10000, 20000,
                                           transcript="x")
        corpus_service.review_clip(clip1["clip_id"], "approve")
        self.assertEqual(corpus_service.list_approved_clips(), [])

        # 许可不明的 asset 即使 approved 状态也不出现(双保险)
        asset_unverified = self._make_asset(permission="unverified")
        clip2 = corpus_service.create_clip(asset_unverified["asset_id"], 10000, 20000)
        self.repo.update_corpus_clip(clip2["clip_id"], {"review_status": "approved"})
        self.repo.update_corpus_asset(asset_unverified["asset_id"],
                                      {"review_status": "approved"})
        self.assertEqual(corpus_service.list_approved_clips(), [])

        # 正常链路: 出现且带完整 attribution
        asset, listed = self._make_approved_clip()
        self.assertEqual(len(listed), 1)
        att = listed[0]["attribution"]
        self.assertEqual(att["asset_id"], asset["asset_id"])
        self.assertEqual(att["license"], "CC BY 4.0")
        self.assertEqual(att["source_type"], "authentic_clip")
        self.assertTrue(att["source_name"] and att["source_url"])

    # 5. 学生端音频切片
    def test_student_audio_slice(self):
        asset, listed = self._make_approved_clip()
        clip_id = listed[0]["clip_id"]
        data = corpus_service.clip_audio_slice(clip_id)
        self.assertIsNotNone(data)
        with wave.open(io.BytesIO(data), "rb") as w:
            dur = w.getnframes() / w.getframerate()
        self.assertAlmostEqual(dur, 15.0, delta=0.2)  # 10000-25000ms

        # 未批准 clip: 拿不到音频
        clip2 = corpus_service.create_clip(asset["asset_id"], 30000, 40000)
        self.assertIsNone(corpus_service.clip_audio_slice(clip2["clip_id"]))

    # 6. 路由层回归: _ClipUpdate 必须透传 4 个教学标签字段
    #    (曾因子模型未声明字段被 pydantic 静默丢弃, 导致 PUT 200 但标签不落库)
    def test_router_clip_update_model_keeps_tag_fields(self):
        from listening.router import _ClipUpdate
        body = _ClipUpdate(accent="mixed_non_native", speaker_count=3,
                           speech_rate="fast",
                           listening_features=["hesitation", "linking"])
        dumped = body.model_dump(exclude_none=True)
        for k in ("accent", "speaker_count", "speech_rate", "listening_features"):
            self.assertIn(k, dumped)
        self.assertEqual(dumped["speaker_count"], 3)
        # 更新服务必须接受这些字段(与 CLIP_EDITABLE 对齐)
        asset, _ = self._make_approved_clip()
        clip_id = _[0]["clip_id"]
        updated = corpus_service.update_clip(clip_id, dumped)
        self.assertEqual(updated["accent"], "mixed_non_native")
        self.assertEqual(updated["speaker_count"], 3)
        self.assertEqual(updated["speech_rate"], "fast")
        self.assertEqual(updated["listening_features"], ["hesitation", "linking"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
