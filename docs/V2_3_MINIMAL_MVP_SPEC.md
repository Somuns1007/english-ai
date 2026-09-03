# V2.3 Minimal MVP Specification

状态：产品/教学边界规格，待验收；不是编码任务  
日期：2026-08-30  
提案名称：**V2.3 = Evidence Foundation + New Input MVP + Selective Probe Pilot**

## 1. Product goal

V2.3 的目标不是构建大型 Sentence Lab，也不是证明学生能力已经提升。它要最小化验证三件事：

1. 系统能可信地区分“未见、已暴露、看过文本、保留 transfer item”；
2. 学生能以低负担方式消费来自 INPUT_POOL 的新材料，保持 meaning-first listening；
3. 当局部失败确有信息价值时，系统能以极少量 Sentence Probe 形成 observation、调难度或 future Local Drill candidate，而不现场做完整诊断/治疗。

V2.3 成功的定义是证据语义和轻量新输入可被可靠运行，不是页面数量、听音总分钟或自动生成的诊断数量。

## 1.1 Normative data-semantics overrides

**Exposure 与 Evidence 必须彻底分离。**Exposure 表示接触事实；Evidence 表示在可解释任务中的表现。pure exposure mode 只创建 Exposure Record，绝不自动创建能力 Evidence。

| 模式/任务 | 可记录 | 明确不记录/不推断 |
|---|---|---|
| pure exposure | 音频开始/完成、暴露次数、文本/字幕使用、媒体版本 | `evidence_valid=true`、independent listening success、comprehension success |
| lightweight meaning check | 单题任务结果和有效性上下文 | understanding stable、material mastered、listening ability strong |
| selective probe | 局部 observation 与 route | diagnosis、ability weakness、stable profile claim |
| future transfer | 合格的独立 task evidence | 由一次成功导出 global improvement |

pure exposure 的 Evidence 为 `not_applicable`，或根本不创建 Evidence Record。Evidence Record 必须引用已发生的 Exposure Record，不能反向由 exposure 推出。

## 2. Hard non-goals

V2.3 明确不做：

- 全文逐句 Sentence Lab；
- 完整 Local Drill；
- Profile 升级或任何 `profile_eligible=true`；
- Near Transfer scoring system；
- Far Transfer benchmark UI；
- longitudinal dashboard；
- 复杂推荐系统、兴趣 feed、内容搜索平台；
- AI 自动无限生成材料；
- 0–100 能力分数；
- working memory、attention、processing speed diagnosis；
- same-item success → skill improved 文案；
- 对 V2.1、V2.2、V2.2.1 的改造或行为变更；
- 大规模抓取/引入新内容。

## 3. Student flow

```text
选择 New Input
  → Listen（正常连续语流；无答案导向的选项预览）
  → 默认最多一个轻量 meaning check，或 pure exposure mode
  → Result
       ├─ 稳定/想继续 → next new input
       ├─ 局部、可行动失败 → optional selective probe
       │       → continue / adjust difficulty / future drill candidate
       ├─ 整体过难 → lower difficulty，返回新输入
       └─ 学生请求 transcript → scaffold；item becomes familiar
```

学生可选 `pure exposure mode`：只听、记录 exposure、无强制检查或诊断。每段默认最多一个低负担理解检查，可为 main idea、speaker intention、简短 self-rating 或一句简短总结中的一种。听前不得显示会明显提示答案的选项。

## 4. Conceptual state machine

```text
unseen
  → allocated_from_input_pool
  → listening
  → lightweight_check_optional
  → result
       ├─ continue
       ├─ probe_optional → probe_second_listen → one_probe → result
       ├─ difficulty_adjustment
       └─ transcript_scaffold
  → completed_familiar
```

补充状态原则：

- `listening` 一旦实际开始音频，即写 exposure；客户端刷新或作答失败不得把它还原为 unseen；
- `transcript_scaffold` 是学习分支，不是失败状态；它会改变未来 evidence eligibility；
- `probe_optional` 只有触发条件满足时可进入；每句最多 second listen + one probe；
- `completed_familiar` 不代表理解成功、能力改善或完成训练计划；
- interruption/audio integrity 异常可使 evidence invalid，但不会撤销已知 exposure。

## 5. Evidence field contract

V2.3 需统一定义并贯穿可解释任务的 attempt/event/result；字段名可在工程阶段调整，但语义不得漂移。pure exposure 不适用能力 evidence 字段，除非显式为 `not_applicable`。

