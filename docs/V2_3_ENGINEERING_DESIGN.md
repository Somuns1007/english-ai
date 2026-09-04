# V2.3 Engineering Design — Evidence Foundation + New Input MVP + Selective Probe Pilot

状态：**工程设计草案（engineering design），非编码授权**。
依据：`docs/V2_3_MINIMAL_MVP_SPEC.md`（产品/语义规格，READY_FOR_V2_3_ENGINEERING_DESIGN）+ `CODEX_PROJECT_HANDOFF_AUDIT.md`（L 段前置决策、K 段隐患处置）。
日期：2026-09-05
本文把规格的语义契约翻译为可实现的表结构、接口、模块边界、状态机与验收测试。**编码仍需 S3 门禁：S1 三处产品确认 + 本设计评审通过。**

---

## 0. 冻结边界（硬约束，先于一切）

V2.3 是**独立子系统**。以下模块**禁止改动行为**（规格 §2 non-goals、§13.9）：

- `backend/listening/v2_practice_service.py`、`cp_sessions/cp_responses/cp_events` schema —— V2.2 冻结；
- `backend/listening/v2_exam_service.py` 的 V2.1 行为、`attempts/answers/behavior_events` —— V2.1 冻结；
- `frontend/.../ListeningPracticeV2View.vue` —— V2.2 冻结。

允许：**只读复用** `v2_exam_service` 的 gate/身份工具函数，但 V2.3 用**独立 gate 开关**（见 §9）。V2.3 绝不把 V2.1/V2.2 的结果当作 transfer evidence。

命名前缀统一 `v2_3_` / `V2_3` / 表前缀 `v3_`，避免与 `cp_`（V2.2）混淆。

---

## 1. 模块与文件布局

```
backend/listening/
  v2_3_input_service.py        # New Input 分配、exposure 记录、轻量 check、transcript reveal
  v2_3_probe_service.py        # Selective Probe 触发校验、observation 产出
  v2_3_ledger.py               # exposure ledger 读写（原子、幂等）
  v2_3_identity.py             # pilot_subject_id 签发与 owner 校验
  v2_3_content_registry.py     # 三内容池 candidate JSON 加载（仿 v2_practice_registry）
  v2_3_dto.py                  # DTO 白名单 + 禁字段断言（值级+键级，见 §10）
  router_v2_3.py               # 独立 APIRouter，挂 /api/listening/v2_3/*
data/v2_3/
  input_pool/*.candidate.json
  near_holdout/*.candidate.json
  far_benchmark/*.candidate.json
backend/tests/
  test_v2_3_input.py
  test_v2_3_probe.py
  test_v2_3_ledger_integrity.py
  test_v2_3_gate_identity.py
```

`router_v2_3.router` 在 `main.py` 里 `include_router`；与现有 listening router 平级、互不影响。

---

## 2. 数据库 schema（新表，全部 `v3_` 前缀）

沿用 V2.2 的 SQLite（`listening.db`），经 `student_repo` 同一连接层扩展，但**新表独立**。所有写操作要幂等、可恢复、并发安全（规格 §13.2）。

### 2.1 `v3_subjects` —— pilot 身份
```sql
CREATE TABLE v3_subjects (
  pilot_subject_id TEXT PRIMARY KEY,   -- 服务端签发, 不可由客户端指定
  created_at       TEXT NOT NULL,
  last_seen_at     TEXT
);
```

