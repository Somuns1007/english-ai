# -*- coding: utf-8 -*-
"""数据访问层: 题库 JSON 只读加载 + SQLite 学生行为持久化。"""
import json
import os
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
# 生产默认写 data/listening.db；测试可用 LISTENING_DB_PATH 环境变量重定向到临时库，
# 以隔离测试写入、避免污染真实库（K6 教训）。未设该变量时行为与之前完全一致。
DB_PATH = Path(os.environ["LISTENING_DB_PATH"]) if os.environ.get("LISTENING_DB_PATH") else (DATA_DIR / "listening.db")


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
-- Post-listening learning is separate from frozen exam/CP evidence.
CREATE TABLE IF NOT EXISTS learning_sources (
  gate_type TEXT NOT NULL, gate_id TEXT NOT NULL, owner_id TEXT NOT NULL,
  snapshot TEXT NOT NULL, PRIMARY KEY(gate_type, gate_id)
);
CREATE TABLE IF NOT EXISTS learning_sessions (
  id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, gate_type TEXT NOT NULL,
  gate_id TEXT NOT NULL, material_id TEXT NOT NULL, snapshot TEXT NOT NULL,
  created_at TEXT NOT NULL, finished_at TEXT,
  UNIQUE(owner_id, gate_type, gate_id, material_id)
);
CREATE TABLE IF NOT EXISTS learning_events (
  session_id TEXT NOT NULL, request_id TEXT NOT NULL, event_type TEXT NOT NULL,
  target_id TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL,
  PRIMARY KEY(session_id, request_id)
);
CREATE TABLE IF NOT EXISTS learning_cards (
  id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, session_id TEXT NOT NULL,
  segment_id TEXT NOT NULL, vocabulary TEXT NOT NULL,
  UNIQUE(owner_id, session_id, segment_id, vocabulary)
);
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
CREATE TABLE IF NOT EXISTS corpus_assets (
  asset_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  source_name TEXT,
  source_url TEXT,
  license TEXT,
  permission_status TEXT NOT NULL DEFAULT 'unverified',
  source_type TEXT NOT NULL DEFAULT 'authentic_clip',
  file_path TEXT,
  duration_ms INTEGER,
  uploaded_at TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'pending_teacher',
  pipeline_status TEXT NOT NULL DEFAULT 'uploaded',
  pipeline_error TEXT,
  raw_asr_text TEXT,
  cleaned_text TEXT,
  asr_confidence REAL,
  transcript_status TEXT NOT NULL DEFAULT 'none',
  asr_segments TEXT DEFAULT '[]',
  revision INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS corpus_clips (
  clip_id TEXT PRIMARY KEY,
  asset_id TEXT NOT NULL,
  start_ms INTEGER NOT NULL,
  end_ms INTEGER NOT NULL,
  transcript TEXT,
  context_before TEXT,
  context_after TEXT,
  speaker_info TEXT,
  scenario_tags TEXT DEFAULT '[]',
  communicative_function TEXT,
  difficulty TEXT,
  expression_matches TEXT DEFAULT '[]',
  review_status TEXT NOT NULL DEFAULT 'pending_teacher',
  revision INTEGER DEFAULT 1,
  revisions_log TEXT DEFAULT '[]',
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_corpus_clips_asset
  ON corpus_clips (asset_id);
CREATE TABLE IF NOT EXISTS cp_sessions (
  id TEXT PRIMARY KEY,
  student_id TEXT NOT NULL,
  material_id TEXT NOT NULL,
  stage TEXT NOT NULL,
  content_manifest TEXT NOT NULL,
  preview_state TEXT DEFAULT '{}',
  first_pass_valid INTEGER DEFAULT 0,
  pass_attempt_count INTEGER DEFAULT 0,
  replay_count INTEGER DEFAULT 0,
  round2_order TEXT DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS cp_responses (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  check_id TEXT NOT NULL,
  content_revision INTEGER NOT NULL,
  content_hash TEXT NOT NULL,
  round INTEGER NOT NULL,
  selected TEXT,
  is_correct INTEGER,
  recovered_after_full_replay INTEGER DEFAULT 0,
  answered_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cp_responses_session
  ON cp_responses (session_id, round);
CREATE TABLE IF NOT EXISTS cp_events (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  student_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload TEXT DEFAULT '{}',
  client_at TEXT,
  server_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cp_events_session
  ON cp_events (session_id, event_type);

-- ── Aural Lexicon (V2.C CET Track, 2026-08-31) ──────────────────────────────
-- New tables only; existing tables above are frozen (V2.1/V2.2).

CREATE TABLE IF NOT EXISTS lex_items (
  item_id TEXT PRIMARY KEY,
  layer TEXT NOT NULL CHECK(layer IN ('L1','L2','L3')),
  surface TEXT NOT NULL,
  gloss TEXT,
  audio_asset_id TEXT,
  source_set INTEGER NOT NULL DEFAULT 2
    CHECK(source_set = 2),          -- sealed guard: only Set 2 allowed
  source_status TEXT NOT NULL DEFAULT 'machine',
  provenance TEXT,
  sealed_source INTEGER NOT NULL DEFAULT 0
    CHECK(sealed_source = 0),       -- Set-1 entries must never appear
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_lex_items_layer ON lex_items (layer);

CREATE TABLE IF NOT EXISTS lex_audio_assets (
  asset_id TEXT PRIMARY KEY,
  item_id TEXT NOT NULL,
  audio_path TEXT NOT NULL,
  context TEXT NOT NULL DEFAULT 'isolated'
    CHECK(context IN ('isolated','sentence')),
  source TEXT NOT NULL DEFAULT 'tts'
    CHECK(source IN ('tts','corpus_clip')),
  tts_voice TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_lex_audio_item ON lex_audio_assets (item_id);

CREATE TABLE IF NOT EXISTS lex_srs (
  srs_id TEXT PRIMARY KEY,
  student_id TEXT NOT NULL,
  item_id TEXT NOT NULL,
  next_due TEXT NOT NULL,
  interval_days REAL NOT NULL DEFAULT 1.0,
  ease_factor REAL NOT NULL DEFAULT 2.5,
  repetitions INTEGER NOT NULL DEFAULT 0,
  last_reviewed TEXT,
  UNIQUE(student_id, item_id)
);
CREATE INDEX IF NOT EXISTS idx_lex_srs_student ON lex_srs (student_id, next_due);

CREATE TABLE IF NOT EXISTS lex_attempts (
  attempt_id TEXT PRIMARY KEY,
  student_id TEXT NOT NULL,
  item_id TEXT NOT NULL,
  task_type TEXT NOT NULL
    CHECK(task_type IN ('hear_identify','micro_dictation','speed_ladder')),
  response TEXT,
  is_correct INTEGER NOT NULL CHECK(is_correct IN (0,1)),
  lexical_item_recognized INTEGER NOT NULL CHECK(lexical_item_recognized IN (0,1)),
  response_latency_ms INTEGER,
  occurred_at TEXT NOT NULL
  -- NO: understanding_stable, ability_improved, diagnosis, material_mastered
);
CREATE INDEX IF NOT EXISTS idx_lex_attempts_student ON lex_attempts (student_id, item_id);

CREATE TABLE IF NOT EXISTS phase0_state (
  student_id TEXT PRIMARY KEY,
  status TEXT NOT NULL DEFAULT 'not_started'
    CHECK(status IN ('not_started','active','completed','forced_exit')),
  entry_score REAL,
  entry_threshold REAL NOT NULL DEFAULT 0.70,
  started_at TEXT,
  completed_at TEXT,
  forced_exit_at TEXT,
  cap_days INTEGER NOT NULL DEFAULT 21,
  daily_vocab_minutes INTEGER NOT NULL DEFAULT 15
);

CREATE TABLE IF NOT EXISTS phase0_test_attempts (
  attempt_id TEXT PRIMARY KEY,
  student_id TEXT NOT NULL,
  item_id TEXT NOT NULL,
  is_correct INTEGER NOT NULL CHECK(is_correct IN (0,1)),
  occurred_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_p0_test_student ON phase0_test_attempts (student_id);

-- Work Order G: Stem Bank prediction attempts
CREATE TABLE IF NOT EXISTS stem_predictions (
  pred_id TEXT PRIMARY KEY,
  student_id TEXT NOT NULL,
  question_no INTEGER NOT NULL,
  source_set INTEGER NOT NULL DEFAULT 2 CHECK(source_set = 2),
  predicted_type TEXT,             -- student's guess for question_type
  is_type_correct INTEGER CHECK(is_type_correct IN (0,1)),
  selected_answer TEXT,            -- A/B/C/D
  is_answer_correct INTEGER CHECK(is_answer_correct IN (0,1)),
  occurred_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_stem_pred_student ON stem_predictions (student_id);
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
            # 仅测试提速：沙盒 overlay 文件系统 fsync 极慢，逐表建 schema 要数秒。
            # 显式设置 LISTENING_UNSAFE_FAST_DB=1 时关闭 fsync/日志落盘（牺牲掉电耐久性），
            # 生产环境不设该变量 → 行为与之前完全一致（默认 synchronous=FULL）。
            if os.environ.get("LISTENING_UNSAFE_FAST_DB") == "1":
                conn.execute("PRAGMA synchronous=OFF")
                conn.execute("PRAGMA journal_mode=MEMORY")
            self._local.conn = conn
        return conn

    def _init_schema(self) -> None:
        conn = self._conn()
        conn.executescript(_SCHEMA)
        # Existing attempts remain unowned; only authenticated new attempts bind an owner.
        try:
            conn.execute("ALTER TABLE attempts ADD COLUMN owner_id TEXT")
        except sqlite3.OperationalError as exc:
            if "duplicate column name" not in str(exc).lower():
                raise
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
                "content_revision": "ALTER TABLE expression_attempts ADD COLUMN content_revision INTEGER",
            },
            "corpus_assets": {
                "reviewed_at": "ALTER TABLE corpus_assets ADD COLUMN reviewed_at TEXT",
                "consent_id": "ALTER TABLE corpus_assets ADD COLUMN consent_id TEXT",
                "speaker_ids": "ALTER TABLE corpus_assets ADD COLUMN speaker_ids TEXT DEFAULT '[]'",
                "commercial_permission": "ALTER TABLE corpus_assets ADD COLUMN commercial_permission INTEGER DEFAULT 0",
                "editing_permission": "ALTER TABLE corpus_assets ADD COLUMN editing_permission INTEGER DEFAULT 0",
                "ai_processing_permission": "ALTER TABLE corpus_assets ADD COLUMN ai_processing_permission INTEGER DEFAULT 0",
                "recorded_at": "ALTER TABLE corpus_assets ADD COLUMN recorded_at TEXT",
            },
            "corpus_clips": {
                "reviewed_at": "ALTER TABLE corpus_clips ADD COLUMN reviewed_at TEXT",
                "accent": "ALTER TABLE corpus_clips ADD COLUMN accent TEXT",
                "speaker_count": "ALTER TABLE corpus_clips ADD COLUMN speaker_count INTEGER",
                "speech_rate": "ALTER TABLE corpus_clips ADD COLUMN speech_rate TEXT",
                "listening_features": "ALTER TABLE corpus_clips ADD COLUMN listening_features TEXT DEFAULT '[]'",
                "origin": "ALTER TABLE corpus_clips ADD COLUMN origin TEXT DEFAULT 'auto'",
                "content_revision": "ALTER TABLE corpus_clips ADD COLUMN content_revision INTEGER DEFAULT 1",
                "metadata_revision": "ALTER TABLE corpus_clips ADD COLUMN metadata_revision INTEGER DEFAULT 1",
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
        self._seed_lex_items(conn)

    def _seed_lex_items(self, conn: sqlite3.Connection) -> None:
        """从 lexicon_v1.json 初始化 lex_items 种子（幂等，INSERT OR IGNORE）。

        只在表为空时批量写入，已有数据时静默跳过（不覆盖已有条目）。
        种子来源：backend/listening/data/lexicon/lexicon_v1.json
        L1: word → surface; L2: phrase → surface + gloss; L3: term → surface
        """
        count = conn.execute("SELECT COUNT(*) FROM lex_items").fetchone()[0]
        if count > 0:
            return  # 已有数据，跳过（幂等保证）

        seed_path = DATA_DIR / "lexicon" / "lexicon_v1.json"
        if not seed_path.exists():
            return

        data = json.loads(seed_path.read_text(encoding="utf-8"))
        now = _now()
        rows: list[tuple] = []

        for item in data.get("L1", []):
            word = item["word"]
            item_id = f"L1_{word.replace(' ', '_').lower()}"
            rows.append((
                item_id, "L1", word, None,
                item.get("source_set", 2),
                item.get("source_status", "machine"),
                item.get("provenance"),
                int(item.get("sealed_source", False)),
                now,
            ))

        for item in data.get("L2", []):
            item_id = item.get("id") or f"L2_{item['phrase'].replace(' ', '_').lower()}"
            rows.append((
                item_id, "L2", item["phrase"], item.get("gloss"),
                item.get("source_set", 2),
                item.get("source_status", "machine"),
                item.get("provenance"),
                int(item.get("sealed_source", False)),
                now,
            ))

        for item in data.get("L3", []):
            item_id = item.get("id") or f"L3_{item['term'].replace(' ', '_').lower()}"
            rows.append((
                item_id, "L3", item["term"], None,
                2,  # L3 来自题干分析，绑定 Set 2
                item.get("source_status", "manual"),
                item.get("provenance"),
                int(item.get("sealed_source", False)),
                now,
            ))

        conn.executemany(
            """INSERT OR IGNORE INTO lex_items
               (item_id, layer, surface, gloss, source_set,
                source_status, provenance, sealed_source, created_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            rows,
        )
        conn.commit()

    # ----- attempts -----

    def create_attempt(
        self, student_id: str, exam_id: str, mode: str,
        owner_id: str | None = None,
    ) -> dict:
        attempt = {
            "id": new_id("att"),
            "student_id": student_id,
            "owner_id": owner_id,
            "exam_id": exam_id,
            "mode": mode,
            "started_at": _now(),
            "submitted_at": None,
            "score": None,
        }
        conn = self._conn()
        conn.execute(
            "INSERT INTO attempts (id, student_id, owner_id, exam_id, mode, started_at)"
            " VALUES (:id, :student_id, :owner_id, :exam_id, :mode, :started_at)",
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
        content_revision: Optional[int] = None,
    ) -> dict:
        """记录一次跨语境场景训练作答。只落库, 不参与画像评分。

        content_revision 快照作答时的场景版本: 教师实质修改文本后,
        旧 attempt 只能关联旧 revision, 不随新 revision 的批准自动升级。
        """
        rid = new_id("expatt")
        conn = self._conn()
        conn.execute(
            "INSERT INTO expression_attempts"
            " (id, student_id, expression_id, scenario_id, scenario_category,"
            " source_type, listen_count_before_submit, reveal_used,"
            " replay_after_reveal, answer_scene, answer_meaning, answer_key_info,"
            " scene_correct, meaning_correct, key_info_correct, all_correct,"
            " duration_ms, source_quality, verification_level,"
            " evidence_strength, evidence_level, content_revision, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                rid, student_id, expression_id, scenario_id, scenario_category,
                source_type, listen_count_before_submit, int(reveal_used),
                answers.get("scene"), answers.get("meaning"), answers.get("key_info"),
                None if correctness.get("scene") is None else int(correctness["scene"]),
                None if correctness.get("meaning") is None else int(correctness["meaning"]),
                None if correctness.get("key_info") is None else int(correctness["key_info"]),
                None if correctness.get("all") is None else int(correctness["all"]),
                duration_ms, source_quality, verification_level,
                evidence_strength, evidence_level, content_revision, _now(),
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

    # ----- corpus (Phase 7, 真实语料 ingestion) -----

    def create_corpus_asset(self, asset: dict) -> dict:
        params = {
            "consent_id": None,
            "speaker_ids": "[]",
            "commercial_permission": 0,
            "editing_permission": 0,
            "ai_processing_permission": 0,
            "recorded_at": None,
            **asset,
        }
        if not isinstance(params["speaker_ids"], str):
            params["speaker_ids"] = json.dumps(
                params["speaker_ids"], ensure_ascii=False)
        for col in ("commercial_permission", "editing_permission",
                    "ai_processing_permission"):
            params[col] = int(bool(params[col]))
        conn = self._conn()
        conn.execute(
            "INSERT INTO corpus_assets"
            " (asset_id, title, source_name, source_url, license, permission_status,"
            " source_type, file_path, duration_ms, uploaded_at, review_status,"
            " pipeline_status, transcript_status, revision, consent_id,"
            " speaker_ids, commercial_permission, editing_permission,"
            " ai_processing_permission, recorded_at)"
            " VALUES (:asset_id, :title, :source_name, :source_url, :license,"
            " :permission_status, :source_type, :file_path, :duration_ms,"
            " :uploaded_at, :review_status, :pipeline_status, :transcript_status, 1,"
            " :consent_id, :speaker_ids, :commercial_permission,"
            " :editing_permission, :ai_processing_permission, :recorded_at)",
            params,
        )
        conn.commit()
        return asset

    def get_corpus_asset(self, asset_id: str) -> Optional[dict]:
        row = self._conn().execute(
            "SELECT * FROM corpus_assets WHERE asset_id = ?", (asset_id,)
        ).fetchone()
        return self._asset_row(row) if row else None

    def list_corpus_assets(self) -> list[dict]:
        rows = self._conn().execute(
            "SELECT * FROM corpus_assets ORDER BY uploaded_at DESC"
        ).fetchall()
        return [self._asset_row(r) for r in rows]

    def update_corpus_asset(self, asset_id: str, fields: dict) -> None:
        if not fields:
            return
        fields = dict(fields)
        json_cols = {"asr_segments", "speaker_ids"}
        for col in json_cols:
            if col in fields and not isinstance(fields[col], str):
                fields[col] = json.dumps(fields[col], ensure_ascii=False)
        sets = ", ".join(f"{k} = :{k}" for k in fields)
        fields["asset_id"] = asset_id
        conn = self._conn()
        conn.execute(
            f"UPDATE corpus_assets SET {sets} WHERE asset_id = :asset_id", fields
        )
        conn.commit()

    def _asset_row(self, row) -> dict:
        d = dict(row)
        d["asr_segments"] = json.loads(d.get("asr_segments") or "[]")
        d["speaker_ids"] = json.loads(d.get("speaker_ids") or "[]")
        for col in ("commercial_permission", "editing_permission",
                    "ai_processing_permission"):
            d[col] = bool(d.get(col))
        return d

    def create_corpus_clip(self, clip: dict) -> dict:
        conn = self._conn()
        conn.execute(
            "INSERT INTO corpus_clips"
            " (clip_id, asset_id, start_ms, end_ms, transcript, context_before,"
            " context_after, speaker_info, scenario_tags, communicative_function,"
            " difficulty, expression_matches, review_status, revision, created_at,"
            " origin)"
            " VALUES (:clip_id, :asset_id, :start_ms, :end_ms, :transcript,"
            " :context_before, :context_after, :speaker_info, :scenario_tags,"
            " :communicative_function, :difficulty, :expression_matches,"
            " :review_status, :revision, :created_at,"
            " COALESCE(:origin, 'auto'))",
            clip,
        )
        conn.commit()
        return clip

    def get_corpus_clip(self, clip_id: str) -> Optional[dict]:
        row = self._conn().execute(
            "SELECT * FROM corpus_clips WHERE clip_id = ?", (clip_id,)
        ).fetchone()
        return self._clip_row(row) if row else None

    def list_corpus_clips(self, asset_id: Optional[str] = None) -> list[dict]:
        sql = "SELECT * FROM corpus_clips"
        params: list = []
        if asset_id:
            sql += " WHERE asset_id = ?"
            params.append(asset_id)
        sql += " ORDER BY start_ms"
        rows = self._conn().execute(sql, params).fetchall()
        return [self._clip_row(r) for r in rows]

    def update_corpus_clip(self, clip_id: str, fields: dict) -> None:
        if not fields:
            return
        fields = dict(fields)
        for col in ("scenario_tags", "expression_matches", "revisions_log",
                    "listening_features"):
            if col in fields and not isinstance(fields[col], str):
                fields[col] = json.dumps(fields[col], ensure_ascii=False)
        sets = ", ".join(f"{k} = :{k}" for k in fields)
        fields["clip_id"] = clip_id
        conn = self._conn()
        conn.execute(
            f"UPDATE corpus_clips SET {sets} WHERE clip_id = :clip_id", fields
        )
        conn.commit()

    def delete_corpus_clips(self, asset_id: str) -> int:
        """重跑切分时清除该 asset 下未审核的自动生成候选 clip(教师手工 clip 不动)。"""
        conn = self._conn()
        cur = conn.execute(
            "DELETE FROM corpus_clips WHERE asset_id = ?"
            " AND review_status = 'pending_teacher' AND origin = 'auto'",
            (asset_id,),
        )
        conn.commit()
        return cur.rowcount

    def _clip_row(self, row) -> dict:
        d = dict(row)
        d["scenario_tags"] = json.loads(d.get("scenario_tags") or "[]")
        d["expression_matches"] = json.loads(d.get("expression_matches") or "[]")
        d["revisions_log"] = json.loads(d.get("revisions_log") or "[]")
        d["listening_features"] = json.loads(d.get("listening_features") or "[]")
        return d

    # ----- V2.2 Continuous Practice (cp_*) -----

    def create_cp_session(
        self, student_id: str, material_id: str,
        manifest: dict, round2_order: dict,
    ) -> dict:
        session = {
            "id": new_id("cps"),
            "student_id": student_id,
            "material_id": material_id,
            "stage": "intro",
            "content_manifest": json.dumps(manifest, ensure_ascii=False),
            "preview_state": "{}",
            "first_pass_valid": 0,
            "pass_attempt_count": 0,
            "replay_count": 0,
            "round2_order": json.dumps(round2_order, ensure_ascii=False),
            "created_at": _now(),
            "updated_at": _now(),
        }
        conn = self._conn()
        conn.execute(
            "INSERT INTO cp_sessions (id, student_id, material_id, stage,"
            " content_manifest, preview_state, first_pass_valid,"
            " pass_attempt_count, replay_count, round2_order, created_at, updated_at)"
            " VALUES (:id, :student_id, :material_id, :stage,"
            " :content_manifest, :preview_state, :first_pass_valid,"
            " :pass_attempt_count, :replay_count, :round2_order, :created_at, :updated_at)",
            session,
        )
        conn.commit()
        return self.get_cp_session(session["id"])

    def get_cp_session(self, session_id: str) -> Optional[dict]:
        row = self._conn().execute(
            "SELECT * FROM cp_sessions WHERE id = ?", (session_id,)
        ).fetchone()
        return self._cp_session_row(row) if row else None

    def find_latest_cp_session(
        self, student_id: str, material_id: str
    ) -> Optional[dict]:
        """刷新恢复用: 该学生在该材料上最近一次的 session。"""
        row = self._conn().execute(
            "SELECT * FROM cp_sessions WHERE student_id = ? AND material_id = ?"
            " ORDER BY created_at DESC LIMIT 1",
            (student_id, material_id),
        ).fetchone()
        return self._cp_session_row(row) if row else None

    def update_cp_session(self, session_id: str, fields: dict) -> None:
        if not fields:
            return
        fields = dict(fields)
        for col in ("preview_state", "round2_order", "content_manifest"):
            if col in fields and not isinstance(fields[col], str):
                fields[col] = json.dumps(fields[col], ensure_ascii=False)
        fields["updated_at"] = _now()
        sets = ", ".join(f"{k} = :{k}" for k in fields)
        fields["id"] = session_id
        conn = self._conn()
        conn.execute(f"UPDATE cp_sessions SET {sets} WHERE id = :id", fields)
        conn.commit()

    def _cp_session_row(self, row) -> dict:
        d = dict(row)
        d["content_manifest"] = json.loads(d.get("content_manifest") or "{}")
        d["preview_state"] = json.loads(d.get("preview_state") or "{}")
        d["round2_order"] = json.loads(d.get("round2_order") or "{}")
        return d

    def add_cp_events(self, session_id: str, student_id: str, events: list) -> int:
        """cp 事件流水。只记录事实, 不做错因推断。"""
        def _get(e, key, default=None):
            if isinstance(e, dict):
                return e.get(key, default)
            return getattr(e, key, default)

        conn = self._conn()
        rows = [
            (
                new_id("evt"),
                session_id,
                student_id,
                _get(e, "event_type"),
                json.dumps(_get(e, "payload", {}) or {}, ensure_ascii=False),
                _get(e, "client_at"),
                _now(),
            )
            for e in events
        ]
        conn.executemany(
            "INSERT INTO cp_events"
            " (id, session_id, student_id, event_type, payload, client_at, server_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        conn.commit()
        return len(rows)

    def list_cp_events(self, session_id: str, event_type: Optional[str] = None) -> list[dict]:
        sql = "SELECT * FROM cp_events WHERE session_id = ?"
        params: list = [session_id]
        if event_type:
            sql += " AND event_type = ?"
            params.append(event_type)
        sql += " ORDER BY server_at, rowid"
        rows = self._conn().execute(sql, params).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["payload"] = json.loads(d.get("payload") or "{}")
            out.append(d)
        return out

    def add_cp_response(
        self, session_id: str, check_id: str, revision: int, content_hash: str,
        round_: int, selected: str, is_correct: bool, recovered: bool = False,
    ) -> dict:
        resp = {
            "id": new_id("cpr"),
            "session_id": session_id,
            "check_id": check_id,
            "content_revision": revision,
            "content_hash": content_hash,
            "round": round_,
            "selected": selected,
            "is_correct": 1 if is_correct else 0,
            "recovered_after_full_replay": 1 if recovered else 0,
            "answered_at": _now(),
        }
        conn = self._conn()
        conn.execute(
            "INSERT INTO cp_responses (id, session_id, check_id, content_revision,"
            " content_hash, round, selected, is_correct, recovered_after_full_replay,"
            " answered_at)"
            " VALUES (:id, :session_id, :check_id, :content_revision,"
            " :content_hash, :round, :selected, :is_correct,"
            " :recovered_after_full_replay, :answered_at)",
            resp,
        )
        conn.commit()
        return resp

    def list_cp_responses(self, session_id: str, round_: Optional[int] = None) -> list[dict]:
        sql = "SELECT * FROM cp_responses WHERE session_id = ?"
        params: list = [session_id]
        if round_ is not None:
            sql += " AND round = ?"
            params.append(round_)
        sql += " ORDER BY answered_at, rowid"
        rows = self._conn().execute(sql, params).fetchall()
        return [dict(r) for r in rows]


exam_repo = ExamRepository()


class _LazyStudentRepo:
    """
    懒加载代理：仅在首次属性访问时真正初始化 StudentRepository。
    这样 import 阶段不会触发 SQLite 写操作，测试可以安全 import 再通过
    patch 替换 svc.student_repo，而不会在 Windows 挂载路径上产生 I/O 错误。
    """
    _real: "StudentRepository | None" = None

    def _get(self) -> "StudentRepository":
        if self._real is None:
            self._real = StudentRepository()
        return self._real

    def __getattr__(self, name: str):
        return getattr(self._get(), name)

    def __setattr__(self, name: str, value):
        if name == "_real":
            object.__setattr__(self, name, value)
        else:
            setattr(self._get(), name, value)


student_repo: StudentRepository = _LazyStudentRepo()  # type: ignore[assignment]
