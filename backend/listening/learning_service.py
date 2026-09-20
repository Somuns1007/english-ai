"""Owned, version-pinned post-listening learning; never emits ability evidence.

Uses existing SQLite and SRS schedule, but keeps lesson cards out of the public
lexicon seed and cold-start recommendations. No model calls or guessed timings.
"""
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from functools import lru_cache

from fastapi import HTTPException

from . import v2_exam_service, v2_practice_service
from .aural_lexicon_service import _sm2_update
from .learning_content import CONTENT, CONTENT_REVISION, GUIDANCE
from .repository import _now, new_id


def dump(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def fail(status, message):
    raise HTTPException(status, message)


def check_release():
    if not v2_exam_service.gate_allows():
        fail(403, "材料尚未发布；学习入口不绕过发布门控")


@lru_cache(maxsize=8)
def _media_hash(path, size, modified):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def media_identity():
    path = v2_exam_service.audio_file("cet6_202606_set2_v2")
    if not path or not path.is_file():
        return None
    stat = path.stat()
    return {"sha256": _media_hash(str(path), stat.st_size, stat.st_mtime_ns)}


def material_snapshot(unit):
    material_id = unit["unit_id"]
    notes = CONTENT[material_id]
    segments = []
    assigned_words = set()
    for source in unit["transcript"]["segments"]:
        # Keep source segment IDs: a source segment may contain several sentences.
        text = re.sub(r"\[\d+(?:-\d+)?\]\s*", "", source["text"])
        text = re.sub(r"^[WM]:\s*", "", text).strip()
        vocabulary = [v for v in notes["vocabulary"]
                      if v["id"] not in assigned_words and v["anchor"].lower() in source["text"].lower()]
        assigned_words.update(v["id"] for v in vocabulary)
        guidance = [{**g, "anchor": re.sub(r"\[\d+(?:-\d+)?\]\s*", "", g["anchor"])}
                    for g in GUIDANCE.get(material_id, []) if g["anchor"] in source["text"]]
        segments.append({"id": source["segment_id"], "text": text,
                         "speaker": source.get("speaker", ""), "vocabulary": vocabulary,
                         "guidance": guidance})
    cp = v2_practice_service.practice_registry.get(material_id)
    audio = {"scope": "whole_set", "start_ms": None, "end_ms": None,
             "identity": media_identity()}
    if cp:
        audio.update(scope="whole_unit", start_ms=cp["material_start_ms"],
                     end_ms=cp["material_end_ms"])
    snapshot = {"material_id": material_id, "title": notes["title"],
                "revision": unit["transcript"]["revision"],
                "source_hash": unit["transcript"]["content_hash"],
                "content_revision": CONTENT_REVISION, "segments": segments, "audio": audio}
    snapshot["hash"] = hashlib.sha256(dump(snapshot).encode()).hexdigest()
    return snapshot


def bind_source(repo, kind, gate_id, owner_id, material_or_exam):
    """Bind authenticated new sources at creation, not a client-claimed UUID later."""
    if not owner_id:
        return
    candidate = v2_exam_service.v2_registry.get("cet6_202606_set2_v2")
    if not candidate:
        return
    units = [u for u in candidate["units"] if
             (kind == "exam_attempt" and material_or_exam == "cet6_202606_set2_v2")
             or (kind == "cp_session" and u["unit_id"] == material_or_exam)]
    if not units:
        return
    snapshot = {u["unit_id"]: material_snapshot(u) for u in units}
    with repo._conn() as conn:
        conn.execute("INSERT OR IGNORE INTO learning_sources VALUES (?,?,?,?)",
                     (kind, gate_id, owner_id, dump(snapshot)))


def protect_source(repo, kind, gate_id, owner_id):
    """Protect newly bound sources even on legacy write paths; unbound history stays legacy."""
    row = repo._conn().execute(
        "SELECT owner_id FROM learning_sources WHERE gate_type=? AND gate_id=?",
        (kind, gate_id)).fetchone()
    if row and row["owner_id"] != owner_id:
        fail(403, "无权操作此学习来源记录，请使用创建记录的账号")


def source(repo, owner, kind, gate_id):
    check_release()
    row = repo._conn().execute(
        "SELECT * FROM learning_sources WHERE gate_type=? AND gate_id=?",
        (kind, gate_id)).fetchone()
    if not row or row["owner_id"] != owner:
        fail(403, "此记录未绑定当前账号。匿名或历史记录不能自动认领；请登录后重新练习")
    record = repo.get_attempt(gate_id) if kind == "exam_attempt" else repo.get_cp_session(gate_id)
    if not record or record["student_id"] != owner:
        fail(403, "学习来源归属不匹配")
    complete = record.get("submitted_at") if kind == "exam_attempt" else record.get("stage") == "result_final"
    if not complete:
        fail(409, "完成本次作答或连续练习后才能开始句段学习")
    return json.loads(row["snapshot"])


def list_materials(repo, owner, kind, gate_id):
    snapshots = source(repo, owner, kind, gate_id)
    return [{"material_id": key, "title": value["title"], "segment_count": len(value["segments"])}
            for key, value in snapshots.items() if key in CONTENT]


def create(repo, owner, kind, gate_id, material_id):
    snapshots = source(repo, owner, kind, gate_id)
    if material_id not in snapshots or material_id not in CONTENT:
        fail(403, "本次记录不能解锁该材料；Set1 仍封存")
    with repo._conn() as conn:
        conn.execute("""INSERT OR IGNORE INTO learning_sessions
            (id,owner_id,gate_type,gate_id,material_id,snapshot,created_at)
            VALUES (?,?,?,?,?,?,?)""",
                     (new_id("learn"), owner, kind, gate_id, material_id, dump(snapshots[material_id]), _now()))
        row = conn.execute("""SELECT id FROM learning_sessions WHERE owner_id=?
            AND gate_type=? AND gate_id=? AND material_id=?""", (owner, kind, gate_id, material_id)).fetchone()
    return state(repo, owner, row["id"])


def owned(repo, owner, session_id):
    check_release()
    row = repo._conn().execute("SELECT * FROM learning_sessions WHERE id=? AND owner_id=?",
                               (session_id, owner)).fetchone()
    if not row:
        fail(404, "学习会话不存在或不属于当前账号")
    if row["material_id"] not in CONTENT:
        fail(403, "该材料当前不可学习")
    source(repo, owner, row["gate_type"], row["gate_id"])
    return dict(row), json.loads(row["snapshot"])


def events(repo, session_id):
    return [dict(r) for r in repo._conn().execute(
        "SELECT * FROM learning_events WHERE session_id=? ORDER BY rowid", (session_id,))]


def state(repo, owner, session_id):
    row, snapshot = owned(repo, owner, session_id)
    history = events(repo, session_id)
    revealed = {e["target_id"] for e in history if e["event_type"] == "reveal"}
    attempted = {e["target_id"] for e in history if e["event_type"] == "attempt"}
    answers = {}
    for event in history:
        if event["event_type"] == "attempt":
            answers[event["target_id"]] = json.loads(event["payload"])
    return {"session_id": session_id, "material_id": row["material_id"],
            "title": snapshot["title"], "finished": bool(row["finished_at"]),
            "content_hash": snapshot["hash"], "source_revision": snapshot["revision"],
            "profile_eligible": False, "review_status": "machine_prechecked",
            "exposure_status": "text_exposed" if revealed else "familiar",
            "audio": {"url": f"/api/listening/learning/sessions/{session_id}/audio",
                      "scope": snapshot["audio"]["scope"], "start_ms": snapshot["audio"]["start_ms"],
                      "end_ms": snapshot["audio"]["end_ms"], "sentence_timing_verified": False},
            "segments": [{"id": s["id"], "number": i + 1, "speaker": s["speaker"],
                          "attempted": s["id"] in attempted, "revealed": s["id"] in revealed,
                          "last_attempt": answers.get(s["id"]),
                          **({"text": s["text"], "vocabulary": s["vocabulary"], "guidance": s.get("guidance", [])} if s["id"] in revealed else {})}
                         for i, s in enumerate(snapshot["segments"])],
            "last_segment_id": next((e["target_id"] for e in reversed(history)
                                      if e["event_type"] in ("attempt", "reveal")), None)}


def segment(snapshot, segment_id):
    found = next((s for s in snapshot["segments"] if s["id"] == segment_id), None)
    if not found:
        fail(404, "句段不属于本次材料")
    return found


def append(conn, session_id, request_id, kind, target, payload):
    prior = conn.execute("SELECT * FROM learning_events WHERE session_id=? AND request_id=?",
                         (session_id, request_id)).fetchone()
    serialized = dump(payload)
    if prior:
        if (prior["event_type"], prior["target_id"], prior["payload"]) != (kind, target, serialized):
            fail(409, "重复请求的内容不一致，请刷新后重试")
        return False
    conn.execute("INSERT INTO learning_events VALUES (?,?,?,?,?,?)",
                 (session_id, request_id, kind, target, serialized, _now()))
    return True


def attempt(repo, owner, session_id, segment_id, text, difficulty, request_id):
    row, snapshot = owned(repo, owner, session_id)
    segment(snapshot, segment_id)
    if row["finished_at"]:
        fail(409, "本次学习已结束；可以查看已揭示内容和复习词卡")
    exposed = any(e["event_type"] == "reveal" for e in events(repo, session_id))
    with repo._conn() as conn:
        append(conn, session_id, request_id, "attempt", segment_id,
               {"text": text, "difficulty": difficulty, "text_exposed": exposed,
                "content_hash": snapshot["hash"], "profile_eligible": False})
    return state(repo, owner, session_id)


def reveal(repo, owner, session_id, segment_id, request_id):
    row, snapshot = owned(repo, owner, session_id)
    segment(snapshot, segment_id)
    history = events(repo, session_id)
    if not any(e["event_type"] == "attempt" and e["target_id"] == segment_id for e in history):
        fail(409, "请先尝试或选择暂时没听出，再揭示文字")
    if row["finished_at"] and not any(e["event_type"] == "reveal" and e["target_id"] == segment_id for e in history):
        fail(409, "本次学习已结束")
    with repo._conn() as conn:
        append(conn, session_id, request_id, "reveal", segment_id,
               {"content_hash": snapshot["hash"], "exposure": "text_exposed"})
    return state(repo, owner, session_id)


def compare(repo, owner, session_id, segment_id):
    data = state(repo, owner, session_id)
    item = next((s for s in data["segments"] if s["id"] == segment_id), None)
    if not item or not item["revealed"]:
        fail(403, "揭示后才能对照听写")
    expected = re.findall(r"[a-z0-9]+(?:'[a-z]+)?", item["text"].lower())
    actual = re.findall(r"[a-z0-9]+(?:'[a-z]+)?", (item["last_attempt"] or {}).get("text", "").lower())
    return {"differences": [{"type": op, "expected": expected[a:b], "written": actual[c:d]}
                            for op, a, b, c, d in SequenceMatcher(None, expected, actual, autojunk=False).get_opcodes()
                            if op != "equal"], "note": "仅对照英文听写；漏词和拼写不等于没听懂，不评定能力"}


def finish(repo, owner, session_id, request_id):
    _, snapshot = owned(repo, owner, session_id)
    with repo._conn() as conn:
        append(conn, session_id, request_id, "finish", "", {"content_hash": snapshot["hash"]})
        conn.execute("UPDATE learning_sessions SET finished_at=COALESCE(finished_at,?) WHERE id=?",
                     (_now(), session_id))
    return state(repo, owner, session_id)


def audio(repo, owner, session_id):
    _, snapshot = owned(repo, owner, session_id)
    if not snapshot["audio"]["identity"] or snapshot["audio"]["identity"] != media_identity():
        fail(409, "音频缺失或版本已变化，不能把新音频当作原会话音频")
    # Issuing media conservatively counts as exposure, not proof of completed playback.
    with repo._conn() as conn:
        append(conn, session_id, new_id("media"), "media_access", "",
               {"content_hash": snapshot["hash"], "completed": False})
    return v2_exam_service.audio_file("cet6_202606_set2_v2")


def save_card(repo, owner, session_id, segment_id, vocabulary_id):
    _, snapshot = owned(repo, owner, session_id)
    item = segment(snapshot, segment_id)
    if not any(e["event_type"] == "reveal" and e["target_id"] == segment_id for e in events(repo, session_id)):
        fail(403, "先在本句中学习，再收藏表达")
    vocabulary = next((v for v in item["vocabulary"] if v["id"] == vocabulary_id), None)
    if not vocabulary:
        fail(403, "词条不属于当前已解锁句段")
    card_id = "learncard_" + hashlib.sha256(dump([owner, snapshot["hash"], vocabulary_id]).encode()).hexdigest()[:24]
    with repo._conn() as conn:
        conn.execute("INSERT OR IGNORE INTO learning_cards VALUES (?,?,?,?,?)",
                     (card_id, owner, session_id, segment_id, dump(vocabulary)))
        conn.execute("""INSERT OR IGNORE INTO lex_srs
            (srs_id,student_id,item_id,next_due) VALUES (?,?,?,?)""", (new_id("srs"), owner, card_id, _now()))
    return {"card_id": card_id, "note": "已加入语境复习；没有核验的词句切片，不计声音识别成绩"}


def due_cards(repo, owner):
    check_release()
    rows = repo._conn().execute("""SELECT c.*,s.next_due FROM learning_cards c JOIN lex_srs s
        ON s.item_id=c.id AND s.student_id=c.owner_id WHERE c.owner_id=? AND s.next_due<=?
        ORDER BY s.next_due,c.id LIMIT 20""", (owner, _now())).fetchall()
    # Context/meaning recall (not aural testing): show the word, never the gloss.
    return [{"card_id": r["id"], "session_id": r["session_id"], "segment_id": r["segment_id"],
             "surface": json.loads(r["vocabulary"])["surface"],
             "next_due": r["next_due"], "task_type": "context_review"} for r in rows]


def card(repo, owner, card_id):
    row = repo._conn().execute("SELECT * FROM learning_cards WHERE id=? AND owner_id=?",
                               (card_id, owner)).fetchone()
    if not row:
        fail(404, "复习卡不存在")
    owned(repo, owner, row["session_id"])
    return row


def reveal_card(repo, owner, card_id, request_id):
    row = card(repo, owner, card_id)
    with repo._conn() as conn:
        append(conn, row["session_id"], request_id, "card_reveal", card_id, {"task_type": "context_review"})
    return {"vocabulary": json.loads(row["vocabulary"]), "review_id": request_id,
            "note": "语境／文字复习，不作为独立声音识别证据"}


def grade_card(repo, owner, card_id, review_id, grade, request_id):
    row = card(repo, owner, card_id)
    conn = repo._conn()
    # One transaction and one grade per due cycle, including double clicks/concurrent tabs.
    with conn:
        conn.execute("BEGIN IMMEDIATE")
        revealed = conn.execute("""SELECT created_at FROM learning_events WHERE session_id=? AND request_id=?
            AND event_type='card_reveal' AND target_id=?""", (row["session_id"], review_id, card_id)).fetchone()
        if not revealed:
            fail(409, "先完成本次卡片揭示")
        inserted = append(conn, row["session_id"], request_id, "card_grade", card_id,
                          {"review_id": review_id, "grade": grade, "task_type": "context_review"})
        if inserted:
            schedule = conn.execute("SELECT * FROM lex_srs WHERE student_id=? AND item_id=?", (owner, card_id)).fetchone()
            if schedule["next_due"] > _now():
                fail(409, "这张卡本轮已复习，请等待下次到期")
            if schedule["last_reviewed"] and revealed["created_at"] <= schedule["last_reviewed"]:
                fail(409, "这是上一轮的揭示，请重新展开本轮词卡")
            interval, ease, repetitions = _sm2_update(schedule["interval_days"], schedule["ease_factor"], schedule["repetitions"], grade)
            due = (datetime.now(timezone.utc) + timedelta(days=interval)).isoformat()
            conn.execute("""UPDATE lex_srs SET next_due=?,interval_days=?,ease_factor=?,repetitions=?,last_reviewed=?
                WHERE student_id=? AND item_id=?""", (due, interval, ease, repetitions, _now(), owner, card_id))
    return {"saved": True, "profile_eligible": False}


def recent(repo, owner):
    check_release()
    rows = repo._conn().execute("""SELECT id,material_id,finished_at FROM learning_sessions
        WHERE owner_id=? ORDER BY created_at DESC LIMIT 20""", (owner,)).fetchall()
    return [{"session_id": r["id"], "material_id": r["material_id"],
             "title": CONTENT[r["material_id"]]["title"], "finished": bool(r["finished_at"])}
            for r in rows if r["material_id"] in CONTENT]
