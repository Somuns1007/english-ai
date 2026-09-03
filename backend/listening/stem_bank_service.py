# -*- coding: utf-8 -*-
"""Stem Bank 服务 (Work Order G).

职责：
  - 加载 Set 2 题干+选项数据（JSON，内部标注）
  - 提供题干浏览、随机练习会话、预测结果记录
  - DTO 白名单：_correct_answer 字段绝不出现在任何响应中

约束：
  - source_set 只能为 2（Set 1 封卷，不可进训练管线）
  - 学生端DTO不含正确答案：学生提交后才返回 is_correct
  - 无 ability 结论字段（understanding_stable / diagnosis 等）
"""

from __future__ import annotations

import json
import random
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .repository import StudentRepository, student_repo

STEM_BANK_PATH = (
    Path(__file__).resolve().parent / "data" / "stem_bank" / "stem_bank.json"
)

# 合法题目类型（来自 Work Order A 分类）
QUESTION_TYPES = ("main_idea", "detail", "suggestion",
                  "cause_effect", "inference", "attitude")

# ──────────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return f"sp_{uuid.uuid4().hex[:12]}"


# ── 数据加载 ───────────────────────────────────────────────────────────

_CACHE: list[dict] | None = None


def _load_bank() -> list[dict]:
    global _CACHE
    if _CACHE is None:
        if not STEM_BANK_PATH.exists():
            return []
        data = json.loads(STEM_BANK_PATH.read_text(encoding="utf-8"))
        _CACHE = data.get("items", [])
    return _CACHE


def _strip_answer(item: dict) -> dict:
    """从词条中移除 _correct_answer（绝不发往客户端）。"""
    return {k: v for k, v in item.items() if k != "_correct_answer"}


# ── 浏览 ────────────────────────────────────────────────────────────────

def get_stems(
    question_type: Optional[str] = None,
    unit_type: Optional[str] = None,
) -> list[dict]:
    """返回 stem bank 词条列表（无正确答案）。"""
    items = _load_bank()
    if question_type:
        items = [it for it in items if it["question_type"] == question_type]
    if unit_type:
        items = [it for it in items if it["unit_type"] == unit_type]
    return [_strip_answer(it) for it in items]


# ── 练习会话 ────────────────────────────────────────────────────────────

def get_practice_session(
    count: int = 5,
    question_type: Optional[str] = None,
    unit_type: Optional[str] = None,
) -> dict:
    """随机抽取 N 道题组成练习会话（无正确答案）。

    每题有三个训练阶段：
      1. type_id   — 仅看题干，判断题目类型
      2. prediction — 仅看题干，预测关键词
      3. answer     — 看选项，作答
    """
    pool = _load_bank()
    if question_type:
        pool = [it for it in pool if it["question_type"] == question_type]
    if unit_type:
        pool = [it for it in pool if it["unit_type"] == unit_type]

    count = min(count, len(pool))
    selected = random.sample(pool, count) if count > 0 else []

    return {
        "count": count,
        "question_types_available": list(QUESTION_TYPES),
        "items": [_strip_answer(it) for it in selected],
    }


# ── 提交预测 ────────────────────────────────────────────────────────────

def record_prediction(
    student_id: str,
    question_no: int,
    predicted_type: Optional[str],
    selected_answer: Optional[str],
    repo: Optional[StudentRepository] = None,
) -> dict:
    """记录学生的类型预测 + 答案选择，返回正确答案与反馈。

    DTO 规则：
      - 只有调用 record_prediction 后才返回 is_correct 与 correct_answer
      - 不含 understanding_stable / ability_improved / diagnosis
    """
    r = repo or student_repo
    bank = _load_bank()
    item = next((it for it in bank if it["question_no"] == question_no), None)
    if item is None:
        raise ValueError(f"question_no {question_no} not in stem bank")
    if item.get("source_set", 2) != 2:
        raise ValueError("only Set 2 questions allowed in training pipeline")

    correct_answer = item["_correct_answer"]
    correct_type = item["question_type"]

    is_type_correct = (
        int(predicted_type == correct_type) if predicted_type else None
    )
    is_answer_correct = (
        int(selected_answer == correct_answer) if selected_answer else None
    )

    # Write to DB
    conn = r._conn()
    conn.execute(
        """INSERT INTO stem_predictions
           (pred_id, student_id, question_no, source_set,
            predicted_type, is_type_correct,
            selected_answer, is_answer_correct, occurred_at)
           VALUES (?,?,?,2,?,?,?,?,?)""",
        (_new_id(), student_id, question_no,
         predicted_type, is_type_correct,
         selected_answer, is_answer_correct,
         _now()),
    )
    conn.commit()

    return {
        "question_no": question_no,
        "correct_type": correct_type,
        "is_type_correct": is_type_correct,
        "correct_answer": correct_answer,
        "is_answer_correct": is_answer_correct,
        # 无 ability 结论
    }


# ── 学生统计 ────────────────────────────────────────────────────────────

def get_student_stats(
    student_id: str,
    repo: Optional[StudentRepository] = None,
) -> dict:
    """返回学生各题型的预测准确率统计（仅事实数字，无 ability 结论）。"""
    r = repo or student_repo
    rows = r._conn().execute(
        """SELECT predicted_type, is_type_correct, is_answer_correct
           FROM stem_predictions WHERE student_id=?""",
        (student_id,),
    ).fetchall()

    type_stats: dict[str, dict] = {qt: {"total": 0, "correct": 0} for qt in QUESTION_TYPES}
    answer_total = answer_correct = 0

    for row in rows:
        pt = row["predicted_type"]
        if pt in type_stats and row["is_type_correct"] is not None:
            type_stats[pt]["total"] += 1
            type_stats[pt]["correct"] += row["is_type_correct"]
        if row["is_answer_correct"] is not None:
            answer_total += 1
            answer_correct += row["is_answer_correct"]

    return {
        "student_id": student_id,
        "total_predictions": len(rows),
        "answer_accuracy": round(answer_correct / answer_total, 3) if answer_total else None,
        "type_accuracy_by_type": {
            qt: {
                "total": s["total"],
                "accuracy": round(s["correct"] / s["total"], 3) if s["total"] else None,
            }
            for qt, s in type_stats.items()
        },
        # 无 ability 结论文案
    }
