# CET-4 / CET-6 听力项目接管审计（V2.2 冻结基线）

审计日期：2026-08-30  
项目根目录：`D:\kimi-workspace\english-ai`  
审计性质：只读接管审计；未修改源码、数据、配置，未修 bug，未开始 V2.3。本文是本轮唯一新增文件。

## 结论摘要

- 指定 Git baseline `fdc9c23` 存在，完整 SHA 为 `fdc9c2311024ab4fafd8314515831218f4ef42b1`，并且就是 `main` 当前 `HEAD`。
- 审计开始时工作树干净；仓库无 Git tag、无可见 remote、`main` 无可见 upstream。
- V2.0b 数据恢复和冻结清单完整：两套 CET-6、每套 25 题 / 7 Units，baseline 中 6 个 artifact 的 SHA-256 与当前文件全部一致。
- V2.0b 仍是 `machine_prechecked`，不是 `teacher_verified`；机器预检 235 个字段中 229 个 `consistent`、6 个 transcript segment 为 `check`。
- V2.1 Exam Reconstruction 已完成并通过 13 项测试；卷面 DTO 保持 `audio_only`、题组同时显示、无题干/答案/transcript/中文/时间题号映射泄漏。
- V2.2 Continuous Practice 已达到 `ENGINEERING_PILOT_ACCEPTED`，不是 `teacher_verified` 或 `student_released`；当前内容仍为 `generated_unverified`。
- 当前事实门控为 `student_release_allowed=false`；审计时进程环境和 `backend/.env` 均未设置 `ALLOW_UNRELEASED_LISTENING_V2`，所以 V2.1/V2.2 学生入口默认关闭。
- V2.2 明确 `profile_eligible=false`，当前 `cp_*` 数据不进入 Profile；实际 dev DB 中三张 `cp_*` 表均为 0 行。
- 全量 backend 回归已在当前 HEAD 实跑：71/71 通过；前端类型检查通过，生产构建在项目外临时目录完成并通过。
- V2.3 尚未编码：没有 Sentence Lab 路由、service、表或学生端页面，只有 V2.2 结果页中的后续阶段文案。
- 发现若干“文档承诺强于实际代码”的冻结差异，重点包括：V2.2 最终状态 API 会返回逐题 `round1_correct`；客户端事件 payload 没有按文档拒绝敏感/诊断词；历史内容 pin 未保存完整题面快照；V2.1 response 没有 revision/hash 绑定。详见 K、L。

---

## A. 当前项目架构

### A1. 总体结构

| 层 | 技术与入口 | 当前职责 |
|---|---|---|
| Frontend | Vue 3 + TypeScript + Vue Router + Vite；`frontend/src` | 写作页、听力首页、legacy 考试/复盘/训练、V2.1 Exam、V2.2 Continuous Practice、Profile、Expression Bridge、Corpus、教师页 |
| Backend | FastAPI；`backend/main.py` | 挂载 `/api/listening` 路由，并保留 `/api/essay` 写作批改 |
| Listening API | `backend/listening/router.py` | 67 个 listening endpoints；V2.1/V2.2 与 legacy/Phase 3–7 并存 |
| 内容数据 | JSON + 音频文件 | legacy `data/exams`、V2.0b `data/v2_full`、V2.2 `data/v2_practice`、表达/真实语料数据 |
| 学生行为数据 | SQLite `backend/listening/data/listening.db` | attempts、行为事件、诊断、训练、表达迁移、corpus、V2.2 cp 会话 |
| 数据访问 | `repository.py` | JSON registry、SQLite schema/轻量迁移、持久化方法 |
| 业务服务 | `service.py`、`review_service.py`、`training_service.py`、`profile_service.py`、`expression_service.py`、`corpus_service.py` | legacy 与 Phase 3–7 能力；V2.2 未调用 Profile 路径 |
| V2 专用服务 | `v2_exam_service.py`、`v2_practice_service.py` | 白名单 DTO、共享 release gate、V2.1 判分、V2.2 状态机/判分/观察事件 |

### A2. 数据轨道

当前有三条明确分离的数据/产品轨道：

