# V2 Listening Learning Model V1.1 Calibration

状态：教学模型校准稿；已加入 Data Semantics Hardening，待工程设计验收  
日期：2026-08-30  
继承：`V2_LISTENING_LEARNING_MODEL_V1.md` 已通过的核心原则  
边界：不修改 V2.1/V2.2/V2.2.1；本文不是代码、数据库或页面规格

## 1. 本次校准的结论

V1 的方向保持不变：Extensive / Comprehensible New Input 是长期训练主干；Exam 与 CET-specific skill 和 General Listening 分轨；same-item recovery、reintegration、Local Drill completion 都不等于 ability improved；未暴露的新材料才有资格作为 transfer evidence。

V1.1 的作用是消除四类可能误读：

1. 将 Daily Input、Near Transfer 与 Far Benchmark 明确隔离为三个内容池；
2. 将 Sentence Probe 从“每段 2–4 句”改为由信息价值和学生负担决定的选择性抽样；
3. 将 Evidence class、evidence accumulation、conclusion permission、confidence 分开，拒绝拍脑袋的次数阈值；
4. 将局部目标改善、跨技能整合、整体听力增长分开更新，不让 far transfer 暂无变化否定真实的局部收益。

所有数字性建议均按来源标识：

- **research-supported direction**：已有研究支持的方向性结论；
- **pilot heuristic**：小范围工程/教学试验的默认启发式；
- **pilot-calibrated parameter**：须用 pilot 决定、当前不锁死的参数；
- **capacity planning hypothesis**：为内容供给与成本估算而设，不是学习科学阈值。

## 2. 三内容池模型

### 2.1 INPUT_POOL

**用途**：Daily / Extensive / ordinary new listening。目标是意义优先、可持续的新输入，不是严格测量。

规则：

- 可被大量消费、可作为学习材料重复；
- 完成独立首听后，学生可选择 captions/transcript scaffold；
- 任一学生一旦播放、预览文本或以其他方式接触该 item，该 student–item 关系即成为 familiar；
- 之后可以用于 learning/review/reintegration，但不得作为该学生的 independent near/far transfer item；
- exposure minutes 是学习条件和使用统计，不是能力增长证据。

### 2.2 NEAR_TRANSFER_HOLDOUT_POOL

**用途**：验证一个已训练目标能否迁移到此前未听过的新句/短段。

规则：

- 必须具备 `target_alignment` annotation，例如 weak form、segmentation、conditional relation 或 spoken-form recognition；
- 不进入 Daily Input、搜索推荐、预览、教师提前展示或 Local Drill；
- student 首次播放前 transcript/caption 必须隐藏；
- 使用、播放、文本预览、被推荐到 INPUT_POOL 或进入 Local Drill 后，立即对该 student–item 退役为 familiar；
- 退役后仍可学习，但 `holdout_eligible=false`，不可重作 independent near transfer；
- 目标相似不等于句面重复；新材料应改变足以避免背原句。

### 2.3 FAR_BENCHMARK_POOL

**用途**：在新主题、新说话人、新语篇中观察整体理解是否跨材料变化。

规则：

- 为保留 benchmark，不进入日常推荐，不做针对某个 target 的显性提示；
- 应具有跨主题、说话人/口音、语篇组织或任务表面的差异，而非只替换名词；
- 使用后对该 student 立即退役；纵向复测必须使用新的 benchmark，不能重复同一篇；
- 比 Near pool 更严格：导出、教师展示、试做、任何 transcript preview 都视为污染；
- far benchmark 只用于整体理解的受控观察，不能直接归因为某一音变/词汇问题。

### 2.4 共同内容与暴露状态

每个内容项目至少需要下列概念字段；这是模型语义，不是本轮要求建表：

| 字段 | 语义 |
|---|---|
| `pool_id` | 内容池身份：`input` / `near_holdout` / `far_benchmark`；池是治理身份，不是难度标签 |
| `item_id` | 长期稳定的内容项目标识；不同 revision 不能复用为“新材料” |
| `exposure_status` | 对某学生的 `unseen` / `audio_exposed` / `text_exposed` / `familiar` / `unknown` |
| `holdout_status` | `eligible` / `reserved` / `retired` / `not_applicable` |
| `retired_at` | 从 holdout 退役的时间；未退役为空 |
| `retired_reason` | `played` / `transcript_preview` / `caption_used` / `teacher_preview` / `input_pool_leak` / `local_drill_use` / `integrity_unknown` 等 |
| `prior_exposure_count` | 已知的该学生、该 `item_id + revision + hash` 暴露次数；未知应为 `unknown`，不能默认为 0 |
| `content_revision` | 可追溯的内容版本 |
| `content_hash` | 该版本不可变内容指纹；变更文本、音频、目标标注或任务均应改变 hash |

