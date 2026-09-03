# -*- coding: utf-8 -*-
"""V2.2 Continuous Practice Pilot 回归测试(无 pytest 依赖):

    venv/Scripts/python.exe -m tests.test_v22_practice

覆盖:
  A. Bundle 白名单 — 无 claimed_answer/hash/provenance/transcript 等禁止字段
  B. Release gate — gate 关闭时全部端点 403 / 空列表
  C. First pass 有效性 — 无心跳覆盖时 round1 拒绝; 有效心跳链后放行
  D. Round1 — 只返回数量, 响应 blob 不含逐题对错/答案
  E. Blind replay 门禁 — 无有效 replay 时 round2 拒绝
  F. Recovery 语义 — round2 答对记 recovered_after_full_replay; 结果只有数量
  G. 中断恢复 — pass_start 无 end → 回 first_pass(允许重开); 无 evidence
  H. 全对直通 — round1 全对直接 result_final, 无 round2
  I. 事件白名单 — 非法事件类型被丢弃
  J. 内容 pin — cp_responses 携带创建时 pin 的 revision/hash
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ["ALLOW_UNRELEASED_LISTENING_V2"] = "true"

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from listening import router as listening_router_mod  # noqa: E402
from listening import v2_exam_service, v2_practice_service  # noqa: E402
from listening.repository import StudentRepository  # noqa: E402

SET1 = "cet6_202606_set1_u1"   # 34300–139780ms, 答案 B/B/B
SET2 = "cet6_202606_set2_u1"   # 142170–248960ms, 答案 C/B/B


def _pass_events(prefix: str, start: int, end: int) -> list[dict]:
    """构造一条有效连续播放事件链: start → 每 5s 心跳 → end。"""
    events = [{"event_type": f"{prefix}_start", "payload": {"position_ms": start}}]
    pos = start + 5000
    while pos < end - 2000:
        events.append({"event_type": f"{prefix}_progress",
                       "payload": {"position_ms": pos}})
        pos += 5000
    events.append({"event_type": f"{prefix}_progress",
                   "payload": {"position_ms": end - 1500}})
    events.append({"event_type": f"{prefix}_end",
                   "payload": {"position_ms": end - 1200}})
    return events


class PracticeTestBase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        repo = StudentRepository(Path(self._tmp.name) / "test.db")
        self.repo = repo
        self._orig = v2_practice_service.student_repo
        v2_practice_service.student_repo = repo
        self.addCleanup(self._restore)
        app = FastAPI()
        app.include_router(listening_router_mod.router)
        self.client = TestClient(app)

    def _restore(self):
        conn = getattr(self.repo._local, "conn", None)
        if conn is not None:
            conn.close()
            self.repo._local.conn = None
        v2_practice_service.student_repo = self._orig
        self._tmp.cleanup()

    def _create(self, material_id: str = SET1) -> str:
        r = self.client.post("/api/listening/v2/practice/sessions",
                             json={"student_id": "t", "material_id": material_id})
        assert r.status_code == 200, r.text
        return r.json()["data"]["session_id"]

    def _events(self, sid: str, events: list[dict]) -> int:
        r = self.client.post(f"/api/listening/v2/practice/sessions/{sid}/events",
                             json={"student_id": "t", "events": events})
        assert r.status_code == 200, r.text
        return r.json()["data"]["saved"]

    def _state(self, sid: str) -> dict:
        r = self.client.get(f"/api/listening/v2/practice/sessions/{sid}")
        assert r.status_code == 200, r.text
        return r.json()["data"]

    def _valid_first_pass(self, sid: str, material_id: str = SET1):
        m = v2_practice_service.practice_registry.get(material_id)
        self._events(sid, _pass_events("cp_pass", m["material_start_ms"],
                                       m["material_end_ms"]))


class BundleWhitelistTest(unittest.TestCase):
    """A. bundle 白名单 + 递归断言。"""

    def test_no_forbidden_keys(self):
        for mid in (SET1, SET2):
            dto = v2_practice_service.material_bundle(mid)
            self.assertIsNotNone(dto)
            v2_practice_service._assert_cp_clean(dto)  # 内部已跑, 显式再跑

    def test_no_answer_or_hash_in_blob(self):
        for mid in (SET1, SET2):
            dto = v2_practice_service.material_bundle(mid)
            blob = json.dumps(dto, ensure_ascii=False)
            for bad in ("claimed_answer", "content_hash", "supporting_segments",
                        "transcript", "provenance", "review_status",
                        "correct_answer", "boundary_status"):
                self.assertNotIn(bad, blob, f"{mid} 泄露 {bad}")

    def test_shape(self):
        dto = v2_practice_service.material_bundle(SET1)
        self.assertEqual(len(dto["checks"]), 3)
        self.assertEqual(dto["audio"]["start_ms"], 34300)
        self.assertEqual(dto["audio"]["end_ms"], 139780)
        for c in dto["checks"]:
            self.assertEqual({o["label"] for o in c["options"]}, {"A", "B", "C", "D"})
            self.assertEqual(set(c.keys()), {"check_id", "target_dimension",
                                             "question", "options"})
        dto2 = v2_practice_service.material_bundle(SET2)
        self.assertEqual(dto2["audio"]["start_ms"], 142170)
        self.assertEqual(dto2["audio"]["end_ms"], 248960)


class GateTest(unittest.TestCase):
    """B. gate 关闭时 403 / 空列表。"""

    def setUp(self):
        self._old = os.environ.get("ALLOW_UNRELEASED_LISTENING_V2")
        os.environ["ALLOW_UNRELEASED_LISTENING_V2"] = "false"
        self.addCleanup(self._restore)
        app = FastAPI()
        app.include_router(listening_router_mod.router)
        self.client = TestClient(app)

    def _restore(self):
        if self._old is None:
            os.environ.pop("ALLOW_UNRELEASED_LISTENING_V2", None)
        else:
            os.environ["ALLOW_UNRELEASED_LISTENING_V2"] = self._old

    def test_gate_closed(self):
        self.assertEqual(self.client.get(
            "/api/listening/v2/practice/materials").json()["data"], [])
        for url in (f"/api/listening/v2/practice/materials/{SET1}",
                    f"/api/listening/v2/practice/materials/{SET1}/audio"):
            self.assertEqual(self.client.get(url).status_code, 403)
        r = self.client.post("/api/listening/v2/practice/sessions",
                             json={"student_id": "t", "material_id": SET1})
        self.assertEqual(r.status_code, 403)

    def test_gate_closed_covers_session_endpoints(self):
        """gate 关闭时: 会话级端点同样不可绕过(无论 session 是否存在)。"""
        sid = "cps_nonexistent"
        self.assertEqual(self.client.get(
            "/api/listening/v2/practice/sessions/find",
            params={"material_id": SET1, "student_id": "t"}).status_code, 403)
        self.assertEqual(self.client.get(
            f"/api/listening/v2/practice/sessions/{sid}").status_code, 403)
        self.assertEqual(self.client.post(
            f"/api/listening/v2/practice/sessions/{sid}/events",
            json={"student_id": "t", "events": [
                {"event_type": "cp_pass_start", "payload": {"position_ms": 34300}}]},
        ).status_code, 403)
        self.assertEqual(self.client.post(
            f"/api/listening/v2/practice/sessions/{sid}/round1",
            json={"answers": {}}).status_code, 403)
        self.assertEqual(self.client.post(
            f"/api/listening/v2/practice/sessions/{sid}/round2",
            json={"answers": {}}).status_code, 403)


class GateBypassMidSessionTest(PracticeTestBase):
    """B2. gate 在 session 创建后关闭: 已有 session 也不得继续推进。"""

    def test_existing_session_blocked_after_gate_closes(self):
        sid = self._create()
        old = os.environ.get("ALLOW_UNRELEASED_LISTENING_V2")
        os.environ["ALLOW_UNRELEASED_LISTENING_V2"] = "false"
        try:
            self.assertEqual(self.client.post(
                f"/api/listening/v2/practice/sessions/{sid}/events",
                json={"student_id": "smoke", "events": [
                    {"event_type": "cp_pass_start",
                     "payload": {"position_ms": 34300}}]},
            ).status_code, 403)
            self.assertEqual(self.client.post(
                f"/api/listening/v2/practice/sessions/{sid}/round1",
                json={"answers": {}}).status_code, 403)
            self.assertEqual(self.client.get(
                f"/api/listening/v2/practice/sessions/{sid}").status_code, 403)
        finally:
            if old is None:
                os.environ.pop("ALLOW_UNRELEASED_LISTENING_V2", None)
            else:
                os.environ["ALLOW_UNRELEASED_LISTENING_V2"] = old
        # 恢复 gate 后 session 仍可用(不丢数据)
        self.assertEqual(self.client.get(
            f"/api/listening/v2/practice/sessions/{sid}").status_code, 200)


class PlaybackRateLockTest(unittest.TestCase):
    """K. 学生端 first_pass 播放速度锁定: 源码级断言。

    - RangePlayer 不提供倍速 UI(audio 无 controls 属性)
    - startPlay 强制 playbackRate = 1.0, ratechange 时重置回 1.0
    - Practice 页面不含倍速选项文案
    """

    SRC = Path(__file__).resolve().parent.parent.parent / \
        "frontend" / "src" / "components" / "listening" / "RangePlayer.vue"
    VIEW = Path(__file__).resolve().parent.parent.parent / \
        "frontend" / "src" / "views" / "listening" / "ListeningPracticeV2View.vue"

    def test_no_native_controls_or_speed_ui(self):
        src = self.SRC.read_text(encoding="utf-8")
        view = self.VIEW.read_text(encoding="utf-8")
        # audio 标签不得带 controls(原生控件含速度菜单)
        audio_tag = src[src.index("<audio"):src.index("</audio>")]
        self.assertNotIn(" controls", audio_tag)
        # 不得出现倍速 UI 文案
        for token in ("倍速", "0.75x", "1.25x", "1.5x", "2x", "playbackRate"):
            self.assertNotIn(token, view)
        # 视图中不得有速度选择控件
        self.assertNotIn("playback-rate", view)

    def test_rate_locked_to_1(self):
        src = self.SRC.read_text(encoding="utf-8")
        self.assertIn("el.playbackRate = 1.0", src)       # startPlay 强制
        self.assertIn("@ratechange", src)                  # 监听外部改速
        self.assertIn("handleRateChange", src)
        self.assertIn("playbackRate !== 1.0", src)         # 立即重置


class FirstPassValidityTest(PracticeTestBase):
    """C. first pass 有效性判定。"""

    def test_round1_rejected_without_valid_pass(self):
        sid = self._create()
        # 只有 start+end, 无心跳覆盖 → 无效
        self._events(sid, [
            {"event_type": "cp_pass_start", "payload": {"position_ms": 34300}},
            {"event_type": "cp_pass_end", "payload": {"position_ms": 139000}},
        ])
        r = self.client.post(f"/api/listening/v2/practice/sessions/{sid}/round1",
                             json={"answers": {}})
        self.assertEqual(r.status_code, 409)
        self.assertIn("no_valid_first_pass", r.text)

    def test_end_event_counts_as_terminal_evidence(self):
        """心跳相位竞态回归: 末心跳距终点 >2s 但 <=9s, end 事件本身证明到达。

        真实案例: Set2 pass1(2026-08-29 浏览器实测), 末心跳 246213,
        end 248960, 间隔 2747ms —— 学生真实听完却曾误判 invalid。"""
        sid = self._create(material_id=SET2)
        events = [{"event_type": "cp_pass_start",
                   "payload": {"position_ms": 142170}}]
        pos = 142171
        while pos < 246213:
            events.append({"event_type": "cp_pass_progress",
                           "payload": {"position_ms": pos}})
            pos += 4514
        events.append({"event_type": "cp_pass_progress",
                       "payload": {"position_ms": 246213}})
        events.append({"event_type": "cp_pass_end",
                       "payload": {"position_ms": 248960}})
        self._events(sid, events)
        state = self._state(sid)
        self.assertTrue(state["first_pass_valid"])
        self.assertEqual(state["stage"], "check_round_1")

    def test_end_event_far_after_last_heartbeat_still_invalid(self):
        """end 事件不能掩盖中断: 末心跳距 end 超过一个心跳周期 → 无效。"""
        sid = self._create(material_id=SET2)
        events = [{"event_type": "cp_pass_start",
                   "payload": {"position_ms": 142170}}]
        pos = 142171
        while pos < 230000:
            events.append({"event_type": "cp_pass_progress",
                           "payload": {"position_ms": pos}})
            pos += 4500
        # 末心跳 ~230000, end 248960: 缺口 ~19s >> 9s, 覆盖不足且心跳断档
        events.append({"event_type": "cp_pass_end",
                       "payload": {"position_ms": 248960}})
        self._events(sid, events)
        state = self._state(sid)
        self.assertFalse(state["first_pass_valid"])
        self.assertEqual(state["stage"], "first_pass")

    def test_interrupted_pass_invalid_and_restartable(self):
        sid = self._create()
        self._events(sid, [
            {"event_type": "cp_pass_start", "payload": {"position_ms": 34300}},
            {"event_type": "cp_pass_progress", "payload": {"position_ms": 50000}},
            {"event_type": "cp_pass_interrupted", "payload": {"position_ms": 51200}},
        ])
        state = self._state(sid)
        self.assertEqual(state["stage"], "first_pass")  # 允许重开
        self.assertFalse(state["first_pass_valid"])
        # 重开后完整播放 → valid
        self._valid_first_pass(sid)
        state = self._state(sid)
        self.assertTrue(state["first_pass_valid"])
        self.assertEqual(state["stage"], "check_round_1")
        self.assertEqual(state["pass_attempt_count"], 2)


class Round1BlindnessTest(PracticeTestBase):
    """D. round1 只返回数量。"""

    def test_round1_returns_counts_only(self):
        sid = self._create()
        self._valid_first_pass(sid)
        r = self.client.post(f"/api/listening/v2/practice/sessions/{sid}/round1",
                             json={"answers": {
                                 "cp_cet6_202606_set1_u1_01": "A",  # 错(正确 B)
                                 "cp_cet6_202606_set1_u1_02": "B",
                                 "cp_cet6_202606_set1_u1_03": "B",
                             }})
        self.assertEqual(r.status_code, 200, r.text)
        blob = json.dumps(r.json(), ensure_ascii=False)
        self.assertNotIn("is_correct", blob)
        self.assertNotIn("claimed_answer", blob)
        self.assertEqual(r.json()["data"]["first_pass_score"],
                         {"correct": 2, "total": 3})
        # 进入 blind_full_replay; state 只给数量
        state = self._state(sid)
        self.assertEqual(state["stage"], "blind_full_replay")
        self.assertEqual(state["first_pass_score"], {"correct": 2, "total": 3})
        blob = json.dumps(state, ensure_ascii=False)
        for bad in ("is_correct", "claimed_answer", "content_hash",
                    "round2_checks"):
            self.assertNotIn(bad, blob)

    def test_result_final_no_round1_correct(self):
        """K1 fix: result_final state 与 summary payload 均不含逐题对错字段。"""
        sid = self._create()
        self._valid_first_pass(sid)
        self.client.post(f"/api/listening/v2/practice/sessions/{sid}/round1",
                         json={"answers": {
                             "cp_cet6_202606_set1_u1_01": "A",   # 错
                             "cp_cet6_202606_set1_u1_02": "B",
                             "cp_cet6_202606_set1_u1_03": "B",
                         }})
        # 有效 replay → 进 check_round_2
        self._events(sid, _pass_events("cp_replay", 34300, 139780))
        # round2
        self.client.post(f"/api/listening/v2/practice/sessions/{sid}/round2",
                         json={"answers": {"cp_cet6_202606_set1_u1_01": "B"}})
        # 验证 result_final state 不含逐题对错
        state = self._state(sid)
        self.assertEqual(state["stage"], "result_final")
        state_blob = json.dumps(state, ensure_ascii=False)
        self.assertNotIn("round1_correct", state_blob,
                         "K1: round1_correct 不得出现在 result_final state")
        self.assertNotIn("is_correct", state_blob,
                         "K1: is_correct 不得出现在 result_final state")
        # 验证 checks 列表只含 check_id + dimension
        result = state.get("result", {})
        for item in result.get("checks", []):
            self.assertNotIn("round1_correct", item,
                             f"K1: checks item {item['check_id']} 含 round1_correct")
        # 验证 summary 事件 payload 也不含逐题对错
        summaries = self.repo.list_cp_events(sid, "cp_session_summary")
        self.assertEqual(len(summaries), 1)
        summary_blob = json.dumps(summaries[0]["payload"], ensure_ascii=False)
        self.assertNotIn("round1_correct", summary_blob,
                         "K1: cp_session_summary payload 含 round1_correct")


class RecoveryFlowTest(PracticeTestBase):
    """E/F. blind replay 门禁 + recovery 语义 + 最终结果。"""

    def test_full_recovery_flow(self):
        sid = self._create()
        self._valid_first_pass(sid)
        self.client.post(f"/api/listening/v2/practice/sessions/{sid}/round1",
                         json={"answers": {
                             "cp_cet6_202606_set1_u1_01": "A",
                             "cp_cet6_202606_set1_u1_02": "B",
                             "cp_cet6_202606_set1_u1_03": "B",
                         }})
        # E: 无有效 replay 时 round2 拒绝
        r = self.client.post(f"/api/listening/v2/practice/sessions/{sid}/round2",
                             json={"answers": {"cp_cet6_202606_set1_u1_01": "B"}})
        self.assertEqual(r.status_code, 409)
        self.assertIn("no_valid_replay", r.text)
        # 有效 blind replay
        self._events(sid, _pass_events("cp_replay", 34300, 139780))
        state = self._state(sid)
        self.assertEqual(state["stage"], "check_round_2")
        # round2 只出错题, 选项为服务端打乱的顺序
        r2 = state["round2_checks"]
        self.assertEqual(len(r2), 1)
        self.assertEqual(r2[0]["check_id"], "cp_cet6_202606_set1_u1_01")
        self.assertEqual({o["label"] for o in r2[0]["options"]}, {"A", "B", "C", "D"})
        # F: recovery 答对 → recovered; 结果只有数量
        r = self.client.post(f"/api/listening/v2/practice/sessions/{sid}/round2",
                             json={"answers": {"cp_cet6_202606_set1_u1_01": "B"}})
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()["data"]
        self.assertEqual(data["recovered"], {"correct": 1, "total": 1})
        self.assertIn("首次抓住:2/3", data["display"])
        self.assertIn("完整重听后恢复:1/1", data["display"])
        blob = json.dumps(data, ensure_ascii=False)
        self.assertNotIn("is_correct", blob)
        # 最终状态 + summary 事件(幂等)
        state = self._state(sid)
        self.assertEqual(state["stage"], "result_final")
        self.assertFalse(state["profile_eligible"])
        summaries = self.repo.list_cp_events(sid, "cp_session_summary")
        self.assertEqual(len(summaries), 1)
        payload = summaries[0]["payload"]
        self.assertEqual(payload["first_pass_score"], "2/3")
        self.assertEqual(payload["recovered"], "1/1")
        self.assertFalse(payload["profile_eligible"])
        # observation 词表: 不含能力推断词
        for obs in payload["observations"]:
            for banned in ("attention", "working_memory", "processing_speed"):
                self.assertNotIn(banned, obs)
        # cp_responses 语义: round2 正确行带 recovered 标记
        r2_rows = self.repo.list_cp_responses(sid, round_=2)
        self.assertEqual(len(r2_rows), 1)
        self.assertEqual(r2_rows[0]["recovered_after_full_replay"], 1)


class AllCorrectDirectTest(PracticeTestBase):
    """H. 全对直通 result_final。"""

    def test_all_correct_skips_recovery(self):
        sid = self._create(SET2)
        self._valid_first_pass(sid, SET2)
        r = self.client.post(f"/api/listening/v2/practice/sessions/{sid}/round1",
                             json={"answers": {
                                 "cp_cet6_202606_set2_u1_01": "C",
                                 "cp_cet6_202606_set2_u1_02": "B",
                                 "cp_cet6_202606_set2_u1_03": "B",
                             }})
        self.assertEqual(r.status_code, 200, r.text)
        state = self._state(sid)
        self.assertEqual(state["stage"], "result_final")
        self.assertEqual(state["result"]["display"],
                         "首次抓住:3/3;完整重听后恢复:0/0")
        summaries = self.repo.list_cp_events(sid, "cp_session_summary")
        self.assertEqual(len(summaries), 1)


class EventWhitelistTest(PracticeTestBase):
    """I. 非法事件类型丢弃。"""

    def test_unknown_events_dropped(self):
        sid = self._create()
        saved = self._events(sid, [
            {"event_type": "cp_preview_open", "payload": {}},
            {"event_type": "hack_the_planet", "payload": {}},
            {"event_type": "cp_preview_mark",
             "payload": {"check_id": "cp_cet6_202606_set1_u1_01",
                         "focus_type": "人物"}},
        ])
        self.assertEqual(saved, 2)
        state = self._state(sid)
        self.assertEqual(state["stage"], "option_preview")
        self.assertTrue(state["preview"]["preview_used"])
        self.assertEqual(state["preview"]["selected_focus_types"],
                         {"cp_cet6_202606_set1_u1_01": "人物"})

    def test_payload_unknown_fields_stripped(self):
        """K2 fix: payload 白名单 — attention/transcript 等任意字段不得写入 DB。"""
        sid = self._create()
        # 发含敏感字段的事件
        r = self.client.post(f"/api/listening/v2/practice/sessions/{sid}/events",
                             json={"student_id": "t", "events": [
                                 {"event_type": "cp_pass_start",
                                  "payload": {
                                      "client_at": "2026-01-01T00:00:00Z",
                                      "position_ms": 0,
                                      "attention": 0.95,           # 禁止字段
                                      "transcript": "hello world",  # 禁止字段
                                      "correct_answer": "B",        # 禁止字段
                                  }},
                             ]})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["data"]["saved"], 1)
        # 验证存入 DB 的事件 payload 不含敏感字段
        stored = self.repo.list_cp_events(sid, "cp_pass_start")
        self.assertEqual(len(stored), 1)
        payload = stored[0].get("payload") or {}
        for bad in ("attention", "transcript", "correct_answer"):
            self.assertNotIn(bad, payload,
                             f"K2: '{bad}' 不得写入 cp_pass_start payload")
        # 合法字段保留
        self.assertIn("position_ms", payload)

    def test_student_id_mismatch_rejected(self):
        """K2 fix: student_id 与 session 属主不符时返回 403。"""
        sid = self._create()   # owner = "t"
        r = self.client.post(f"/api/listening/v2/practice/sessions/{sid}/events",
                             json={"student_id": "other_student",
                                   "events": [{"event_type": "cp_pass_start",
                                               "payload": {}}]})
        self.assertEqual(r.status_code, 403,
                         "K2: 冒名写事件应返回 403，实际: " + str(r.status_code))


class ContentPinTest(PracticeTestBase):
    """J. cp_responses 携带 pin 的 revision/hash; 内容漂移不悄悄生效。"""

    def test_responses_pinned(self):
        sid = self._create()
        self._valid_first_pass(sid)
        self.client.post(f"/api/listening/v2/practice/sessions/{sid}/round1",
                         json={"answers": {
                             "cp_cet6_202606_set1_u1_01": "B",
                             "cp_cet6_202606_set1_u1_02": "B",
                             "cp_cet6_202606_set1_u1_03": "B",
                         }})
        rows = self.repo.list_cp_responses(sid, round_=1)
        expected = {
            "cp_cet6_202606_set1_u1_01": (1, "8339f45b95cae6f5bfc54a54d84b68b26bcc0e5c3cd85b0c331ff483ec66e12e"),
            "cp_cet6_202606_set1_u1_02": (3, "2827fcaebdc892f038dd46e707169430c5dc0c9b88cf433182129d838bef8b44"),
            "cp_cet6_202606_set1_u1_03": (2, "29c85d0da8102a123780443c491e3dd49de34fdc9f5b1365c61a37327072a43c"),
        }
        self.assertEqual(len(rows), 3)
        for r in rows:
            rev, h = expected[r["check_id"]]
            self.assertEqual(r["content_revision"], rev)
            self.assertEqual(r["content_hash"], h)
        # 恢复接口可找回 session
        r = self.client.get("/api/listening/v2/practice/sessions/find",
                            params={"material_id": SET1, "student_id": "t"})
        self.assertEqual(r.json()["data"]["session_id"], sid)

    def test_content_drift_does_not_retroactively_apply(self):
        """session 开始后内容 revision 变化: 旧 session 仍按 pin 判分并标记 drift。"""
        sid = self._create()
        self._valid_first_pass(sid)
        material = v2_practice_service.practice_registry.get(SET1)
        orig_hash = material["checks"][0]["content_hash_full"]
        try:
            # 模拟教师在 session 开始后修改了 check 01 的内容(hash 变化)
            material["checks"][0]["content_hash_full"] = "0" * 64
            material["checks"][0]["revision"] = 99
            material["checks"][0]["claimed_answer"] = "C"  # 新版本"答案"变了
            r = self.client.post(f"/api/listening/v2/practice/sessions/{sid}/round1",
                                 json={"answers": {
                                     "cp_cet6_202606_set1_u1_01": "B",  # 旧版本答案
                                     "cp_cet6_202606_set1_u1_02": "B",
                                     "cp_cet6_202606_set1_u1_03": "B",
                                 }})
            self.assertEqual(r.status_code, 200, r.text)
            rows = self.repo.list_cp_responses(sid, round_=1)
            row1 = [r0 for r0 in rows if r0["check_id"] == "cp_cet6_202606_set1_u1_01"][0]
            # pin 的 revision/hash 不变
            self.assertEqual(row1["content_revision"], 1)
            self.assertEqual(row1["content_hash"], orig_hash)
            # 判分基准也不悄悄切到新版本
            self.assertEqual(row1["is_correct"], 1)
            # state 明确标记 drift
            state = self._state(sid)
            self.assertTrue(state["content_drifted"])
        finally:
            material["checks"][0]["content_hash_full"] = orig_hash
            material["checks"][0]["revision"] = 1
            material["checks"][0]["claimed_answer"] = "B"


if __name__ == "__main__":
    unittest.main(verbosity=2)