1. **Legacy 轨道**：`backend/listening/data/exams/*.json` → `ExamRepository` → `/api/listening/exams*` → `ListeningExamView.vue` 及复盘/训练/Profile。
2. **V2.1 轨道**：`backend/listening/data/v2_full/*.candidate.json` → `V2ExamRegistry` → `/api/listening/v2/exams*` → `ListeningExamV2View.vue`。V2 exam id 在原 id 后加 `_v2`，避免与 legacy JSON 混用。
3. **V2.2 轨道**：`backend/listening/data/v2_practice/cp_items.candidate.json` → `V2PracticeRegistry` → `/api/listening/v2/practice*` → `ListeningPracticeV2View.vue`，状态写入 `cp_sessions/cp_responses/cp_events`。

### A3. 启动与部署特征

- `frontend/vite.config.ts` 在开发环境把 `/api` 代理到 `http://localhost:8000`。
- `backend/main.py` 在导入时强制要求 `DEEPSEEK_API_KEY`，即使只想运行 listening API，也会受写作模块密钥约束；这是现有单体入口的运维耦合。
- `listening.db`、`listening_dev.db`、`dist`、`node_modules`、`venv` 等均被 `.gitignore` 排除；数据库现状不属于 Git baseline。

---

## B. 当前 Git 状态与 baseline

### B1. 当前状态

- 分支：`main`
- 审计前状态：clean（`git status --short --branch` 仅输出 `## main`）
- HEAD：`fdc9c2311024ab4fafd8314515831218f4ef42b1`
- 短 SHA：`fdc9c23`
- 提交时间：2026-08-29 02:55:57 +0800
- 提交标题：`V2.2 Continuous Practice Pilot: ENGINEERING_PILOT_ACCEPTED 封版`
- 当前无 tag；未看到 remote 或 upstream 配置。

### B2. baseline 结论

`fdc9c23` 不只是存在，而是当前 HEAD 本身，因此用户给定的冻结 baseline 与仓库当前状态一致。该提交同时加入/冻结 V2.0b 数据、V2.1、V2.2、两套测试、设计/验收文档及截图；Git 历史中没有单独的 V2.0/V2.1 提交节点。

### B3. V2.0b artifact 完整性

`V2_0B_BASELINE.json` 列出的 6 个 artifact 已逐一重算 SHA-256，全部与 baseline 匹配：

- 两套 `v2_full/*.candidate.json`
- `machine_precheck_full.json`
- `payload_assert_report.json`
- 两套 `payload_preview/*.exam_payload.json`

因此“当前文件仍等于 V2.0b 冻结内容”可确认。注意：运行时 service 不会自动重算/拒绝 hash 不匹配；冻结目前靠 Git + baseline 清单，而非启动时强制校验。

---

## C. V2.0 / V2.1 / V2.2 各自完成了什么

### C1. V2.0 / V2.0b：数据恢复与语义冻结

已完成：

- 恢复两套 2026 年 6 月 CET-6 听力数据：每套 25 题、7 Units。
- Set1 共 69 个 transcript segments；Set2 共 74 个。
- 每套 100 个英文选项；payload assertion 报告为 25 题、100 选项、0 answer conflicts。
- 顶层与全部 50 题为 `machine_prechecked`；两套各有 5 个 transcript 为 `machine_prechecked`、2 个为 `machine_prechecked_with_warnings`。
- `machine_precheck_full.json`：235 个字段中 229 个 `consistent`，6 个 transcript segment 仍为 `check`。
- 统一纠正了状态语义：机器核验不得叫 `teacher_verified`。
- V2.0 不提供题目级/句子级时间戳，`timing_status=unverified_disabled`。
- 创建 `V2_0B_BASELINE.json`，冻结 artifact hash 和 release gate。

未完成：

- 真人教师逐字核对英文选项、题干、transcript。
- 6 个 `check` transcript segment 的真人收口。
- 句子级音频时间戳。
- 学生发布。

### C2. V2.1：Exam Reconstruction

已完成：

- 新建 `v2_exam_service.py`，从 V2.0b candidate 文件组装学生端白名单 DTO。
- 学生卷面仅包含：题号、英文 A/B/C/D 选项、Unit 元信息；不返回题干、答案、中文、transcript、解析、evidence、provenance、revision/hash 或时间定位。
- 两套卷面均为 7 Units / 25 题，题组大小固定为 `[4,4,3,4,3,3,4]`。
- 一个 Unit 的 3–4 题由 `UnitQuestionGroup.vue` 同时显示。
- 整套音频播放；DTO 不含 audio time → question 映射，前端仅把当前浏览 Unit 作为行为上下文，不声称“当前音频题号”。
- 支持 exam/practice 两种 attempt mode、答案自动保存、刷新恢复、Unit 停留和音频/改答事件记录、统一提交。
- 提交只返回总分和题数，不返回逐题答案明细。
- V2.1 入口由共享 release gate 控制。