内容池切换必须是治理动作，不能因为同一音频换了题目就重新标为 unseen。新 revision 若与旧音频的实质暴露高度重合，是否可当新项目必须由内容治理审核，默认保守处理为 familiar。

## 3. Exposure Ledger：先回答“是否真的新”

任何 future transfer eligibility 必须先查询 exposure ledger，而不是依赖学生自报。最小记录为：

| 字段 | 最小语义 |
|---|---|
| `student_id` | 暴露归属；匿名模式也必须有稳定匿名会话/主体语义 |
| `item_id` | 被暴露项目 |
| `first_exposed_at` / `last_exposed_at` | 首次与最近一次已知暴露时间 |
| `exposure_count` | 已知播放/接触次数，不将失败写入视作未暴露 |
| `audio_completed` | 是否达到预定义完整性条件；不是理解成功 |
| `transcript_revealed` | 是否看过 transcript |
| `captions_used` | 是否使用 captions；应与 transcript 区分但同样影响独立性 |
| `meaning_check_attempted` | 是否尝试轻量理解检查；不等于答对 |
| `material_pool` | 当次暴露时的池身份，便于审计串池 |
| `content_revision` / `content_hash` | 当次暴露的准确内容版本 |

建议附加 `exposure_source`（student play / recommendation preview / teacher demo / drill / import）、`audio_started_at`、`audio_completed_at`、`integrity_status`。若日志缺失或身份不可靠，应选择保守结论：不能用作 independent holdout evidence。

## 4. Transfer contamination policy

Near/Far holdout item 对某 student 一旦发生以下任何事件，必须 `holdout_eligible=false` 并写入 `retired_reason`：

- 音频开始播放，不以“是否完整播放”作为逃避条件；
- transcript、caption、文本摘要或答案预览；
- 教师课上/演示中提前展示；
- 推荐、导出或误放入 INPUT_POOL；
- 用于 Local Drill、Sentence Probe demo 或内容审核演示；
- 完整性、身份或历史暴露无法可靠判断。

退役是 student–item 级别的默认规则；若系统发生全局泄露（公开链接、内容被推荐到大量用户），内容运营应考虑 item 级全局退役。学生“我没认真听”不恢复 holdout 资格。

## 5. Selective Probe：抽样而不是硬编码句数

Sentence Probe 是 selective sampling：目的不是覆盖全文，而是在有价值时用 second listen + 至多一个 probe，产生“继续 / 调难度 / future Local Drill candidate”的低推断观察。

抽样数量共同由以下因素决定：

- material duration；
- continuous failure density；
- historical evidence 是否显示某目标重复；
- student fatigue 与 time budget；
- 该 probe 是否会改变后续路线（evidence information gain）；
- material difficulty，尤其是否存在广泛词汇未知；
- 学生主动请求深挖。

**MVP pilot heuristic，非 research-validated threshold：**

| 材料形态 | 通常抽样范围 | 说明 |
|---|---:|---|
| short conversation | 1–3 句 | 只抽取可改变路由的句子 |
| medium passage | 2–4 句 | 可覆盖不同处理层，但不求逐句覆盖 |
| long recording | 3–5 句 | 仍必须有总时间/疲劳上限 |

这些不是长期架构硬规则，更不是“错 N 题必 probe N 句”。任何材料都必须有上限：失败越多时，优先检查有效性与整体难度；不能自动把全文每句送入 probe。

### 值得 probe 的条件

- isolated failure，且一句 probe 能有效区分词义、声音映射或关系处理；
- 历史上有相似、有效但尚未验证的 observation；
- 高价值句：对主旨、说话人立场、条件/否定/转折等关键信息有决定性作用；
- target relation ambiguity、lexical uncertainty 或 acoustic uncertainty 会改变训练建议；
- 学生主动请求帮助，且明确进入 optional learning mode。