### 2.2 `v3_exposure_ledger` —— 暴露账本（规格 §6）
```sql
CREATE TABLE v3_exposure_ledger (
  pilot_subject_id     TEXT NOT NULL,
  item_id              TEXT NOT NULL,
  media_id             TEXT NOT NULL,
  material_pool        TEXT NOT NULL,          -- input / near_holdout / far_benchmark
  first_exposed_at     TEXT,
  last_exposed_at      TEXT,
  exposure_count       INTEGER NOT NULL DEFAULT 0,
  exposure_started     INTEGER NOT NULL DEFAULT 0,  -- bool
  meaningful_exposure  INTEGER NOT NULL DEFAULT 0,  -- 仅学习分析, 绝不恢复 holdout 资格
  audio_completed      INTEGER NOT NULL DEFAULT 0,  -- 只表播放完整, 不表理解
  transcript_revealed  INTEGER NOT NULL DEFAULT 0,
  captions_used        INTEGER NOT NULL DEFAULT 0,
  meaning_check_attempted INTEGER NOT NULL DEFAULT 0,
  media_hash           TEXT NOT NULL,
  task_revision        TEXT, task_hash TEXT,
  transcript_revision  TEXT, annotation_revision TEXT, metadata_revision TEXT,
  PRIMARY KEY (pilot_subject_id, item_id, media_id)   -- 幂等键: 同一(主体,项,媒体)唯一
);
CREATE INDEX ix_v3_ledger_subject ON v3_exposure_ledger(pilot_subject_id);
```
> **主键即幂等保证**：`INSERT ... ON CONFLICT(pilot_subject_id,item_id,media_id) DO UPDATE` 保证并发双提交不会重复建暴露、不会把 holdout 重复分配给同一主体（规格 §13.2）。

### 2.3 `v3_evidence` —— 证据记录（规格 §5）
```sql
CREATE TABLE v3_evidence (
  id                 TEXT PRIMARY KEY,
  pilot_subject_id   TEXT NOT NULL,
  item_id            TEXT NOT NULL,
  media_id           TEXT NOT NULL,
  exposure_ref       TEXT NOT NULL,     -- 必须引用已发生的 ledger 行, 不可反推
  task_type          TEXT NOT NULL,     -- lightweight_meaning_check / probe
  evidence_valid     INTEGER NOT NULL,
  invalid_reason     TEXT,              -- interruption/audio_integrity/device/... /identity_unknown/unknown
  independent_attempt INTEGER NOT NULL,
  familiar_item      INTEGER NOT NULL,
  prior_exposure_count TEXT NOT NULL,   -- 数字或 'unknown'; 绝不默认 0
  transcript_exposed_before_attempt INTEGER NOT NULL,
  transfer_item      INTEGER NOT NULL DEFAULT 0,   -- V2.3 New Input 恒 0
  transfer_distance  TEXT NOT NULL DEFAULT 'none',  -- V2.3 只能 none
  audio_integrity    TEXT NOT NULL,
  interruption_detected INTEGER NOT NULL DEFAULT 0,
  content_revision   TEXT NOT NULL, content_hash TEXT NOT NULL,
  result_payload     TEXT,             -- 仅任务结果, 经 DTO 白名单过滤
  profile_eligible   INTEGER NOT NULL DEFAULT 0,   -- 恒 0
  created_at         TEXT NOT NULL
);
```

### 2.4 `v3_probe_records` —— probe observation（规格 §10）
```sql
CREATE TABLE v3_probe_records (
  id                 TEXT PRIMARY KEY,
  pilot_subject_id   TEXT NOT NULL,
  item_id            TEXT NOT NULL,
  sentence_or_span_id TEXT NOT NULL,
  candidate_reason   TEXT NOT NULL,     -- 只能来自预标注/学生自标/历史证据 (§10 Trigger)
  probe_type         TEXT NOT NULL,
  target_relation    TEXT,
  observation        TEXT NOT NULL,     -- *_observation 或 insufficient_evidence, 禁 diagnosis
  route              TEXT NOT NULL,     -- continue/adjust_difficulty/future_local_drill_candidate/insufficient_evidence
  audio_start_ms     INTEGER, audio_end_ms INTEGER,
  media_hash TEXT, task_hash TEXT, annotation_revision TEXT,
  created_at         TEXT NOT NULL
);
```

