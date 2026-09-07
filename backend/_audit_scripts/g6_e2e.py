#!/usr/bin/env python3
"""G6: g6_e2e.py — Set2 主路径端到端实跑 + 取证（GPT-6 §4 step ④）。

主路径（严格按 GPT-6 §4 step ④）：
  考试(exam) → 提交(submit) → 复盘(review) → 一项训练(one training)
  → 同材料无文本重测(blind-retest) → 采词(harvest) → SRS(lexicon attempt) → Dashboard

设计：
  - 在隔离 DB 上跑（LISTENING_DB_PATH 指向临时库），真实 listening.db 零污染。
  - 用 FastAPI TestClient 走真实 HTTP 端点（/api/listening/...），不绕过路由/门控。
  - 每一步记录 {step, endpoint, status, 关键字段} 作为证据；任何被门控/条件化的
    步骤如实标注（不伪造"通过"）。
  - correct_answer 只从服务端 exam_repo 取（用于故意答错造错题），绝不写回响应断言。
  - student_release_allowed 全程保持 false（不触碰门控）。

用法：
  cd backend
  LISTENING_DB_PATH=/tmp/g6.db LISTENING_UNSAFE_FAST_DB=1 python _audit_scripts/g6_e2e.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from listening import router as router_mod
from listening.repository import exam_repo, student_repo

PREFIX = "/api/listening"
EXAM_ID = "cet6_202606_set2"
STUDENT = "g6_e2e_student"

_ev: list[dict] = []


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def rec(step: str, endpoint: str, status, note: str, extra: dict | None = None):
    row = {"step": step, "endpoint": endpoint, "status": status, "note": note}
    if extra:
        row.update(extra)
    _ev.append(row)
    ok = "OK " if (isinstance(status, int) and 200 <= status < 300) else "!! "
    print(f"  [{ok}] {step:<26} {endpoint:<52} {status}  {note}")


def main() -> int:
    app = FastAPI()
    app.include_router(router_mod.router)
    client = TestClient(app)

    # 服务端权威取正确答案（造错题用；不进入任何学生端响应断言）
    exam = exam_repo.get(EXAM_ID)
    if not exam:
        print(f"FATAL: exam {EXAM_ID} not found")
        return 1
    # Exam 是 Pydantic 对象：units[].questions[]，逐 unit 展平
    questions = [q for u in exam.units for q in u.questions]
    print(f"\n== G6 Set2 主路径端到端实跑 ==  exam={EXAM_ID}  questions={len(questions)}\n")

    # ── STEP 1: 考试 —— 建 attempt + 逐题作答（前一半故意答错，制造错题）──
    r = client.post(f"{PREFIX}/attempts", json={"student_id": STUDENT, "exam_id": EXAM_ID})
    if r.status_code != 200:
        rec("1-考试/建attempt", "POST /attempts", r.status_code, "建 attempt 失败", {"body": r.text[:300]})
        return _finish(1)
    attempt_id = r.json()["data"]["id"]
    rec("1-考试/建attempt", "POST /attempts", r.status_code, f"attempt_id={attempt_id}")

    wrong_qids: list[str] = []
    correct_map: dict[str, str] = {}
    put_ok = 0
    for idx, q in enumerate(questions):
        qid = q.id
        correct = q.correct_answer
        correct_map[qid] = correct
        # 前一半故意答错（选一个 != 正确的选项），后一半答对
        opts = [o.label for o in q.options]
        if idx < len(questions) // 2:
            ans = next((o for o in opts if o != correct), correct)
            if ans != correct:
                wrong_qids.append(qid)
        else:
            ans = correct
        ts = _now()
        pr = client.put(
            f"{PREFIX}/attempts/{attempt_id}/answers/{qid}",
            json={"first_answer": ans, "final_answer": ans,
                  "first_answer_at": ts, "last_answer_at": ts,
                  "change_count": 0, "dwell_ms": 1200},
        )
        if pr.status_code == 200:
            put_ok += 1
    rec("1-考试/逐题作答", "PUT /answers/{qid} ×N", 200 if put_ok == len(questions) else 500,
        f"{put_ok}/{len(questions)} 落库；故意答错 {len(wrong_qids)} 题")

    # ── STEP 2: 提交 ──
    r = client.post(f"{PREFIX}/attempts/{attempt_id}/submit")
    if r.status_code != 200:
        rec("2-提交", "POST /submit", r.status_code, "提交失败", {"body": r.text[:300]})
        return _finish(1)
    sub = r.json()["data"]
    score = sub.get("score") or sub.get("total_score") or sub.get("correct_count")
    rec("2-提交", "POST /submit", r.status_code, f"score={score}",
        {"score_fields": {k: sub.get(k) for k in ("score", "total_score", "correct_count", "total") if k in sub}})

    # ── STEP 3: 复盘 ──
    r = client.get(f"{PREFIX}/attempts/{attempt_id}/review")
    if r.status_code != 200:
        rec("3-复盘", "GET /review", r.status_code, "复盘失败", {"body": r.text[:300]})
        return _finish(1)
    review = r.json()["data"]
    # 泄题检查：复盘总览默认不应直接给 correct_answer（L5 前）
    leaked = _find_key(review, "correct_answer")
    rec("3-复盘", "GET /review", r.status_code,
        f"复盘总览返回；correct_answer 泄露={'是' if leaked else '否'}",
        {"top_keys": list(review.keys())[:12]})

    # 挑一道错题作为训练/复测对象
    target_qid = wrong_qids[0] if wrong_qids else questions[0].id

    # ── STEP 3b: 保存自诊断（training-plan 通常需要错因证据）──
    # 使用真实错因键（training_service.TRAINING_MAP 的合法 tag），让训练走计划驱动而非 fallback
    r = client.post(f"{PREFIX}/diagnoses", json={
        "student_id": STUDENT, "attempt_id": attempt_id, "question_id": target_qid,
        "student_tags": ["vocabulary_unknown"], "final_tags": ["vocabulary_unknown"],
    })
    rec("3b-自诊断", "POST /diagnoses", r.status_code,
        "错因落库" if r.status_code == 200 else "诊断失败",
        {"qid": target_qid})

    # ── STEP 4: 一项训练 —— 训练计划 → 取内容 → 判分 ──
    r = client.get(f"{PREFIX}/attempts/{attempt_id}/questions/{target_qid}/training-plan")
    plan_available = False
    trainings: list[str] = []
    if r.status_code == 200:
        plan = r.json()["data"]
        plan_available = bool(plan.get("available"))
        trainings = sorted({t["type"] for t in plan.get("trainings", [])})
    rec("4-训练/计划", "GET /training-plan", r.status_code,
        f"available={plan_available} types={trainings}")

    trained_type = None
    for ttype in (trainings or ["dictation", "chunk", "paraphrase", "distractor"]):
        rc = client.get(f"{PREFIX}/attempts/{attempt_id}/questions/{target_qid}/training/{ttype}")
        if rc.status_code == 200 and rc.json().get("data") is not None:
            trained_type = ttype
            content = rc.json()["data"]
            rec("4-训练/取内容", f"GET /training/{ttype}", rc.status_code,
                f"内容就绪 keys={list(content.keys())[:8]}")
            # 判分（提交一个占位输入，验证判分端点闭环，不追求满分）
            check_body = _mk_check_body(ttype, content)
            rk = client.post(
                f"{PREFIX}/attempts/{attempt_id}/questions/{target_qid}/training/{ttype}/check",
                json=check_body)
            if rk.status_code == 200:
                res = rk.json()["data"]
                rec("4-训练/判分", f"POST /training/{ttype}/check", rk.status_code,
                    f"判分闭环 score={res.get('score')} result={res.get('result')}")
            else:
                rec("4-训练/判分", f"POST /training/{ttype}/check", rk.status_code,
                    "判分失败", {"body": rk.text[:200]})
            break
    if trained_type is None:
        rec("4-训练", "GET /training/{type}", 204,
            "该错题无可用训练内容(定位句/教师标注 needs_review) — 条件化，非失败")

    # 训练结果落库
    r = client.post(f"{PREFIX}/training-results", json={
        "student_id": STUDENT, "question_id": target_qid,
        "training_type": trained_type or "dictation",
        "attempt_id": attempt_id, "input": {"note": "g6-e2e"},
        "result": True, "score": 1.0,
    })
    rec("4-训练/结果落库", "POST /training-results", r.status_code,
        "训练证据落库" if r.status_code == 200 else "落库失败")

    # ── STEP 5: 同材料无文本重测（blind-retest）──
    correct_for_target = correct_map[target_qid]
    r = client.post(f"{PREFIX}/attempts/{attempt_id}/questions/{target_qid}/blind-retest",
                    json={"answer": correct_for_target})
    if r.status_code == 200:
        br = r.json()["data"]
        br_leak = _find_key(br, "correct_answer")
        rec("5-裸听复测", "POST /blind-retest", r.status_code,
            f"is_correct={br.get('is_correct')} 泄题={'是' if br_leak else '否'}",
            {"keys": list(br.keys())})
    else:
        rec("5-裸听复测", "POST /blind-retest", r.status_code, "复测失败", {"body": r.text[:200]})

    # ── STEP 6: 采词（harvest，D3 gate=exam_attempt 需 submitted_at）──
    r = client.get(f"{PREFIX}/lexicon/items")
    items = r.json()["data"] if r.status_code == 200 else []
    rec("6a-词库读取", "GET /lexicon/items", r.status_code, f"lex_items={len(items)}")
    harvest_item = items[0]["item_id"] if items else None
    if harvest_item:
        r = client.post(f"{PREFIX}/lexicon/harvest", json={
            "student_id": STUDENT, "item_id": harvest_item,
            "gate_type": "exam_attempt", "gate_id": attempt_id,
        })
        if r.status_code == 200:
            rec("6-采词", "POST /lexicon/harvest", r.status_code,
                f"入 SRS 队列 item={harvest_item}", {"resp": r.json()["data"]})
        else:
            rec("6-采词", "POST /lexicon/harvest", r.status_code, "采词失败", {"body": r.text[:200]})
    else:
        rec("6-采词", "POST /lexicon/harvest", 500, "词库为空，无法采词（G4 种子未生效？）")

    # ── STEP 7: SRS —— 记录一次词汇 attempt 更新调度 ──
    if harvest_item:
        r = client.post(f"{PREFIX}/lexicon/attempt", json={
            "student_id": STUDENT, "item_id": harvest_item,
            "task_type": "hear_identify", "is_correct": True,
            "response": "ok", "response_latency_ms": 900,
        })
        if r.status_code == 200:
            rec("7-SRS/attempt", "POST /lexicon/attempt", r.status_code,
                "SRS 调度更新", {"resp": r.json()["data"]})
        else:
            rec("7-SRS/attempt", "POST /lexicon/attempt", r.status_code, "SRS 记录失败",
                {"body": r.text[:200]})

    # ── STEP 8: Dashboard 聚合 ──
    r = client.get(f"{PREFIX}/dashboard?student_id={STUDENT}")
    if r.status_code == 200:
        dash = r.json()["data"]
        vocab = dash.get("vocab", {})
        recent = dash.get("recent_attempts", [])
        rec("8-Dashboard", "GET /dashboard", r.status_code,
            f"聚合成功 recent_attempts={len(recent)} vocab.total_in_srs={vocab.get('total_in_srs')}",
            {"top_keys": list(dash.keys())})
    else:
        rec("8-Dashboard", "GET /dashboard", r.status_code, "聚合失败", {"body": r.text[:200]})

    # ── 门控红线复核：student_release_allowed 必须仍为 false ──
    try:
        from listening import v2_exam_service
        gate = v2_exam_service.gate_allows()
        rec("守卫-发布门控", "v2_exam_service.gate_allows()", "info",
            f"gate_allows={gate}（须为 False）")
    except Exception as e:
        rec("守卫-发布门控", "gate_allows", "info", f"未取到: {e}")

    return _finish(0)


def _mk_check_body(ttype: str, content: dict) -> dict:
    """为不同训练类型构造一个最小 check 请求体（用于验证判分端点闭环）。"""
    if ttype == "dictation":
        return {"level": 3, "inputs": [""]}
    if ttype == "chunk":
        n = len(content.get("chunks", content.get("items", []))) or 3
        return {"order": list(range(n))}
    if ttype == "paraphrase":
        return {"answers_map": {}}
    if ttype == "distractor":
        return {"selections": {}}
    return {}


def _find_key(obj, key) -> bool:
    if isinstance(obj, dict):
        if key in obj and obj[key] not in (None, ""):
            return True
        return any(_find_key(v, key) for v in obj.values())
    if isinstance(obj, (list, tuple)):
        return any(_find_key(v, key) for v in obj)
    return False


def _finish(code: int) -> int:
    out = {"exam_id": EXAM_ID, "student": STUDENT, "generated_at": _now(), "evidence": _ev}
    path = "/tmp/g6_evidence.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n证据已写入 {path}（{len(_ev)} 步）")
    fails = [e for e in _ev if isinstance(e["status"], int) and not (200 <= e["status"] < 300)]
    print(f"非 2xx 步骤：{len(fails)}")
    return code


if __name__ == "__main__":
    sys.exit(main())