### 不值得 probe 的条件

- 材料整体过难、未知词遍布，局部 probe 没有信息增益；
- 明显 interruption、audio integrity 不足或身份/暴露历史不确定；
- transcript 已在本次独立尝试前暴露；
- 已达到疲劳/时间上限；
- 学生明确只想继续听；
- probe 结果不会改变路线。

主动深挖允许进入 optional learning mode，但该模式的所有结果为 scaffolded learning record，不构成 independent diagnostic evidence。

## 6. Evidence hierarchy：类别、累计、结论、置信度分离

| Evidence class | 定义 | 可观察的累计维度 | Conclusion permission | 默认 confidence 上限 |
|---|---|---|---|---|
| E0 | 单次原始事件或答题 | 无须累计 | “发生了 X” | 很低 |
| E1 | 有效 same-item 表现/recovery/reintegration | 暴露条件、完成度 | “在此熟悉材料中恢复/整合” | 很低；不谈能力 |
| E2 | 同次或同材料的多个有效 observation，形成待验证问题 | 句子多样性、处理类型、排除噪音 | “出现待验证的 hypothesis” | 低 |
| E3 | 多个有效、独立、未暴露的 near-transfer observations | items、targets、materials、dates、条件一致性 | “该目标处理在新材料中的表现可能正在改善/重复出现” | 低至中，视累计而定 |
| E4 | 跨材料的 far-transfer evidence，显示整合表现可跨新语篇出现 | topics、speakers、formats、materials、dates | “在陌生短篇/语篇中的综合处理更稳定” | 中，仍可撤销 |
| E5 | 跨日期、跨主题、跨说话人、可比条件下的远迁移趋势 | 时间跨度、材料广度、趋势稳定性、反证 | “近期整体 listening 表现呈改善趋势” | 中至较高；永不等于永久标签 |

每个 class 必须同时保存：

1. **Evidence accumulation**：已积累多少 item、材料、日期、主题/说话人范围及有效率；
2. **Conclusion permission**：此 class 允许哪一级文字；
3. **Confidence**：由累计广度、一致性、条件可比性、噪音和反证共同决定；
4. **Calibration parameters**：`min_items`、`min_materials`、`min_days`、`pass_rate` 等均为 **pilot-calibrated parameters**，当前不锁死。

绝不将“3 次 = E3”“2 篇 = E4”“7 天 = E5”写入模型。E3/E4/E5 的定义来自证据性质与独立性；数值门槛只能在已知学生、材料和测量可靠性的 pilot 后临时配置，并且必须版本化和可审计。

## 7. Three-layer Improvement Model

### 7.1 `skill_gain_status`：特定处理目标

对象为 spoken-form recognition、segmentation、weak-form processing、conditional relation processing 等清晰 target。若多个有效、独立、未暴露的 near-transfer items 显示更稳定的处理，可写：

> 该目标处理在新材料中的表现可能正在改善。

这不是“整体听力提高”，也不要求 far transfer 已立刻变化。状态建议为 `not_assessed` / `insufficient_evidence` / `possible_gain` / `mixed` / `no_current_gain_signal`；它是可撤销的当前证据状态，不是能力分数。

### 7.2 `integration_status`：跨技能协同

对象是新 sentence/short passage 中词汇识别、声音映射、句子关系等共同支持意义构建。需要未暴露短篇材料中的综合、有效表现，而不是把多个 drill 分数相加。允许表述：

> 在短篇陌生语流中的综合处理更稳定。

状态同样独立：`not_assessed` / `insufficient_evidence` / `possible_stabilization` / `mixed` / `no_current_signal`。

### 7.3 `global_growth_status`：整体听力趋势

对象是跨材料、跨主题、跨说话人、跨日期的完整陌生语篇表现。只有 E5 级趋势才允许接近：

> 近期整体 listening 表现呈改善趋势。

状态：`not_assessed` / `insufficient_evidence` / `possible_growth_trend` / `mixed` / `no_current_growth_signal`。它不能由 exposure minutes、CET 单次分数、recovery 或 profile 推断替代。

三者独立更新。例如 near transfer 有进步而 far benchmark 暂无变化，允许 `skill_gain_status=possible_gain`、`integration_status=insufficient_evidence`、`global_growth_status=no_current_growth_signal`；这表示整体证据尚未出现，**不表示局部训练无效**。

