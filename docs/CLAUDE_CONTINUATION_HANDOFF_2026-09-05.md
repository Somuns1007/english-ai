# Claude Continuation Handoff — CET Listening Project

> 后续更新：用户要求优先审查 Claude 的 Word 总结与 Review Prompt 后，已形成 [最新独立审核与完整交接报告](D:/kimi-workspace/english-ai/docs/GPT6_INDEPENDENT_REVIEW_AND_HANDOFF_2026-09-05.md)。当前续接请以新报告为准。本简版的“下一步推进 V2.3”优先级、前端验证口径及功能完成度已被新报告补充/纠正。

生成日期：2026-09-05  
项目根目录：`D:\kimi-workspace\english-ai`  
盘点性质：只读状态核查后的续接说明；本文件不构成新的编码授权。

## 1. 一句话状态

项目当前停在：**V2.3 的教学模型、MVP 规格、数据语义 hardening 和 engineering design 已完成；V2.3 尚未编码。**

下一步不是直接写 V2.3 代码，而是完成/获得 engineering-design 所列的 3 项 S1 产品确认；随后才需要一次单独的编码放行。

与此同时，仓库里已存在一批与 V2.3 分开的已提交功能（Aural Lexicon、Strict Pacing、Stem Bank、Harvest、Dashboard），以及 V2.2/V2.1 冻结审计问题的修复。不要把这些功能误认作 V2.3 实现。

## 2. Git snapshot（以本次盘点为准）

| 项目 | 当前事实 |
|---|---|
| Branch | `main` |
| HEAD | `f064dcd19a3cedaefa144ee6781cbfee2db857c2` |
| HEAD subject | `docs(V2.3): 工程设计草案(非编码授权)` |
| Working tree | clean（`git status --short --branch` 仅为 `## main`） |
| 原冻结 baseline | `fdc9c23` 存在，且是当前 HEAD 的祖先，不再是 HEAD |
| Latest V2.3 artifact | `docs/V2_3_ENGINEERING_DESIGN.md`，提交 `f064dcd` |

请先从当前 HEAD 开始，不要 reset/checkout 回 `fdc9c23`。后续若要开 V2.3 实现，应先由用户确认并建立新的可识别基线/tag/commit；当前仓库仍没有 Git tag 或 remote/upstream 的可用基线治理。

## 3. 已完成的教学/产品决策

以下已经完成并通过，不应重新争论或在编码时偷换语义：

1. Extensive / Comprehensible New Input 是长期学习主干；Exam/CET-specific skill 与 General Listening 分轨。
2. Option Preview 是 CET-specific skill，不能进入 General Listening Profile。
3. Same-item recovery、Reintegration、Local Drill completion 都不等于 skill improved 或 transfer。
4. Transfer 必须使用此前未暴露的新材料；Near/Far holdout 和 INPUT_POOL 不可混用。
5. Sentence Lab 是选择性 sampling/probe，不是每个学生都经历的全文逐句流程。
6. Observation ≠ diagnosis；不生成 working memory、attention、processing speed 等伪诊断。
7. Transcript/caption 是 attempt 后可选 scaffold；一旦暴露，未来同 material attempt 不再是 independent auditory evidence。
8. Profile 只应使用更强的跨材料、跨时间证据；V2.3 全程 `profile_eligible=false`。

权威文档阅读顺序：

1. `docs/V2_LISTENING_LEARNING_MODEL_AUDIT.md`
2. `docs/V2_LISTENING_LEARNING_MODEL_V1_1.md`
3. `docs/V2_3_MINIMAL_MVP_SPEC.md`
4. `docs/V2_3_ENGINEERING_DESIGN.md`
5. `CODEX_PROJECT_HANDOFF_AUDIT.md`

## 4. V2.3 的准确停点

### 已完成：设计，不是实现

`docs/V2_3_MINIMAL_MVP_SPEC.md` 与 `docs/V2_3_ENGINEERING_DESIGN.md` 已定义：

- V2.3 能力包：**Evidence Foundation + New Input MVP + Selective Probe Pilot**；
- 三内容池：`INPUT_POOL`、`NEAR_TRANSFER_HOLDOUT_POOL`、`FAR_BENCHMARK_POOL`；
- exposure ledger、holdout contamination/retirement、内容版本和媒体身份；
- `pilot_subject_id` 的最小身份边界；
- New Input 轻量流程、轻量 meaning check、transcript scaffold；
- Selective Probe 的候选来源、上限、输出范围；
- 独立 V2.3 release gate、`profile_eligible=false`；
- 未来 DB/schema、模块、API conceptual contract 与验收测试矩阵。

### 未完成：任何 V2.3 实现

本次盘点未发现以下实现资产：

- `backend/listening/v2_3_*.py`；
- V2.3 router/service/registry/DTO/identity/ledger 实现；
- `v3_*` SQLite 表或 migration；
- V2.3 endpoint；
- V2.3 Vue view/component；
- V2.3 自动化测试；
- V2.3 input/holdout fixture 内容；
- V2.3 实际 release gate。

