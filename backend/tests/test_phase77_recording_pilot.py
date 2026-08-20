# -*- coding: utf-8 -*-
"""Phase 7.7 Human Recording Pilot 准备工程回归测试(无 pytest 依赖):

    venv/Scripts/python.exe -m tests.test_phase77_recording_pilot

覆盖验收底线:
1. revision 拆分: 标签编辑只 bump metadata_revision, 实质编辑才 bump
   content_revision 并回落待审核; 旧 revision 列与 content_revision 同步
2. 授权门控(批准): owned 素材缺 consent_id 时 asset/clip 均不可批准
3. 授权门控(学生端): owned 素材授权被移除后, 列表与音频切片立即不可见
4. 教师手动匹配: communicative_equivalent 只能由教师建立(teacher_judgement),
   规则匹配器永不自动产生; 非法类型/不存在表达/重复关联均被拒绝
5. create_asset 授权字段持久化
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


CONSENT = {
    "consent_id": "CONSENT-2026-0001",
    "speaker_ids": ["SPK_A", "SPK_B"],
    "commercial_permission": True,
    "editing_permission": True,
    "ai_processing_permission": True,
    "recorded_at": "2026-08-20",
}


class RecordingPilotTest(unittest.TestCase):
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

    def _make_asset(self, permission="verified_open_license", consent=None) -> dict:
        return corpus_service.create_asset(
            _wav_bytes(60.0), "rec.wav", "真人录音", "SelfRecorded",
            None, "self_recorded", permission, consent=consent,
        )

    # 1. revision 拆分
    def test_revision_split_content_vs_metadata(self):
        asset = self._make_asset()
        clip = corpus_service.create_clip(asset["asset_id"], 10000, 25000,
                                          transcript="Could we maybe postpone it?")
        corpus_service.review_clip(clip["clip_id"], "approve")
        cid = clip["clip_id"]

        # 标签编辑: 只 bump metadata_revision, 不打断 approved 状态
        c1 = corpus_service.update_clip(cid, {"difficulty": "easy"})
        self.assertEqual(c1["content_revision"], 1)
        self.assertEqual(c1["metadata_revision"], 2)
        self.assertEqual(c1["revision"], 1)  # 旧列 = content_revision
        self.assertEqual(c1["review_status"], "approved")
        self.assertEqual(c1["revisions_log"][-1]["bump"], "metadata")

        # 实质编辑(transcript): bump content_revision + 回落待审核
        c2 = corpus_service.update_clip(cid, {"transcript": "Could we postpone it?"})
        self.assertEqual(c2["content_revision"], 2)
        self.assertEqual(c2["revision"], 2)
        self.assertEqual(c2["metadata_revision"], 2)  # 不再连带膨胀
        self.assertEqual(c2["review_status"], "pending_teacher")
        self.assertEqual(c2["revisions_log"][-1]["bump"], "content")

        # 区间调整同样属于实质修改
        c3 = corpus_service.update_clip(cid, {"end_ms": 24000})
        self.assertEqual(c3["content_revision"], 3)
        self.assertEqual(c3["metadata_revision"], 2)

    # 2. 授权门控: 批准
    def test_consent_gate_on_approve(self):
        # owned 无 consent_id: asset 和 clip 都批不了
        asset = self._make_asset(permission="owned")
        r = corpus_service.review_asset(asset["asset_id"], "approve")
        self.assertEqual(r["error"], "permission")
        clip = corpus_service.create_clip(asset["asset_id"], 10000, 20000)
        r2 = corpus_service.review_clip(clip["clip_id"], "approve")
        self.assertEqual(r2["error"], "permission")

        # 补上 consent_id 后可以批准
        corpus_service.update_asset_metadata(
            asset["asset_id"], {"consent_id": "CONSENT-2026-0001"})
        r3 = corpus_service.review_asset(asset["asset_id"], "approve")
        self.assertEqual(r3["review_status"], "approved")
        r4 = corpus_service.review_clip(clip["clip_id"], "approve")
        self.assertEqual(r4["review_status"], "approved")

        # verified_open_license 公开语料不需要 consent
        asset2 = self._make_asset()
        self.assertEqual(
            corpus_service.review_asset(asset2["asset_id"], "approve")["review_status"],
            "approved")

    # 3. 授权门控: 学生端
    def test_consent_gate_student_side(self):
        asset = self._make_asset(permission="owned", consent=CONSENT)
        corpus_service.review_asset(asset["asset_id"], "approve")
        clip = corpus_service.create_clip(asset["asset_id"], 10000, 25000,
                                          transcript="hello")
        corpus_service.review_clip(clip["clip_id"], "approve")
        self.assertEqual(len(corpus_service.list_approved_clips()), 1)
        self.assertIsNotNone(corpus_service.clip_audio_slice(clip["clip_id"]))

        # 授权记录被移除(模拟撤回): 学生端立即不可见
        self.repo.update_corpus_asset(asset["asset_id"], {"consent_id": None})
        self.assertEqual(corpus_service.list_approved_clips(), [])
        self.assertIsNone(corpus_service.clip_audio_slice(clip["clip_id"]))

    # 4. 教师手动匹配(communicative_equivalent)
    def test_teacher_add_communicative_equivalent(self):
        asset = self._make_asset()
        clip = corpus_service.create_clip(asset["asset_id"], 10000, 25000,
                                          transcript="sorry, we don't have any rooms available")
        cid = clip["clip_id"]

        # 规则匹配器: "we don't have any rooms available" 不会命中
        # fully booked 的任何登记形态, 更不会产生 communicative_equivalent
        corpus_service.run_matching(asset["asset_id"])
        after = corpus_service.student_repo.get_corpus_clip(cid)
        for m in after["expression_matches"]:
            self.assertNotEqual(m["match_type"], "communicative_equivalent")

        # 教师听完判断: 功能等价 fully booked, 手动建立
        r = corpus_service.add_clip_match(
            cid, "exp_fully_booked", "we don't have any rooms available",
            "communicative_equivalent", note="真人口语等价说法, 未使用目标词")
        m = r["expression_matches"][-1]
        self.assertEqual(m["status"], "approved")
        self.assertEqual(m["match_method"], "teacher_judgement")
        self.assertEqual(m["match_type"], "communicative_equivalent")
        self.assertEqual(m["confidence"], 0.5)
        self.assertTrue(m["note"])

        # 非法类型 / 不存在表达 / 重复关联
        self.assertEqual(corpus_service.add_clip_match(
            cid, "exp_fully_booked", "x", "fuzzy_auto")["error"], "bad_match_type")
        self.assertEqual(corpus_service.add_clip_match(
            cid, "exp_nonexistent", "x", "exact_expression")["error"], "no_expression")
        self.assertEqual(corpus_service.add_clip_match(
            cid, "exp_fully_booked", "y", "related_expression")["error"], "duplicate")

    # 5. create_asset 授权字段持久化
    def test_consent_fields_persist(self):
        asset = self._make_asset(permission="owned", consent=CONSENT)
        got = corpus_service.student_repo.get_corpus_asset(asset["asset_id"])
        self.assertEqual(got["consent_id"], "CONSENT-2026-0001")
        self.assertEqual(got["speaker_ids"], ["SPK_A", "SPK_B"])
        self.assertTrue(got["commercial_permission"])
        self.assertTrue(got["editing_permission"])
        self.assertTrue(got["ai_processing_permission"])
        self.assertEqual(got["recorded_at"], "2026-08-20")

        # 无 consent 时字段为安全的空默认
        asset2 = self._make_asset()
        got2 = corpus_service.student_repo.get_corpus_asset(asset2["asset_id"])
        self.assertIsNone(got2["consent_id"])
        self.assertEqual(got2["speaker_ids"], [])
        self.assertFalse(got2["commercial_permission"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
