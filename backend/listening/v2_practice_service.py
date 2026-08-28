# -*- coding: utf-8 -*-
"""V2.2 Continuous Practice 服务: 两段 Pilot 材料的连续理解训练。

安全与教学原则:
  - 学生端 bundle 白名单组装 + 递归禁止字段断言(复用 v2_exam 的断言器,
    并追加 cp 专用禁词); claimed_answer / hash / provenance 永不下发。
  - release gate 与 V2.1 Exam 完全共用(student_release_allowed / 开发预览开关)。
  - 正确性判定只在服务端; round1 只返回数量, round2 只返回恢复数量,
    任何路径都不向学生返回逐题对错或正确答案。
  - 证据语义: round2 答对 = recovered_after_full_replay, 不是"第二遍理解率";
    不产生 attention/working_memory/processing_speed 类推断; profile_eligible=False。
"""
import json
import random
import threading
from pathlib import Path
from typing import Optional

from . import v2_exam_service
from .repository import DATA_DIR, student_repo

PRACTICE_DIR = DATA_DIR / "v2_practice"
CP_ITEMS_PATH = PRACTICE_DIR / "cp_items.candidate.json"
AUDIO_DIR = DATA_DIR / "audio"

# 状态机阶段
STAGES = [
    "intro", "option_preview", "first_pass", "check_round_1",
    "blind_full_replay", "check_round_2", "result_final",
]

# cp 专用禁止字段(在 v2_exam_service.FORBIDDEN_KEYS 之外追加)
CP_FORBIDDEN_KEYS = {
    "claimed_answer", "content_hash_blind", "content_hash_full",
    "supporting_segments", "boundary_status", "content_status",
    "review_pack", "release_gate", "is_correct",
    "recovered_after_full_replay", "content_manifest",
}

# dimension → observation 词根(封闭词表)
_DIM_OBS = {
    "speaker_relationship": "continuous_speaker_tracking",
    "change_tracking_attitude": "continuous_change_tracking",
    "conditional_scope": "continuous_condition_scope",
    "main_situation": "continuous_main_situation",
    "initial_vs_final_decision": "continuous_final_decision",
    "attitude_target_speaker_swap": "continuous_attitude_target",
}

# 允许的客户端事件类型(白名单)
CP_EVENT_TYPES = {
    "cp_preview_open", "cp_preview_mark", "cp_preview_skip",
    "cp_pass_start", "cp_pass_progress", "cp_pass_end", "cp_pass_interrupted",
    "cp_replay_start", "cp_replay_progress", "cp_replay_end", "cp_replay_interrupted",
}

# first pass / blind replay 有效性判定参数
_END_TOLERANCE_MS = 2000       # 距区间终点 2s 内视为到达
_HEARTBEAT_MAX_GAP_MS = 9000   # 相邻 progress 位置差上限(心跳 5s + 容差)
_COVERAGE_MIN_RATIO = 0.90     # progress 覆盖区间长度比例下限