补充说明：V2.1 页面显式给 `AudioPlayer` 传 `controls="full"`，因此即使在 `exam_mode` 也允许 pause/seek/replay，并记录事实事件。当前产品原则没有要求 Exam Mode 禁止这些控制，但这与 legacy `exam_mode` 默认锁 seek/replay 的行为不同。

### C3. V2.2：Continuous Practice Engineering Pilot

已完成：

- 两个材料：Set1 Conversation 1、Set2 Conversation 1；每段 3 道 check，共 6 道。
- check 冻结 revisions：`1,3,2` 与 `2,1,1`；状态全部 `generated_unverified`。
- 七阶段状态机：`intro → option_preview → first_pass → check_round_1 → blind_full_replay → check_round_2 → result_final`。
- First Pass 原速 1.0、无 pause/seek/replay UI；4.5 秒位置心跳，服务端以 9 秒最大间隔、覆盖率、end 事件综合判定有效性。
- 中断 pass 无效、允许完整重开；有效 pass 后不能重新获得 First Pass。
- Round 1 响应只返回数量；有错时进入 blind full replay，不显示答案、transcript、解析或答案区间。
- Round 2 只重出 Round 1 错题，服务端固定该 session 的随机选项顺序；成功语义为 `recovered_after_full_replay`。
- 结果 UI 只显示“首次抓住 X/Y；完整重听后恢复 A/B”，并声明观察不构成能力评定、不进入 Profile。
- session 创建时 pin check revision/hash/answer key；`cp_responses` 冗余保存 revision/hash。
- 新增 `cp_sessions`、`cp_responses`、`cp_events` 三表和 9 个 API endpoints。
- 补充验收修正了 heartbeat/end 竞态，并给 `RangePlayer` 增加 playbackRate 1.0 锁定。
- 文档结论：`ENGINEERING_PILOT_ACCEPTED`；当前不是 teacher verified/student released。

当前实现有一个已写入设计与测试的例外：Round 1 若 3/3 全对，会直接进入 `result_final`，跳过 blind replay 和 Round 2。

---

## D. 当前学生端路由

### D1. 当前可注册的学生路由

| 路由 | 页面/用途 | 状态 |
|---|---|---|
| `/` | Home | 当前入口 |
| `/writing` | 写作批改 | legacy/并行产品 |
| `/listening` | 听力首页 | 当前只展示 gate 放行的 V2.1/V2.2 卡片 |
| `/listening/v2/exams/:examId` | V2.1 Exam | 当前 release gate 默认关闭 |
| `/listening/v2/practice/:materialId` | V2.2 Continuous Practice | 当前 release gate 默认关闭 |
| `/listening/exams/:examId` | legacy 考试/练习页 | 路由保留，但首页隐藏入口 |
| `/listening/review/:attemptId` | legacy 逐题复盘 | 路由保留 |
| `/listening/mistakes` | legacy 错题本 | 路由保留 |
| `/listening/profile` | Evidence Profile | 路由保留；V2.2 不写入 |
| `/listening/corpus` | 已批准真实语料 clips | 路由保留 |
| `/listening/expressions` | Expression Bridge 列表 | 路由保留 |
| `/listening/expressions/:expressionId` | Expression 训练 | 路由保留 |

### D2. 教师路由（非学生端）

- `/listening/teacher/expressions`
- `/listening/teacher/expressions/:expressionId`
- `/listening/teacher/corpus`
- `/listening/teacher/corpus/:assetId`

教师 API 需要服务端 `TEACHER_TOKEN`；前端 token 存于 sessionStorage。

### D3. Sentence Lab 路由

不存在。当前仅 V2.2 result_final 文案提到“后续阶段（Sentence Lab）开放”，没有可点击链接。

---

## E. 当前 backend API

所有 listening endpoints 统一前缀：`/api/listening`。当前 `router.py` 共 67 个 endpoints。

### E1. V2.1 Exam（3 个专用 endpoints + 通用 attempt endpoints）