换言之，`V2_3_ENGINEERING_DESIGN.md` 里的文件路径、DDL、端点和状态机是**未来实现蓝图**，不是已存在的代码。

## 5. V2.3 Data Semantics（不可降级的约束）

### Exposure 与 Evidence 分离

- pure exposure 只写 Exposure Record：`pilot_subject_id`、`item_id`、`media_id/media_hash`、开始/完成/次数、文本/字幕暴露及版本上下文。
- pure exposure 不创建 `evidence_valid=true`、comprehension success、independent listening success 或任何能力结论；可无 Evidence Record，或为 `not_applicable`。
- 只有 meaning check、probe、未来 transfer task 才创建 Evidence Record；Evidence 必须引用既有 Exposure。
- 单条 lightweight check 只允许 `meaning_check_correct` / `lightweight_check_passed` 或未通过；不能写“理解稳定”“材料掌握”“听力强”。

### Media identity 与 version 分离

学生是否听过主要由实质 `media_id/media_hash` 决定。必须分离：

- `item_id`：教学/治理容器；
- `media_id/media_hash`：实质音频身份；
- `task_revision/task_hash`：题目/meaning check/probe；
- `transcript_revision`；
- `annotation_revision`；
- `metadata_revision`。

换题、改 transcript、改标注、改 difficulty 都不能让同一实质音频重新变 `unseen`。历史记录要能还原当时的 media/task/transcript/annotation/metadata versions。

### Global 与 subject–item state 分离

- 全局内容治理：pool、global holdout/release 状态和所有 revision；
- 单主体状态：暴露、familiar、prior exposure、text exposure、student holdout eligibility、retirement time/reason。

某主体听过 Near/Far holdout 后，默认只退役这个 subject–item；只有 public leak、误进大规模 INPUT 推荐、公开展示或受影响范围不可确认，才考虑全局退役。

### Holdout 的保守规则

真实音频只要开始播放，即使只听 1 秒、立刻关闭、学生说没听懂，也永久污染该 subject–item holdout。`meaningful_exposure` 仅用于学习分析，绝不能恢复 holdout eligibility。

## 6. V2.3 scope 与 hard exclusions

### 允许的 MVP

1. Evidence Foundation：exposure ledger、版本/身份、熟悉度、独立性和污染治理。
2. New Input MVP：从 INPUT_POOL 分配新材料、连续听、默认最多一个轻量 meaning check 或 pure exposure、结束后可 reveal transcript scaffold。
3. Selective Probe Pilot：有可解释候选的局部 second listen + 一个 probe；只输出 `continue`、`adjust_difficulty`、`future_local_drill_candidate` 或 `insufficient_evidence`。

### 明确不做

- 全文逐句 Sentence Lab；完整 Local Drill；
- Near Transfer scoring 或 Far Benchmark UI；
- Profile 升级、longitudinal dashboard、能力分数；
- 复杂推荐/feed/搜索、AI 无限生成、批量内容抓取；
- 工作记忆/注意力/速度诊断；
- V2.1/V2.2/V2.2.1 的行为改造；
- 把 same-item success 写成 skill improved。

## 7. Selective Probe 必须遵守的来源规则

不能因为 main-idea check 错一题，就凭模型猜测某句是故障点。Probe candidate 只能来自：

1. 内容预标注的 `probe_candidates`；
2. 学生主动标记的 sentence/span；
3. 已有重复 historical evidence 与当前预标注 target-aligned candidate 的匹配；
4. 已明确定位 sentence/span 的局部任务。

每个候选最少应可追溯：`sentence_or_span_id`、audio boundary、`candidate_reason`、possible probe type、target relation 及相应版本/hash。模型可排序候选，不能自由生成“你在这里没听懂”的位置声明。每句最多 second listen + one probe；数量/时间上限是 pilot heuristic，不是研究阈值。

## 8. 当前已经实现并提交的其他功能（不要与 V2.3 混淆）

提交 `9450e30` / `ce90050` 已实现后端与前端的：

- Aural Lexicon；
- Strict Pacing；
- Stem Bank；
- Transcript Harvest；
- Listening Dashboard；
- 相关 JSON 数据、服务、路由、Vue views/components 和测试文件。

这些不是 V2.3 New Input MVP，也不自动满足 V2.3 的 exposure ledger/holdout/evidence contract。若后续需要复用其中代码，必须先按 V2.3 语义评审，不能直接把 legacy/新功能的行为数据灌入 V2.3 evidence。

## 9. 已提交的冻结差异修复

在 `fdc9c23` 之后已经提交的修复，均不是待做事项：