class V2PracticeRegistry:
    """启动时加载 data/v2_practice/cp_items.candidate.json; 文件变化自动重载。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._materials: dict[str, dict] = {}
        self._signature: Optional[int] = None

    def reload_if_changed(self) -> None:
        if not CP_ITEMS_PATH.exists():
            return
        sig = CP_ITEMS_PATH.stat().st_mtime_ns
        if sig == self._signature:
            return
        data = json.loads(CP_ITEMS_PATH.read_text(encoding="utf-8"))
        materials = {m["material_id"]: m for m in data["materials"]}
        with self._lock:
            self._materials = materials
            self._signature = sig

    def get(self, material_id: str) -> Optional[dict]:
        self.reload_if_changed()
        with self._lock:
            return self._materials.get(material_id)

    def list_ids(self) -> list[str]:
        self.reload_if_changed()
        with self._lock:
            return sorted(self._materials)


practice_registry = V2PracticeRegistry()


def _gate() -> bool:
    return v2_exam_service.gate_allows()


# ---------------------------------------------------------------- 学生端 DTO

def material_summaries() -> list[dict]:
    """列表: 只含元信息, 不含题目内容。"""
    if not _gate():
        return []
    out = []
    for mid in practice_registry.list_ids():
        m = practice_registry.get(mid)
        out.append({
            "material_id": mid,
            "exam_id": m["exam_id"],
            "title": m["title"],
            "check_count": len(m["checks"]),
            "has_audio": audio_file(mid) is not None,
            "data_status": "generated_unverified",
            "student_release_allowed": False,
        })
    return out


def audio_file(material_id: str) -> Optional[Path]:
    m = practice_registry.get(material_id)
    if not m:
        return None
    path = (DATA_DIR / m["audio_path"]).resolve()
    if not str(path).startswith(str(AUDIO_DIR.resolve().parent)):
        return None
    return path if path.exists() else None


def material_bundle(material_id: str) -> Optional[dict]:
    """学生端白名单 bundle: 无答案/无 hash/无 provenance。组装后递归断言。"""
    m = practice_registry.get(material_id)
    if not m:
        return None
    dto = {
        "material_id": material_id,
        "exam_id": m["exam_id"],
        "title": m["title"],
        "audio": {
            "scope": "material_range",
            "url": f"/api/listening/v2/practice/materials/{material_id}/audio",
            "start_ms": m["material_start_ms"],
            "end_ms": m["material_end_ms"],
        },
        "checks": [
            {
                "check_id": c["check_id"],
                "target_dimension": c["target_dimension"],
                "question": c["question"],
                "options": [
                    {"label": label, "text": c["options"][label]}
                    for label in ("A", "B", "C", "D")
                ],
            }
            for c in m["checks"]
        ],
    }
    _assert_cp_clean(dto)
    return dto


def _assert_cp_clean(obj, path: str = "") -> None:
    """先跑 cp 专用禁词, 再复用 v2_exam 的通用禁词断言。"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k not in CP_FORBIDDEN_KEYS, f"CP FORBIDDEN KEY {k!r} at {path or '<root>'}"
            _assert_cp_clean(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _assert_cp_clean(v, f"{path}[{i}]")
    v2_exam_service.assert_no_forbidden(obj, path)


# ---------------------------------------------------------------- session

def _answer_key(material: dict) -> dict[str, str]:
    return {c["check_id"]: c["claimed_answer"] for c in material["checks"]}


def create_session(student_id: str, material_id: str) -> Optional[dict]:
    material = practice_registry.get(material_id)
    if not material:
        return None
    # pin 创建时刻的 revision/hash/判分基准: 内容漂移后旧 session 不悄悄切新版本
    manifest = {
        c["check_id"]: {
            "revision": c["revision"],
            "content_hash_full": c["content_hash_full"],
            "answer_key": c["claimed_answer"],
        }
        for c in material["checks"]
    }
    rng = random.Random()
    round2_order = {}
    for c in material["checks"]:
        labels = ["A", "B", "C", "D"]
        rng.shuffle(labels)
        round2_order[c["check_id"]] = labels
    return student_repo.create_cp_session(student_id, material_id, manifest, round2_order)


def find_session(student_id: str, material_id: str) -> Optional[dict]:
    return student_repo.find_latest_cp_session(student_id, material_id)


def get_session(session_id: str) -> Optional[dict]:
    return student_repo.get_cp_session(session_id)


def _content_drifted(session: dict, material: dict) -> bool:
    """pin 的 hash 与当前内容文件是否一致(教师改内容后旧 session 可还原)。"""
    pinned = session.get("content_manifest") or {}
    for c in material["checks"]:
        p = pinned.get(c["check_id"])
        if not p or p.get("content_hash_full") != c["content_hash_full"]:
            return True
    return False


def _pass_valid(
    events: list[dict], start_ms: int, end_ms: int, prefix: str
) -> bool:
    """连续播放有效性: 最后一次 start 之后,
    progress 心跳单调前进、间距不超限、覆盖到位, 且有 end 事件。
    不接受单个 play/end 事件作为完成证据。"""
    starts = [i for i, e in enumerate(events) if e["event_type"] == f"{prefix}_start"]
    if not starts:
        return False
    tail = events[starts[-1]:]
    if any(e["event_type"] == f"{prefix}_interrupted" for e in tail):
        return False
    ends = [e for e in tail if e["event_type"] == f"{prefix}_end"]
    if not ends:
        return False
    end_pos = int(ends[-1]["payload"].get("position_ms", -1))
    if end_pos < 0:
        return False
    positions = [
        int(e["payload"].get("position_ms", -1))
        for e in tail if e["event_type"] == f"{prefix}_progress"
    ]
    if any(p < 0 for p in positions):
        return False
    if not positions:
        return False
    # 单调性 + 心跳间距
    for a, b in zip(positions, positions[1:]):
        if b < a - 500 or b - a > _HEARTBEAT_MAX_GAP_MS:
            return False
    # 最后一个心跳到 end 事件之间同样不得超出一个心跳周期;
    # end 事件本身即为"到达终点"的证据, 不要求恰有心跳落在终点 2s 内
    if end_pos < positions[-1] - 500:
        return False
    if end_pos - positions[-1] > _HEARTBEAT_MAX_GAP_MS:
        return False
    # 覆盖: 心跳必须从起点附近一路到终点附近
    span = end_ms - start_ms
    covered = (positions[-1] - positions[0]) if len(positions) > 1 else 0
    if positions[0] > start_ms + _HEARTBEAT_MAX_GAP_MS:
        return False
    if covered < span * _COVERAGE_MIN_RATIO - _HEARTBEAT_MAX_GAP_MS:
        return False
    return max(positions[-1], end_pos) >= end_ms - _END_TOLERANCE_MS


def derive_stage(session: dict, events: list[dict], responses: list[dict]) -> str:
    """由事件流 + 作答记录推导当前阶段(event-sourced, 刷新安全)。"""
    material = practice_registry.get(session["material_id"])
    if not material:
        return session["stage"]
    n_checks = len(material["checks"])
    r1 = [r for r in responses if r["round"] == 1]
    r2 = [r for r in responses if r["round"] == 2]
    wrong_ids = {r["check_id"] for r in r1 if not r["is_correct"]}

    if r1 and len(r2) >= len(wrong_ids):
        return "result_final"
    if r1 and wrong_ids:
        if _pass_valid(events, material["material_start_ms"],
                       material["material_end_ms"], "cp_replay"):
            return "check_round_2"
        return "blind_full_replay"
    if r1 and len(r1) >= n_checks:
        # 全对: 无需 recovery, 直接给最终结果
        return "result_final"
    if session.get("first_pass_valid"):
        return "check_round_1"
    if any(e["event_type"] == "cp_pass_start" for e in events):
        # started 但尚未 valid: interrupted → 允许重开 first pass
        return "first_pass"
    if any(e["event_type"] in ("cp_preview_open", "cp_preview_skip") for e in events):
        return "option_preview"
    return "intro"


def session_state(session_id: str) -> Optional[dict]:
    """学生端恢复/轮询用。按阶段只返回该阶段允许看到的信息。"""
    session = student_repo.get_cp_session(session_id)
    if not session:
        return None
    material = practice_registry.get(session["material_id"])
    if not material:
        return None
    events = student_repo.list_cp_events(session_id)
    responses = student_repo.list_cp_responses(session_id)
    stage = derive_stage(session, events, responses)
    if stage != session["stage"]:
        student_repo.update_cp_session(session_id, {"stage": stage})
        session["stage"] = stage

    state = {
        "session_id": session_id,
        "material_id": session["material_id"],
        "stage": stage,
        "pass_attempt_count": session["pass_attempt_count"],
        "replay_count": session["replay_count"],
        "first_pass_valid": bool(session["first_pass_valid"]),
        "preview": session["preview_state"],
        "content_drifted": _content_drifted(session, material),
        "profile_eligible": False,
    }
    r1 = [r for r in responses if r["round"] == 1]
    if stage in ("blind_full_replay", "check_round_2", "result_final") and r1:
        first_score = sum(1 for r in r1 if r["is_correct"])
        state["first_pass_score"] = {"correct": first_score, "total": len(r1)}
    if stage == "check_round_2":
        wrong_ids = [r["check_id"] for r in r1 if not r["is_correct"]]
        order = session.get("round2_order") or {}
        checks_by_id = {c["check_id"]: c for c in material["checks"]}
        state["round2_checks"] = [
            {
                "check_id": cid,
                "question": checks_by_id[cid]["question"],
                "options": [
                    {"label": label, "text": checks_by_id[cid]["options"][label]}
                    for label in order.get(cid, ["A", "B", "C", "D"])
                ],
            }
            for cid in wrong_ids if cid in checks_by_id
        ]
    if stage == "result_final":
        state["result"] = _final_result(session, material, responses)
    _assert_cp_clean(state)
    return state


def _final_result(session: dict, material: dict, responses: list[dict]) -> dict:
    """最终结果: 只有数量与 observation, 无逐题对错/答案。"""
    r1 = [r for r in responses if r["round"] == 1]
    r2 = [r for r in responses if r["round"] == 2]
    first_score = sum(1 for r in r1 if r["is_correct"])
    recovered = sum(1 for r in r2 if r["recovered_after_full_replay"])
    wrong_total = sum(1 for r in r1 if not r["is_correct"])
    dim_by_id = {c["check_id"]: c["target_dimension"] for c in material["checks"]}
    checks_obs = []
    observations = []
    for r in r1:
        dim = dim_by_id.get(r["check_id"], "")
        root = _DIM_OBS.get(dim, "continuous_check")
        mark = "correct" if r["is_correct"] else "failed"
        observations.append(f"{root}_{mark}")
        checks_obs.append({
            "check_id": r["check_id"],
            "dimension": dim,
            "round1_correct": bool(r["is_correct"]),
        })
    return {
        "first_pass_score": {"correct": first_score, "total": len(r1)},
        "recovered": {"correct": recovered, "total": wrong_total},
        "display": f"首次抓住:{first_score}/{len(r1)};完整重听后恢复:{recovered}/{wrong_total}",
        "observations": observations,
        "checks": checks_obs,
        "profile_eligible": False,
        "note": "观察性记录, 不构成能力推断; 不进入画像。",
    }


def record_events(session_id: str, student_id: str, events: list) -> Optional[dict]:
    """追加事件 + 副作用(preview 状态 / pass 计数 / 有效性 / stage)。"""
    session = student_repo.get_cp_session(session_id)
    if not session:
        return None
    clean = []
    for e in events:
        etype = e.get("event_type") if isinstance(e, dict) else getattr(e, "event_type", None)
        if etype not in CP_EVENT_TYPES:
            continue
        clean.append(e)
    if not clean:
        return {"saved": 0}
    student_repo.add_cp_events(session_id, student_id, clean)

    all_events = student_repo.list_cp_events(session_id)
    material = practice_registry.get(session["material_id"])
    updates: dict = {}
    # preview 状态(只记行为)
    preview = dict(session.get("preview_state") or {})
    for e in clean:
        etype = e.get("event_type") if isinstance(e, dict) else getattr(e, "event_type")
        payload = e.get("payload") if isinstance(e, dict) else getattr(e, "payload", {})
        payload = payload or {}
        if etype == "cp_preview_open":
            preview["preview_used"] = True
            preview.setdefault("opened_at", payload.get("client_at"))
        elif etype == "cp_preview_skip":
            preview["preview_skipped"] = True
        elif etype == "cp_preview_mark":
            marks = preview.setdefault("selected_focus_types", {})
            if payload.get("check_id") and payload.get("focus_type"):
                marks[payload["check_id"]] = payload["focus_type"]
        if payload.get("preview_duration_ms") is not None:
            preview["preview_duration_ms"] = payload["preview_duration_ms"]
    if preview != (session.get("preview_state") or {}):
        updates["preview_state"] = preview
    # pass 计数与有效性
    pass_starts = sum(1 for e in all_events if e["event_type"] == "cp_pass_start")
    if pass_starts != session["pass_attempt_count"]:
        updates["pass_attempt_count"] = pass_starts
    if material and not session["first_pass_valid"]:
        if _pass_valid(all_events, material["material_start_ms"],
                       material["material_end_ms"], "cp_pass"):
            updates["first_pass_valid"] = 1
    if material:
        if _pass_valid(all_events, material["material_start_ms"],
                       material["material_end_ms"], "cp_replay"):
            replay_ends = sum(1 for e in all_events if e["event_type"] == "cp_replay_end")
            if replay_ends != session["replay_count"]:
                updates["replay_count"] = replay_ends
    if updates:
        student_repo.update_cp_session(session_id, updates)
        session = student_repo.get_cp_session(session_id)
    # stage 快照
    responses = student_repo.list_cp_responses(session_id)
    stage = derive_stage(session, all_events, responses)
    if stage != session["stage"]:
        student_repo.update_cp_session(session_id, {"stage": stage})
    return {"saved": len(clean)}


def submit_round1(session_id: str, answers: dict) -> Optional[dict]:
    """round 1 判分: 需要有效 first pass; 全部 check 一次性提交; 只返回数量。"""
    session = student_repo.get_cp_session(session_id)
    if not session:
        return None
    material = practice_registry.get(session["material_id"])
    if not material:
        return None
    if not session["first_pass_valid"]:
        return {"error": "no_valid_first_pass"}
    if student_repo.list_cp_responses(session_id, round_=1):
        return {"error": "already_submitted"}
    pinned = session["content_manifest"]
    key = {cid: p.get("answer_key") for cid, p in pinned.items()}  # 判分基准 = pin 时刻
    if set(answers.keys()) != set(key.keys()):
        return {"error": "incomplete_answers"}
    for cid, sel in answers.items():
        sel = (sel or "").strip().upper()
        if sel not in ("A", "B", "C", "D"):
            return {"error": "bad_label"}
        p = pinned[cid]
        student_repo.add_cp_response(
            session_id, cid, p["revision"], p["content_hash_full"],
            1, sel, sel == key[cid],
        )
    student_repo.add_cp_events(session_id, session["student_id"], [
        {"event_type": "cp_round1_submit", "payload": {"check_count": len(answers)}},
    ])
    r1 = student_repo.list_cp_responses(session_id, round_=1)
    first_score = sum(1 for r in r1 if r["is_correct"])
    student_repo.update_cp_session(session_id, {"stage": derive_stage(
        student_repo.get_cp_session(session_id),
        student_repo.list_cp_events(session_id), r1)})
    # 全对: 直接写 summary 并进 result_final; 否则进 blind replay
    if first_score == len(r1):
        _write_summary(session_id)
        student_repo.update_cp_session(session_id, {"stage": "result_final"})
    return {"first_pass_score": {"correct": first_score, "total": len(r1)}}


def submit_round2(session_id: str, answers: dict) -> Optional[dict]:
    """recovery 判分: 只允许 round1 错题; 需要有效 blind replay;
    答对记 recovered_after_full_replay(不称为"第二遍理解率")。"""
    session = student_repo.get_cp_session(session_id)
    if not session:
        return None
    material = practice_registry.get(session["material_id"])
    if not material:
        return None
    events = student_repo.list_cp_events(session_id)
    if not _pass_valid(events, material["material_start_ms"],
                       material["material_end_ms"], "cp_replay"):
        return {"error": "no_valid_replay"}
    r1 = student_repo.list_cp_responses(session_id, round_=1)
    if not r1:
        return {"error": "no_round1"}
    if student_repo.list_cp_responses(session_id, round_=2):
        return {"error": "already_submitted"}
    wrong_ids = {r["check_id"] for r in r1 if not r["is_correct"]}
    if not wrong_ids:
        return {"error": "nothing_to_recover"}
    if set(answers.keys()) != wrong_ids:
        return {"error": "incomplete_answers"}
    pinned = session["content_manifest"]
    key = {cid: p.get("answer_key") for cid, p in pinned.items()}  # 判分基准 = pin 时刻
    for cid, sel in answers.items():
        sel = (sel or "").strip().upper()
        if sel not in ("A", "B", "C", "D"):
            return {"error": "bad_label"}
        p = pinned[cid]
        correct = sel == key[cid]
        student_repo.add_cp_response(
            session_id, cid, p["revision"], p["content_hash_full"],
            2, sel, correct, recovered=correct,
        )
    student_repo.add_cp_events(session_id, session["student_id"], [
        {"event_type": "cp_round2_submit", "payload": {"check_count": len(answers)}},
    ])
    _write_summary(session_id)
    student_repo.update_cp_session(session_id, {"stage": "result_final"})
    responses = student_repo.list_cp_responses(session_id)
    result = _final_result(student_repo.get_cp_session(session_id), material, responses)
    return {
        "first_pass_score": result["first_pass_score"],
        "recovered": result["recovered"],
        "display": result["display"],
    }


def _write_summary(session_id: str) -> None:
    """session 完成时聚合一条 cp_session_summary 事件(幂等)。"""
    if student_repo.list_cp_events(session_id, "cp_session_summary"):
        return
    session = student_repo.get_cp_session(session_id)
    material = practice_registry.get(session["material_id"])
    responses = student_repo.list_cp_responses(session_id)
    result = _final_result(session, material, responses)
    student_repo.add_cp_events(session_id, session["student_id"], [
        {"event_type": "cp_session_summary", "payload": {
            "material_id": session["material_id"],
            "first_pass_score": f"{result['first_pass_score']['correct']}/{result['first_pass_score']['total']}",
            "recovered": f"{result['recovered']['correct']}/{result['recovered']['total']}",
            "checks": result["checks"],
            "observations": result["observations"],
            "profile_eligible": False,
        }},
    ])
