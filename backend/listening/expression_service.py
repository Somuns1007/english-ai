# -*- coding: utf-8 -*-
"""Phase 6 Expression Bridge: 表达数据层 + 跨语境听力训练服务。

纪律约束:
- 表达必须来源可追溯(official_exam), AI 场景明确标注 ai_generated, 不冒充真实语料。
- TTS 音频标注 ai_generated_tts, 不冒充真实人类语料。
- 本模块只把 cross-context 训练行为写入 expression_attempts 证据表,
  不读写任何画像评分输入(profile_service 不消费本表, 由测试保证)。
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
    )

    expression = expression_repo.get_expression(s["expression_id"])
    return {
        "attempt_id": record["id"],
        "correct": correctness,
        "answers": {k: s["questions"][k]["answer"] for k in QUESTION_KEYS},
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