- `GET /v2/exams`
- `GET /v2/exams/{exam_id}/paper`
- `GET /v2/exams/{exam_id}/audio`
- `POST /attempts`
- `GET /attempts/in-progress`
- `PUT /attempts/{attempt_id}/answers/{question_id}`
- `POST /attempts/{attempt_id}/events`
- `GET /attempts/{attempt_id}/events`
- `POST /attempts/{attempt_id}/submit`

### E2. V2.2 Continuous Practice（9 个）

- `GET /v2/practice/materials`
- `GET /v2/practice/materials/{material_id}`
- `GET /v2/practice/materials/{material_id}/audio`
- `POST /v2/practice/sessions`
- `GET /v2/practice/sessions/find`
- `GET /v2/practice/sessions/{session_id}`
- `POST /v2/practice/sessions/{session_id}/events`
- `POST /v2/practice/sessions/{session_id}/round1`
- `POST /v2/practice/sessions/{session_id}/round2`

### E3. Legacy 考试、行为、复盘、训练与 Profile

- `GET /exams`
- `GET /exams/{exam_id}`
- `GET /exams/{exam_id}/questions`
- `GET /audio/{exam_id}`
- `GET /tag-dictionary`
- `GET /self-diagnosis-options`
- `GET /attempts/{attempt_id}/review`
- `POST /attempts/{attempt_id}/questions/{question_id}/hint`
- `POST /attempts/{attempt_id}/questions/{question_id}/retry`
- `GET /attempts/{attempt_id}/questions/{question_id}/candidates`
- `POST /diagnoses`
- `POST /training-results`
- `GET /mistakes`
- `GET /attempts/{attempt_id}/questions/{question_id}/training-plan`
- `GET /attempts/{attempt_id}/questions/{question_id}/training/{training_type}`
- `POST /attempts/{attempt_id}/questions/{question_id}/training/{training_type}/check`
- `POST /attempts/{attempt_id}/questions/{question_id}/blind-retest`
- `GET /profile`
- `GET /profile/causes`
- `GET /profile/skills`

### E4. Expression Bridge

- `GET /expressions`
- `GET /expressions/{expression_id}`
- `GET /expressions/scenarios/{scenario_id}/audio`
- `GET /expressions/scenarios/{scenario_id}/audio-meta`
- `POST /expressions/scenarios/{scenario_id}/reveal-early`
- `POST /expressions/scenarios/{scenario_id}/submit`
- `POST /expression-attempts/{attempt_id}/replayed`

### E5. 教师 Expression / Corpus 与学生 Corpus

- 教师 Expression：list/detail/update expression、update scenario、review expression/scenario、regenerate audio（7 个）。
- 教师 Corpus：upload/list/detail/audio/update/review asset，run ASR/segmentation/matching，update/review/create clip，review/add matches（13 个）。
- 学生 Corpus：`GET /corpus/clips`、`GET /corpus/clips/{clip_id}/audio`。

另有非 listening API：`POST /api/essay`。

---

## F. 当前数据库表

运行时数据库：`backend/listening/data/listening.db`，SQLite，当前 364,544 bytes；被 Git ignore，不属于冻结提交。审计以只读方式读取实际 schema 和行数。

| 表 | 当前行数 | 用途 |
|---|---:|---|
| `attempts` | 4 | legacy/V2.1 作答会话、模式、提交时间、总分 |
| `attempt_answers` | 52 | 每题首答/终答/改答/停留/首答对错/重听/提示计数 |
| `behavior_events` | 185 | attempt 级客观行为事件流 |
| `diagnoses` | 1 | 学生自判、AI tags、最终 tags、诊断 revision |
| `training_results` | 1 | 训练输入、结果、score、错误明细、provenance、诊断 revision 快照 |
| `expression_attempts` | 0 | Expression Bridge 跨语境作答及 evidence strength |
| `corpus_assets` | 2 | 音频来源、许可、授权链、ASR、审核和 revision |
| `corpus_clips` | 45 | clip 区间、transcript、教学标签、匹配、content/metadata revision |
| `cp_sessions` | 0 | V2.2 session、stage、manifest、preview、pass/replay、round2 顺序 |
| `cp_responses` | 0 | V2.2 Round 1/2 response、content revision/hash、recovery 标记 |
| `cp_events` | 0 | V2.2 事件流和 session summary |

补充：`backend/listening/data/listening_dev.db` 是 0 byte 的 ignored legacy 文件；实际 repository 使用的是 `listening.db`。

