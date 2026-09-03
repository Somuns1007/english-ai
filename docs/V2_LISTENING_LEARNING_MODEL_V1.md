# V2 Listening Learning Model V1

状态：产品/教学模型提案，待验收  
日期：2026-08-30  
前提：V2.2 保持冻结；本文不是数据库、API、页面或 V2.3 编码规格

## 1. 模型目标

产品的最高目标不是“把做错的 CET 题讲明白”，而是帮助学生在**未见过、正常连续语流**中更稳定地把 speech 转换为 meaning，并能跨材料、跨时间保持改善。

模型同时服务两个但不混淆的目标：

- **CET track**：熟悉考试约束、选项预览、信息选择、干扰项和时间管理；
- **General listening track**：词汇可用性、声音—词汇映射、连续语流分词、句子关系、语篇建构与流利处理。

CET 是一种定期测量和专项练习场景，不是整个学习系统的唯一内容源。

## 2. 最终学习闭环

```text
持续主干：Comprehensible New Input / Extensive Listening
                         │
定期校准：Exam 或 unseen Continuous Baseline
                         │
             ┌───────────┴───────────┐
         表现足够                     出现失败
      回到更多新输入        Selective Sentence Probe
                                      │
                         evidence 不足 ├─→ 继续新输入/调难度
                         evidence 可行动 └─→ Local Drill
                                                   │
                                      Reintegration（原材料）
                                                   │
                                      Near Transfer（新句）
                                                   │
                                      Far Transfer（新语篇）
                                                   │
                                Spaced / Longitudinal Reassessment
                                                   │
                                      Qualified Profile Evidence
```

Extensive Listening 不是闭环最后一步，而是贯穿全周期的独立主干。诊断—修复支线必须短、有退出条件，不能吞噬主干。

## 3. 各层职责：input、action、output、evidence、next step

| 层 | Input | Student action | Output | Evidence | Next step |
|---|---|---|---|---|---|
| 0. Readiness & validity | 设备/环境检查、材料暴露记录 | 确认耳机、无 transcript、是否练过 | 有效性上下文 | noise/familiarity flags | 无效则重试或不计证据 |
| 1. Extensive New Input | 相对可理解、此前未听过的多样音频 | 以意义为主连续听；极少量轻检查 | 输入分钟、完成度、主观理解 | 低推断性的 exposure/engagement | 继续输入；异常困难则调难度 |
| 2. Calibration / Exam | 定期 CET 或保留的新材料 | 在真实约束下听并作答 | A 类 test performance | 有效独立 attempt + 题型上下文 | 足够则回输入；失败进入有限采样 |
| 3. Continuous Baseline | 未提示的完整 Conversation/Passage | 第一遍连续原速；必要时 blind replay | Round 1 + recovery count | A 与 B 分开 | 快速通过或选句 probe |
| 4. Selective Sentence Probe | 从失败处抽取少量高信息句 | 首听/second listen；最多一个 probe | 局部 observation | lexical/acoustic/segmentation/relation 候选 | 继续或 queue Local Drill |
| 5. Local Drill | evidence-backed 目标 | 短、针对性练习；需要时延迟揭示文本 | 训练内表现 | 不独立，默认不支持能力增长 | 达标后 reintegration |
| 6. Reintegration | 已练过的原 Conversation/Passage | 无提示重听整体并完成意义任务 | 熟悉材料整合结果 | same-item integration | 进入未见过的 near transfer |
| 7. Near Transfer | 保留的新句/短段，含相似目标现象 | 无 transcript、正常声音完成任务 | C 类结果 | valid + independent + unseen + target-aligned | 通过则继续/等待 far；失败回训练假设 |
| 8. Far Transfer | 新主题、新说话人、新语篇正常流 | 以整体意义完成低污染任务 | D 类结果 | cross-material independent evidence | 多次跨材料后进入趋势候选 |
| 9. Longitudinal Reassessment | 隔日/隔周的新材料样本 | 在相近约束下复测 | E 类时间序列 | 重复、跨日期、跨材料 | Profile 更新或撤销假设 |

## 4. Transfer Model

### Level 0：Same-item recovery

材料已听过；包括 blind full replay、见过答案后的重听、Local Drill 内成功和 reintegration。价值是反馈、信心和整合，不是迁移。

