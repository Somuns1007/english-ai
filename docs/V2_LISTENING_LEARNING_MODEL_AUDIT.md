# V2 Listening Learning Model Audit

状态：教学架构审计稿，不是开发规格  
日期：2026-08-30  
审计对象：当前 `Exam → Continuous Practice → Sentence Lab → Local Drill → Review → Profile` 规划  
边界：不修改 V2.1、V2.2、V2.2.1；不把本文视为 V2.3 开工授权

## 0. 审计结论

**明确选择：B．现有规划顺序需要调整。**

同时，调整顺序必然伴随部分模块重新定义，但主判断不是“仅补功能”，也不是“全部推倒重来”。现有 Exam、Continuous Practice、事件记录、内容 revision/hash、release/profile gate 和 observation ≠ diagnosis 原则均有保留价值；根本缺口在于它们尚未组成“新材料输入—有限定位—针对性修复—重新整合—独立迁移—跨时间复测”的学习闭环。

当前规划最容易优化的是**少量熟悉真题上的表现**，而不是证明学生在陌生英语中的实时处理能力持续提高。若把 Sentence Lab 和 Local Drill 直接串成所有学生的必经路径，会放大以下问题：

- 新音频输入量过低，分析旧材料占比过高；
- 同一句重听、见过 transcript 后的成功被误写为能力改善；
- CET 选项处理和一般听力处理混为一谈；
- 单次错误被过度归因于词汇、连读、注意或记忆；
- 缺少独立的新材料 transfer test，Profile 没有足够强的证据来源。

因此，Sentence Lab 不应天然等于 V2.3，也不应是 Continuous Practice 后的固定长流程。它应被缩减为**选择性句子采样与低成本定位层**；Local Drill 是证据支持后的修复层；Reintegration 和 Transfer 必须分开；Extensive Listening 应成为持续存在的输入主干。

## 1. 审计依据与当前事实

本审计复核了 `CODEX_PROJECT_HANDOFF_AUDIT.md` 及以下冻结材料：

- `V2.2_Continuous_Practice_设计稿.md`
- `V2.2_Pilot_Acceptance_Report.md`
- `V2.2_Pilot_Acceptance_Supplement.md`
- `V2.2_Pilot_Independent_Review_Pack.md`
- `V2.2_Pilot_Checks_内容稿.md`

当前可信事实是：V2.0b 只有机器预检，V2.1 Exam Reconstruction 已完成，V2.2 Continuous Practice 达到 `ENGINEERING_PILOT_ACCEPTED`；`student_release_allowed=false`，`profile_eligible=false`，V2.3 尚未编码。V2.2 的 3 道 continuous checks 主要测 speaker relationship、change/attitude、final position/scope、main situation、initial-vs-final decision、attitude target 等整体理解，不是句子级听辨诊断。

V2.2 的安全边界是正确的：第一遍连续原速、不暂停/拖动/重播；Round 1 后只做 blind full replay；不揭示答案、transcript 或答案位置；第二遍答对只称 `recovery`；不据此推断 processing speed、attention 或 working memory；不进入 Profile。

但工程验收不能替代教学有效性证明。71/71 backend tests 证明状态机和既定约束得到较好执行，不证明学生经过数周后能更好地听懂陌生材料。

## 2. 五类结果必须永久分开

| 类型 | 可观察结果 | 可以支持的最低限度表述 | 不能支持的表述 |
|---|---|---|---|
| A. Test performance | CET 题做对 | “本次、此题、此测试格式下答对” | “真实英语都能听懂” |
| B. Same-item recovery | 熟悉材料重听后答对/复述 | “在增加一次输入与内容熟悉度后恢复” | “底层能力已提高” |
| C. Near transfer | 未听过的新句，含相似声音/词汇/结构现象，处理成功 | “目标处理可能正在改善” | “广泛听力流利度已形成” |
| D. Far transfer | 未听过、不同主题/说话人/语篇的连续材料仍能理解 | “改善可跨材料出现” | “长期稳定” |
| E. Long-term fluency growth | 跨日期、跨材料、正常连续语流表现持续改善 | “当前证据支持长期趋势” | 永久、不可逆的能力标签 |

其中 B 不是 C，Reintegration 也不是 C。学生已经知道内容时，重新听原 Conversation 只证明能否把修复过的局部重新放回已知整体。

## 3. CET 做题与真正听懂英语