| 字段 | 合法值/含义 | 生命周期规则 |
|---|---|---|
| `evidence_valid` | 是否可用于后续推断；不是写入成功 | interruption/identity/integrity 等失败可置 false；false 仍保留 telemetry |
| `invalid_reason` | `interruption` / `audio_integrity` / `device` / `environment` / `accidental_response` / `identity_unknown` / `unknown` 等 | 无效时必须可解释；不能反推 attention weakness |
| `independent_attempt` | 完成时无答案、无文本、无等价提示且暴露历史符合要求 | transcript/caption 在本 attempt 前暴露则 false；false 不妨碍 learning record |
| `familiar_item` | 此 pilot subject 是否已有任何已知实质媒体暴露 | 播放、文本、教师展示、drill 等任一暴露后为 true |
| `prior_exposure_count` | 已知暴露次数或 `unknown` | 绝不默认为 0 |
| `transcript_exposed_before_attempt` | 本 attempt 前是否看过对应文字 | reveal 后的未来 attempt 必为 true |
| `transfer_item` | 此 attempt 是否来自受控 near/far holdout | V2.3 New Input 默认 false |
| `transfer_distance` | `none` / `near` / `far` | V2.3 只能产生 `none`；未来 transfer 才可用 near/far |
| `audio_integrity` | 正常/异常/未知的完整性状态 | 异常或未知时通常不得形成强证据 |
| `interruption_detected` | 是否检测到中断 | 中断影响有效性，不取消 familiarity |
| `content_revision` / `content_hash` | 本次实际消费的不可变内容版本 | 所有 evidence 与 exposure 必须绑定 |

V2.3 的 probe 输出只能是 observation，例如 `lexical_uncertainty_observation`、`acoustic_mapping_observation`、`relation_processing_observation` 或 `insufficient_evidence`；不得写 diagnosis、能力分、teacher verification 或 profile recommendation。

### Lightweight meaning-check conclusion permission

每条 New Input 默认最多一个轻量 check；一题正确只允许写 `meaning_check_correct` / `lightweight_check_passed`，一题错误只允许写该任务未通过。单题错对不能单独证明 `understanding_stable`、`material_mastered`、`material_too_hard` 或任何能力结论。

V2.3 的 difficulty routing 只是 routing heuristic，可综合轻量 check、student `perceived_difficulty`、audio integrity、近期同 `content_difficulty_band` 表现和广泛 unknown-vocabulary signal；不得升级为 diagnosis。

## 6. Exposure ledger

V2.3 必须具备 exposure ledger 的最小语义：

```text
pilot_subject_id
item_id
media_id
first_exposed_at
last_exposed_at
exposure_count
exposure_started
meaningful_exposure
audio_completed
transcript_revealed
captions_used
meaning_check_attempted
material_pool
media_hash
task_revision
task_hash
transcript_revision
annotation_revision
metadata_revision
```

语义规则：

- 首次真实音频开始就创建/更新暴露，不等待完成；`exposure_started`、`meaningful_exposure`、`audio_completed` 是不同分析事实；
- `audio_completed` 只说明播放完整，不说明理解；
- `transcript_revealed` 或 `captions_used` 永久影响该 student–item 的独立性；
- ledger 缺失、identity 不明或 revision/hash 不可追溯时，future holdout eligibility 必须保守拒绝；
- 所有未来 transfer 分配在选择项目之前查询 ledger。

对 transfer holdout，只要真实音频开始播放，即不可逆暴露并退役该 subject–item holdout；即使只听 1 秒、立刻关闭或自称没认真听也不恢复。`meaningful_exposure` 只供学习分析，绝不恢复资格。

## 7. Content-pool schema and governance

### 7.1 Identity and revision model

学生的听觉熟悉度由实质媒体身份而非题目或难度修改决定。下列对象必须分开：

| 对象 | 语义 |
|---|---|
| `item_id` | 教学/治理容器的稳定 ID |
| `media_id` / `media_hash` | 实质音频身份与不可变媒体指纹；决定 exposure/familiarity 的主要依据 |
| `task_revision` / `task_hash` | meaning check、probe 或未来任务的版本；更新不重置媒体熟悉度 |
| `transcript_revision` | transcript/caption 版本；文本更新不重置音频暴露 |
| `annotation_revision` | probe candidate、target alignment、audio boundary 等标注版本 |
| `metadata_revision` | difficulty、topic、speaker 等运营标注；更新不重置 eligibility |

