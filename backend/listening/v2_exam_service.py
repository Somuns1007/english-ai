# -*- coding: utf-8 -*-
"""V2.1 Exam Mode 服务: 从 v2_full candidate 数据提供白名单 exam DTO。

安全原则:
  - 白名单组装, 不是"返回完整对象让前端不显示"。
  - 作答阶段绝不返回 question_text / transcript / correct_answer / 中文选项 /
    解析 / evidence / timing / provenance / review_status 等字段。
  - V2 exam_id = candidate exam_id + "_v2", 与 legacy 题库(data/exams)隔离。
  - 音频只有整套原始文件; 不做基于 unverified timestamp 的 unit 切分。
"""
import json
import os
import re
import threading
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).resolve().parent / "data"
V2_DIR = DATA_DIR / "v2_full"
AUDIO_DIR = DATA_DIR / "audio"
BASELINE_PATH = V2_DIR / "V2_0B_BASELINE.json"


def student_release_allowed() -> bool:
    """release gate 的唯一事实来源: V2.0b baseline。"""
    if BASELINE_PATH.exists():
        try:
            data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
            return bool(data.get("release_gate", {}).get("student_release_allowed", False))
        except Exception:
            return False
    return False


def allow_unreleased() -> bool:
    """开发预览开关: 显式配置才放行未 release 内容。生产默认 False。"""
    return os.getenv("ALLOW_UNRELEASED_LISTENING_V2", "").strip().lower() in ("1", "true", "yes")


def gate_allows() -> bool:
    """学生可见性闸门: 已 release 或显式开发预览。"""
    return student_release_allowed() or allow_unreleased()

# 作答阶段禁止出现在 DTO 任何位置的字段(递归断言用)
FORBIDDEN_KEYS = {
    "question_text", "question_text_zh", "transcript", "raw_extracted_text",
    "cleaned_text", "cleaning_diffs", "correct_answer", "source_explanation",
    "distractor_analysis", "explanation", "analysis", "analysis_raw",
    "evidence_text", "evidence_marker", "evidence_start_ms", "evidence_end_ms",
    "audio_start_ms", "audio_end_ms", "timing_status", "timing_note",
    "provenance", "review_status", "review_note", "teacher_annotation",
    "ai_annotation", "text_zh", "options_zh", "stem_zh", "content_hash",
    "field_hashes", "revision", "audio_provenance", "segments",
    "diagnosis_candidates", "_meta", "answer_booklet", "options_ocr_repaired",
    "question_text_asr_similarity",
}

CJK_RE = re.compile(r"[一-鿿]")