### 2.5 内容池状态 `v3_holdout_state` —— per-subject 退役（规格 §7.2）
```sql
CREATE TABLE v3_holdout_state (
  pilot_subject_id TEXT NOT NULL,
  item_id          TEXT NOT NULL,
  holdout_status   TEXT NOT NULL,   -- eligible/reserved/retired/not_applicable
  retired_at       TEXT,
  retired_reason   TEXT,            -- played/text_exposed/teacher_preview/cross_pool/drill/integrity_unknown
  PRIMARY KEY (pilot_subject_id, item_id)
);
```
> Global 退役（`global_holdout_retired`）走内容治理侧字段，存 candidate JSON 的 `_meta`，不在此表。

---

## 3. 内容池存储（candidate JSON，仿 V2.2 registry）

每 item 一条 candidate 记录，字段对齐规格 §7.1/§7.2：

```jsonc
{
  "item_id": "v3_input_0001",
  "pool_id": "input",                    // input / near_holdout / far_benchmark
  "media": { "media_id": "...", "media_hash": "...", "audio_file": "...", "duration_ms": 0 },
  "task_revision": "r1", "task_hash": "...",
  "transcript_revision": "r1", "annotation_revision": "r1", "metadata_revision": "r1",
  "difficulty_band": "medium",           // 运营标签, 非能力分
  "difficulty_attrs": { "duration": .., "speech_rate": .., "provenance": "machine_estimated|human_checked" },
  "lightweight_check": { "type": "main_idea", "prompt": "...", "options": [...], "answer_key": "..." },
  "probe_candidates": [ { "sentence_or_span_id": "...", "audio_start_ms": .., "audio_end_ms": ..,
                          "candidate_reason": "...", "possible_probe_type": "...", "target_relation": "..." } ],
  "transcript": "...(仅 reveal 后经 scaffold 端点返回, 不进 allocate/listen DTO)",
  "_meta": { "review_status": "machine_prechecked|generated_unverified",
             "source": "...", "license": "...", "global_holdout_retired": false }
}
```

`v2_3_content_registry` 启动加载三目录、按 `pool_id` 建索引；**INPUT 与 holdout 物理分目录**，加载即校验 `pool_id` 与目录一致，防串池（规格 §7 串池防线）。

---

## 4. 状态机实现映射（规格 §4）

| 概念状态 | 实现事实来源 | 关键不变式 |
|---|---|---|
| `unseen` | `v3_exposure_ledger` 无行 或 `exposure_started=0` | 未播放才可被 allocate |
| `listening` | 音频真实开始 → 立即 `exposure_started=1`、写 first/last_exposed_at、`exposure_count += 1` | **刷新/作答失败不得回退为 unseen**（§4） |
| `lightweight_check_optional` | 提交 check → 建 `v3_evidence`（task_type=lightweight_meaning_check） | 单题对错不写能力结论（§5.1） |
| `result` | 由 ledger + evidence 派生，不单独持久化 | 只出完成/轻量结果/self-report/难度建议（§9） |
| `probe_optional` | 触发校验通过 → `v3_probe_records` | 每句 ≤1 second listen + 1 probe（§10） |
| `transcript_scaffold` | reveal 端点 → `transcript_revealed=1` | 永久降级后续 `independent_attempt`（§11） |
| `completed_familiar` | `audio_completed=1` 或任何暴露 | 不代表理解/能力/计划完成（§4） |

---

## 5. Allocate New Input（规格 §9、§12）

`POST /api/listening/v2_3/input/allocate` → 服务端：
1. 读 `v3_exposure_ledger`（该 subject）得已暴露 media_id 集；
2. 从 INPUT_POOL 选一个该 subject `unseen`（无暴露行）且 revision/hash 可追溯的 item；
3. **找不到 → 诚实返回 `{status:"inventory_exhausted", replay_available:true}`**，绝不拿 familiar 冒充 new（§9、P1 风险）；
4. 返回的 listen DTO **不含 transcript、不含答案导向选项**（先听后查）。

分配是查询而非预留：不写 ledger，只有真实播放才写（避免"分配即暴露"的误记）。