| Commit | 已处理事项 |
|---|---|
| `cbc78fc` | V2.2 `result_final` / summary 的 `round1_correct` 泄露（K1） |
| `f8cef7c` | V2.2 event payload 白名单与 student/session binding（K2） |
| `ba91f27` | V2.2 完整题面/options/dimension snapshot pin，及 removed check drift（K3） |
| `754f36a` | observations/checks 并行数组泄露旁路硬化（K1 深修） |
| `76c1d36` | V2.1 已有 attempt 的 gate 覆盖，及 release metadata 读取 baseline（K6/K9） |

不要重复实现这些修复，也不要为了 V2.3 把 V2.2 主流程继续拉长。V2.2 当前功能修改已在这些提交中发生；接下来应视为冻结，不再随意改动。

## 10. 数据与发布现状

- `V2_0B_BASELINE.json` 当前仍写 `student_release_allowed=false`；V2.0b 是 `machine_prechecked`，不是 `teacher_verified`。
- V2.2 Pilot 仍为 `ENGINEERING_PILOT_ACCEPTED`，不等于学生发布或 teacher verification；`profile_eligible=false`。
- 2026-09-04 的 `49c0cf0` 已对 transcript/OCR 做重建校正并重新 seal V2.0b 相关 artifact。不要假设旧 `fdc9c23` 的 hash 仍是当前数据 hash；需要时以当前 baseline JSON 和 `49c0cf0` 为准。
- 当前正式听力材料仍实际以 CET-6 为主；CET-4 内容不是已完成的 V2.3 fixture。
- V2.3 工程设计建议独立开关 `ALLOW_UNRELEASED_LISTENING_V2_3`，不得复用会同时放行 V2.1/V2.2 的开关；这只是设计，尚未实现。

## 11. 测试与环境事实

本次未能完成新的回归实跑，原因必须如实保留：

- 系统 Python：`E:\python\python.exe`，未安装 `pytest`；
- `backend\venv\Scripts\python.exe` 的 shebang 指向已不存在的 Kimi runtime，因此虚拟环境当前不可用；
- 工作树仍 clean，测试尝试没有造成文件改动。

后续在可用环境中应先恢复/重建隔离环境，再按下列顺序验证：

```powershell
cd D:\kimi-workspace\english-ai\backend
<working-python> -m pip install -r requirements.txt
<working-python> -m pytest -q

cd D:\kimi-workspace\english-ai\frontend
npm run type-check
npm run build
```

不要把“测试未运行”写成“测试通过”。`backend/pytest.ini` 已配置测试路径与 30 秒 timeout；现有仓库包含 V2.1/V2.2 回归和新增 Aural Lexicon / pacing / harvest / dashboard 测试文件。

## 12. V2.3 编码前仍需用户确认的 S1 门禁

`docs/V2_3_ENGINEERING_DESIGN.md` §14 明确列出以下编码前确认：

1. **内容来源（最硬）**：INPUT_POOL 可授权、可审核的音频来源；设计中“已验证片段 + 标注内部 TTS”只是不阻塞设计的封闭 pilot 默认，不是正式来源批准。
2. **难度标注责任**：`easy/medium/hard` 的人工标注人、审核标准和 inter-rater 策略。
3. **编码放行时点**：用户是否在本工程设计评审后明确授权编码。

当前文档结论为 `READY_FOR_V2_3_ENGINEERING_DESIGN`，含义是**可以讨论工程设计**；不等于 `READY_FOR_V2_3_IMPLEMENTATION`。

## 13. 建议 Claude 的下一步

1. 先阅读 §3 所列文档和 `docs/V2_3_ENGINEERING_DESIGN.md`，确认不把 design 当 implementation。
2. 向用户收集/确认 §12 三项 S1 门禁；没有编码授权时只做审阅或回答问题。
3. 若获编码授权，先建立新的 V2.3 implementation baseline/tag，并修复/重建本地 Python 测试环境；不要直接在未知依赖环境中开始迁移。
4. 实现顺序应遵循 engineering design：独立 gate/identity → registry/fixture governance → exposure ledger → New Input → meaning check/reveal → selective probe → 测试矩阵。
5. 每完成一步都验证：pure exposure 不产 evidence、媒体换题不重置 unseen、holdout 播放即退役、transcript 让未来 attempt 失去独立性、V2.1/V2.2 回归未受影响。

## 14. 禁止事项（交接后仍有效）

- 不把 V2.3 做成大 Sentence Lab；
- 不创建完整 Local Drill、Near/Far student flow 或 Profile 升级；
- 不直接把现有 Aural Lexicon/Strict Pacing/legacy training 数据当 V2.3 transfer evidence；
- 不再随意修改 V2.1/V2.2/V2.2.1；
- 不将 machine/model 标为 `teacher_verified`；
- 不因页面能打开、学生听过很多分钟或同材料恢复成功而声称 listening ability improved；
- 不忽略测试环境失效问题，也不假称当前回归已通过。

---

交接结论：**当前适合继续 V2.3 engineering design review 与获取 S1/编码授权；不适合在未经确认的情况下直接编码。**