当前 schema 没有声明外键约束；`cp_responses` 也没有 `(session_id, check_id, round)` 唯一约束，幂等主要依赖 service 层先查后写。

---

## G. 当前测试覆盖

### G1. 本轮实跑结果

- Backend：`python -B -m unittest discover -s tests -v` → **71/71 OK**，耗时 224.624s。
- Frontend：`vue-tsc --noEmit` → 通过。
- Frontend：Vite production build → 通过，113 modules transformed；输出放在项目外审计临时目录，未覆盖项目 `dist`。

### G2. V2.1：13 项

覆盖：

- 白名单 DTO / forbidden key 递归断言
- 7 Units、25 题、题组大小和 A/B/C/D 完整性
- 中文泄漏
- question stem 泄漏
- correct answer 泄漏
- 无 audio time → question cue
- create/save/refresh/submit 完整状态流
- V2 列表和音频
- legacy exam 隔离
- release gate 关闭、preview override、baseline source

### G3. V2.2：18 项

覆盖：

- bundle 白名单、无答案/hash/transcript/provenance 泄漏、shape/boundary
- 9 个 endpoint 的 release gate 和 mid-session gate 关闭
- playbackRate 源码锁定断言
- first-pass 无心跳拒绝、end/heartbeat 竞态、远端断档、中断重开
- Round 1 数量响应和 blind state
- replay 门禁、完整 recovery、summary、Profile 隔离
- 3/3 全对直通
- event type 白名单
- response revision/hash pin 和模拟 content drift

### G4. 当前测试缺口

- 未断言 `result_final` session state 不得返回逐题 `round1_correct`；实际会返回。
- 未测试白名单 event type 内 payload 的敏感字段/诊断词拒绝；实际不会拒绝。
- 未测试 session owner 与请求 `student_id` 一致性；实际没有绑定校验。
- 未测试 V2.1 已有 attempt 在 gate 关闭后是否仍可保存/提交；实际通用 endpoints 不重查 gate。
- 未测试 V2.1 response 对 content revision/hash 的历史绑定；当前没有该绑定。
- content drift 测试只改 hash/revision/answer，不改题干/选项；因此未覆盖旧 session 题面恢复。
- playbackRate 测试主要是源码字符串断言；浏览器实测证据来自验收文档，本轮未重新启动浏览器。
- 弱网、并发双提交、session 越权、长期 SQLite 并发和移动端真实设备没有自动化覆盖。

---

## H. 当前 release/profile gate

### H1. Release gate

唯一数据事实来源是：`backend/listening/data/v2_full/V2_0B_BASELINE.json`。

当前值：

```text
student_release_allowed = false
ALLOW_UNRELEASED_LISTENING_V2 process env = unset
ALLOW_UNRELEASED_LISTENING_V2 backend/.env = unset
effective gate = closed
```

关闭时：

- V2.1/V2.2 列表返回空数组，首页不渲染卡片。
- V2.1 paper/audio/create-attempt 返回 403。
- V2.2 bundle/audio/create/find/state/events/round1/round2 返回 403。
- 只有显式设置 `ALLOW_UNRELEASED_LISTENING_V2=true` 才能进行开发预览。

### H2. Profile gate

- V2.2 `session_state` 和 `cp_session_summary` 均写死 `profile_eligible=false`。
- V2.2 service 不调用 `profile_service`、mastery、recommendation 或 legacy training 写路径。
- `cp_*` 三表与 Profile 使用的 attempts/diagnoses/training_results 分离。
- 当前结论：V2.2 evidence 不会进入正式 Profile。

### H3. Teacher verification

- V2.0b：`machine_prechecked`，不是 `teacher_verified`。
- V2.2 checks：`generated_unverified`，不是 `teacher_verified`。
- 当前没有任何事实支持学生发布或正式 Profile 使用。

---

## I. 可直接或有条件复用到 V2.3 的代码

原则：V2.2 已冻结，建议新建 V2.3 模块/路由/表来复用模式，不应把 Sentence Lab 继续塞进 `v2_practice_service.py` 的主流程。