---

## 6. Record exposure（原子）

`POST /api/listening/v2_3/input/{item_id}/exposure`，body 仅 `{event: "audio_started"|"audio_completed"|"meaningful", position_ms}`：
- `audio_started` → upsert ledger，`exposure_started=1`；
- 若该 item 属 holdout（防误配）→ 同事务写 `v3_holdout_state` 退役 `retired_reason=played`，且**不可逆**（§6：听 1 秒也退役）；
- `audio_completed` → `audio_completed=1`（不推断理解）；
- 事务保证 ledger + holdout 状态一起更新（§12 Start/record exposure 原子性）。

---

## 7. Lightweight meaning check / Transcript reveal / Probe

- **Check**：`POST .../check` 保存任务结果 + 有效性上下文，建 `v3_evidence`；只允许写 `meaning_check_correct/lightweight_check_passed` 或未通过；**禁**能力诊断（§5.1）。
- **Reveal**：`POST .../reveal-transcript` 原子置 `transcript_revealed=1`、`familiar_item=true`；若 holdout 则退役；返回 transcript 作 scaffold；**reveal 前/中的 attempt 不算 independent auditory evidence**（§11）。
- **Probe**：`POST .../probe`：
  1. 校验触发四条件同时成立（失败局部 + evidence 有效 + 可能改下一步 + 未触上限）（§10 Trigger）；
  2. candidate **只能取自** item 预标注 `probe_candidates` / 学生自标 span / 历史证据对齐（§10）——模型只排序不自由指定；
  3. 校验疲劳/时间/数量上限（可配置：short 1–3、medium 2–4、long 3–5 句，每句 ≤1 second listen + 1 probe）；
  4. 输出**只允许** observation + route 四值；**禁** diagnosis、答案位置泄露、多 probe 诊断树。

---

## 8. 身份模型（规格 §14 Pilot identity minimum，根治审计 K2/§12 owner 一致）

`v2_3_identity`：首次访问服务端签发 `pilot_subject_id`（随机),写 `v3_subjects`,通过 **HttpOnly cookie** 下发,跨刷新/跨 session 稳定。

- **所有写端点**从 cookie 解析 subject，**忽略 body 里任何 student/subject 字段**（消除 V2.2 "anonymous 可互写"根因）；
- session owner 与 ledger owner 必须一致，客户端无法伪造他人主体（§14、§13.8）；
- 完整登录/跨设备合并是 non-goal，但为正式发布前置。

---

## 9. 独立 release gate（规格 §14、审计 K6/K9 教训）

- **独立环境开关** `ALLOW_UNRELEASED_LISTENING_V2_3`，**不复用** `ALLOW_UNRELEASED_LISTENING_V2`（避免一个开关同放 V2.1/2.2/2.3，规格 §14、审计 L-14）；
- gate 在 **allocate/exposure/check/reveal/probe 全部端点**入口复查（对齐 K6 修复后的 V2.2 mid-session 全端点门控）；
- 所有 summary DTO 的 `student_release_allowed` **读 baseline，不写死**（K9 教训）；
- 全部 V2.3 记录 `profile_eligible=false`（§14）。

---

## 10. DTO 白名单 + 禁字段（补 K2 的值级盲区）

`v2_3_dto._assert_v3_clean(obj)`：
- **键级**：禁 `answer/correct_answer/transcript/attention/working_memory/round1_correct/diagnosis/skill/...`（复用并扩展 V2.2 禁词表）；
- **值级（新增，堵 K1 同类旁路）**：对 observation/route 等枚举字段做**白名单枚举校验**，禁止任何自由字符串携带逐项对错/答案位置；
- **禁并行数组**：结果 DTO 不得同时返回"逐项标识数组 + 同序对错数组"（K1 深修教训固化为设计规则）；
- **实现用显式 `raise`，非裸 `assert`**（避免 `python -O` 剥离，S0/审计裸 assert 教训）。