允许表述：“第二遍恢复”“在熟悉材料中重新整合成功”。

### Level 1：Near transfer

必须是学生未听过的新句/短段，保留目标现象但改变表面内容。例如训练弱读/分词后，用不同词汇和说话人的新句测试；训练条件/转折关系后，用不同主题的新句验证关系理解。

最小资格：

- `evidence_valid=true`
- `independent_attempt=true`
- `familiar_item=false`
- `transfer_item=true`
- `transfer_distance=near`
- 对应 transcript 未在作答前暴露
- 内容 revision/hash 可追溯

一次成功只允许写“在一个 near-transfer item 上成功”。至少出现重复的、独立 near-transfer evidence，才允许“目标处理**可能正在改善**”。具体次数是待 pilot 校准的 product hypothesis。

### Level 2：Far transfer

新 Conversation/Passage 应改变主题、词汇表面、说话人/口音或语篇组织中的若干项，在正常连续语流中测整体意义。不能把只换一个名词的模板句称为 far transfer。

Far transfer 不必每次追问目标音变，因为过度聚焦会提示学生；它应使用稀疏、整体意义任务，检验修复是否在自然处理链中仍有价值。

### Level 3：Longitudinal transfer

跨日期、跨材料的 near/far 表现持续优于个人基线，并在相近难度与有效条件下复现。它才支持长期 Profile 的趋势性语言。即使达到此层，也应写“近期持续表现显示……”，不写永久能力定论。

## 5. Reintegration 与 Transfer 的硬隔离

| 特征 | Reintegration | Transfer |
|---|---|---|
| 材料 | 已训练的原材料 | 此前未听过的新材料 |
| 目的 | 局部修复能否回到整体 | 能否把处理能力带到新输入 |
| 熟悉度 | 高 | 低/无 |
| transcript 历史 | 可能已暴露 | 作答前不得暴露 |
| 可支持结论 | same-item integration | near/far transfer |
| Profile 权重 | 很低或不进入 | 满足有效性后可逐级进入 |

任何产品文案、API 字段、分析报表均不得把二者合并为 `post_training_success` 后直接推断能力改善。

## 6. Extensive Listening / Daily Input Model

### 6.1 定位

选择 **A + C：产品上是独立模块，教学上穿插整个体系。**

不与 Transfer 合并，理由是二者优化目标相反：

- Extensive Listening 追求大量、可理解、低负担、兴趣与持续性，测量应稀疏；
- Transfer 追求保留、未暴露、受控与可比较的证据，材料不能提前消费；
- 二者可以共享内容治理和难度模型，但 transfer holdout pool 必须隔离，避免材料熟悉污染证据。

### 6.2 设计原则

- 大量新材料，主题、说话人、语速与语篇类型逐步扩展；
- 难度应让学生能抓住主要意义，不能长期处在逐词崩溃状态；
- 不要求每段做题；可用一句自评、主旨选择或口头摘要的稀疏采样；
- 默认不显示 transcript；遇到困难可在结束后提供可关闭的 captions/transcript，但该材料后续不再算 independent transfer；
- 记录 exposure minutes、completion、支持方式和主观理解即可，不据“听完”生成能力诊断；
- 兴趣、可持续性和内容多样性优先于每分钟都生成标签。

### 6.3 难度逻辑

词汇覆盖研究可作为内容推荐参考，但不应用固定百分比替代真实理解。推荐器应综合：已知词汇估计、语速、口音、语篇长度、句法、主题知识、视觉支持与学生近期完成感。连续多段过难时先降难度或补词汇，不应默认增加 Sentence Lab 深度。

## 7. Vocabulary × Acoustic Mapping 分离

### 7.1 最小诊断协议

```text
未听懂目标表达
  └─ second listen（仍无文字）
       ├─ 成功：same-item recovery，通常结束
       └─ 失败：只选择一个 probe
            ├─ 文字义 probe 失败 → lexical observation
            ├─ 文字义通过 + 新声音识别失败 → acoustic/segmentation observation
            └─ 词识别通过 + 关系 probe 失败 → sentence-processing observation
```

系统不必每次从头跑三步。已有可靠文字词汇证据时可跳过文字义 probe；已有声学证据时可优先做关系 probe。Probe 的选择依据是预期信息增益，而不是页面完整度。