class V2ExamRegistry:
    """启动时加载 data/v2_full/*.candidate.json; 文件变化自动重载。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._exams: dict[str, dict] = {}      # v2 exam_id -> candidate record
        self._baseline_hash: Optional[str] = None
        self._signature: tuple = ()

    def _dir_signature(self) -> tuple:
        if not V2_DIR.exists():
            return ()
        return tuple(
            (p.name, p.stat().st_mtime_ns)
            for p in sorted(V2_DIR.glob("*.candidate.json"))
        )

    def reload_if_changed(self) -> None:
        sig = self._dir_signature()
        if sig == self._signature:
            return
        exams = {}
        for path in sorted(V2_DIR.glob("*.candidate.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            v2_id = data["exam_id"] + "_v2"
            exams[v2_id] = data
        with self._lock:
            self._exams = exams
            self._signature = sig

    def get(self, v2_exam_id: str) -> Optional[dict]:
        self.reload_if_changed()
        with self._lock:
            return self._exams.get(v2_exam_id)

    def list_ids(self) -> list[str]:
        self.reload_if_changed()
        with self._lock:
            return sorted(self._exams)


v2_registry = V2ExamRegistry()


def is_v2_exam(exam_id: str) -> bool:
    return v2_registry.get(exam_id) is not None


# ---------------------------------------------------------------- DTO 组装

_UNIT_QUESTION_COUNTS = {"set1": [4, 4, 3, 4, 3, 3, 4], "set2": [4, 4, 3, 4, 3, 3, 4]}


def exam_summaries() -> list[dict]:
    """听力首页用: 不含任何题目内容。release gate 关闭时普通列表为空。"""
    out = []
    if not gate_allows():
        return out
    titles = {
        "cet6_202606_set1_v2": "2026 年 6 月大学英语六级真题(第 1 套)",
        "cet6_202606_set2_v2": "2026 年 6 月大学英语六级真题(第 2 套)",
    }
    for v2_id in v2_registry.list_ids():
        cand = v2_registry.get(v2_id)
        out.append({
            "id": v2_id,
            "exam_type": "cet6",
            "title": titles.get(v2_id, cand["exam_id"]),
            "question_count": len(cand["questions"]),
            "unit_count": len(cand["units"]),
            "has_audio": audio_file(v2_id) is not None,
            "question_delivery": "audio_only",
            "data_status": "machine_prechecked",  # 非 teacher_verified
            # K9 fix: 读 baseline, 不再写死 False; 避免 baseline 改 true 后 metadata 仍显 false
            "student_release_allowed": student_release_allowed(),
        })
    return out


def audio_file(v2_exam_id: str) -> Optional[Path]:
    cand = v2_registry.get(v2_exam_id)
    if not cand:
        return None
    # 整套音频, 与 unit 无关; 文件名沿用 candidate 的 audio_path
    rel = cand["units"][0]["audio_path"]  # e.g. audio/cet6_202606_set1.mp3
    path = (DATA_DIR / rel).resolve()
    if not str(path).startswith(str(AUDIO_DIR.resolve().parent)):
        return None
    return path if path.exists() else None


def paper_dto(v2_exam_id: str) -> Optional[dict]:
    """作答阶段白名单 DTO。组装后立即跑递归禁止字段断言。"""
    cand = v2_registry.get(v2_exam_id)
    if not cand:
        return None
    q_by_unit: dict[str, list[dict]] = {}
    for q in cand["questions"]:
        num = q["number"]
        unit_id = _unit_id_for_number(cand, num)
        q_by_unit.setdefault(unit_id, []).append({
            "question_id": q["question_id"],
            "number": num,
            "options": [
                {"label": o["label"], "text_en": o["text_en"]}
                for o in q["options"]
            ],
        })
    units = []
    for u in cand["units"]:
        uid = u["unit_id"]
        qs = sorted(q_by_unit.get(uid, []), key=lambda x: x["number"])
        units.append({
            "unit_id": uid,
            "section": u["section"],
            "unit_type": u["type"],
            "display_title": u["title"],
            "question_range": [qs[0]["number"], qs[-1]["number"]] if qs else None,
            "questions": qs,
        })
    dto = {
        "exam_id": v2_exam_id,
        "question_delivery": "audio_only",
        "audio": {"scope": "whole_set", "url": f"/api/listening/v2/exams/{v2_exam_id}/audio"},
        "units": units,
    }
    assert_no_forbidden(dto)
    return dto


def _unit_id_for_number(cand: dict, number: int) -> str:
    """unit 归属按 candidate unit 顺序与题号区间推导(题号连续)。"""
    for u in cand["units"]:
        lo, hi = _unit_range(cand, u)
        if lo <= number <= hi:
            return u["unit_id"]
    raise ValueError(f"question {number} not in any unit")


def _unit_range(cand: dict, unit: dict) -> tuple:
    idx = [u["unit_id"] for u in cand["units"]].index(unit["unit_id"])
    set_key = "set1" if "set1" in cand["exam_id"] else "set2"
    counts = _UNIT_QUESTION_COUNTS[set_key]
    lo = sum(counts[:idx]) + 1
    return lo, lo + counts[idx] - 1


def assert_no_forbidden(obj, path: str = "") -> None:
    """递归断言: 禁止字段出现在 DTO 任何位置。"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            # 显式 raise 而非 assert: python -O 会剥离 assert, 使泄漏防护失效
            if k in FORBIDDEN_KEYS:
                raise AssertionError(f"FORBIDDEN KEY {k!r} at {path or '<root>'}")
            assert_no_forbidden(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            assert_no_forbidden(v, f"{path}[{i}]")


def assert_no_cjk_in_options(dto: dict) -> None:
    for u in dto["units"]:
        for q in u["questions"]:
            for o in q["options"]:
                assert not CJK_RE.search(o["text_en"]), (
                    f"CJK in option {q['question_id']}{o['label']}")


# ---------------------------------------------------------------- 判分

def grade_attempt(answers: list[dict], v2_exam_id: str) -> dict:
    """按 final_answer 判分。只返回分数, 不返回答案明细。"""
    cand = v2_registry.get(v2_exam_id)
    key = {q["question_id"]: q["correct_answer"] for q in cand["questions"]}
    score = 0
    first_marks = {}
    for ans in answers:
        qid = ans["question_id"]
        if qid not in key:
            continue
        final = (ans.get("final_answer") or "").strip().upper()
        first = (ans.get("first_answer") or "").strip().upper()
        if final and final == key[qid]:
            score += 1
        first_marks[qid] = (first == key[qid]) if first else None
    return {
        "score": score,
        "question_count": len(cand["questions"]),
        "first_marks": first_marks,
    }