## 8. Transcript scaffold policy

硬规则：

```text
Before independent attempt: transcript/caption hidden
After attempt: student may reveal transcript/caption as scaffold
Reveal 后:
  independent_attempt = false（对后续该 item attempt）
  familiar_item = true
  transcript_exposed_before_future_attempt = true
  holdout_eligible = false（若原为 holdout）
```

已揭示文本的 item 可继续用于 learning、review、reintegration 或 optional deep study；不能再用作任何 near/far transfer。若只是完成无文本音频但未揭示 transcript，item 也已因播放成为 familiar，不能再作该学生的 holdout。

## 9. Extensive Input：教学优先级与工程优先级

教学上，Extensive / Comprehensible New Input 是长期主干：新语音量、可理解度、意义优先和持续接触不可被重诊断流程挤掉。它是学习条件，不是自动的能力证据：

> “本周听了 86 分钟新材料”可以展示；“因此听力提高了 18%”不可以展示。

工程上，V2.3 只需验证最小 New Input MVP：能正确分池、记录 exposure、更新 familiarity、在 transcript exposure 后降级证据、给材料最小难度标记，并让学生完成低负担听。它不要求先造大型内容平台、复杂兴趣推荐、全量搜索、AI 无限生成或长期个性化 feed。

## 10. Revised student routing V1.1

| 路由 | 观察 | 下一步 | 不做什么 |
|---|---|---|---|
| A. 理解稳定 | 新材料的轻量检查/自评稳定，条件有效 | 继续 INPUT_POOL 新输入；按计划低频校准 | 不强制 probe 或 drill |
| B. 局部失败但 second-listen recovery | 同材料第二遍恢复 | 多数情况下继续；仅记录 recovery | 不自动 drill，不称 improvement |
| C. 局部失败且历史相似 evidence 重复 | 有价值、有效且尚未验证的局部模式 | selective probe；生成 future Local Drill candidate | V2.3 不执行完整 drill，不进 Profile |
| D. 整体非常困难 | 多处失败、词汇/语篇负荷过高 | 核验有效性，降低 difficulty，回到可理解输入 | 不做十几个 probe，不贴“连读/注意力”标签 |
| E. 主动深挖 | 学生请求分析某句 | optional learning mode，可用 scaffold | 不作为 independent diagnostic/transfer evidence |

## 11. Revised version roadmap

| 版本 | 能力包 | 为什么在这里 |
|---|---|---|
| V2.3 | Evidence Foundation + New Input MVP + Selective Probe Pilot | 先建立“是否新、是否独立、是否有效”的地基，同时验证低负担新输入与选择性分流 |
| V2.4 | Evidence-backed Local Drill + Reintegration + Near Transfer | 修复须由证据授权，且必须用未暴露的近迁移验证，不把同句成功当技能增长 |
| V2.5 | Far Transfer + Independent Reassessment + Provisional Profile | 先有保留 benchmark 与跨材料证据，再允许初步、可撤销的 profile 模式 |
| V2.6 | Longitudinal Profile + Adaptive Input Recommendation | 只有累积了纵向有效证据，才值得做长期趋势与自适应推荐 |

这比 `Sentence Lab → Local Drill → Review → Profile` 更符合闭环：内容暴露与证据独立性先于诊断；训练先于近迁移；跨语篇证据先于画像；大量新输入始终并行存在。

## 12. V1.1 的待校准边界

- 1–3 / 2–4 / 3–5 个 probe 是 **pilot heuristic**；
- 新/旧材料时间比例、20/40/60 分钟建议是 **product hypothesis**；
- E3–E5 的 `min_items`、`min_materials`、`min_days`、`pass_rate` 是 **pilot-calibrated parameters**；
- INPUT / near / far 内容库存数字是 **capacity planning hypothesis**；
- 不应把任何一个上述数字展示成研究证明的个体能力阈值。

本模型保留 V1 的研究边界：词汇与语言知识、过程性元认知教学、阶段性文字脚手架、显式语音特征训练和支持性泛听均有方向性依据；对最佳剂量、具体阈值和远迁移强度不作伪精确承诺。

## 13. Data Semantics Hardening：Exposure 与 Evidence 分离

