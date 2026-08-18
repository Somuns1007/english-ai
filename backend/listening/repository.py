# -*- coding: utf-8 -*-
"""数据访问层: 题库 JSON 只读加载 + SQLite 学生行为持久化。"""
import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .models import Exam

DATA_DIR = Path(__file__).resolve().parent / "data"
EXAMS_DIR = DATA_DIR / "exams"
AUDIO_DIR = DATA_DIR / "audio"
DB_PATH = DATA_DIR / "listening.db"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


# ---------- 题库(JSON 只读) ----------


class ExamRepository:
    """启动时扫描 data/exams/*.json; 新增套题只需放新 JSON, 无需改代码。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._exams: dict[str, Exam] = {}
        self._signature: tuple = ()
        self.reload()

    def _dir_signature(self) -> tuple:
        if not EXAMS_DIR.exists():
            return ()
        return tuple(
            (p.name, p.stat().st_mtime_ns)
            for p in sorted(EXAMS_DIR.glob("*.json"))
        )

    def reload(self) -> None:
        exams: dict[str, Exam] = {}
        if EXAMS_DIR.exists():
            for path in sorted(EXAMS_DIR.glob("*.json")):
                data = json.loads(path.read_text(encoding="utf-8"))
                exam = Exam.model_validate(data)
                exams[exam.id] = exam
        with self._lock:
            self._exams = exams
            self._signature = self._dir_signature()

    def reload_if_changed(self) -> None:
        """新增/替换套题 JSON 后无需重启服务即可上线。"""
        if self._dir_signature() != self._signature:
            self.reload()

    def list(self) -> list[Exam]:
        self.reload_if_changed()
        with self._lock:
            return sorted(self._exams.values(), key=lambda e: (e.year, e.month, e.set_no))

    def get(self, exam_id: str) -> Optional[Exam]:
        self.reload_if_changed()
        with self._lock:
            return self._exams.get(exam_id)

    def audio_file(self, exam_id: str) -> Optional[Path]:
        exam = self.get(exam_id)
        if not exam:
            return None
        path = (DATA_DIR / exam.audio_path).resolve()
        # 防目录穿越
        if not str(path).startswith(str(AUDIO_DIR.resolve().parent)):
            return None
        return path if path.exists() else None


def load_tag_dictionary() -> dict:
    path = DATA_DIR / "tag_dictionary.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


# ---------- 学生行为(SQLite) ----------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS attempts (
  id TEXT PRIMARY KEY,
  student_id TEXT NOT NULL,
  exam_id TEXT NOT NULL,
  mode TEXT NOT NULL,
  started_at TEXT NOT NULL,
  submitted_at TEXT,
  score INTEGER
);
CREATE TABLE IF NOT EXISTS attempt_answers (
  attempt_id TEXT NOT NULL,
  question_id TEXT NOT NULL,
  first_answer TEXT,
  final_answer TEXT,
  first_answer_at TEXT,
  last_answer_at TEXT,
  change_count INTEGER DEFAULT 0,
  dwell_ms INTEGER DEFAULT 0,
  is_first_correct INTEGER,
  relisten_count INTEGER DEFAULT 0,
  max_hint_level INTEGER DEFAULT 0,
  PRIMARY KEY (attempt_id, question_id)
);
CREATE TABLE IF NOT EXISTS behavior_events (
  id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL,
  student_id TEXT NOT NULL,
  question_id TEXT,
  event_type TEXT NOT NULL,
  payload TEXT DEFAULT '{}',
  client_at TEXT,
  server_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_behavior_attempt
  ON behavior_events (attempt_id, event_type);
CREATE TABLE IF NOT EXISTS diagnoses (
  id TEXT PRIMARY KEY,
  student_id TEXT NOT NULL,
  attempt_id TEXT NOT NULL,
  question_id TEXT NOT NULL,
  student_tags TEXT DEFAULT '[]',
  ai_tags TEXT DEFAULT '[]',
  final_tags TEXT DEFAULT '[]',
  revision INTEGER DEFAULT 1,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS training_results (
  id TEXT PRIMARY KEY,
  student_id TEXT NOT NULL,
  question_id TEXT NOT NULL,
  training_type TEXT NOT NULL,
  attempt_id TEXT,
  diagnosis_id TEXT,
  diagnosis_revision INTEGER,
  provenance TEXT,
  trigger_tags TEXT DEFAULT '[]',
  input TEXT DEFAULT '{}',
  result INTEGER,
  score REAL,
  error_details TEXT DEFAULT '[]',
  hints_used INTEGER DEFAULT 0,
  duration_ms INTEGER,
  pre_result INTEGER,
  post_result INTEGER,
  completed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS expression_attempts (
  id TEXT PRIMARY KEY,
  student_id TEXT NOT NULL,
  expression_id TEXT NOT NULL,
  scenario_id TEXT NOT NULL,
  scenario_category TEXT,
  source_type TEXT,
  listen_count_before_submit INTEGER DEFAULT 0,
  reveal_used INTEGER DEFAULT 0,
  replay_after_reveal INTEGER DEFAULT 0,
  answer_scene TEXT,
  answer_meaning TEXT,
  answer_key_info TEXT,
  scene_correct INTEGER,
  meaning_correct INTEGER,
  key_info_correct INTEGER,
  all_correct INTEGER,
  duration_ms INTEGER,
  source_quality TEXT,
  verification_level TEXT,
  evidence_strength REAL,
  evidence_level TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_expr_attempts_student
  ON expression_attempts (student_id, expression_id);
"""