CET 正确率是有价值但混合了多个构念的指标：语言理解、信息保持、题目格式、选项预览、干扰项辨别、时间压力和偶然作答共同决定结果。多项选择听力测试的表现会受到题目/选项呈现方式影响；因此，考试分数不能被当作纯粹的 general listening ability。[Yanagawa & Green (2008)](https://doi.org/10.1016/j.system.2007.12.003) 的实验显示不同 preview 格式会改变得分，并提示 lexical matching 等 test-method 效应；[Wu (1998)](https://doi.org/10.1177/026553229801500102) 同样把结果视为 listening ability 与 test method 的共同产物。

二者关系不是“无关”，而是：

- 底层 spoken-word recognition、句法语义整合、语篇建构越好，通常越有利于 CET；
- CET 特定的题型熟悉、选项映射和干扰项识别也能提高正确率；
- 因而 CET 提分可能来自一般能力、考试技能或二者混合，必须用独立任务拆分。

**Option Preview 应定义为 CET-specific test-taking skill。**它可以训练预判信息类别、快速比较选项、降低考试流程负荷，但不能写入 general listening Profile。V2.2 当前“不评分、不进 Profile”是正确边界。

## 4. 底层 listening processing 的合理拆分

听力不是单一能力。产品至少要区分：

1. **Lexical knowledge**：看到词形是否知道常用义、搭配和语境义。
2. **Spoken-form / acoustic mapping**：已知词义能否从真实声音变体激活词项。
3. **Segmentation / connected speech**：能否从连续语流中划分词界、处理弱读、同化、省音和重音线索。
4. **Sentence relation processing**：词已识别后，能否整合否定、指代、时序、条件、转折、施受关系和修饰范围。
5. **Discourse processing**：能否跨句追踪说话人立场、变化、因果、主旨、信息结构与关键细节。
6. **CET option mapping / distractor control**：能否把理解映射到考试选项并避开词面匹配、偷换对象或时序的干扰。

spoken-word recognition 是把语流单位与心理词汇中的词项匹配，并不是“耳朵是否灵”这样单一原因；连续语流分词需要多种声学、音系、词汇和语境线索。[Sheppard & Butler (2019)](https://doi.org/10.1016/j.system.2019.102150) 直接讨论了 aural decoding 与 comprehension 的区分；[In’nami et al. (2022)](https://doi.org/10.1075/bpa.13.08inn) 汇总 118 项研究后发现，语言知识（尤其词汇和语法）与 L2 listening 的关系总体强于工作记忆、元认知等认知/情感变量。这支持“先区分语言知识与声音映射”，也反对仅凭一次错误推断 working memory 或 attention。

## 5. Vocabulary × Listening：不能把 accommodation 都归因于“没听清”

学生没听懂 `accommodation` 至少有三种路径：

- 看到文字仍不知道意思：lexical knowledge evidence；
- 看到文字知道意思，但在未经提示的真实声音中认不出来：spoken-form/acoustic mapping evidence；
- 词都能认出，却没整合出“谁为谁安排住宿、计划后来如何变化”：sentence/discourse evidence。

词汇覆盖与理解呈连续关系，不是一个机械阈值。[van Zeeland & Schmitt (2013)](https://doi.org/10.1093/applin/ams074) 在受控叙事材料中发现，90% 覆盖下许多学习者已有一定理解，但个体差异大；95% 时表现更稳定。该研究不能推出“所有材料达到 95% 就一定可理解”，更不能把 95% 作为学生 release gate。背景知识、文本类型、任务和词汇深度仍会改变表现。

低成本 Probe 可以按顺序只问一个最有信息量的问题：

1. 先在无 transcript 情况下 second listen；若成功，只记 same-item recovery。
2. 若仍失败，系统基于已有信息只选一个 probe：
   - **文字义 probe**：显示目标词/短语，要求选择语境义；失败支持 lexical observation。
   - **声音—词形 probe**：学生已证明认识文字时，播放不暴露答案位置的短语或新例句，选择听到的已知词；失败支持 acoustic/segmentation observation。
   - **关系 probe**：学生已识别关键词时，询问谁做什么、否定/转折/时序或同义关系；失败支持 sentence relation observation。
3. Probe 后结束现场诊断：快速继续，或把 evidence-backed 项目排入 Local Drill。

不是每个错句都跑完整诊断树。只有某一步的答案会改变后续训练选择时，probe 才有信息价值。

## 6. 研究依据及其边界

### 6.1 有较一致支持的方向

- **过程与元认知教学**：Vandergrift & Tafaghodtari 的一学期准实验中，接受预测、监控、评价和问题解决循环的组在控制初始差异后优于对照组，较弱学习者收益更明显。[Language Learning, 2010](https://doi.org/10.1111/j.1467-9922.2009.00559.x)。这支持适量的计划—监控—反思，不支持把每段音频变成长问卷。
- **语言知识是核心相关因素**：118 项研究的 meta-analysis 显示 L2 listening 与其组成因素总体为中等相关，词汇/语法等语言知识关系更强。[In’nami et al., 2022](https://doi.org/10.1075/bpa.13.08inn)。相关不等于因果，也不能据单次表现诊断个体。
- **显式语音特征训练可以改善被训练的知觉类别**：17 项研究的 meta-analysis 对超音段特征教学报告较大正效应，但结果首先适用于被测语音类别，不能自动外推到整段陌生语篇。[Gordon & Darcy, 2019](https://doi.org/10.1016/j.system.2019.04.007)。
- **字幕可支持当下理解与词汇学习**：18 项研究的 meta-analysis 报告 captions 对 listening comprehension 与 vocabulary learning 的总体大效应，且测试类型调节 listening 效应。[Montero Perez et al., 2013](https://doi.org/10.1016/j.system.2013.07.013)。这支持把 transcript/captions 作为阶段性脚手架，不支持从一开始永久展示，也不证明无字幕 transfer。
- **泛听有积极但仍有限的实证**：Chang & Millett 的项目显示 supported extensive listening 可促进 listening fluency，但此领域研究规模与情境仍有限。[ELT Journal, 2014](https://doi.org/10.1093/elt/cct052)；[RELC Journal, 2016](https://doi.org/10.1177/0033688216631175)。它足以支持建立输入主干，不足以规定精确分钟比例。

### 6.2 必须谨慎解释的方向

- **Repeated listening**：第二遍通常会提升同一材料的得分和理解，因为熟悉度增加、焦虑下降、注意资源得到释放；这正是 recovery 有价值的原因。但它同时污染独立性，因此不得作为 transfer。关于重复能否产生远迁移，证据远弱于同材料即时收益。
- **Captions / transcript**：整体上有帮助，但结果会受任务与测试方式影响。学生在有文字条件下答对，只能证明“有脚手架时理解”；产品必须另测无文字的新材料，才能谈 auditory transfer。
- **Vocabulary coverage**：90%、95%、98% 是研究条件下的描述性参考，不是普适悬崖。产品可用其估算可理解度，却不应显示伪精准的“覆盖率达到 X 即适合”。
- **Metacognitive instruction**：积极结果并不意味着策略训练越多越好。策略说明占用大量时间、减少实际输入时，可能反过来损害练习密度。
- **Extensive listening**：方向合理，但现有研究常受样本、教师情境、材料支持方式和测量任务限制；最佳剂量未知。
- **Transfer**：L2 listening 研究没有为本产品提供一个已验证的三层阈值。Near/Far 分层是基于学习迁移逻辑的产品证据设计，具体通过标准必须由后续 pilot 校准，标为 product hypothesis。

对 2000–2022 年 System 听力研究的综合回顾也强调该领域受瞬时输入、连贯语音、个体差异与任务特征共同影响，支持多层处理模型而非单因果标签。[Goh (2022)](https://doi.org/10.1016/j.system.2022.102970)

## 7. 现有模块逐项评价

| 模块 | 真正训练/测量 | 不能证明及主要风险 | 审计处置 |
|---|---|---|---|
| Exam | CET 约束下的连续听、信息选择、答题流程；测 test performance | 单次正确不能证明自然听力；受猜测和题型影响 | 保留，作为低频校准与 CET 专项，不做每日主干 |
| Option Preview | 选项结构扫描、预测信息类别、干扰项预警 | 不能证明 general listening；可能诱发词面匹配 | 保留但明确标为 CET-specific；不进 Profile |
| Continuous Practice | 第一遍整体理解、无控制连续输入；第二遍 recovery | 3/3 不等于底层无问题；第二遍成功不是 transfer；错题不直接定位原因 | 保留，作为未提示 baseline 与分流入口，不强制接 Sentence Lab |
| Sentence Lab | 应只做少量句子的 second listen、一个高信息 probe、证据采样 | 重流程会压低输入量、制造 transcript 依赖、过拟合原句和疲劳 | 重新定义为 selective probe layer；有上限、可跳过，不现场完成治疗 |
| Local Drill | 针对已证实的词汇、声音映射、分词、关系、语篇或 CET 映射做短修复 | 单个错题不足以授权；同句成功不能证明迁移 | 保留并重构入口；必须 evidence-backed，之后必接 reintegration 与新材料验证 |
| Review | 间隔复现历史材料、复核修复是否保持 | 复习旧材料仍有熟悉度；不能替代 transfer | 分成 spaced reintegration 与 independent reassessment；前者不进迁移证据 |
| Profile | 汇总跨材料、跨时间倾向，决定建议 | 最易把 observation 固化成伪诊断；模型不能自称 teacher_verified | 保留但延后；只有高层有效证据进入，显示置信度、范围和可撤销性 |

## 8. Sentence Lab 的最小职责

建议采用以下上限原则：

```text
首听正确 → 快速通过（必要时仅做极少量质量抽样）
首听失败 → second listen → 最多一个高信息量 probe
                                  ├─ 证据不足：继续新输入
                                  └─ 有可行动证据：queue to Local Drill
```

Sentence Lab 不负责：遍历全文每句、一次性完成病因树、当场把每句练到全对、为学生贴稳定能力标签、把 transcript 当默认界面。每段 Conversation 只抽取少量高价值句；若失败广泛，优先判断材料过难或词汇覆盖不足，而不是生成几十个局部 drill。

Transcript 只能在 blind attempts 与必要 probe 之后作为修复脚手架出现。见过 transcript 的后续成绩必须标记 `transcript_exposed_before_attempt=true`，不得作为独立 auditory evidence。

## 9. Local Drill 的证据门槛

| Drill 类型 | 允许进入所需证据 | 不足证据示例 |
|---|---|---|
| Lexical knowledge | 音频失败后，文字义/语境义 probe 也失败；最好在不同语境再现 | 只因 CET 题错 |
| Spoken-form / acoustic mapping | 文字义已通过；无文字听辨失败；在目标词或新例句中复现更强 | 看 transcript 后说“原来是这个词” |
| Segmentation / connected speech | 单词分开可认，连续 span 边界/弱读辨识失败；最好跨两个新例 | 一次没听到就称“连读不好” |
| Sentence relation | 关键词识别通过，但施受、否定、条件、转折、时序/指代 probe 失败 | 只记住某个词但题错 |
| Discourse tracking / retention | 多个句子级处理基本通过，但在有效、独立的整段新材料中反复丢失主旨/变化/说话人；先排除噪音 | 一次走神或耳机中断 |
| CET option mapping / distractor | 对内容的非选择题/释义理解通过，但在 CET 选项映射中反复被特定干扰项吸引 | 听力本身未验证就归因“粗心” |

“最好”“反复”的具体次数须经 pilot 校准；当前不能伪造精确阈值。

## 10. 当前体系的主要缺口

### 10.1 缺少真正的 Transfer Layer

当前 V2.2 只有同材料 blind replay 与 recovery。它对教学有用，但没有新材料，因此不能验证 near/far transfer。任何 Local Drill 若没有独立 transfer，都只能报告“训练项目内表现改善”。

### 10.2 缺少持续的新材料输入主干

Exam、句子分析和 Local Drill 都是高交互、低音频量活动。若占据大部分时间，学生会形成“分析能力很强、实时语流经验很少”的结构性失衡。长期 fluency 需要大量相对可理解的新语音与意义映射经验；不是每段都应做题或诊断。

### 10.3 缺少 Reintegration 与 Transfer 的语义隔离

训练后重听原文应保留，因为它检验局部修复能否放回整体；但必须命名为 reintegration，并在数据层与 unseen transfer 分开。

### 10.4 缺少证据有效性与熟悉度语义

现有 revision/hash 原则有价值，但学习证据还需要标记是否独立、是否熟悉、是否提前看文本、是否遭遇中断/设备问题，以及是否为 transfer item。

### 10.5 Profile 目前没有足够强的上游证据

V2.2 `profile_eligible=false` 是正确的。若未来直接把 Sentence Lab/Local Drill 结果接入 legacy Profile，会把被提示、熟悉材料和训练内成功混为长期能力。Profile 必须等待跨新材料、跨日期证据。

## 11. Noise 与有效性审计

建议未来每条候选证据至少具备以下语义；本文不要求本轮建表：

| 字段 | 含义 |
|---|---|
| `evidence_valid` | 是否可用于能力推断；不是“数据是否成功写入” |
| `invalid_reason` | interruption / device / environment / accidental_click / integrity / identity 等 |
| `independent_attempt` | 在无答案、无 transcript、无等价提示下完成 |
| `familiar_item` | 此人是否已听过或练过该内容 |
| `transfer_item` | 是否为专门保留、此前未暴露的新材料 |
| `transfer_distance` | none / near / far |
| `prior_exposure_count` | 已知暴露次数；未知应为 unknown，不能默认 0 |
| `transcript_exposed_before_attempt` | 此次作答前是否看过对应文字 |
| `audio_integrity` | 音频是否完整、速度正常、无异常断点 |
| `interruption_detected` | 页面、网络、播放或设备中断 |
| `response_revision/content_hash` | 行为绑定的内容版本 |

`evidence_valid=false` 的记录仍可用于产品故障分析，但不得进入学习推断。学生自报走神也不能反推稳定 attention weakness。

## 12. 两个真实 Pilot 的分流模拟

以下分流同时适用于 Set1 Conversation 1（职场访谈）和 Set2 Conversation 1（周年旅行/住宿计划）；具体句子只作为例子，不把当前机器预检内容视为教师确认素材。

### 学生 A：Round 1 为 3/3

- 记录 A 类 test/continuous performance：本次整体理解 checks 全对。
- 不强制 Sentence Lab，不进入 Local Drill。
- 下一步优先听一段难度相近的新材料；可把它作为普通 extensive input，或在定期校准时作为 far-transfer-like reassessment。
- 只有极低比例质量抽样可检查是否靠选项猜中，但不能让每个全对者再走重流程。

### 学生 B：Round 1 为 2/3，blind full replay 后恢复

- 结果只叫 same-item recovery。
- 不显示错题答案位置，不直接切答案区间。
- 可结束本段并继续新输入；若该错误与历史有效 observation 重复，才抽取一条相关句做 second listen + 一个 probe。
- Probe 有可行动证据时排入 Local Drill；修复后先 reintegrate 原 Conversation，再用未听过的相似句做 near transfer。
- 未经过新句验证，不得写“能力提升”。

### 学生 C：Continuous 很差，Sentence Lab 多句失败

- 先核验播放完整性、熟悉度、环境与 transcript 暴露，排除无效证据。
- 不把整段 8/12 个 segments 全部送入诊断树；最多抽 2–4 条高信息句。
- 若文字义 probe 广泛失败，主要路线应是词汇支撑 + 更可理解的新输入，而不是大量 connected-speech drill。
- 若文字认识但新语音中识别失败，建立 provisional acoustic/segmentation observations，再排入相应 Local Drill。
- 若词句级成功但整体变化/立场仍反复丢失，才考虑 discourse tracking 训练。
- 修复后 reintegrate 原文；near transfer 仍失败则保持局部 hypothesis，不升级 Profile；同时降低 extensive material 难度，维持输入量。

结论：**不是所有学生都必须走 `Continuous → Sentence Lab → Local Drill`。**A 应快速离开旧材料，B 多数情况下也可继续，C 才需要受限采样与分流。

## 13. 风险优先级

### P0：若不处理将产生错误产品结论

- 将 recovery、reintegration 或有 transcript 的成绩写成 listening ability improved；
- Local Drill 完成后没有 unseen transfer；
- 单次错误直接进入长期 Profile；
- 把 Option Preview 当 general listening；
- 未标 familiar/independent/noise 的数据参与诊断。

### P1：会限制长期学习价值

- Sentence Lab 默认全文逐句、无耗时上限；
- 新材料输入低于旧材料分析，且长期持续；
- 内容难度远超学生词汇/句法基础，却继续做声学微诊断；
- transcript 出现过早或永久显示；
- CET 真题成为唯一材料域，无法测试跨主题/说话人迁移。

### P2：需要通过 pilot 校准

- Sentence 抽样数量、probe 触发阈值；
- near/far transfer 的通过标准和间隔；
- extensive material 的可理解度估计；
- 20/40/60 分钟方案中的比例；
- Profile 升级所需的最少跨材料/跨日期证据。

## 14. 最终判断及原因

选择 **B：现有规划顺序需要调整**，原因如下：

1. 现有顺序是线性漏斗，容易让每个学生在同一旧材料上越走越深；真实学习应允许全对者快速回到新输入、轻度失败者直接继续、只有证据充分者进入修复。
2. Transfer 不能放在 Review/Profile 的隐含位置，必须成为 Local Drill 后的显式验证层。
3. Extensive Listening 不是流程末尾奖励，而是整个系统持续存在的主干。
4. Sentence Lab 应从“全文逐句训练”重新定义为“选择性定位与分流”；完整治疗移到 Local Drill。
5. Review 必须拆分熟悉材料的 spaced reintegration 与独立新材料 reassessment。
6. Profile 必须位于长期证据之后，不能接收 test performance、same-item recovery 或无效 observation 的直接推断。

这不是 D，因为现有工程资产和约束可以复用；也不是 A，因为仅补一个 Transfer 页面或泛听页面不能修复证据语义和强制线性路径。下一阶段应先接受新的学习模型，再决定版本号和页面，而不是先宣布 V2.3 = Sentence Lab。