历史任务/证据必须记录当时全部相关版本。换一道题、调 difficulty label 或修正 annotation 不能让同一实质音频重新变 `unseen`。是否构成新 `media_id` 由内容治理审核，默认保守。

### 7.2 Global vs subject–item state

| 层 | 字段/事实 |
|---|---|
| Global content governance | `pool_id`、`global_holdout_status`、`content_release_status`、media/task/transcript/annotation/metadata revisions |
| Subject–item exposure/eligibility | `pilot_subject_id`、`exposure_status`、`prior_exposure_count`、text exposure、`student_holdout_eligible`、`retired_at`、`retired_reason` |

一个 Near/Far item 被某主体使用，只默认退役其 `student_holdout_eligible`，并不全局删除素材。public leak、误入大规模 INPUT recommendation、公开教师展示或受影响主体无法确认时，才可置 `global_holdout_retired=true`。

| 字段 | 说明 |
|---|---|
| `pool_id` | `input` / `near_holdout` / `far_benchmark` |
| `item_id` | 稳定项目 ID |
| `exposure_status` | per pilot subject：`unseen` / `audio_exposed` / `text_exposed` / `familiar` / `unknown` |
| `holdout_status` | `eligible` / `reserved` / `retired` / `not_applicable` |
| `retired_at` | holdout 退役时间 |
| `retired_reason` | 播放、文本、教师预览、串池、drill 使用、完整性未知等 |
| `prior_exposure_count` | per student 的已知次数/unknown |
| `media/task/transcript/annotation/metadata revisions` | 见 7.1；历史可完整还原，但 metadata/task 更新不重置音频暴露 |
| `target_alignment` | near holdout 专用：目标处理标签与标注依据 |
| `difficulty_band` | `easy` / `medium` / `hard`，是运营标签不是精确能力分 |

串池防线：

- INPUT_POOL item 不可被重新标成 holdout；
- near/far holdout 不可出现在日常推荐、搜索预览、教师演示或 Local Drill；
- holdout item 一旦播放、文本预览、教师展示、误推荐到 input 或用于 drill，立刻退役并写 `retired_reason`；
- 用过的 far benchmark 的纵向复测必须换新 item；
- 同一实质音频即使改变题目或 revision，也不得借版本号洗白为 unseen，除非内容治理人工判定暴露不再实质重合。

## 8. Difficulty MVP

V2.3 只提供可审计的粗粒度 `content_difficulty_band`：`easy` / `medium` / `hard`，不向学生伪装为科学精确分数，更不等于“对该学生的难度”。学生侧单独记录 `perceived_difficulty`，可来自自评/实际交互；单次 perceived hard 不得改写长期能力标签。最小属性：

| 属性 | 来源类型 | 说明 |
|---|---|---|
| `duration` | machine-extracted | 音频时长；可靠但不代表难度 |
| `speech_rate` | machine-estimated，需抽检 | 可由 ASR/对齐估计；受静音、重叠说话影响 |
| `lexical_difficulty` | machine-estimated + 人工抽检 | 基于词频/覆盖估算；不等同学生词汇知识 |
| `syntactic_density` | machine-estimated + 人工抽检 | 依赖 transcript 质量，适合作粗标记 |
| `discourse_complexity` | 人工 annotation 优先 | 多线叙事、立场变化、推断负荷等 |
| `speaker_count` | machine-extracted + 人工校验 | 说话人数量与切换 |
| `accent_familiarity` | 人工 annotation + user-dependent | 内容属性与学生经历不同，不能只写一个真值 |
| `topic_familiarity` | user-dependent | 学生自评/历史偏好，可未知 |
| `support_level` | 系统事实 | 是否允许 captions/transcript、是否有图片/提示 |

MVP 只需用这些属性给出保守 band；若整体失败，优先调低 band 或提高 support，而不是推断学生某个底层缺陷。

## 9. New Input interaction contract

- 从 INPUT_POOL 分配此前未暴露的合适 item；找不到时诚实显示库存不足/可复听，而不把 familiar 内容伪装成 new；
- 先听后查：默认隐藏 transcript/captions；听前无答案导向选项；
- 每段默认最多一个轻量 meaning check，允许跳过或 pure exposure；
- Result 只可呈现完成、轻量理解结果、self-report、difficulty 调整建议及是否可选择 scaffold；
- 不显示“你在某能力上提高了”“你注意力不足”等总结；
- transcript/caption reveal 后该 item 保留学习价值，但转为 familiar/scaffolded。