| 可复用资产 | 复用方式 | 限制 |
|---|---|---|
| `v2_exam_service.student_release_allowed/gate_allows` | 复用统一发布闸门模式 | V2.3 最好有独立内容 gate，避免一次开关误放行所有 V2 内容 |
| `assert_no_forbidden` / 白名单 DTO 思路 | 直接复用安全组装原则与递归断言 | V2.3 需要按阶段定义不同字段白名单，transcript 不能全局一刀切 |
| `V2PracticeRegistry` | 复用文件签名 + reload registry 模式 | 不要复用当前 cp schema 作为 Sentence Lab 内容 schema |
| `derive_stage` 的事件推导模式 | 复用“服务端权威状态、刷新恢复”模式 | 新状态机应独立，避免 V2.2 主流程无限加长 |
| `cp_sessions/cp_responses/cp_events` 的分层思路 | 复用 session/response/event 分离、revision/hash 冗余原则 | V2.3 应建新表；必须补完整题面/句面版本快照或可解析版本仓库 |
| `RangePlayer.vue` | 可复用区间起止、进度和事件发射核心 | 当前组件专为不可暂停/不可拖动/不可重播而写；Sentence Lab 的逐句重放控制需要新 mode 或新组件，不能直接沿用全部交互 |
| `ListeningPracticeV2View.vue` | 可复用 bundle → find/create session → refresh state 的页面骨架 | 不应直接追加 Sentence Lab stages；建议新 route/view |
| `listeningApi.ts` 的 `request<T>` | 可直接复用统一 fetch/error 处理 | V2.2 types 目前放在 API 文件而不是统一 types 文件，可在 V2.3 前统一约定但不必改冻结代码 |
| `training_service.py` + Dictation/Chunk/Paraphrase 组件 | 可作为 Local Drill 的能力积木 | 只能在合适阶段揭示文本；不要把 legacy “错题→定位句”路径直接接到 V2.2 错题 |
| V2.0b transcript segments 的 `segment_id/revision/content_hash/speaker/text` | 可作为 Sentence Lab 候选语料输入 | 不是学生可用成品：存在 warning/check，且没有句子级人工时间戳、未 teacher verified |
| corpus 的 revision 拆分、许可 gate 和教师审核模式 | 可复用治理思路 | corpus clip slicing 当前面向已批准真实语料，不等于 CET mp3/m4a 的 Sentence Lab 切句实现 |

---

## J. 仍然存在的旧 legacy 代码

### J1. 数据与页面

- `backend/listening/data/exams/cet6_202606_set1.json`
- `backend/listening/data/exams/cet6_202606_set2.json`
- `frontend/src/views/listening/ListeningExamView.vue`
- `frontend/src/components/listening/QuestionCard.vue`
- `/listening/exams/:examId` 路由

听力首页已隐藏 legacy exam 卡片，但路由、API、数据和判分仍可用。

### J2. Phase 3–7 功能

- 逐题复盘、五级提示、retry、candidate diagnosis
- Dictation / Chunk / Paraphrase / Distractor 对症训练
- blind retest、错题本、Profile
- Expression Bridge、教师 Expression 审核
- Corpus ingestion、许可/授权链、ASR、切分、匹配、学生 clip

这些不是 V2.2 的一部分，但仍与 V2 共用 `router.py`、`repository.py` 和同一 SQLite。

### J3. 兼容字段与遗留资产

- `TrainingResultIn` 仍保留 `pre_result/post_result` 兼容字段。
- `models.py` 仍有 legacy `question_enter/question_leave` 和含 transcript/题干/答案的通用模型。
- `AudioPlayer.vue` 同时兼容 legacy 默认权限和 V2.1 显式 `controls`。
- `listening_dev.db` 为 0 byte 遗留文件。
- `_audit_scripts/`、`_incoming_source/`、V2 pilot/full payload preview 和截图均保留在仓库。
- `frontend/dist`、smoke log 文件存在但被 ignore，不属于 Git baseline。

---

## K. 与交接描述或文档不一致的地方

以下均为审计发现；本轮没有修复。

### K1. 高优先级：V2.2 最终状态 API 泄露逐题 Round 1 对错

`v2_practice_service._final_result()` 返回：

```text
result.checks[].check_id
result.checks[].dimension
result.checks[].round1_correct
```

`session_state()` 在 `result_final` 阶段把该对象完整下发。前端 TypeScript interface 没声明 `checks`，页面也没显示，但网络响应实际可见。这与“任何端点只返回数量 / 不揭示哪题错”的验收描述不一致。现有测试没有覆盖最终 state 的该字段。

### K2. 高优先级：V2.2 event payload 没有执行文档所称的敏感词拒绝

