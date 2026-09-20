# -*- coding: utf-8 -*-
"""Aural Lexicon 服务 (V2.C CET Track, 2026-08-31).

职责:
  - 词条加载（JSON lexicon → SQLite lex_items）
  - SM-2 简化版 SRS 调度
  - attempt 记录（只写 lexical 字段，禁止 listening ability 结论）
  - Phase 0 状态机（入口测试 + 封顶强制退出）

约束（见 FINAL_CET_LISTENING_MASTER_PLAN.md §3.0）:
  - source_set 只允许 2；sealed_source 必须为 0
  - attempt 字段：lexical_item_recognized 是唯一 evidence 字段
  - 禁止任何 understanding_stable / ability_improved / diagnosis 类字段与文案
  - Phase 0 active 期间不开六级单元练习、全真、probe
"""

from __future__ import annotations

import json
import math
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from .repository import StudentRepository, student_repo

# ── 配置（所有 heuristic 均可通过 pilot 调整）──────────────────────────
PHASE0_DEFAULT_THRESHOLD = 0.70      # 入口测试词汇覆盖率阈值
PHASE0_CAP_DAYS = 21                 # Phase 0 硬上限（天）
PHASE0_DAILY_VOCAB_MIN = 15          # Phase 0 每日词汇分钟数
NORMAL_DAILY_VOCAB_MIN = 10          # 正常期每日词汇分钟数
SESSION_ITEM_CAP_PHASE0 = 20         # Phase 0 单次会话最大词条数
SESSION_ITEM_CAP_NORMAL = 10         # 正常期单次会话最大词条数
ENTRY_TEST_SAMPLE_SIZE = 40          # 入口测试抽样词条数

LEXICON_PATH = Path(__file__).resolve().parent / "data" / "lexicon" / "lexicon_v1.json"

# ── 工具函数 ──────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


# ── 词库加载 ───────────────────────────────────────────────────────────

def seed_lexicon(repo: Optional[StudentRepository] = None) -> dict:
    """将 lexicon_v1.json 词条写入 lex_items 表（幂等，已存在则跳过）。

    Returns: {"inserted": N, "skipped": N, "sealed_rejected": N}
    """
    r = repo or student_repo
    if not LEXICON_PATH.exists():
        return {"error": f"lexicon not found at {LEXICON_PATH}"}

    data = json.loads(LEXICON_PATH.read_text(encoding="utf-8"))
    inserted = skipped = sealed_rejected = 0

    conn = r._conn()
    all_items = data.get("L1", []) + data.get("L2", []) + data.get("L3", [])
    for item in all_items:
        # Sealed guard: reject any item sourced from Set 1
        if item.get("sealed_source", False):
            sealed_rejected += 1
            continue

        source_set = item.get("source_set", 2)
        if source_set != 2:
            sealed_rejected += 1
            continue

        layer = item.get("source_layer", "L1")
        surface = item.get("word") or item.get("phrase") or item.get("term", "")
        if not surface:
            continue

        item_id = f"lex_{layer}_{uuid.uuid5(uuid.NAMESPACE_DNS, surface).hex[:12]}"

        existing = conn.execute(
            "SELECT item_id FROM lex_items WHERE item_id=?", (item_id,)
        ).fetchone()
        if existing:
            skipped += 1
            continue

        conn.execute(
            """INSERT INTO lex_items
               (item_id, layer, surface, gloss, source_set, source_status,
                provenance, sealed_source, created_at)
               VALUES (?,?,?,?,?,?,?,0,?)""",
            (
                item_id, layer, surface,
                item.get("gloss") or item.get("pedagogical_note"),
                source_set,
                item.get("source_status", "machine"),
                item.get("provenance", ""),
                _now(),
            ),
        )
        inserted += 1

    conn.commit()
    return {"inserted": inserted, "skipped": skipped, "sealed_rejected": sealed_rejected}


def _all_item_ids(repo: StudentRepository) -> list[str]:
    rows = repo._conn().execute("SELECT item_id FROM lex_items").fetchall()
    return [r["item_id"] for r in rows]


# ── SRS (SM-2 简化版) ──────────────────────────────────────────────────