payload 入库前走字段白名单过滤（仿 K2 修复），只留声明字段。

---

## 11. 数据完整性规则落地对照（规格 §13）

| §13 规则 | 落地点 |
|---|---|
| 1 可追溯不可前端声称 | 所有 revision/hash 服务端从 registry 取，body 不接受 |
| 2 幂等/可恢复/并发不重复分配 | ledger 复合主键 + ON CONFLICT upsert；holdout 退役同事务 |
| 3 历史 attempt 绑定当时版本 | `v3_evidence` 存 content_revision/hash 快照（不指针） |
| 4 invalid ≠ 无暴露 | evidence_valid=false 仍保留 ledger 暴露 |
| 5 unknown 不静默转 unseen | ledger 无行=unseen；unknown 显式存 |
| 6 revision 绑定音频+文本+支持+难度+标注 | ledger/evidence 五 revision 字段 |
| 7 payload 禁推断性字段 | §10 白名单 |
| 8 identity 与 ownership 一致 | §8 cookie owner |
| 9 独立于冻结 V2.2 | §0 边界 + 独立表/路由/gate |

---

## 12. 验收测试矩阵（规格 §15 + 针对性异常）

- `test_v2_3_input`：allocate 只给 unseen；库存耗尽诚实返回；listen DTO 无 transcript/答案；exposure 后不再 unseen；audio_completed 不写能力结论。
- `test_v2_3_ledger_integrity`：并发双 exposure 不重复建行（幂等）；holdout 播放即退役且不可逆；revision drift 后历史 evidence 仍绑旧 hash；reveal 后 independent_attempt 降级。
- `test_v2_3_probe`：触发四条件缺一即拒；candidate 越出预标注/自标/历史范围即拒；上限生效；输出只在四 route 内；无答案位置泄露。
- `test_v2_3_gate_identity`：gate 关闭时全端点 403；body 伪造他人 subject 被忽略（用 cookie owner）；越权写他人 ledger 被拒；独立 gate 不受 V2 开关影响。
- 冻结回归：跑 V2.1(14)/V2.2(24) 全绿，证明零行为变更。
- 串池：near/far item 不出现在 allocate/推荐；误配即退役写 reason。

---

## 13. 首轮封闭 fixture（规格 §16）

8–12 个 INPUT items，覆盖 2–3 个 `difficulty_band`、不同 speaker/topic/duration；含若干 pure exposure、若干 lightweight-check、少量带 `probe_candidates`。Near/Far 各放极少量**只验 schema/ledger/串池逻辑**，不开放学生 transfer 流程。

**内容源（S1 待确认前的设计默认）**：先用**已核验的会话材料片段 + 明确标注 `review_status` 的内部 TTS** 跑通封闭 pilot；CET 真题**不作日常来源**（版权+熟悉度，规格 §16 来源表）。正式来源待 S1-Q2 确认。

---

## 14. 仍需产品确认（S1，编码门禁前必答）

1. **内容来源（Q2，最硬）**：INPUT_POOL 可授权/可审核的音频源是什么？设计已给"已验证片段+标注 TTS"作 pilot 默认,不阻塞设计,但正式来源需你定。
2. **难度标注责任人（Q7）**：easy/medium/hard 谁人工标、审核标准、inter-rater 策略。
3. **编码放行时点（§18/§19）**：设计评审通过即放行,还是另需单独确认。

其余 §18 问题已在设计内取默认：独立 gate=YES、身份=服务端 cookie `pilot_subject_id`、仅 CET-6、transcript≡caption 均污染独立性、probe 上限走全局配置、首轮 8–12 封闭 fixture。

---

## 15. 编码授权声明

本文是 **engineering design**，对应规格 §19 的 `READY_FOR_V2_3_ENGINEERING_DESIGN`。
**尚未授权编码**。开工前置：S1 三处确认到位 + 本设计评审通过 → 另建 tag/commit + 独立验收文档（当前仓库无 tag/remote）。