## 10. Selective Probe contract

### Trigger

只有同时满足“失败局部、证据有效、probe 可能改变下一步、未触及疲劳/时间上限”时才可建议 probe。候选只能来自以下可解释来源之一：

- 内容预先 annotation 的 `probe_candidates`；
- 学生播放中/后主动标记“这里没跟上”；
- 已有重复 historical evidence，且当前材料有预标注的 target-aligned candidate；
- 已定位到某一具体 sentence/span 的局部任务。

模型可以从候选中排序/选择，不能因一次 main-idea check 做错而自由指定某句话并声称“学生就是这里没听懂”。每个 `probe_candidate` 最少包含：`sentence_or_span_id`、`audio_start/end boundary`、`candidate_reason`、`possible_probe_type`、`target_relation`，以及能还原 media/task/annotation 版本的 revision/hash 信息。

### Suppression

整体过难、未知词广泛、明显中断、transcript 已提前暴露、疲劳上限、学生只想继续、或信息增益很低时禁止/不建议 probe。

### Interaction boundary

- 采用 selective sampling，而非全文覆盖；
- **pilot heuristic**：short conversation 通常 1–3 句，medium passage 2–4 句，long recording 3–5 句；
- 每句最多一次 second listen + 一个 probe；
- 总量与总时长必须有可配置上限；任何数值是 pilot heuristic/pilot-calibrated parameter，不是研究阈值；
- 输出只允许 `continue`、`adjust_difficulty`、`future_local_drill_candidate`、`insufficient_evidence`。

V2.3 不实施 future Local Drill candidate 的完整治疗，只保存为后续版本可审计的候选。

## 11. Transcript policy

硬规则：

```text
Independent attempt 前：transcript/caption hidden
Attempt 后：学生可主动 reveal 作为 scaffold
Reveal 后：
  independent_attempt = false（对之后同 item 的 attempts）
  familiar_item = true
  transcript_exposed_before_future_attempt = true
  holdout_eligible = false（若 item 原属于 holdout）
```

音频播放本身也使 item 对该 student familiar；reveal 不会使之前已经完成的、条件完整的 first attempt 追溯失效，但会使未来同 item attempt 不再独立。若 reveal 发生在 attempt 前或 attempt 中，则该 attempt 不属于 independent auditory evidence。

## 12. API-level conceptual contracts

本节描述未来接口必须表达的行为契约，不授权本轮创建 API。

| 概念操作 | 必须保证 | 禁止 |
|---|---|---|
| Allocate New Input | 只从 INPUT_POOL 分配对该 student `unseen` 且版本可追溯的 item | 从 holdout 或 familiar item 伪装分配 |
| Start/record exposure | 原子地更新 ledger 与 exposure status | 播放后仍可作为 unseen |
| Submit lightweight check | 保存任务上下文与有效性；不生成能力诊断 | 自动写 Profile 或 skill improved |
| Reveal transcript/captions | 原子地更新 scaffold 与独立性状态 | reveal 后仍允许该 item 作 transfer |
| Request/record probe | 校验触发与上限；输出 observation | 多 probe 诊断树、答案位置泄露 |
| Query future transfer eligibility | 先查 ledger、holdout 状态与 revision/hash | 仅信任前端或学生自报 |
| Content administration | 保留池、revision、hash、退役原因可审计 | 允许不留痕串池 |

## 13. Data integrity rules

1. exposure、transcript reveal、holdout retirement 与 content revision/hash 必须可追溯、不可被前端任意声称；
2. 同一 student–item 状态更新要幂等、可恢复，并避免并发下重复把 holdout 分配给同一主体；
3. 任何历史 attempt 必须绑定实际消费版本，不可因内容更新而改写为新材料；
4. evidence invalid 不等于 exposure 不存在；
5. `unknown` 是合法保守状态，不能静默转成 `unseen`；
6. 内容 revision/hash 应绑定音频、文本、支持物、难度标签和 target annotation 的可审核版本范围；
7. 事件 payload 不接受答案、transcript、attention、working-memory 等不应存在的推断性字段；
8. student identity 与 session/ledger ownership 必须一致；
9. V2.3 应独立于冻结的 V2.2 session semantics，不能借用其结果当 transfer evidence。

## 14. Release and profile policy

