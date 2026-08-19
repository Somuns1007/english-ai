# -*- coding: utf-8 -*-
"""Phase 6/6.1 Expression Bridge: 表达数据层 + 跨语境听力训练服务 + 迁移证据规则。

纪律约束:
- 表达必须来源可追溯(official_exam), AI 场景明确标注 ai_generated, 不冒充真实语料。
- TTS 音频标注 ai_generated_tts, 不冒充真实人类语料。
- Phase 6.1 起 cross-context 证据以独立 cross_context 段回流画像,
  与 cross-question(cause/skill)证据严格分开, 不合成模糊"迁移分数"。
- 证据等级梯度(不允许越级):
    ai_generated+pending_teacher < ai_generated+approved
    < official_exam < teacher-verified authentic_clip
- pending_teacher 内容最多提供 provisional 证据, 不能把迁移状态推到 demonstrated。
"""
import json
import threading
from pathlib import Path
from typing import Optional

from .repository import DATA_DIR, student_repo

EXPRESSIONS_DIR = DATA_DIR / "expressions"
EXPRESSIONS_PATH = EXPRESSIONS_DIR / "expressions.json"
SCENARIOS_PATH = EXPRESSIONS_DIR / "scenarios.json"
AUDIO_INDEX_PATH = EXPRESSIONS_DIR / "audio_index.json"

QUESTION_KEYS = ("scene", "meaning", "key_info")


