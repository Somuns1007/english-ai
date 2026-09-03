# -*- coding: utf-8 -*-
"""Dashboard 聚合服务 (Work Order H).

职责：
  - 汇总 Phase 0 状态、今日词汇、题型预测统计、近期答题记录
  - 所有返回字段均为事实数字/状态，禁止 ability 结论文案

Copy 规范（贯穿本模块）：
  ❌ "你已掌握"、"能力提升"、"尚未达标"
  ✅ "已练习 N 次"、"近 5 次正确率 X%"、"覆盖率 Y%（阈值 70%）"
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from .repository import StudentRepository, student_repo
from . import aural_lexicon_service as lex_svc
from . import stem_bank_service as stem_svc


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_dashboard(
    student_id: str,
    repo: Optional[StudentRepository] = None,
) -> dict:
    """聚合学生仪表盘所需的全部数据（一次请求，无 ability 结论）。"""
    r = repo or student_repo

    # ── Phase 0 状态 ──────────────────────────────────────────────────
    phase0 = lex_svc.get_phase0_status(student_id, r)

    # ── 今日词汇会话（不执行引入，只统计数量）────────────────────────
    due_items = lex_svc.get_due_items(student_id, cap=100, repo=r)
    total_in_srs = r._conn().execute(
        "SELECT count(*) as c FROM lex_srs WHERE student_id=?", (student_id,)
    ).fetchone()["c"]
    total_lex_items = r._conn().execute(
        "SELECT count(*) as c FROM lex_items"
    ).fetchone()["c"]

    daily_cap = (
        lex_svc.PHASE0_DAILY_VOCAB_MIN
        if phase0.get("phase0_active")
        else lex_svc.NORMAL_DAILY_VOCAB_MIN
    )

    # ── 题型预测统计 ───────────────────────────────────────────────────
    stem_stats = stem_svc.get_student_stats(student_id, r)

    # ── 近期答题（最近 5 次已提交）────────────────────────────────────
    attempts = r.list_submitted_attempts(student_id)
    recent = sorted(
        attempts,
        key=lambda a: a.get("submitted_at") or "",
        reverse=True,
    )[:5]
    recent_out = [
        {
            "attempt_id": a["id"],
            "exam_id": a.get("exam_id", ""),
            "score": a.get("score"),
            "submitted_at": a.get("submitted_at"),
        }
        for a in recent
    ]

    # ── 词汇采集进度 ───────────────────────────────────────────────────
    # 通过 harvest 进入 SRS 的词（相对于直接 introduce_new_items 的区别是
    # 这里不再细分，直接用 total_in_srs 反映采集+SRS整体进度）

    return {
        "student_id": student_id,
        "generated_at": _now(),
        # Phase 0 —— 只显示事实：覆盖率数字、天数、阈值
        "phase0": {
            "status": phase0["status"],
            "phase0_active": phase0.get("phase0_active", False),
            "exam_practice_allowed": phase0.get("exam_practice_allowed", True),
            "entry_score": phase0.get("entry_score"),
            "entry_threshold": phase0.get("entry_threshold", 0.70),
            "cap_days": phase0.get("cap_days", 21),
            "started_at": phase0.get("started_at"),
            "completed_at": phase0.get("completed_at"),
            "forced_exit_at": phase0.get("forced_exit_at"),
        },
        # 词汇 —— 只显示数量
        "vocab": {
            "due_count": len(due_items),
            "total_in_srs": total_in_srs,
            "total_lex_items": total_lex_items,
            "daily_minutes_cap": daily_cap,
            "session_item_cap": (
                lex_svc.SESSION_ITEM_CAP_PHASE0
                if phase0.get("phase0_active")
                else lex_svc.SESSION_ITEM_CAP_NORMAL
            ),
        },
        # 题型预测 —— 只显示正确率数字
        "stem_bank": {
            "total_predictions": stem_stats["total_predictions"],
            "answer_accuracy": stem_stats["answer_accuracy"],
            "type_accuracy_by_type": stem_stats["type_accuracy_by_type"],
        },
        # 近期答题
        "recent_attempts": recent_out,
    }