### 7.2 accommodation 示例

- 学生看到 `accommodation` 仍无法选择“住宿安排”：记录 lexical observation，路线为词义、搭配、语境和间隔复现。
- 学生能解释文字，但在未见过的新句中听不出：记录 provisional spoken-form observation，路线为音形映射、重音/弱化变体和多说话人新例。
- 学生能听出 `accommodation`，却误解谁安排、为谁安排或计划变化：记录 sentence/discourse observation，不进入单词听辨 drill。

这些都是可撤销 observation；单次结果不能升级为稳定 diagnosis。

## 8. Selective Sentence Probe Policy

Sentence 层的职责只有三项：

1. 确认失败是否在 second listen 后自然恢复；
2. 用最多一个 probe 区分最可能改变路线的两类解释；
3. 生成“继续 / 调整难度 / queue Local Drill”决定。

默认限制（均为待 pilot 验证的 product hypothesis）：

- 每段只抽 2–4 个高信息句，不全文逐句；
- 单句最多一次 second listen + 一个 probe；
- 达到时间/疲劳上限即停止，剩余问题不强行诊断；
- 首听正确快速通过；
- transcript 只在训练阶段、完成独立证据采样后出现；
- 全面对困难时优先判定“材料不合适/词汇基础不足”，而非生成大量局部标签。

## 9. Local Drill Model

Local Drill 不是“错题答案区间精听”，而是由证据授权的短修复单元：

| 路线 | 训练内容 | 结束条件 | 必接验证 |
|---|---|---|---|
| Lexical | 词义、常见搭配、语境辨义、声音与意义同时编码 | 文字义与听觉义均可用 | 新例句 near transfer |
| Acoustic mapping | 多说话人、多速度但自然的词/短语识别 | 无文字下在变化声音中识别 | 新句 near transfer |
| Segmentation | 词界、弱读、重音、连贯语流对比 | 不依赖 transcript 划分新 span | 新句/短段 near transfer |
| Sentence relation | 施受、否定、时序、条件、转折、指代、范围 | 能从新句构建正确命题 | 新关系句 near transfer |
| Discourse | 说话人、立场变化、因果、主旨与结构更新 | 在新短语篇中追踪稳定 | 新 Conversation far transfer |
| CET mapping | 选项释义映射、干扰类型、预览策略 | 内容理解与选项选择差距缩小 | CET-specific 新题，不进 general Profile |

若训练只在原句达标，状态为 `drill_completed`，不是 `skill_improved`。

## 10. Evidence Hierarchy 与结论权限

| Level | 证据 | 允许的结论 | Profile policy |
|---|---|---|---|
| E0 | 单次原始行为/答题 | “发生了 X” | 不进入能力 Profile |
| E1 | 有效的同材料观察或 recovery | “在此材料出现/恢复” | 仅学习记录 |
| E2 | 跨句重复 observation，但可能同材料/同次会话 | “形成待验证 hypothesis” | 可进入临时队列，不展示稳定结论 |
| E3 | 多个有效、独立 near-transfer items 上重复 | “可能存在/正在改善某目标处理” | provisional profile，可见范围和低/中置信 |
| E4 | 跨材料 far-transfer 中重复，排除明显噪音 | “该倾向在多个新材料中重复出现” | 可进入当前能力 Profile，仍可撤销 |
| E5 | 跨日期、跨材料、可比条件下持续 | “近期长期趋势支持……” | long-term Profile / trajectory |

具体语句权限：

- “可能存在 acoustic mapping difficulty”：至少 E2，且需证明文字词义可用、声音识别失败；只可作为 provisional hypothesis。
- “这一问题在多个新材料中重复出现”：至少 E4，必须有多个独立、未暴露材料，不能由同一 Conversation 的多句替代。
- 进入 long-term Profile：原则上 E5；E3/E4 可进入明确标注为 provisional/current 的区域，但不得伪装成长期稳定能力。

Profile 每项都应呈现 evidence scope、有效样本数、材料/日期跨度、最后更新时间、置信等级与反证；新证据不支持时必须可降级或移除。机器生成 hypothesis 不能成为 `teacher_verified`。

## 11. Noise Policy

### 11.1 有效性字段