`record_events()` 只过滤 `event_type`，没有对白名单事件的 payload 调用 `_assert_cp_clean`，也没有 payload field whitelist。实测在临时库中可持久化 `attention`、`transcript`、`correct_answer` 等任意字段。文档“payload 禁词一律拒绝、事件中不含答案/transcript”的承诺不成立。

同一接口还接受请求体中的任意 `student_id`，没有校验它等于 session owner；临时验证可把其他 student id 写进该 session 的事件。

### K3. 高优先级：历史版本绑定并未完整满足“内容可还原”

- V2.2 pin 了 revision/hash/answer key，但没有 pin question、options、dimension 的完整快照。
- drift 后 Round 2 的题干/选项来自当前 material，判分却使用旧 answer key；旧 session 不能完整还原当时题面。
- `_content_drifted()` 只遍历当前 checks，不能发现“旧 manifest 有题但当前题被删除”的情况。
- V2.1 `attempt_answers` 完全不保存 candidate question revision/hash，提交判分读取当前 candidate；若 V2.0b 文件后续变化，历史 response 无法绑定原版本。
- legacy response 同样没有普遍的 content revision/hash 绑定。

因此“content revision + content_hash 必须绑定历史 response”目前只在 V2.2 response 行上部分实现，尚未成为全系统保证。

### K4. Set2 material_end 文档存在 40ms 冲突

- Independent Review Pack ADDENDUM 2 最终候选：`249000ms`，并写明取代 `248960ms` 建议。
- 当前 `cp_items.candidate.json`、service bundle、tests、主验收浏览器记录：`248960ms`。
- 运行时事实是 **248960ms**。

差异只有 40ms，且都位于机器确认的静音窗口，但冻结 source of truth 不唯一；V2.3 句子级时间轴不能继承这种歧义。

### K5. Round 1 后并非总会 blind full replay

交接原则写“round1 后 blind full replay”；当前代码和测试对 3/3 全对设置了直通 `result_final`。该例外在 V2.2 设计/验收中有记录，但若产品原则要求无条件 replay，则当前实现不一致。

### K6. V2.1 gate 没有覆盖已有 attempt 的所有后续 endpoints

V2.1 paper/audio/create-attempt 会检查 gate；但通用 in-progress、answer、events、submit endpoints 对已有 V2 attempt 不重新检查 gate。与 V2.2 的 mid-session 全端点 gate 相比，V2.1 仍可在 gate 关闭后继续写入/提交一个预先创建的 attempt。

### K7. 文档内部存在历史口径

- `V2.2_Pilot_Acceptance_Report.md` 写 gate 关闭后“全部端点 404”，实际是列表空数组、其余 403；Supplement 已以 403/空列表纠正。
- 主报告记录 65 tests / V2.2 12 项，Supplement 与当前实跑是 71 tests / V2.2 18 项；应以 Supplement 为准。
- `V2.2_Pilot_Checks_内容稿.md` 仍以早期 rev1、Set2 起点约 138.3s、“待编码”为口径；后续 Independent Review Pack ADDENDUM 和当前 JSON 已取代它。
- `docs/` 没有单独命名的 V2.0/V2.1 设计或验收 Markdown；V2.0b 事实主要在 baseline JSON，V2.1 事实主要在代码、测试、截图和 V2.2 验收中的回归章节。

### K8. machine-only 数据仍残留 `manual_*` provenance 命名

baseline 明确无人类 teacher verification，但 candidate provenance 中仍出现 `manual_review` / `manual_clean`，machine report 也有 `manual_clean` 布尔字段。顶层状态没有冒充 `teacher_verified`，但命名容易被后续开发误读为真人审核，应继续以 `_meta.review_status=machine_prechecked` 为唯一解释。

### K9. release metadata 是硬编码 false

V2.1/V2.2 summary DTO 中的 `student_release_allowed` 目前写死为 `false`，而 gate 读取 baseline。当前 baseline 本来就是 false，所以没有运行时冲突；未来若只把 baseline 改为 true，列表会可见但 metadata 仍显示 false。

### K10. “CET-4/CET-6 项目”当前实际只有 CET-6 听力数据

当前 legacy、V2.0b、V2.1、V2.2 的正式听力材料均为 CET-6；未发现 CET-4 listening candidate、路由卡片或测试 fixture。V2.3 是否同时覆盖 CET-4 需要明确。

---

## L. V2.3 开始前需要确认的风险点