- V2.3 内容默认内部 engineering pilot；内容质量、版权与来源审查未完成前不得学生发布；
- 建议独立 release gate，不能以一个环境变量同时放行 V2.1/V2.2/V2.3；
- 全部 V2.3 记录 `profile_eligible=false`；
- V2.3 的 probe 和 New Input 只产生 exposure、validity、轻量理解结果与 observation；
- 模型/机器不得自称 `teacher_verified`；机器难度估算和 target annotation 必须标明来源与人工审核状态；
- V2.1/V2.2 的现有 release/profile gates 不因 V2.3 开发而改变。

### Pilot identity minimum

V2.3 engineering pilot 使用 `pilot_subject_id`，而不是把所有人硬编码为 `anonymous`。它必须跨刷新/跨 session 稳定，服务端 session owner 与 exposure ledger owner 必须一致，客户端不得任意伪造其他主体。完整登录与跨设备账号合并是 V2.3 non-goal，但为正式 student release 的前置要求。

## 15. Engineering-pilot acceptance checklist

除页面/API 测试以外，pilot 必须能证明：

- [ ] 新材料 exposure 被正确记录；
- [ ] 已听过的 material 不再标为 unseen；
- [ ] transcript/caption reveal 正确降级后续 independent evidence；
- [ ] INPUT_POOL 与 near/far holdout 不串池；
- [ ] 学生可以 pure exposure，不被强迫诊断；
- [ ] 局部失败不会自动生成 diagnosis；
- [ ] 整体过难优先触发 difficulty adjustment；
- [ ] selective probe 有可配置数量/时间上限，且不会全文逐句化；
- [ ] probe 结果只生成 observation/route，不能生成 stable ability claim；
- [ ] 所有 V2.3 records 为 `profile_eligible=false`；
- [ ] UI、API、事件与结果文案不存在 same-item success → skill improved；
- [ ] content revision/hash 与 exposure ledger 可完整追溯；
- [ ] holdout 污染会立即退役并记录原因；
- [ ] 旧 V2.1/V2.2 不被破坏，冻结测试与行为回归通过；
- [ ] 中断、刷新、弱网、重复请求、身份越权、串池与 revision drift 有针对性测试。

## 16. Content inventory hypothesis

以下是 **capacity planning hypothesis，不是 research fact 或 release threshold**。实际库存取决于学生日均使用、复习策略、主题多样性、版权预算和材料质量。120–180 分钟/30–60 items 不是第一轮 engineering pilot 的前置条件。

| 池 | MVP 建议库存 | 目的与计算逻辑 |
|---|---|---|
| INPUT_POOL | 约 120–180 分钟、30–60 条短材料 | 以 5–10 分钟/日的新输入可支撑约 2–3 周而不立刻重复；不足时宁可诚实提供复听模式 |
| NEAR_TRANSFER_HOLDOUT_POOL | 每个 target 约 8–12 条未见短句/短段，且至少有多说话人/表面变体 | 给 pilot 留出失败、污染与多次独立采样余量；不可把同模板改写当多条 |
| FAR_BENCHMARK_POOL | 约 12–18 条独立短语篇，总计约 60–120 分钟 | 支撑数周按批次使用新的 benchmark；每次使用后退役，纵向不复用同篇 |

以上不等于“材料达到此数便可做长期 growth claim”；它只是避免系统在几天后不得不把熟悉材料伪装成新材料的最低供给思考。

### First closed engineering-pilot fixture

第一轮封闭 engineering pilot 可缩小为 **8–12 个 INPUT_POOL items**：覆盖至少 2–3 个 `content_difficulty_band`、不同 speaker/topic/duration，包含若干 pure exposure item、若干 lightweight-check item，和少量带预标注 `probe_candidates` 的 item。具体数量是 **engineering pilot fixture**，不是正式产品库存目标。

Near/Far pool 在 V2.3 只验证 schema、ledger 查询和 contamination logic，不开放完整学生 transfer 流程。

### 来源与适用性

| 来源 | INPUT_POOL | Near holdout | Far benchmark | 主要风险 |
|---|---|---|---|---|
| 正规授权真实人声 | 合适 | 合适，需严格保留 | 最合适，需版本/泄露治理 | 成本、版权、审核 |
| 公开许可语料 | 合适，需许可/难度/音质审核 | 可用，需防公开泄露与 target 标注 | 可用但需评估已知暴露 | 许可范围、学生可能已接触 |
| 教师录制真实语音 | 合适 | 合适，易控制目标 | 可用，需说话人/主题多样性 | 人工制作与审核成本 |
| TTS | 可作为早期 INPUT/局部材料 | 仅当 target 不依赖真实变异且有人工验收 | 不宜单独承担 general far benchmark | 声音自然性、变异度、合成痕迹 |
| 机器生成文本+配音 | 仅限内部、审核后 | 风险较高 | 不建议作为高权重 benchmark | 事实/版权/自然度/重复模板 |
| CET/市售真题整理 | 不宜作为日常唯一来源 | 不宜直接作 holdout | 需明确版权和既有暴露后才考虑 | 版权、泄露、熟悉度、当前 V2.0b 未 teacher verified |