候选 evidence 应携带：

```text
evidence_valid
invalid_reason
independent_attempt
familiar_item
transfer_item
transfer_distance
prior_exposure_count
transcript_exposed_before_attempt
audio_integrity
interruption_detected
content_revision
content_hash
```

### 11.2 判定规则

- 播放不完整、网络中断、设备异常：保留 telemetry，`evidence_valid=false`。
- 学生提前看 transcript：可作 scaffolded learning record，`independent_attempt=false`。
- 多次练过同一材料：`familiar_item=true`；只能作 review/reintegration。
- 随手点错：若学生立即纠正且行为模式支持，标记 uncertain/invalid，不反推“粗心型学生”。
- 走神：可由学生自报并使本条证据无效，不生成 attention diagnosis。
- prior exposure 不确定：记录 `unknown`；不能为方便而当作首次。
- Transfer pool 一旦提前暴露，即从 holdout 中退役。

## 12. Student Routing

### Route A：Continuous 3/3

```text
valid 3/3 → 记录 test/continuous performance
          → 不进入 Sentence Probe / Local Drill
          → 返回新材料输入
          → 按计划参加未来 far/longitudinal reassessment
```

Set1 可直接进入新的职场或非职场材料；Set2 可进入新的计划协商材料，但不能把高度模板化的改写句称为 far transfer。

### Route B：2/3，完整重听恢复

```text
2/3 → blind full replay → recovery
    → 记录 same-item recovery
    → 若无历史重复 evidence：继续新输入
    → 若相似 observation 已重复：一个选择性 probe
    → 有可行动 evidence 才 queue Local Drill
```

Local Drill 后先重听原 Conversation（reintegration），再使用新句做 near transfer。原文无论听得多好都不是 transfer。

### Route C：Continuous 差，多句失败

```text
先验有效性/材料难度检查
  → 抽 2–4 个高信息句
  → 每句最多一个 probe
  → 广泛 lexical failure：词汇支撑 + 降低新输入难度
  → 特定 acoustic/relation evidence：短 Local Drill
  → Reintegration
  → Near transfer
  → 保持可理解的 Extensive Listening 主干
```

不要求一次会话完成整棵树。若同一段耗时持续增长，应退出旧材料而不是把坚持误当成学习质量。

## 13. Profile Policy

Profile 分三层显示，而非一个确定性标签列表：

1. **Recent observations**：E0–E2，仅描述发生了什么及有效性，不称能力。
2. **Provisional patterns**：E3，有明确目标、证据范围和不确定性；可用于推荐但不可高权重固化。
3. **Cross-material trends**：E4–E5，跨材料/跨时间；允许进入长期趋势，但必须可更新、降级和删除。

以下永不单独进入 general listening Profile：CET option preview、单题正确/错误、same-item recovery、见 transcript 后的成绩、无效或熟悉材料、模型推断的 attention/working memory/processing speed。

Profile 的推荐逻辑也必须区分“需要更多证据”和“需要训练”；证据不足时优先采样，不应直接处方。

## 14. 20 / 40 / 60 分钟使用路径

下列比例是 **product hypothesis，不是 research fact**。研究支持泛听、针对性教学和元认知活动均有价值，但没有给出适用于 CET 中国大学生的一刀切分钟配方。

长期周平均建议：**新/未见音频 60%–80%，旧材料分析与修复 20%–40%**。基础薄弱者短期可接近 50:50，但不建议连续多周让新输入低于 40%。Transfer 属于新材料，但因测量要求较高，不能用全部 extensive input 充当 transfer。

### 每天 20 分钟

- 10–12 分钟：可理解的新材料泛听；
- 3–5 分钟：Continuous/CET 或 near transfer，按日轮换；
- 3–5 分钟：只有有 evidence 时做一个 Local Drill 或 reintegration；
- 0–2 分钟：简短计划/反思，不做长问卷。

不要求每天同时完成 CET、probe、drill 和 far transfer。每周 1–2 次 CET 校准即可，其余日把时间还给新输入。

### 每天 40 分钟

- 18–22 分钟：Extensive Listening 新材料；
- 6–8 分钟：CET/Continuous baseline（非每日可轮换）；
- 6–10 分钟：选择性 probe + Local Drill；
- 4–6 分钟：reintegration 或 near transfer；
- far transfer 可每周集中一次替换上述一段。