class ExpressionRepository:
    """expressions.json / scenarios.json / audio_index.json 只读加载, 变更自动重载。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._expressions: dict[str, dict] = {}
        self._scenarios: dict[str, dict] = {}
        self._audio_index: dict[str, dict] = {}
        self._signature: tuple = ()
        self.reload()

    def _signature_now(self) -> tuple:
        sig = []
        for p in (EXPRESSIONS_PATH, SCENARIOS_PATH, AUDIO_INDEX_PATH):
            sig.append((p.name, p.stat().st_mtime_ns if p.exists() else 0))
        return tuple(sig)

    def reload(self) -> None:
        expressions: dict[str, dict] = {}
        scenarios: dict[str, dict] = {}
        audio_index: dict[str, dict] = {}
        if EXPRESSIONS_PATH.exists():
            doc = json.loads(EXPRESSIONS_PATH.read_text(encoding="utf-8"))
            expressions = {e["expression_id"]: e for e in doc.get("expressions", [])}
        if SCENARIOS_PATH.exists():
            doc = json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))
            scenarios = {s["scenario_id"]: s for s in doc.get("scenarios", [])}
        if AUDIO_INDEX_PATH.exists():
            audio_index = json.loads(AUDIO_INDEX_PATH.read_text(encoding="utf-8"))
        with self._lock:
            self._expressions = expressions
            self._scenarios = scenarios
            self._audio_index = audio_index
            self._signature = self._signature_now()

    def reload_if_changed(self) -> None:
        if self._signature_now() != self._signature:
            self.reload()

    def get_expression(self, expression_id: str) -> Optional[dict]:
        self.reload_if_changed()
        with self._lock:
            return self._expressions.get(expression_id)

    def list_expressions(self) -> list[dict]:
        self.reload_if_changed()
        with self._lock:
            return list(self._expressions.values())

    def get_scenario(self, scenario_id: str) -> Optional[dict]:
        self.reload_if_changed()
        with self._lock:
            return self._scenarios.get(scenario_id)

    def scenarios_for(self, expression_id: str) -> list[dict]:
        self.reload_if_changed()
        with self._lock:
            return [s for s in self._scenarios.values() if s["expression_id"] == expression_id]

    def audio_meta(self, scenario_id: str) -> Optional[dict]:
        self.reload_if_changed()
        with self._lock:
            return self._audio_index.get(scenario_id)

    def audio_file(self, scenario_id: str) -> Optional[Path]:
        meta = self.audio_meta(scenario_id)
        if not meta:
            return None
        path = (EXPRESSIONS_DIR / meta["file"]).resolve()
        # 防目录穿越
        if not str(path).startswith(str(EXPRESSIONS_DIR.resolve())):
            return None
        return path if path.exists() else None


expression_repo = ExpressionRepository()


def _public_question(qu: dict) -> dict:
    """题干 + 选项, 不含答案(答案只在提交后返回)。"""
    return {"question": qu["question"], "options": qu["options"]}


def _public_scenario(s: dict) -> dict:
    """学生端场景视图: 无 text(先听不看文本), 无答案, 标注 AI 生成身份。"""
    return {
        "scenario_id": s["scenario_id"],
        "expression_id": s["expression_id"],
        "scenario": s["scenario"],
        "communicative_function": s["communicative_function"],
        "difficulty": s["difficulty"],
        "source_type": s["source_type"],
        "review_status": s["review_status"],
        "questions": {k: _public_question(s["questions"][k]) for k in QUESTION_KEYS},
        "has_audio": expression_repo.audio_meta(s["scenario_id"]) is not None,
    }


def list_expressions(student_id: str) -> list[dict]:
    """表达卡片列表: 表达/中文义/来源题/场景数/该学生完成进度。"""
    attempts = student_repo.list_expression_attempts(student_id)
    done_scenarios: dict[str, set] = {}
    correct_scenarios: dict[str, set] = {}
    for a in attempts:
        done_scenarios.setdefault(a["expression_id"], set()).add(a["scenario_id"])
        if a["all_correct"]:
            correct_scenarios.setdefault(a["expression_id"], set()).add(a["scenario_id"])

    result = []
    for e in sorted(expression_repo.list_expressions(), key=lambda x: x["expression_id"]):
        scenarios = expression_repo.scenarios_for(e["expression_id"])
        eid = e["expression_id"]
        result.append({
            "expression_id": eid,
            "expression": e["expression"],
            "meaning": e["meaning"],
            "communicative_function": e["communicative_function"],
            "source_exam_id": e["source_exam_id"],
            "source_question_id": e["source_question_id"],
            "source_sentence": e["source_sentence"],
            "source_type": e["source_type"],
            "review_status": e["review_status"],
            "scenario_count": len(scenarios),
            "done_count": len(done_scenarios.get(eid, set())),
            "correct_count": len(correct_scenarios.get(eid, set())),
        })
    return result


def expression_detail(expression_id: str, student_id: str) -> Optional[dict]:
    e = expression_repo.get_expression(expression_id)
    if not e:
        return None
    scenarios = expression_repo.scenarios_for(expression_id)
    attempts = student_repo.list_expression_attempts(student_id, expression_id)
    latest_by_scenario: dict[str, dict] = {}
    for a in attempts:
        latest_by_scenario[a["scenario_id"]] = a
    return {
        **e,
        "scenarios": [
            {
                **_public_scenario(s),
                "last_attempt": (
                    {
                        "all_correct": bool(latest_by_scenario[s["scenario_id"]]["all_correct"]),
                        "created_at": latest_by_scenario[s["scenario_id"]]["created_at"],
                    }
                    if s["scenario_id"] in latest_by_scenario else None
                ),
            }
            for s in scenarios
        ],
    }


def scenario_audio_path(scenario_id: str) -> Optional[Path]:
    return expression_repo.audio_file(scenario_id)


def scenario_audio_meta(scenario_id: str) -> Optional[dict]:
    """音频元信息(voice/provider/source_type), 供 UI 诚实标注 AI 合成音。"""
    return expression_repo.audio_meta(scenario_id)


def submit_scenario(
    scenario_id: str,
    student_id: str,
    answers: dict,
    listen_count_before_submit: int,
    reveal_used: bool,
    duration_ms: Optional[int],
) -> Optional[dict]:
    """服务端判分 + 落库 + 返回揭示内容(text/目标表达位置/答案)。"""
    s = expression_repo.get_scenario(scenario_id)
    if not s:
        return None

    correctness: dict = {}
    for key in QUESTION_KEYS:
        ans = answers.get(key)
        correctness[key] = None if ans is None else (ans == s["questions"][key]["answer"])
    correctness["all"] = all(c is True for c in correctness.values())

    # Phase 6.1: 提交时快照证据强度 + 来源质量/审核等级(可解释证据链的一环)
    strength, level, factors = evidence_strength(
        correctness, listen_count_before_submit, reveal_used, duration_ms
    )
    record = student_repo.add_expression_attempt(
        student_id=student_id,
        expression_id=s["expression_id"],
        scenario_id=scenario_id,
        scenario_category=s["scenario"],
        source_type=s["source_type"],
        listen_count_before_submit=listen_count_before_submit,
        reveal_used=reveal_used,
        answers=answers,
        correctness=correctness,
        duration_ms=duration_ms,
        source_quality=s["source_type"],
        verification_level=s["review_status"],
        evidence_strength=strength,
        evidence_level=level,
        content_revision=s.get("revision", 1),
    )

    expression = expression_repo.get_expression(s["expression_id"])
    return {
        "attempt_id": record["id"],
        "correct": correctness,
        "answers": {k: s["questions"][k]["answer"] for k in QUESTION_KEYS},
        "evidence": {
            "strength": strength,
            "level": level,
            "factors": factors,
            "verification_level": s["review_status"],
            "source_quality": s["source_type"],
        },
        # 揭示内容: 提交后才返回
        "text": s["text"],
        "target_expression": s["target_expression"],
        "target_surface": s.get("target_surface") or s["target_expression"],
        "related_expressions": s["related_expressions"],
        "expression_meaning": expression["meaning"] if expression else None,
        "source_type": s["source_type"],
    }


def record_replay_after_reveal(attempt_id: str) -> bool:
    return student_repo.increment_expression_replay(attempt_id)


# ---------- Phase 6.1: 迁移证据强度规则(纯规则, 无 LLM) ----------

# 证据来源质量梯度(权重): 未来加入 authentic_clip 时无需重构
SOURCE_QUALITY_WEIGHT = {
    "ai_generated": 0.6,
    "official_exam": 0.9,
    "authentic_clip": 1.0,
}
# 审核等级上限: pending_teacher 内容最多 provisional(0.5), 不允许高置信
VERIFICATION_WEIGHT = {
    "pending_teacher": 0.5,
    "approved": 1.0,
    "teacher_verified": 1.0,
}
# 三题权重: 表达含义是跨语境迁移的核心, 关键信息次之, 场景判断再次
QUESTION_WEIGHT = {"meaning": 0.5, "key_info": 0.3, "scene": 0.2}

EVIDENCE_LEVELS = ("none", "weak", "medium", "strong")


def evidence_strength(
    correctness: dict,
    listen_count_before_submit: int,
    reveal_used: bool,
    duration_ms: Optional[int],
) -> tuple:
    """计算单次场景作答的证据强度。返回 (strength: 0..1, level, factors)。

    规则(显式, 可解释):
    - 正确性基底 = 0.5*meaning + 0.3*key_info + 0.2*scene
    - 盲听系数: 看过文本(reveal_used) ×0.3 —— 看文本后答对与盲听答对证据强度必须不同
    - 播放系数: 1 次 ×1.0 / 2 次 ×0.85 / 3 次 ×0.7 / ≥4 次 ×0.55 / 0 次 = 0(没听不算证据)
    - 速度护栏: 全对但总时长 < 8 秒, 疑似未听直接答, ×0.5
    """
    base = sum(
        QUESTION_WEIGHT[k] for k in QUESTION_KEYS if correctness.get(k) is True
    )
    if listen_count_before_submit <= 0:
        listen_factor = 0.0
    elif listen_count_before_submit == 1:
        listen_factor = 1.0
    elif listen_count_before_submit == 2:
        listen_factor = 0.85
    elif listen_count_before_submit == 3:
        listen_factor = 0.7
    else:
        listen_factor = 0.55
    blind_factor = 0.3 if reveal_used else 1.0
    speed_factor = 1.0
    if correctness.get("all") and duration_ms is not None and duration_ms < 8000:
        speed_factor = 0.5

    strength = round(base * listen_factor * blind_factor * speed_factor, 3)
    if strength >= 0.75:
        level = "strong"
    elif strength >= 0.45:
        level = "medium"
    elif strength > 0:
        level = "weak"
    else:
        level = "none"
    factors = {
        "correctness_base": round(base, 3),
        "listen_factor": listen_factor,
        "blind_factor": blind_factor,
        "speed_factor": speed_factor,
    }
    return strength, level, factors


def verification_weight(review_status: Optional[str]) -> float:
    return VERIFICATION_WEIGHT.get(review_status or "pending_teacher", 0.5)


def _best_attempts_per_scenario(attempts: list, current_revision_of=None) -> dict:
    """去重规则 1: 同一场景刷多次, 只取一份代表证据。

    优先级: ①当前 revision 的 attempt 优先于过期 revision 的
    (内容实质修改后, 旧证据不能代表新内容);
    ②同 revision 状态下取证据强度最高; ③并列取最早。
    """
    def _key(a):
        cur = True
        if current_revision_of is not None:
            cur = (a.get("content_revision") or 1) == current_revision_of(a["scenario_id"])
        # sorted 升序: (False<True, 强度升序, 时间升序); 取最后一个
        return (cur, a.get("evidence_strength") or 0, a["created_at"])

    best: dict = {}
    for a in sorted(attempts, key=_key):
        best[a["scenario_id"]] = a  # 后者覆盖前者, 最优排最后
    return best


def expression_transfer_state(student_id: str, expression_id: str) -> dict:
    """单个表达的迁移状态机 + 可解释证据明细。

    状态规则(去重后):
    - not_demonstrated: 没有任何场景的 best attempt 达到 medium
    - emerging: ≥1 个场景 best ≥ medium, 但未达 demonstrated
    - demonstrated: ≥2 个【不同】场景的 best 均为 strong 且盲听(reveal_used=0),
      且这些场景当前全部 approved(pending_teacher 最多 provisional → emerging)

    去重规则 2: demonstrated 要求 distinct scenario ≥ 2,
    同一场景重复成功不累计。
    """
    attempts = student_repo.list_expression_attempts(student_id, expression_id)

    def _current_revision(scenario_id: str) -> int:
        s = expression_repo.get_scenario(scenario_id)
        return s.get("revision", 1) if s else 1

    best = _best_attempts_per_scenario(attempts, _current_revision)

    details = []
    strong_blind_approved = 0
    has_medium_plus = False
    has_provisional = False
    for sid, a in sorted(best.items()):
        scenario = expression_repo.get_scenario(sid)
        review_status = scenario["review_status"] if scenario else "pending_teacher"
        current_revision = scenario.get("revision", 1) if scenario else None
        # content_revision 保护: 教师实质修改文本后(revision 递增),
        # 旧 attempt 只能关联旧 revision, 不计入新内容的 demonstrated 资格。
        # 历史 attempt 该列为 NULL: 其作答时全部场景均为 rev 1(未编辑过),
        # 故 NULL 按 rev 1 处理——场景一旦编辑(rev≥2)即自动判为过期证据。
        attempt_revision = a.get("content_revision") or 1
        revision_current = attempt_revision == current_revision
        v_weight = verification_weight(review_status)
        contribution = round((a["evidence_strength"] or 0) * v_weight, 3)
        blind = not a["reveal_used"]
        strong_blind = (
            a["evidence_level"] == "strong" and blind
        )
        if a["evidence_level"] in ("medium", "strong") and revision_current:
            has_medium_plus = True
        if review_status != "approved":
            has_provisional = True
        if strong_blind and review_status == "approved" and revision_current:
            strong_blind_approved += 1
        details.append({
            "scenario_id": sid,
            "scenario": a["scenario_category"],
            "attempt_id": a["id"],
            "attempt_count_for_scenario": sum(
                1 for x in attempts if x["scenario_id"] == sid
            ),
            "blind": blind,
            "reveal_used": bool(a["reveal_used"]),
            "listen_count_before_submit": a["listen_count_before_submit"],
            "replay_after_reveal": a["replay_after_reveal"],
            "content_revision": attempt_revision,
            "current_revision": current_revision,
            "revision_current": revision_current,
            "answers": {
                "scene": a["answer_scene"],
                "meaning": a["answer_meaning"],
                "key_info": a["answer_key_info"],
            },
            "correct": {
                "scene": bool(a["scene_correct"]),
                "meaning": bool(a["meaning_correct"]),
                "key_info": bool(a["key_info_correct"]),
            },
            "evidence_strength": a["evidence_strength"],
            "evidence_level": a["evidence_level"],
            "verification_level": review_status,
            "verification_weight": v_weight,
            "contribution": contribution,
        })

    if strong_blind_approved >= 2:
        state = "demonstrated"
    elif has_medium_plus:
        state = "emerging"
    else:
        state = "not_demonstrated"

    return {
        "expression_id": expression_id,
        "transfer_state": state,
        "distinct_scenarios_with_evidence": len(best),
        "strong_blind_approved_scenarios": strong_blind_approved,
        "capped_by_pending_teacher": has_provisional and state == "emerging",
        "scenario_evidence": details,
    }


def cross_context_profile(student_id: str) -> dict:
    """画像的 cross-context 段: 与 cross-question(cause/skill)严格分开。"""
    expressions = []
    counts = {"demonstrated": 0, "emerging": 0, "not_demonstrated": 0}
    for e in sorted(expression_repo.list_expressions(), key=lambda x: x["expression_id"]):
        eid = e["expression_id"]
        if not student_repo.list_expression_attempts(student_id, eid):
            continue  # 无行为的表达不进画像, 避免噪声
        st = expression_transfer_state(student_id, eid)
        counts[st["transfer_state"]] += 1
        expressions.append({
            "expression_id": eid,
            "expression": e["expression"],
            "meaning": e["meaning"],
            **st,
        })
    return {
        "summary": {
            **counts,
            "total_expressions_trained": len(expressions),
            "note": (
                "cross-context 证据独立于 cross-question(cause/skill)证据; "
                "AI 生成场景 pending_teacher 期间最多 provisional, 不能判定 demonstrated"
            ),
        },
        "expressions": expressions,
    }


def early_reveal(scenario_id: str) -> Optional[dict]:
    """放弃盲听, 提前揭示文本。返回内容不含答案; reveal_used 在提交时落库。"""
    s = expression_repo.get_scenario(scenario_id)
    if not s:
        return None
    return {
        "text": s["text"],
        "target_expression": s["target_expression"],
        "target_surface": s.get("target_surface") or s["target_expression"],
    }


# ---------- Phase 6.1: 教师审核(最小可用版) ----------

from datetime import datetime, timezone  # noqa: E402


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_write_json(path: Path, doc: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    expression_repo.reload()


def _load_scenarios_doc() -> dict:
    return json.loads(SCENARIOS_PATH.read_text(encoding="utf-8"))


def _load_expressions_doc() -> dict:
    return json.loads(EXPRESSIONS_PATH.read_text(encoding="utf-8"))


def teacher_expression_overview() -> list:
    """教师审核列表: 表达 + 场景审核状态汇总。"""
    result = []
    for e in sorted(expression_repo.list_expressions(), key=lambda x: x["expression_id"]):
        scenarios = expression_repo.scenarios_for(e["expression_id"])
        result.append({
            "expression_id": e["expression_id"],
            "expression": e["expression"],
            "meaning": e["meaning"],
            "source_exam_id": e["source_exam_id"],
            "source_question_id": e["source_question_id"],
            "source_sentence": e["source_sentence"],
            "review_status": e["review_status"],
            "revision": e.get("revision", 1),
            "reviewed_at": e.get("reviewed_at"),
            "scenarios": [
                {
                    "scenario_id": s["scenario_id"],
                    "scenario": s["scenario"],
                    "review_status": s["review_status"],
                    "revision": s.get("revision", 1),
                    "reviewed_at": s.get("reviewed_at"),
                    "has_audio": expression_repo.audio_meta(s["scenario_id"]) is not None,
                }
                for s in scenarios
            ],
        })
    return result


def teacher_expression_detail(expression_id: str) -> Optional[dict]:
    """教师视图: 完整内容(含 text 与答案), 供审核。"""
    e = expression_repo.get_expression(expression_id)
    if not e:
        return None
    scenarios = expression_repo.scenarios_for(expression_id)
    return {
        **e,
        "scenarios": [
            {**s, "audio_meta": expression_repo.audio_meta(s["scenario_id"])}
            for s in scenarios
        ],
    }


def update_expression(expression_id: str, fields: dict) -> Optional[dict]:
    """教师编辑表达(中文义/交际功能/同义表达)。编辑即 revision+1, 回到 pending_teacher。"""
    allowed = {"meaning", "communicative_function", "related_expressions"}
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not updates:
        return {"error": "no_fields"}
    doc = _load_expressions_doc()
    for e in doc["expressions"]:
        if e["expression_id"] == expression_id:
            e.update(updates)
            e["revision"] = e.get("revision", 1) + 1
            e["review_status"] = "pending_teacher"  # 内容变更后必须重新审核
            _atomic_write_json(EXPRESSIONS_PATH, doc)
            return e
    return None


def update_scenario(scenario_id: str, fields: dict) -> Optional[dict]:
    """教师编辑场景(text/scenario/交际功能/难度/target_surface)。

    text 变更会使既有 TTS 音频失配: 立即作废音频索引与文件, 需重新生成。
    编辑即 revision+1, review_status 回到 pending_teacher。
    """
    allowed = {"text", "scenario", "communicative_function", "difficulty", "target_surface"}
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not updates:
        return {"error": "no_fields"}
    doc = _load_scenarios_doc()
    for s in doc["scenarios"]:
        if s["scenario_id"] == scenario_id:
            text_changed = "text" in updates and updates["text"] != s["text"]
            if "text" in updates and (s.get("target_surface") or s["target_expression"]) not in updates["text"]:
                return {"error": "target_missing",
                        "message": "编辑后的 text 必须仍包含 target_surface/target_expression"}
            s.update(updates)
            s["revision"] = s.get("revision", 1) + 1
            s["review_status"] = "pending_teacher"
            _atomic_write_json(SCENARIOS_PATH, doc)
            if text_changed:
                _invalidate_audio(scenario_id)
            return s
    return None


def review_expression(expression_id: str, action: str) -> Optional[dict]:
    if action not in ("approve", "reject"):
        return {"error": "bad_action"}
    doc = _load_expressions_doc()
    for e in doc["expressions"]:
        if e["expression_id"] == expression_id:
            e["review_status"] = "approved" if action == "approve" else "rejected"
            e["reviewed_at"] = _utc_now()
            _atomic_write_json(EXPRESSIONS_PATH, doc)
            return e
    return None


def review_scenario(scenario_id: str, action: str) -> Optional[dict]:
    if action not in ("approve", "reject"):
        return {"error": "bad_action"}
    doc = _load_scenarios_doc()
    for s in doc["scenarios"]:
        if s["scenario_id"] == scenario_id:
            s["review_status"] = "approved" if action == "approve" else "rejected"
            s["reviewed_at"] = _utc_now()
            _atomic_write_json(SCENARIOS_PATH, doc)
            return s
    return None


def _invalidate_audio(scenario_id: str) -> None:
    """文本变更后作废旧音频: 删索引条目与文件, has_audio 变 False。"""
    if not AUDIO_INDEX_PATH.exists():
        return
    index = json.loads(AUDIO_INDEX_PATH.read_text(encoding="utf-8"))
    meta = index.pop(scenario_id, None)
    if meta:
        old = EXPRESSIONS_DIR / meta["file"]
        if old.exists():
            old.unlink()
        _atomic_write_json(AUDIO_INDEX_PATH, index)


def regenerate_scenario_audio(scenario_id: str, voice: Optional[str] = None) -> Optional[dict]:
    """教师审核后重新生成该场景 TTS(单嗓音整段, V1 限制不变)。"""
    import asyncio

    from .tools.generate_scenario_audio import (
        AUDIO_DIR,
        PROVIDER,
        SOURCE_TYPE,
        SPEED,
        VOICES,
        generate_one,
        text_to_speech_text,
    )

    s = expression_repo.get_scenario(scenario_id)
    if not s:
        return None
    voice_id = voice if voice in VOICES else VOICES[hash(scenario_id) % len(VOICES)]
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    out = AUDIO_DIR / f"{scenario_id}.mp3"
    asyncio.run(generate_one(scenario_id, text_to_speech_text(s["text"]), voice_id, out))

    index = json.loads(AUDIO_INDEX_PATH.read_text(encoding="utf-8")) if AUDIO_INDEX_PATH.exists() else {}
    index[scenario_id] = {
        "scenario_id": scenario_id,
        "file": f"audio/{scenario_id}.mp3",
        "voice_id": voice_id,
        "provider": PROVIDER,
        "speed": SPEED,
        "generated_at": _utc_now(),
        "source_type": SOURCE_TYPE,
    }
    _atomic_write_json(AUDIO_INDEX_PATH, index)
    return index[scenario_id]