本节优先于本文此前任何可能混淆“听过”和“表现”的表述。Exposure 只回答学生接触过什么；Evidence 只回答学生在一个可解释任务中表现了什么。

**pure exposure mode 只产生 Exposure Record，不产生能力 Evidence。**其最小记录是：

```text
pilot_subject_id / item_id / media_id / media_hash
exposure_started / meaningful_exposure / audio_completed / exposure_count
transcript_revealed / captions_used
task_revision / task_hash / transcript_revision / annotation_revision / metadata_revision
```

pure exposure 不得产生 `evidence_valid=true`、independent listening success、comprehension success 或 ability claim。可不创建 Evidence Record，或显式标作 `evidence_not_applicable`。`meaningful_exposure` 只用于学习分析；对于 holdout，只要真实音频开始播放即是不可逆暴露，不能用“只听了一秒/未认真听”恢复资格。

Evidence Record 必须引用发生过的 Exposure Record，且只在提交 meaning check、Sentence Probe 或未来 transfer task 时创建：

| 任务 | 可记录 | 禁止结论 |
|---|---|---|
| lightweight meaning check | `meaning_check_correct` / `lightweight_check_passed` / 未答 | understanding stable、material mastered、listening ability strong |
| selective probe | 局部 observation 与 route | diagnosis、stable profile claim |
| future transfer task | 有效、独立任务 evidence | 一次成功即 global growth |

单条 lightweight check 的错对仅能参与 routing heuristic。它可与 student `perceived_difficulty`、audio integrity、近期同内容 band 表现和广泛 unknown-vocabulary signal 一起建议 `adjust_difficulty`，但绝不是能力 diagnosis 或“材料已证实过难”。

## 14. Media identity, global state, and pilot identity

学生是否听过材料，主要由**实质媒体**决定，不能因换题、改 transcript、改难度或 revision +1 重置。至少分开：

| 概念 | 语义 |
|---|---|
| `item_id` | 教学/治理项目的稳定容器 ID |
| `media_id` / `media_hash` | 实质音频身份与不可变指纹；决定听觉暴露与 familiar 的主要依据 |
| `task_revision` / `task_hash` | meaning check/probe/未来任务的版本；更新不重置媒体熟悉度 |
| `transcript_revision` | transcript/caption 版本；文本更新不重置音频暴露 |
| `annotation_revision` | probe candidates、target alignment、边界等标注版本 |
| `metadata_revision` | difficulty、主题、说话人等运营元数据；更新不重置 eligibility |

历史任务/证据必须保留当时的 media、task、transcript、annotation、metadata 版本。实质媒体变更是否构成新的 `media_id` 必须由内容治理审核，默认保守。

状态分两层：

| 层 | 管理事实 |
|---|---|
| Global content governance | `pool_id`、`global_holdout_status`、`content_release_status` 和上述版本 |
| Student–item state | `pilot_subject_id`、exposure/familiarity、prior exposure、text exposure、`student_holdout_eligible`、retired time/reason |

某 Near/Far item 被一个主体使用，默认只退役该 subject–item，而不是全局删除内容；只有 public leak、误进大规模 INPUT recommendation、公开教师展示或受影响主体不可确认时，才考虑 `global_holdout_retired=true`。

V2.3 最低身份为 `pilot_subject_id`：跨刷新/跨 session 稳定；服务端 owner 与 ledger owner 一致；客户端不得伪造其他主体。跨设备账号合并为 non-goal，但属正式 student release 前置要求。

## 15. First engineering-pilot fixture

120–180 分钟 / 30–60 items 仍只是长期 **capacity planning hypothesis**，不是首轮 engineering pilot 前置条件。首轮封闭 pilot 可以使用 8–12 个 INPUT_POOL fixture：覆盖 2–3 个 `content_difficulty_band`、不同 speaker/topic/duration、若干 pure-exposure item、若干 lightweight-check item，以及少量带预标注 `probe_candidates` 的 item。

Near/Far pool 在 V2.3 只验证治理 schema、ledger 查询与 contamination/retirement logic，不开放完整 transfer。`content_difficulty_band` 是内容属性的粗标；`perceived_difficulty` 是学生自评/交互事实；二者不得相互替代，也不得由单次 perceived hard 改写长期能力结论。