def _sm2_update(
    interval_days: float,
    ease_factor: float,
    repetitions: int,
    grade: int,          # 0-5; 0-2=失败, 3-5=成功
) -> tuple[float, float, int]:
    """返回 (new_interval_days, new_ease_factor, new_repetitions)."""
    if grade < 3:
        new_reps = 0
        new_interval = 1.0
    else:
        new_reps = repetitions + 1
        if new_reps == 1:
            new_interval = 1.0
        elif new_reps == 2:
            new_interval = 6.0
        else:
            new_interval = round(interval_days * ease_factor, 2)

    # Ease factor adjustment
    delta = 0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02)
    new_ef = max(1.3, ease_factor + delta)

    return new_interval, new_ef, new_reps


def get_due_items(
    student_id: str,
    cap: int = SESSION_ITEM_CAP_NORMAL,
    repo: Optional[StudentRepository] = None,
) -> list[dict]:
    """返回当前到期的 SRS 词条（按 next_due 排序，上限 cap 条）。

    对从未学过的词，先不放入 SRS 队列（由前端「今日新词」按序引入）。
    """
    r = repo or student_repo
    now = _now()
    rows = r._conn().execute(
        """SELECT s.srs_id, s.item_id, s.next_due, s.interval_days,
                  s.ease_factor, s.repetitions,
                  i.layer, i.surface, i.gloss, i.audio_asset_id
           FROM lex_srs s JOIN lex_items i ON i.item_id=s.item_id
           WHERE s.student_id=? AND s.next_due<=?
           ORDER BY s.next_due ASC
           LIMIT ?""",
        (student_id, now, cap),
    ).fetchall()
    return [dict(r) for r in rows]


def introduce_new_items(
    student_id: str,
    batch: int = 5,
    repo: Optional[StudentRepository] = None,
) -> list[dict]:
    """为学生引入从未进入 SRS 队列的新词条（每次 batch 条）。"""
    r = repo or student_repo
    rows = r._conn().execute(
        """SELECT i.item_id, i.layer, i.surface, i.gloss, i.audio_asset_id
           FROM lex_items i
           WHERE i.item_id NOT IN (
               SELECT item_id FROM lex_srs WHERE student_id=?
           )
           ORDER BY i.layer, i.item_id
           LIMIT ?""",
        (student_id, batch),
    ).fetchall()
    items = [dict(r) for r in rows]

    # Register them in SRS with next_due = now (immediately due as new cards)
    conn = r._conn()
    now = _now()
    for item in items:
        srs_id = _new_id("srs")
        conn.execute(
            """INSERT OR IGNORE INTO lex_srs
               (srs_id, student_id, item_id, next_due, interval_days,
                ease_factor, repetitions, last_reviewed)
               VALUES (?,?,?,?,1.0,2.5,0,NULL)""",
            (srs_id, student_id, item["item_id"], now),
        )
    conn.commit()
    return items