建议在任何编码前由产品/教学/数据负责人确认以下决策：

1. **Sentence Lab 范围**：先做 V2.2 两段 Conversation 1，还是两套 CET-6 全文；是否包含 CET-4（当前无 CET-4 数据）。
2. **V2.2 冻结策略**：V2.3 是否必须新建独立 route/service/tables，并禁止改动 `v2_practice_service.py`、`ListeningPracticeV2View.vue` 和 `cp_*` schema。建议答案是“是”。
3. **进入 Sentence Lab 的入口**：从 V2.2 result_final 进入、从独立材料页进入，还是两者都有；不能把主流程无限拉长。
4. **文本揭示门槛**：先整句盲听/定位/复述/听写到什么条件后才允许 transcript；失败时允许给哪一级提示，什么内容绝不能直接给答案位置。
5. **Local Drill 边界**：哪些失败升级到 Local Drill；Sentence Lab 主流程最多几步；legacy 五级提示/听写/分块哪些可复用，哪些需要禁止。
6. **音频切句标准**：sentence start/end 的人工验收流程、padding、speaker turn 与 sentence 的关系、口播排除、revision/hash 规则。当前 V2.0b 没有句子级 timestamp。
7. **内容质量 gate**：哪些 transcript/check 必须先 teacher verified；6 个 machine `check` segment 和 4 个 warning units 如何处理；机器/模型绝不能自行升级状态。
8. **版本快照方案**：response 必须绑定 `sentence_id + revision + content_hash`；还需决定保存完整 sentence/options/timing snapshot，还是保存可长期解析的 immutable version artifact。仅 pin hash 不足以还原。
9. **Profile policy**：V2.3 初期是否继续 `profile_eligible=false`；若产生 evidence，只允许哪些 observation，何时经过多次/跨材料证据才能进入 Profile。
10. **全对 replay 规则**：确认 V2.2 的 3/3 直通是否符合最终产品原则，避免 V2.3 依赖一个未确认的上游分支。
11. **冻结差异处置**：K1–K3 是否作为 V2.3 前置 hardening；若不改冻结 V2.2，V2.3 至少不得信任其 final API 的逐题隐私、任意 event payload 或不完整 snapshot。
12. **身份与会话**：V2.2 页面固定 `student_id='anonymous'`，API 也无 session owner 校验；正式学生环境需要何种身份/授权模型。
13. **重复训练策略**：V2.2 `find_latest_cp_session` 总是恢复最近 session，完成后 UI 没有“新建一次训练”；V2.3 是否允许多次独立 session、如何区分复习与新证据。
14. **Gate 粒度**：V2.3 是否独立开关；避免 `ALLOW_UNRELEASED_LISTENING_V2` 同时放行 V2.1/V2.2/V2.3。
15. **数据库约束与并发**：是否在 V2.3 新表增加 FK、唯一约束、幂等 key/transaction；当前 service 层先查后写不足以覆盖并发双提交。
16. **来源与许可**：现有 CET 数据来自市面出版真题整理资料，不是官方数字源；学生发布前需确认内容使用权与来源标注策略。
17. **后端启动解耦**：是否把 listening API 与写作 `DEEPSEEK_API_KEY` 的强制依赖解耦，避免 Sentence Lab 无模型功能也无法启动。
18. **验收基线**：V2.3 开工前建议另建明确 tag/commit 和单独设计/验收文档；当前只有 `main@fdc9c23`，没有 tag、remote/upstream，也没有独立 V2.0/V2.1 文档包。

---

## 最终接管判断

用户给出的总体状态判断基本成立：

- V2.0b 数据恢复完成但未 teacher verified：**成立**。
- V2.1 Exam Reconstruction 完成：**成立**。
- V2.2 Engineering Pilot 已通过：**成立**。
- V2.2 状态为 `ENGINEERING_PILOT_ACCEPTED`：**成立**。
- `student_release_allowed=false`：**成立，且当前 effective gate 关闭**。
- `profile_eligible=false`：**成立**。
- V2.2 已冻结：**Git baseline 成立；不应在未决策前继续修改**。
- V2.3 尚未编码：**成立**。

但不能把“71/71 测试通过”解释成产品约束全部兑现。K1–K3 是测试未覆盖的真实实现差异；它们不改变本轮“禁止修复、禁止开始 V2.3”的结论，但必须在 V2.3 架构和验收口径确定前得到明确处置决策。