class StudentRepository:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self._db_path = db_path
        self._local = threading.local()
        self._init_schema()

    def _conn(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self._db_path)
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
        return conn

    def _init_schema(self) -> None:
        conn = self._conn()
        conn.executescript(_SCHEMA)
        # 轻量迁移: 为早期 dev 库补充新列
        migrations = {
            "attempt_answers": {
                "last_answer_at": "ALTER TABLE attempt_answers ADD COLUMN last_answer_at TEXT",
                "dwell_ms": "ALTER TABLE attempt_answers ADD COLUMN dwell_ms INTEGER DEFAULT 0",
            },
            "diagnoses": {
                "revision": "ALTER TABLE diagnoses ADD COLUMN revision INTEGER DEFAULT 1",
            },
            "training_results": {
                "attempt_id": "ALTER TABLE training_results ADD COLUMN attempt_id TEXT",
                "diagnosis_id": "ALTER TABLE training_results ADD COLUMN diagnosis_id TEXT",
                "diagnosis_revision": "ALTER TABLE training_results ADD COLUMN diagnosis_revision INTEGER",
                "provenance": "ALTER TABLE training_results ADD COLUMN provenance TEXT",
                "trigger_tags": "ALTER TABLE training_results ADD COLUMN trigger_tags TEXT DEFAULT '[]'",
                "input": "ALTER TABLE training_results ADD COLUMN input TEXT DEFAULT '{}'",
                "result": "ALTER TABLE training_results ADD COLUMN result INTEGER",
                "score": "ALTER TABLE training_results ADD COLUMN score REAL",
                "error_details": "ALTER TABLE training_results ADD COLUMN error_details TEXT DEFAULT '[]'",
                "hints_used": "ALTER TABLE training_results ADD COLUMN hints_used INTEGER DEFAULT 0",
                "duration_ms": "ALTER TABLE training_results ADD COLUMN duration_ms INTEGER",
            },
            "expression_attempts": {
                "source_quality": "ALTER TABLE expression_attempts ADD COLUMN source_quality TEXT",
                "verification_level": "ALTER TABLE expression_attempts ADD COLUMN verification_level TEXT",
                "evidence_strength": "ALTER TABLE expression_attempts ADD COLUMN evidence_strength REAL",
                "evidence_level": "ALTER TABLE expression_attempts ADD COLUMN evidence_level TEXT",
            },
        }
        for table, cols in migrations.items():
            existing = {
                row[1]
                for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
            }
            for col, ddl in cols.items():
                if col not in existing:
                    conn.execute(ddl)
        conn.commit()
    # ----- attempts -----

    def create_attempt(self, student_id: str, exam_id: str, mode: str) -> dict:
        attempt = {
            "id": new_id("att"),
            "student_id": student_id,
            "exam_id": exam_id,
            "mode": mode,
            "started_at": _now(),
            "submitted_at": None,
            "score": None,
        }
        conn = self._conn()
        conn.execute(
            "INSERT INTO attempts (id, student_id, exam_id, mode, started_at)"
            " VALUES (:id, :student_id, :exam_id, :mode, :started_at)",
            attempt,
        )
        conn.commit()
        return attempt

    def get_attempt(self, attempt_id: str) -> Optional[dict]:
        row = self._conn().execute(
            "SELECT * FROM attempts WHERE id = ?", (attempt_id,)
        ).fetchone()
        return dict(row) if row else None

    def upsert_answer(self, attempt_id: str, question_id: str, fields: dict) -> None:
        conn = self._conn()
        conn.execute(
            "INSERT INTO attempt_answers (attempt_id, question_id)"
            " VALUES (?, ?) ON CONFLICT (attempt_id, question_id) DO NOTHING",
            (attempt_id, question_id),
        )
        sets = ", ".join(f"{k} = :{k}" for k in fields)
        if sets:
            fields = dict(fields, attempt_id=attempt_id, question_id=question_id)
            conn.execute(
                f"UPDATE attempt_answers SET {sets}"
                " WHERE attempt_id = :attempt_id AND question_id = :question_id",
                fields,
            )
        conn.commit()

    def list_answers(self, attempt_id: str) -> list[dict]:
        rows = self._conn().execute(
            "SELECT * FROM attempt_answers WHERE attempt_id = ?", (attempt_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def submit_attempt(self, attempt_id: str, score: int) -> Optional[dict]:
        conn = self._conn()
        conn.execute(
            "UPDATE attempts SET submitted_at = ?, score = ? WHERE id = ?",
            (_now(), score, attempt_id),
        )
        conn.commit()
        return self.get_attempt(attempt_id)

    def latest_attempt_for_exam(self, student_id: str, exam_id: str) -> Optional[dict]:
        row = self._conn().execute(
            "SELECT * FROM attempts WHERE student_id = ? AND exam_id = ?"
            " AND submitted_at IS NOT NULL ORDER BY submitted_at DESC LIMIT 1",
            (student_id, exam_id),
        ).fetchone()
        return dict(row) if row else None

    def list_submitted_attempts(self, student_id: str) -> list[dict]:
        """画像聚合用: 该学生全部已提交 attempt, 按提交时间升序。"""
        rows = self._conn().execute(
            "SELECT * FROM attempts WHERE student_id = ?"
            " AND submitted_at IS NOT NULL ORDER BY submitted_at",
            (student_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def find_in_progress_attempt(
        self, student_id: str, exam_id: str, mode: str
    ) -> Optional[dict]:
        """刷新恢复用: 查找未提交的同模式 attempt。"""
        row = self._conn().execute(
            "SELECT * FROM attempts WHERE student_id = ? AND exam_id = ?"
            " AND mode = ? AND submitted_at IS NULL"
            " ORDER BY started_at DESC LIMIT 1",
            (student_id, exam_id, mode),
        ).fetchone()
        return dict(row) if row else None

    # ----- behavior events -----

    def add_behavior_events(
        self, student_id: str, attempt_id: str, events: list
    ) -> int:
        """追加行为事件流水。只做客观记录, 不做任何错因推断。

        events 元素可以是 BehaviorEventIn 或等价 dict。
        """
        def _get(e, key, default=None):
            if isinstance(e, dict):
                return e.get(key, default)
            return getattr(e, key, default)

        conn = self._conn()
        rows = [
            (
                new_id("evt"),
                attempt_id,
                student_id,
                _get(e, "question_id"),
                _get(e, "event_type"),
                json.dumps(_get(e, "payload", {}) or {}, ensure_ascii=False),
                _get(e, "client_at"),
                _now(),
            )
            for e in events
        ]
        conn.executemany(
            "INSERT INTO behavior_events"
            " (id, attempt_id, student_id, question_id, event_type, payload, client_at, server_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        conn.commit()
        self._apply_event_side_effects(attempt_id, events)
        return len(rows)

    def _apply_event_side_effects(self, attempt_id: str, events: list) -> None:
        """把关键事件聚合成 attempt_answers 上的便捷计数, 原始事件仍全量保留。

        relisten_count: 该题作答期间整段 Unit 重播次数(不代表精准复听定位句)
        max_hint_level: hint_open 事件 payload.level 的最大值
        """
        def _get(e, key, default=None):
            if isinstance(e, dict):
                return e.get(key, default)
            return getattr(e, key, default)

        conn = self._conn()
        relisten: dict[str, int] = {}
        hint: dict[str, int] = {}
        for e in events:
            qid = _get(e, "question_id")
            if not qid:
                continue
            etype = _get(e, "event_type")
            if etype == "audio_replay":
                relisten[qid] = relisten.get(qid, 0) + 1
            elif etype == "hint_open":
                level = int((_get(e, "payload", {}) or {}).get("level", 0) or 0)
                hint[qid] = max(hint.get(qid, 0), level)
        for qid, count in relisten.items():
            conn.execute(
                "INSERT INTO attempt_answers (attempt_id, question_id, relisten_count)"
                " VALUES (?, ?, ?)"
                " ON CONFLICT (attempt_id, question_id)"
                " DO UPDATE SET relisten_count = relisten_count + ?",
                (attempt_id, qid, count, count),
            )
        for qid, level in hint.items():
            conn.execute(
                "INSERT INTO attempt_answers (attempt_id, question_id, max_hint_level)"
                " VALUES (?, ?, ?)"
                " ON CONFLICT (attempt_id, question_id)"
                " DO UPDATE SET max_hint_level = MAX(max_hint_level, ?)",
                (attempt_id, qid, level, level),
            )
        conn.commit()

    def list_behavior_events(
        self, attempt_id: str, event_type: Optional[str] = None
    ) -> list[dict]:
        sql = "SELECT * FROM behavior_events WHERE attempt_id = ?"
        params: list = [attempt_id]
        if event_type:
            sql += " AND event_type = ?"
            params.append(event_type)
        sql += " ORDER BY COALESCE(client_at, server_at), server_at, id"
        rows = self._conn().execute(sql, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["payload"] = json.loads(d["payload"])
            result.append(d)
        return result

    # ----- diagnoses -----

    def upsert_diagnosis(
        self,
        student_id: str,
        attempt_id: str,
        question_id: str,
        student_tags: list[str],
        ai_tags: list[dict],
        final_tags: list[str],
    ) -> dict:
        """同一题反复诊断时 id 稳定、revision 递增。

        训练结果通过 (diagnosis_id, diagnosis_revision) 精确回溯
        "哪一次诊断结论触发了这次训练"; 旧训练的 revision 快照不被重写。
        """
        conn = self._conn()
        row = conn.execute(
            "SELECT id, revision FROM diagnoses"
            " WHERE attempt_id = ? AND question_id = ?",
            (attempt_id, question_id),
        ).fetchone()
        diag_id = row["id"] if row else new_id("diag")
        revision = (row["revision"] or 0) + 1 if row else 1
        conn.execute(
            "INSERT INTO diagnoses"
            " (id, student_id, attempt_id, question_id, student_tags, ai_tags,"
            " final_tags, revision, updated_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
            " ON CONFLICT (id) DO UPDATE SET"
            " student_tags = excluded.student_tags, ai_tags = excluded.ai_tags,"
            " final_tags = excluded.final_tags, revision = excluded.revision,"
            " updated_at = excluded.updated_at",
            (
                diag_id, student_id, attempt_id, question_id,
                json.dumps(student_tags, ensure_ascii=False),
                json.dumps(ai_tags, ensure_ascii=False),
                json.dumps(final_tags, ensure_ascii=False),
                revision,
                _now(),
            ),
        )
        conn.commit()
        return {"id": diag_id, "revision": revision}

    def get_diagnosis(self, attempt_id: str, question_id: str) -> Optional[dict]:
        row = self._conn().execute(
            "SELECT * FROM diagnoses WHERE attempt_id = ? AND question_id = ?",
            (attempt_id, question_id),
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        for k in ("student_tags", "ai_tags", "final_tags"):
            d[k] = json.loads(d[k])
        return d

    # ----- training -----

    def add_training_result(
        self,
        student_id: str,
        question_id: str,
        training_type: str,
        pre_result: Optional[bool] = None,
        post_result: Optional[bool] = None,
        *,
        attempt_id: Optional[str] = None,
        diagnosis_id: Optional[str] = None,
        diagnosis_revision: Optional[int] = None,
        provenance: Optional[str] = None,
        trigger_tags: Optional[list[str]] = None,
        input: Optional[dict] = None,
        result: Optional[bool] = None,
        score: Optional[float] = None,
        error_details: Optional[list] = None,
        hints_used: int = 0,
        duration_ms: Optional[int] = None,
    ) -> dict:
        rid = new_id("train")
        conn = self._conn()
        conn.execute(
            "INSERT INTO training_results"
            " (id, student_id, question_id, training_type, attempt_id, diagnosis_id,"
            " diagnosis_revision, provenance, trigger_tags,"
            " input, result, score, error_details, hints_used, duration_ms,"
            " pre_result, post_result, completed_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                rid, student_id, question_id, training_type, attempt_id, diagnosis_id,
                diagnosis_revision, provenance,
                json.dumps(trigger_tags or [], ensure_ascii=False),
                json.dumps(input or {}, ensure_ascii=False),
                None if result is None else int(result),
                score,
                json.dumps(error_details or [], ensure_ascii=False),
                hints_used, duration_ms,
                None if pre_result is None else int(pre_result),
                None if post_result is None else int(post_result),
                _now(),
            ),
        )
        conn.commit()
        return {"id": rid}

    def list_training_results(
        self, student_id: str, question_id: Optional[str] = None
    ) -> list[dict]:
        sql = "SELECT * FROM training_results WHERE student_id = ?"
        params: list = [student_id]
        if question_id:
            sql += " AND question_id = ?"
            params.append(question_id)
        sql += " ORDER BY completed_at"
        rows = self._conn().execute(sql, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["input"] = json.loads(d["input"] or "{}")
            d["error_details"] = json.loads(d["error_details"] or "[]")
            d["trigger_tags"] = json.loads(d.get("trigger_tags") or "[]")
            result.append(d)
        return result

    # ----- expression bridge (Phase 6, cross-context 证据; 不回流画像) -----

    def add_expression_attempt(
        self,
        student_id: str,
        expression_id: str,
        scenario_id: str,
        scenario_category: Optional[str],
        source_type: Optional[str],
        listen_count_before_submit: int,
        reveal_used: bool,
        answers: dict,
        correctness: dict,
        duration_ms: Optional[int],
        source_quality: Optional[str] = None,
        verification_level: Optional[str] = None,
        evidence_strength: Optional[float] = None,
        evidence_level: Optional[str] = None,
    ) -> dict:
        """记录一次跨语境场景训练作答。只落库, 不参与画像评分。"""
        rid = new_id("expatt")
        conn = self._conn()
        conn.execute(
            "INSERT INTO expression_attempts"
            " (id, student_id, expression_id, scenario_id, scenario_category,"
            " source_type, listen_count_before_submit, reveal_used,"
            " replay_after_reveal, answer_scene, answer_meaning, answer_key_info,"
            " scene_correct, meaning_correct, key_info_correct, all_correct,"
            " duration_ms, source_quality, verification_level,"
            " evidence_strength, evidence_level, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                rid, student_id, expression_id, scenario_id, scenario_category,
                source_type, listen_count_before_submit, int(reveal_used),
                answers.get("scene"), answers.get("meaning"), answers.get("key_info"),
                None if correctness.get("scene") is None else int(correctness["scene"]),
                None if correctness.get("meaning") is None else int(correctness["meaning"]),
                None if correctness.get("key_info") is None else int(correctness["key_info"]),
                None if correctness.get("all") is None else int(correctness["all"]),
                duration_ms, source_quality, verification_level,
                evidence_strength, evidence_level, _now(),
            ),
        )
        conn.commit()
        return {"id": rid}

    def increment_expression_replay(self, attempt_id: str) -> bool:
        """揭示文本后再次播放音频的计数。"""
        conn = self._conn()
        cur = conn.execute(
            "UPDATE expression_attempts SET replay_after_reveal = replay_after_reveal + 1"
            " WHERE id = ?",
            (attempt_id,),
        )
        conn.commit()
        return cur.rowcount > 0

    def get_expression_attempt(self, attempt_id: str) -> Optional[dict]:
        row = self._conn().execute(
            "SELECT * FROM expression_attempts WHERE id = ?", (attempt_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_expression_attempts(
        self, student_id: str, expression_id: Optional[str] = None
    ) -> list[dict]:
        sql = "SELECT * FROM expression_attempts WHERE student_id = ?"
        params: list = [student_id]
        if expression_id:
            sql += " AND expression_id = ?"
            params.append(expression_id)
        sql += " ORDER BY created_at"
        rows = self._conn().execute(sql, params).fetchall()
        return [dict(r) for r in rows]


exam_repo = ExamRepository()
student_repo = StudentRepository()