def record_attempt(
    student_id: str,
    item_id: str,
    task_type: str,
    is_correct: bool,
    response: Optional[str] = None,
    response_latency_ms: Optional[int] = None,
    repo: Optional[StudentRepository] = None,
) -> dict:
    """记录一次词汇 attempt 并更新 SRS 调度。

    evidence 字段：只写 lexical_item_recognized（0/1）。
    禁止字段：understanding_stable / material_mastered / ability_improved / diagnosis。
    """
    if task_type not in ("hear_identify", "micro_dictation", "speed_ladder"):
        raise ValueError(f"invalid task_type: {task_type}")
    if item_id.startswith("learncard_"):
        raise ValueError("Context-review cards cannot be graded as aural recognition")

    r = repo or student_repo
    conn = r._conn()
    now = _now()
    attempt_id = _new_id("lxa")

    recognized = 1 if is_correct else 0

    conn.execute(
        """INSERT INTO lex_attempts
           (attempt_id, student_id, item_id, task_type, response,
            is_correct, lexical_item_recognized, response_latency_ms, occurred_at)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (attempt_id, student_id, item_id, task_type,
         response, int(is_correct), recognized,
         response_latency_ms, now),
    )

    # Update SRS
    srs = conn.execute(
        "SELECT * FROM lex_srs WHERE student_id=? AND item_id=?",
        (student_id, item_id),
    ).fetchone()

    grade = 4 if is_correct else 1   # simplified: correct=4, wrong=1
    if srs:
        new_interval, new_ef, new_reps = _sm2_update(
            srs["interval_days"], srs["ease_factor"], srs["repetitions"], grade
        )
        next_due = (datetime.now(timezone.utc) + timedelta(days=new_interval)).isoformat()
        conn.execute(
            """UPDATE lex_srs SET next_due=?, interval_days=?, ease_factor=?,
               repetitions=?, last_reviewed=?
               WHERE student_id=? AND item_id=?""",
            (next_due, new_interval, new_ef, new_reps, now, student_id, item_id),
        )
    else:
        # First attempt — create SRS entry
        srs_id = _new_id("srs")
        new_interval = 1.0 if not is_correct else 1.0
        next_due = (datetime.now(timezone.utc) + timedelta(days=new_interval)).isoformat()
        conn.execute(
            """INSERT INTO lex_srs
               (srs_id, student_id, item_id, next_due, interval_days,
                ease_factor, repetitions, last_reviewed)
               VALUES (?,?,?,?,?,2.5,?,?)""",
            (srs_id, student_id, item_id, next_due, new_interval,
             1 if is_correct else 0, now),
        )

    conn.commit()
    return {
        "attempt_id": attempt_id,
        "lexical_item_recognized": recognized,
        # Explicitly NO ability conclusions
    }


# ── Phase 0 状态机 ──────────────────────────────────────────────────────

def get_phase0_status(
    student_id: str,
    repo: Optional[StudentRepository] = None,
) -> dict:
    r = repo or student_repo
    row = r._conn().execute(
        "SELECT * FROM phase0_state WHERE student_id=?", (student_id,)
    ).fetchone()
    if not row:
        return {
            "student_id": student_id,
            "status": "not_started",
            "phase0_active": False,
            "exam_practice_allowed": True,
        }

    status = row["status"]
    # Check forced-exit cap
    if status == "active" and row["started_at"]:
        started = datetime.fromisoformat(row["started_at"])
        cap = timedelta(days=row["cap_days"])
        if datetime.now(timezone.utc) - started > cap:
            status = _force_exit_phase0(student_id, r)

    return {
        "student_id": student_id,
        "status": status,
        "phase0_active": status == "active",
        "exam_practice_allowed": status != "active",
        "entry_score": row["entry_score"],
        "entry_threshold": row["entry_threshold"],
        "started_at": row["started_at"],
        "completed_at": row["completed_at"],
        "forced_exit_at": row["forced_exit_at"],
        "cap_days": row["cap_days"],
        "daily_vocab_minutes": row["daily_vocab_minutes"],
    }


def _force_exit_phase0(student_id: str, repo: StudentRepository) -> str:
    now = _now()
    repo._conn().execute(
        """UPDATE phase0_state SET status='forced_exit', forced_exit_at=?
           WHERE student_id=?""",
        (now, student_id),
    )
    repo._conn().commit()
    return "forced_exit"


def start_entry_test(
    student_id: str,
    repo: Optional[StudentRepository] = None,
) -> dict:
    """抽取入口测试词条（40条，从 L1/L2 抽样）。不写 phase0_state，只返回词条列表。"""
    r = repo or student_repo
    rows = r._conn().execute(
        """SELECT item_id, layer, surface, gloss FROM lex_items
           WHERE layer IN ('L1','L2')
           ORDER BY RANDOM()
           LIMIT ?""",
        (ENTRY_TEST_SAMPLE_SIZE,),
    ).fetchall()
    return {
        "student_id": student_id,
        "items": [dict(row) for row in rows],
        "instructions": "听音识义：听到音频后选择正确含义（4选1）",
        "time_limit_minutes": 5,
    }


def complete_entry_test(
    student_id: str,
    results: list[dict],   # [{"item_id": ..., "is_correct": bool}, ...]
    threshold: float = PHASE0_DEFAULT_THRESHOLD,
    repo: Optional[StudentRepository] = None,
) -> dict:
    """处理入口测试结果，决定是否进入 Phase 0。

    results 每条只允许 item_id + is_correct（无 listening ability 字段）。
    """
    r = repo or student_repo
    conn = r._conn()
    now = _now()

    # Record test attempts
    for res in results:
        conn.execute(
            """INSERT INTO phase0_test_attempts
               (attempt_id, student_id, item_id, is_correct, occurred_at)
               VALUES (?,?,?,?,?)""",
            (_new_id("p0t"), student_id, res["item_id"],
             int(bool(res["is_correct"])), now),
        )

    # Calculate score
    total = len(results)
    correct = sum(1 for r2 in results if r2.get("is_correct"))
    score = correct / total if total > 0 else 0.0

    # Determine phase
    enter_phase0 = score < threshold

    existing = conn.execute(
        "SELECT student_id FROM phase0_state WHERE student_id=?", (student_id,)
    ).fetchone()

    if enter_phase0:
        new_status = "active"
        if existing:
            conn.execute(
                """UPDATE phase0_state SET status='active', entry_score=?,
                   entry_threshold=?, started_at=?, completed_at=NULL,
                   forced_exit_at=NULL
                   WHERE student_id=?""",
                (score, threshold, now, student_id),
            )
        else:
            conn.execute(
                """INSERT INTO phase0_state
                   (student_id, status, entry_score, entry_threshold,
                    started_at, cap_days, daily_vocab_minutes)
                   VALUES (?,?,?,?,?,?,?)""",
                (student_id, "active", score, threshold, now,
                 PHASE0_CAP_DAYS, PHASE0_DAILY_VOCAB_MIN),
            )
    else:
        new_status = "completed"
        if existing:
            conn.execute(
                """UPDATE phase0_state SET status='completed', entry_score=?,
                   completed_at=? WHERE student_id=?""",
                (score, now, student_id),
            )
        else:
            conn.execute(
                """INSERT INTO phase0_state
                   (student_id, status, entry_score, entry_threshold, completed_at)
                   VALUES (?,?,?,?,?)""",
                (student_id, "completed", score, threshold, now),
            )

    conn.commit()
    return {
        "student_id": student_id,
        "entry_score": round(score, 3),
        "threshold": threshold,
        "phase0_entered": enter_phase0,
        "status": new_status,
        # NO ability conclusion text — only factual result
    }


def complete_phase0(
    student_id: str,
    retest_score: float,
    repo: Optional[StudentRepository] = None,
) -> dict:
    """Phase 0 复测达标 → 标记完成。"""
    r = repo or student_repo
    now = _now()
    r._conn().execute(
        """UPDATE phase0_state SET status='completed', completed_at=?, entry_score=?
           WHERE student_id=? AND status='active'""",
        (now, retest_score, student_id),
    )
    r._conn().commit()
    return {"student_id": student_id, "status": "completed"}


# ── 词条全量查询（供采集面板高亮用）─────────────────────────────────────

def get_all_items(repo: Optional[StudentRepository] = None) -> list[dict]:
    """返回 lex_items 全部词条（source_set=2, sealed_source=0）。
    仅用于前端 transcript 高亮匹配，不含 SRS 状态。
    """
    r = repo or student_repo
    rows = r._conn().execute(
        "SELECT item_id, layer, surface, gloss FROM lex_items ORDER BY layer, surface"
    ).fetchall()
    return [dict(row) for row in rows]


# ── 听后词汇采集（D3 红线：提交后才允许）──────────────────────────────────

_VALID_GATE_TYPES = ("exam_attempt", "cp_session")


def harvest_word(
    student_id: str,
    item_id: str,
    gate_type: str,
    gate_id: str,
    repo: Optional[StudentRepository] = None,
) -> dict:
    """将词条加入学生 SRS 队列（听后采集入口）。

    D3 红线：
      - gate_type='exam_attempt' → attempts.submitted_at IS NOT NULL
      - gate_type='cp_session'  → cp_sessions.stage = 'result_final'
    均不满足时抛出 ValueError("D3_GATE_BLOCKED")。
    """
    if gate_type not in _VALID_GATE_TYPES:
        raise ValueError(f"invalid gate_type: {gate_type}")

    r = repo or student_repo

    # ── D3 门禁 ───────────────────────────────────────────────────────
    if gate_type == "exam_attempt":
        attempt = r.get_attempt(gate_id)
        if not attempt or not attempt.get("submitted_at"):
            raise ValueError("D3_GATE_BLOCKED")
        if attempt.get("student_id") != student_id:
            raise ValueError("D3_GATE_BLOCKED: source owner mismatch")
        if attempt.get("exam_id") in ("cet6_202606_set1", "cet6_202606_set1_v2"):
            raise ValueError("D3_GATE_BLOCKED: sealed source")
    else:  # cp_session
        session = r.get_cp_session(gate_id)
        if not session or session.get("stage") != "result_final":
            raise ValueError("D3_GATE_BLOCKED")
        if session.get("student_id") != student_id:
            raise ValueError("D3_GATE_BLOCKED: source owner mismatch")
        if session.get("material_id", "").startswith("cet6_202606_set1_u"):
            raise ValueError("D3_GATE_BLOCKED: sealed source")

    # ── 验证 item 存在 ─────────────────────────────────────────────────
    conn = r._conn()
    row = conn.execute(
        "SELECT item_id, surface FROM lex_items WHERE item_id=?", (item_id,)
    ).fetchone()
    if not row:
        raise ValueError(f"item_id not found: {item_id}")

    # A completed CP unit is not permission to harvest vocabulary from other units.
    if gate_type == "cp_session" and session["material_id"].startswith("cet6_202606_set2_u"):
        from .v2_exam_service import v2_registry
        candidate = v2_registry.get("cet6_202606_set2_v2")
        unit = next((u for u in (candidate or {}).get("units", [])
                     if u["unit_id"] == session["material_id"]), None)
        if not unit or row["surface"].casefold() not in unit["transcript"]["cleaned_text"].casefold():
            raise ValueError("D3_GATE_BLOCKED: vocabulary source does not match unit")

    # ── 幂等：已在 SRS 中则跳过 ───────────────────────────────────────
    existing = conn.execute(
        "SELECT srs_id FROM lex_srs WHERE student_id=? AND item_id=?",
        (student_id, item_id),
    ).fetchone()
    if existing:
        return {
            "harvested": False,
            "already_tracked": True,
            "item_id": item_id,
            "surface": row["surface"],
        }

    # ── 写入 SRS（next_due=now → 今日新词）────────────────────────────
    srs_id = _new_id("srs")
    now = _now()
    conn.execute(
        """INSERT INTO lex_srs
           (srs_id, student_id, item_id, next_due, interval_days,
            ease_factor, repetitions, last_reviewed)
           VALUES (?,?,?,?,1.0,2.5,0,NULL)""",
        (srs_id, student_id, item_id, now),
    )
    conn.commit()
    return {
        "harvested": True,
        "already_tracked": False,
        "item_id": item_id,
        "surface": row["surface"],
    }


def get_daily_session(
    student_id: str,
    repo: Optional[StudentRepository] = None,
) -> dict:
    """返回今日词汇会话：到期复习 + 适量新词。"""
    r = repo or student_repo
    phase = get_phase0_status(student_id, r)
    is_phase0 = phase["phase0_active"]
    cap = SESSION_ITEM_CAP_PHASE0 if is_phase0 else SESSION_ITEM_CAP_NORMAL
    daily_minutes = PHASE0_DAILY_VOCAB_MIN if is_phase0 else NORMAL_DAILY_VOCAB_MIN

    due = get_due_items(student_id, cap=cap, repo=r)
    new_batch = max(0, min(5, cap - len(due)))
    new_items = introduce_new_items(student_id, batch=new_batch, repo=r) if new_batch > 0 else []

    return {
        "student_id": student_id,
        "phase0_active": is_phase0,
        "daily_minutes_cap": daily_minutes,
        "due_review": due,
        "new_items": new_items,
        "total_items": len(due) + len(new_items),
    }