### 每天 60 分钟

- 25–32 分钟：多样的新材料泛听；
- 8–12 分钟：CET/Continuous；
- 10–15 分钟：证据支持的 intensive/Local Drill；
- 5 分钟：reintegration；
- 8–10 分钟：near/far transfer（按计划轮换）。

当日没有可行动 evidence 时，不为填满 60 分钟而制造 drill；把时间转给难度合适的新材料。高强度 Sentence/Drill 不宜连续占据整段会话。

## 15. Review Model

Review 应拆为两类队列：

- **Spaced Reintegration Queue**：隔日/隔周重听旧材料，检查保持与整合；标熟悉，不算 transfer。
- **Independent Reassessment Queue**：从 holdout pool 抽取新材料，按 near/far 定义产生可比较证据；完成后材料退役为 familiar。

旧材料复习可以帮助巩固，但 Profile 结论必须主要由第二类和纵向数据驱动。

## 16. 未来 V2.3 / V2.4 / V2.5 映射建议

版本号应代表能力包，不机械对应现有页面名。以下只是产品排序提案，须先验收教学模型。

### V2.3：Evidence Foundation + Input Volume MVP

- 明确五类 outcome 与 validity/familiarity/independence 语义；
- 建立 transfer holdout 内容治理原则；
- 上线低诊断负担的 Daily/Extensive Listening MVP；
- 仅做 selective Sentence Probe pilot，不做全文逐句治疗；
- 继续 `profile_eligible=false`，先验证分流和耗时。

理由：若先做重 Sentence Lab，系统会在缺少新输入和迁移证据时进一步强化旧材料过拟合。

### V2.4：Evidence-backed Repair + Reintegration + Near Transfer

- 按六类问题建立 Local Drill 入口证据；
- 每个 drill 都有明确退出条件；
- 原材料 reintegration 独立命名；
- 建立未暴露新句/短段 near-transfer pilot；
- 校准 probe 数量、疲劳、难度和重复证据阈值。

### V2.5：Far Transfer + Longitudinal Profile

- 建立跨主题/说话人/语篇的 far-transfer benchmark；
- 引入 spaced independent reassessment；
- 只有经过验证的 E3–E5 证据进入分层 Profile；
- 对 CET-specific 与 general listening Profile 完全分轨；
- 评估数周/月的真实增长，而非单次 session completion。

如果内容供给、teacher verification 或 holdout 池不足，版本应延后相应能力，不得用重复真题假装 transfer。

## 17. 验收指标

未来 pilot 不应只验收页面完成率和测试通过数，还应观察：

- 每周新音频分钟数及其占比；
- 学生在旧材料上的平均分析耗时与疲劳/退出；
- Probe 是否真正改变了 route，而不是增加步骤；
- 各 Local Drill 的 evidence-backed 比例；
- recovery、reintegration、near、far 是否在数据和文案中零混用；
- transcript 暴露后 evidence 是否正确降级；
- transfer pool 是否保持未暴露；
- Profile 中每条结论是否能追溯到有效、跨材料、跨日期 evidence；
- CET 分数与 independent listening measures 是否分别报告；
- 低水平学生是否获得更可理解的输入，而不是更长的失败树。

## 18. 仍待产品/教学确认的决策

1. 是否接受“B：重排顺序”作为总审计结论。
2. 是否接受 Extensive Listening 先于重型 Sentence Lab 进入下一能力包。
3. Sentence Probe 每段 2–4 句及单句一个 probe 的 pilot 上限。
4. Near/Far transfer 的材料距离、保留池和退役规则。
5. E3/E4/E5 的样本数与时间跨度如何通过 pilot 校准，而非拍脑袋固定。
6. CET-specific Profile 是否完全独立，或只保留为考试准备统计。
7. V2.0b/Pilot 内容未 teacher verified 时，哪些只可用于内部研究。
8. CET-4 内容尚不存在时，未来模型验证是否先限定 CET-6。
9. 新材料的版权、来源、难度标注与教师审核资源。
10. 纵向有效性研究采用何种独立 outcome measure，避免只用产品内同类题自证。

在这些决策完成前，不应把本模型直接翻译成 V2.3 页面或数据库设计。