所有来源在进入学生端前仍受内容质量、版权、人工审核与 release gate 约束。现有 V2.0b/Pilot 内容为 machine-prechecked/generated-unverified，不能因被写入 V2.3 规划而升级状态。

## 17. Risks

### P0

- 没有 exposure ledger 或 ledger 不能区分 revision/hash，导致“新材料”无法证明；
- holdout 串池或污染后仍被当作 transfer；
- transcript reveal 后独立性未降级；
- V2.3 把 recovery/轻量检查自动转成 skill/profile claim；
- 使用未审核、无版权或机器状态不清的内容面对学生。

### P1

- New Input 被多个选择题与 prompt 重新变成做题产品；
- Probe 默认化，逐渐演变为全文 Sentence Lab；
- 粗难度标签被误解为个人精准能力；
- 库存不足，迫使频繁重复或将熟悉项目伪装成 unseen；
- 只用 TTS 或单一口音，导致“新输入量”缺乏真实语流多样性。

### P2

- 本地匿名身份、跨设备与 exposure ledger 的归并规则；
- 中断后“已播放”与“未构成可用 evidence”的一致呈现；
- target annotation 的人工成本和 inter-rater policy；
- material difficulty 的人工/机器协作边界；
- 未来 near/far 指标的 pilot-calibrated parameters。

## 18. Questions requiring product confirmation

1. V2.3 是否确认只面向内部 engineering pilot，且保持独立 release gate？
2. MVP 首批可用的、可授权且可审核的新内容来源是什么？
3. INPUT_POOL 初始库存以 120–180 分钟/30–60 条为 planning 假设是否可接受，还是先做更小的封闭试验？
4. student identity 的最小形式是什么，能否支撑跨会话/跨设备 exposure ledger？
5. transcript 与 caption 是否同等视为 independent evidence 污染；若有例外，必须明确哪些例外。
6. Probe 的疲劳/时间上限应由全局产品策略还是课程/材料策略配置？
7. `easy/medium/hard` 的首批人工标注责任人、审核标准与 content revision policy 是什么？
8. Near/Far holdout 是否在 V2.3 仅做治理和库存准备，而完全不向学生端开放？
9. V2.3 是否应先限定 CET-6/通用英语中的一个内容域，鉴于当前正式材料实际只有 CET-6？
10. 未来 V2.4 使用 future Local Drill candidate 时，哪种 evidence accumulation 才能升级为可行动训练建议？

完成上述确认前，V2.3 不应进入编码。本规格故意不包含路由、表、服务、API 或前端实现方案。

## 19. ENGINEERING READINESS

| Decision | Status | Basis |
|---|---|---|
| Teaching model stable? | YES | V1.1 已验收；本轮只收紧语义，不改变主循环 |
| Exposure semantics stable? | YES | Exposure Record、ledger、`exposure_started` / `meaningful_exposure` / `audio_completed` 与保守 holdout 规则已定义 |
| Evidence semantics stable? | YES | pure exposure 不产 Evidence；meaning check/probe 的结论权限已限定 |
| Content pool governance stable? | YES | 三池、global/subject 两层状态、污染和退役策略已定义 |
| Identity minimum defined? | YES | `pilot_subject_id`、owner 一致性与反伪造边界已定义 |
| Probe provenance defined? | YES | 候选来源、最低字段和禁止自由定位规则已定义 |
| Pilot inventory feasible? | YES | 第一轮可使用 8–12 个封闭 fixture；长期库存仍是 planning hypothesis |
| V2.1/V2.2 frozen boundaries preserved? | YES | V2.3 独立设计；本规格不授权修改冻结模块 |

**Decision: `READY_FOR_V2_3_ENGINEERING_DESIGN`**

这表示可以进入 engineering design（数据模型、接口契约、状态机和验收设计）的讨论，**不是直接编码授权**。编码仍需独立的产品/工程确认。
