# CET-6 听力系统独立审核与 Claude 续接报告

日期：2026-09-05。项目：`D:\kimi-workspace\english-ai`。审查基线：`main@f064dcd19a3cedaefa144ee6781cbfee2db857c2`。

本报告按用户最新要求，优先回应 `PROMPT_for_GPT6_Review.md` 和 `CET6_Listening_System_Summary_for_Review.docx`，同时保留项目全过程与接手后的提交审计，供 Claude 恢复上下文。仅生成/更新交接文档，未修改业务代码、配置或数据，未修复缺陷，未启动 V2.3。

## 阅读结论

“近期先把两套真题上的既有学习体验跑通，暂缓 V2.3 新素材扩展”是合理的工程优先级。现有训练可以继续保留；当前最需要完成的是端到端闭环、数据来源一致性、测试可信度和学习结果表述的校准。

不能据送审稿认定系统已整体工程验收通过。仓库确有大量已实现功能，但存在明确集成断点；文档把部分“代码已提交”写成“已建成可用”，把一组后端测试写成“全量”，并把若干局部修复写成完整保证。V2.2 历史 Pilot 的验收结论仍应保留，但不能覆盖后来添加的功能或证明当前 HEAD 全部可用。

| 审核维度 | 判断 | 核心理由 |
|---|---|---|
| 教学方法学 | 【有隐患】 | 训练方向可保留；听前教词一律有害、同材料盲测证明真正听懂等表述过强 |
| 数据语义 | 【严重问题】 | 原则合理；当前重封工件之间有文本漂移，未来账本设计也未形成完整历史证据模型 |
| 工程与安全 | 【严重问题】 | 现有前端类型检查失败，Pacing 提交接口错误，身份与结果暴露边界仍有缺口 |
| 范围与优先级 | 【通过】 | 先修通两套材料上的已有路径合理；验收目标应限定为学习体验和工程可靠性 |
| V2.3 未来设计 | 【有隐患】 | 独立子系统方向合理，身份、幂等、媒体等价与历史版本设计仍需补齐，继续暂缓编码 |

### 证据边界

本次读取了送审 Word 的正文和表格文本、审查 Prompt、此前三轮用户规格要求、仓库文档、代码、Git 历史及实际 SQLite 状态，并做了只读类型检查与数据对照。Word 的版式不在本次验收范围。研究依据使用下面各节所链接的论文原始出版页、期刊全文和研究综合；这不是穷尽所有 SLA 文献的系统综述。

报告明确区分三类信息：本次直接核验的事实；提交说明/历史报告中的声明；基于代码的风险推断。没有重新运行成功的后端测试，不计为本次通过。Git 作者账号也不被当作某个 AI 模型的身份证明。

## 第一部分 分维度对抗式审核

### 1 教学方法学 【有隐患】

#### 1.1 精听四件套可以保留，但分别测到什么必须讲清楚

| 活动 | 可以支持的学习/观察 | 不能直接证明 | 建议 |
|---|---|---|---|
| 句级听写/微听写 | 在指定音频条件下的声音识别、分词和拼写表现 | 单凭错字不能区分听辨、拼写、键盘输入或记忆负担；答对不能证明整体理解 | 分开记录声音识别与拼写误差，允许低书写负担的意义检查 |
| 意群排序 | 语块与句子关系加工 | 若先给全部文字，可能主要测阅读和重组 | 标注有无文字支架，保留返回完整语流的环节 |
| 改写理解 | 意义等价判断、句子关系理解 | 阅读选项做对不等于裸听处理提高 | 明确任务输入模态、提示和材料熟悉度 |
| 干扰项辨析 | CET 选项映射、排除与考试策略 | General Listening 全局能力 | 放入 CET Track，统计和文案与一般听力分开 |
| 同材料 blind retest | 去除当前屏幕支架后的恢复或保持 | 材料未见、独立迁移、整体听力增长 | 使用 same-item recovery/retention 标签，必要时另做延迟复测 |

过程导向听力教学有实证支持，但这不等于本项目的四组件组合、顺序和参数已被验证。Vandergrift 与 Tafaghodtari 的学期研究支持引导计划、监控、评价等过程的教学；它不能证明本项目任意一次听写或 blind retest 就构成能力提高。[研究原始出版页](https://onlinelibrary.wiley.com/doi/abs/10.1111/j.1467-9922.2009.00559.x)

送审稿 §4.1 的“盲测……验证是否真的听懂”建议改为：“观察学生在已熟悉材料上、撤去当前文本支架后的表现；不据此宣称迁移或整体能力提高。”学生已经看过答案/原文，即使现在隐藏文字，记忆条件也没有消失。

#### 1.2 Chang & Read 2006 不能支持一律禁止听前教词

送审稿 §1.2 把“禁止听前预教当篇生词”写成教学硬裁决，并援引 Chang & Read 2006。该研究比较四类听力支持，在其研究条件下词汇教学帮助最小。这个结果不足以推广为“任何听前词汇教学都会造成固着或损害学习”。[Chang & Read 2006](https://onlinelibrary.wiley.com/doi/abs/10.2307/40264527)

另一个直接研究中，两种词汇预备活动组的听力测验表现均优于无准备组；这说明效果依赖任务和实施方式，至少不能把普遍有害视为定论。[Mihara 2015](https://tesl-ej.org/wordpress/issues/volume19/ej74/ej74a3/)

建议采用两条清楚的规则：

- 进行未辅助、独立听力测量时，不提前教本篇答案相关词汇，并记录支持条件。
- 进行学习时，可以在需要时提供词汇、字幕或原文支架；这些尝试标为 supported/familiar，不冒充独立测量。

一般词汇学习、主题知识和事先看过同一材料也应区分。学过一个通用词，并不自动污染所有含这个词的新材料；定向预教保留测验的答案线索才需要特别治理。

#### 1.3 Transcript 的问题是证据条件，不是它本身有害

字幕研究综合发现字幕对听力理解和词汇学习有积极作用，同时效果受测验类型影响。其研究对象主要是带字幕视频，不能直接替本项目规定唯一最优的原文揭示顺序。[Montero Perez 等 2013](https://doi.org/10.1016/j.system.2013.07.013)

“首轮测量前隐藏文本、尝试后可选揭示”可以作为当前默认；学生已经整体听不动时，不应为了保住所谓干净证据而让其反复挫败。允许退出测量、进入辅助学习，并诚实降低证据结论权限。

同样，学生稍后揭示原文，不应抹掉此前确实独立完成的历史首答。应冻结首答发生时的条件，另记 reveal 时间，限制后续尝试。不能用一个可变布尔值把过去、现在、未来三种状态混成一团。

#### 1.4 听觉词汇与 SRS 的方向可保留，参数不应被视为研究阈值

代码中的入口阈值 0.70、Phase 0 上限 21 天、每日 10/15 分钟、40 题抽样均属于产品参数。目前未找到其所引用的 `FINAL_CET_LISTENING_MASTER_PLAN.md`，也未发现针对这些阈值的校准报告。

尤其不建议在尚无验证时把词汇入口测验变成“未达标不得听完整材料”的长期教学规则。可以推荐短时词汇练习，同时允许适合难度的整段听力。当前实际训练使用浏览器 Speech Synthesis；固定 TTS 声音/变速任务成功，不等于在多说话人自然语流中也能识别。

长期新输入仍有教学价值，但本轮不必先造内容平台。意义导向输入的词汇学习研究支持输入的价值，也显示学习量和条件存在差异；不能把听过多少分钟转成能力增长百分比。[Webb 等 2023 研究综合](https://www.cambridge.org/core/journals/language-teaching/article/how-effective-is-second-language-incidental-vocabulary-learning-a-metaanalysis/E38E3468FD2090B1FA3051051DE8E70C)

**本项处置建议：**保留训练资产；改正过强研究解释和 blind retest 文案；用选择性训练与返回完整语流替代每题必做四件套。没有证据支持把整个组合称为伪科学，也没有证据支持称其为已验证的长期提效方案。

### 2 数据语义 【严重问题】

#### 2.1 Exposure 与 Evidence 分离原则通过，实现仍待完成

Pure exposure 只证明接触；meaning check/probe 才有可解释任务表现；同材料 recovery、reintegration 与新材料 transfer 分离。这些是合理的证据治理原则。

但它们主要存在于 V2.3 规格与设计中。当前仓库没有 V2.3 ledger/service/API/表，不能把未来设计写成当前全系统已经具备的保护。Legacy、词汇、Stem、V2.1 和 V2.2 也尚未共享完整的跨模式 exposure 治理。

#### 2.2 当前重封存在工件不同步

`49c0cf0` 修改了两套 legacy JSON、两套 V2 candidate 和 baseline；同时声明另四个 artifact 的 hash 未变。本次重算清单六项，全部匹配。这只能证明文件与清单一致。

直接反例：

- 当前 Set2 candidate 的 Q2B：`There are few warm places to go at this time of the year.`
- 同一封印清单中的 Set2 payload preview：`There are few warm places to go to at this time of the year.`

证据文件：`backend/listening/data/v2_full/cet6_202606_set2.candidate.json:925` 与 `backend/listening/data/v2_full/payload_preview/cet6_202606_set2.exam_payload.json:97`。

`machine_precheck_full.json` 仍保留重建前的候选文本与旧生成时间，payload assertion/preview 也未随此次候选重建同步更新。送审稿的“全维度终审、零真实内容差异”因而不能解释为当前所有派生工件完全一致。本文没有重新逐页进行整套 PDF 真人终审，也不认定某一次 OCR 修正必然错误。

重封说明引用的 `extract2.py`、`clean.py` 未在项目中找到；所指 `_audit_scripts/v2c_assemble.py` 在该提交主要是换行改写。后续应提交可复现的抽取/清洗入口，明确文本规范化和 hash 算法版本，重新生成 precheck、preview、assertion，再封印。只更新候选文件 hash 不足以完成这条证据链。

当前 Set1/Set2 transcript segments 为 69/75，共 144；旧接管报告的 69/74 是旧基线数字。数量变化必须与 revision 和对应报告一起解释。

#### 2.3 媒体 hash 不能单独充当全部熟悉度规则

同一音频换题、修改难度不能重新 unseen，这一原则正确。还需处理：同一录音转 MP3/WAV、重编码、音量变化、裁掉静音或切成片段后，文件字节 hash 会变化，但学习内容可能仍熟悉。

建议分离不可变录音身份、音频文件 hash、派生来源/区间和题目版本。对母音频与片段建立来源关系；未知等价关系保守标记，不能“hash 不同即新材料”。这是当前设计的风险推断，需要验收用例，不是本轮声称已发现在线绕过。

只按 subject–item 退役也不够：同一实质录音复制为另一个 item 后，熟悉度和 holdout eligibility 必须继承。物理分目录能防误放文件，不能自动防重复录音跨池。

#### 2.4 历史事实需要尝试级快照

当前 V2.3 DDL 把 ledger 设计为同一主体/项/媒体的可更新聚合行，却没有完整 exposure event/attempt 层。若下一次听同一材料时覆盖 task_revision，过去究竟用哪版题就可能无法还原。

`v3_evidence.exposure_ref` 是 TEXT，ledger 却没有对应单一 ID 或明确复合外键；evidence 仍用通用 content_revision/content_hash，未完整保存规格要求的 media/task/transcript/annotation/metadata 版本。Probe 也缺少与具体 attempt/evidence 的完整绑定。

建议以后采用不可变 exposure/attempt event + 派生聚合状态；每条 evidence 引用具体尝试及当时版本，不能只依赖当前 ledger。此次仅提出设计问题，暂不创建任何表。

### 3 工程与安全 【严重问题】

#### 3.1 K1 的已修范围与尚未解决的承诺

`cbc78fc` 去掉直接 `round1_correct` 后，`754f36a` 又去掉与题目同序的 `observations[]/checks[]` 旁路；当前 `_final_result()` 使用维度曝光次数，不带逐题对错。对这一具体最终结果旁路，静态核对确认修复已落实。

但 `session_state()` 的 `check_round_2` 明确只把 Round 1 错题放入 `round2_checks`，包含 check_id 和题面。客户端据此就知道首轮哪些题错了。因此：

- “最终结果不再通过并行数组泄漏逐题对错”：有代码依据。
- “整个生命周期任何端点都无法知道哪题错”：不成立。
- “重听之前不揭示错题答案/原文/答案位置”：是另一条较窄的承诺，不能与上一条混用。

这首先是产品要求与状态机设计的冲突。若允许完整盲重听后定向重答，应明确该时点允许获知重答题集合；若全程禁止知道错题集合，就不能只给错题。本文没有替用户改变被冻结的 Round 2 规则。

还需控制多会话反复试答结合总分的差分推断；即使只给总分，开放无限低成本重复测验也不能承诺答案绝对不可推知。目前未做在线攻击实测。

#### 3.2 K2 是部分缓解，不是授权体系

事件 payload 已有按事件类型的字段白名单；event 写入也检查请求 student_id 与 session owner 一致。但 ID 仍由客户端声明，V2.2 页面还是 `anonymous`。State/Round1/Round2 也未呈现一致的服务端 owner 授权校验。

同机单人、仅本地预览时风险相对有限；一旦局域网或多学生共用，就不能依赖难猜 session_id。身份问题不必等待 V2.3 才被承认：可以在多主体 Pilot 前单独排入经授权的安全修复，或者继续维持明确的单用户隔离边界。

当前事件白名单主要控制键；对允许字段的值还需要类型、枚举和长度限制。例如 focus_type 不能只是任意字符串，position_ms 应受范围和类型约束。客户端心跳能检测部分异常，但不能证明人确实听了，更不能推断注意力或工作记忆。

#### 3.3 K3 仍不能标成全系统历史快照已解决

`ba91f27` 给 V2.2 manifest 补了 question/options/dimension，Round 2 使用快照并检测删题，修复有实际价值。

残余包括：V2.1 的 attempt_answers 没有完成 candidate revision/hash 历史绑定；V2.2 `_final_result()` 仍从当前 material 取 dimension，因此维度变更或删题会影响旧会话摘要。正确状态应是“V2.2 重答题面 pin 已加固，其他历史还原边界待处理”。

#### 3.4 K6/K9 已加固，但发布门控仍有边界

`76c1d36` 已给既有 V2.1 attempt 的 events 写入、answers、submit 补 gate，并使摘要 release metadata 读取 baseline。已有 attempt 的 in-progress/events 读取路径并非全都具有同样 gate，文档不宜笼统写“全端点”。

当前 baseline `student_release_allowed=false`，本次检查进程和 backend/.env 的预览开关均未设置，V2.1/V2.2 实际 gate 关闭；V2.2 `profile_eligible=false`，Profile 不读取 cp_*。

另一个治理风险是 V2.2 直接复用 V2.0b gate：将来仅放开 V2.0b 就可能一起放出仍为 generated_unverified 的 V2.2 checks。Legacy 与新增 D–H API 也不是统一由这个 gate 保护。必须明确哪些内容/路由被发布闸门覆盖。

#### 3.5 “已建成”功能中的可定位断点

| 模块 | 当前证据 | 后果与建议 |
|---|---|---|
| Strict Pacing | `StrictPacingPlayer.vue:353` 附近发送 POST `/attempts/{id}/answers`；后端实际只有 PUT `/attempts/{id}/answers/{question_id}`；逐题响应未检查 | 按当前代码答案无法正常保存，后续仍可能提交空卷；先修真实请求链并验答案落库与得分 |
| V2.2 Harvest | `ListeningPracticeV2View.vue:242`、245 读取 bundle.transcript；DTO 类型与后端都不提供它 | 类型检查失败、采词面板无正文；不能直接往盲听 bundle 塞 transcript，应先裁定独立的后置学习入口 |
| Aural Lexicon | 页面用 `aq_student_id`，其他相关页面使用共享的 `aq_listening_student_id`；V2.2 又是 anonymous | 词汇、采词、Dashboard 数据分属不同主体；先统一身份与现有记录处理策略 |
| Lexicon 初始化 | 实际 DB 的 lex_items 为 0，种子 JSON 虽有 182 条但无自动初始化；入口测试无题 | 新用户学习链无法完成；增加明确、受控的开发初始化/空库存行为验收 |
| Stem Bank | 练习 DTO 已有正确 question_type；只提交题型时 predict 已返回 correct_answer；前端分两次请求，后端两次 INSERT | 提前暴露、重复统计；拆清阶段可见字段和一次任务的记录语义 |
| Stem/Dashboard 统计 | type_accuracy 按学生预测类型分组；两次 INSERT 增加计数 | 不能直接称“各真实题型准确率”；修统计定义并验证真实用户路径 |
| Phase 0 | status 返回 exam_practice_allowed，但核心考试服务不依此阻断；入口正确率/阈值由客户端上报 | 当前门禁与测量均不可信；先确定它是建议还是强制政策，避免直接强化未验证的教学限制 |

Strict Pacing 目前只有 Set2 的 25 个窗口数据；Set1 API 返回 404。送审稿对两种音源的分析不等于“两套都已具备可用 Pacing”。这里应明确可用范围。

Stem Bank 数据还有与修正后正式题库漂移的迹象。后续必须把该派生库加入同一内容版本核验，不能只校验 v2_full。

#### 3.6 测试数字与本次验证

送审稿所列 18+22+16+13+17+24+14 确实等于 124，但只覆盖 7 个测试文件。仓库另有 Phase 4.1–7.7 的 7 个文件、40 个测试方法；本次静态计数为 14 文件、164 个 test_* 方法。方法数量不是本次 pytest 实跑结果，不应写“164/164 通过”。

本次可重复的前端检查：

```powershell
cd D:\kimi-workspace\english-ai\frontend
npm exec vue-tsc -- --noEmit --project tsconfig.app.json
```

实际失败，5 个错误：StrictPacingPlayer 的 onMounted/watch 未使用；listeningApi 的 LexItem 未使用；PracticeView 两处 transcript 类型不存在。项目 build 脚本为 `vue-tsc -b && vite build`，当前应用类型检查未通过。

直接 `vue-tsc --noEmit` 返回 0 的结果不能用作证据：根 tsconfig 的 files 为空，通过 references 指向 app/node，前一命令没有实际检查应用项目。这纠正了此前简版交接中的“前端检查通过”口径。

本次后端无法复跑：系统 Python 缺 pytest/FastAPI 等依赖，backend/venv 指向已不存在的 Kimi runtime。当前 requirements 已修正 httpx 拼写并加入 pytest，但 main.py 还导入未列出的 python-dotenv/openai，且强依赖 DEEPSEEK_API_KEY。干净环境安装清单后能否启动完整应用，尚不能认定。

更严重的是测试质量：`test_e2e_flow.py` 的存答案步骤容忍 404，随后只检查 score 是整数。这不能证明前端答题闭环。`test_v21_exam.py` 的 K6 用例又使用全局 repository 创建 k6_test，实际 ignored DB 有该残留，说明至少这条测试存在隔离问题。再次回归前应先在临时 DB 中测试，不能把测试当作生产/开发数据写入脚本。

### 4 范围与优先级 【通过】

近期先在两套真题上完成工程闭环，合理且比继续增加模块更可验收。建议下一工作包暂称“两套真题现有流程落地验收”，无需提前赋予 V2.3 版本号。

建议顺序如下；这是一份待授权执行清单，本次未实现。

1. 固定当前提交、隔离测试数据库，恢复可运行环境；真实类型检查通过。
2. 修复 Pacing 保存与提交、统一学生身份、明确词库初始化/空状态、修 Stem 阶段泄漏与重复统计。
3. 同步 candidate、precheck、preview、assertion、Stem 等派生数据，补可复现脚本与 hash 规范，保持 student_release_allowed=false。
4. 选择一条已知支持的主路径实跑：Set2 普通考试 → 提交 → 复盘 → 按需一项训练 → 同材料无文本重测 → 采词 → SRS → Dashboard。核对网络、DB、恢复状态和显示结果。
5. 单独验 V2.2 的封闭开发预览；决定 Harvest 是暂不提供还是后置独立学习入口，先保持 First Pass/盲重听的现有训练约束。
6. 在代表性路径通过后覆盖两套/各 Unit，验证音频边界、题面与答案来源。Pacing 若仍只支持 Set2，就明确显示这一范围。
7. 以真实使用反馈确认是否存在值得补的局部学习缺口。不要在已有闭环尚未跑通时直接加全文逐句长流程。

高价值、低成本项包括：完成后的继续/退出路径，刷新恢复，音频中断重试，空库存状态，错字与听辨错的区别，明确“熟悉材料重测”文案，以及一份附网络/DB 证据的端到端验收记录。

只有两套材料时，可以验学习体验、流程可靠性和同材料表现；无法单靠反复使用它们有力证明跨主题、跨说话人、跨时间的整体听力增长。将两套中的部分材料留给尚未暴露的主体可以支持有限内部探索，但换题、切句或重编码不能制造新的独立语料。

### 5 V2.3 未来设计 【有隐患】

独立 router/service/表/DTO 和独立 gate 的方向可行；不必现在编码。当前工程草案还不适合直接照抄建表。

| 设计问题 | 具体原因 | 将来设计验收条件 |
|---|---|---|
| 并发分配 | 文档称主键保证不重复分配，但 allocate 明确只查询、不预留 | 区分分配预留和实际暴露，明确并发同主体分配规则；预留不能算已听 |
| 事件幂等 | ledger 的 upsert 不能防重复 audio_started 请求反复增加 exposure_count | 以 session/event id 定义幂等，事务绑定 exposure 与退役 |
| 文本-only 暴露 | unseen 写成“无 ledger 或 exposure_started=0” | 即使未播放，只要原文已看也必须 familiar/失去对应 holdout 资格 |
| 状态命名 | completed_familiar 同时表示完整听完和任何一秒暴露 | familiarity 与 completion 分开建模 |
| 历史证据 | evidence_ref 无明确 FK，聚合 ledger 不能还原历次题版 | 不可变 attempt/event、完整版本快照和可追溯引用 |
| 媒体等价 | 同音频换编码/切片或复制 item 可穿透简单 hash/目录规则 | 来源关系、跨 item 熟悉度继承及保守处理未知关系 |
| Cookie 身份 | HttpOnly 只阻止脚本读取，不能单独证明主体真伪；清 cookie 又可成为新主体 | 服务端不可伪造 token、全端点 owner 校验、适当 cookie/CSRF 配置；明确 Pilot 身份重置边界 |
| 音频/文本资源 | 分配接口白名单不能约束独立音频/原文 URL | 所有资源访问同样执行 pool/release/owner/阶段约束；holdout 不向普通列表或静态目录泄漏 |
| 独立 release 来源 | 有环境开关名，独立内容放行事实来源不够具体 | 规定 V2.3 自己的 release manifest 和按内容审核条件，不能借 V2.0b 一起放行 |
| 冻结边界 | 设计要求扩展共享 repo、接入 main；冻结文件此前也有硬化和 Harvest 修改 | 明确“允许装配、禁止行为回归”，建立新的后硬化基线；独立文件不自动保证隔离 |

当前没有 V2.3 页面、API、v3_* 表或 fixture。Near/Far pool 的设计验证也不等于已开展有效迁移测量。继续暂缓外部素材和 V2.3 编码符合最新优先级。

## 第二部分 模型分配建议

以下按能力档位分工，不对未实测的具体型号做排名。标准是错误的后果、可验证性以及需要多少跨文件判断。

| 工作类型 | 建议模型档位 | 原因与验收边界 |
|---|---|---|
| 教学法/数据语义裁决 | 顶配推理模型，关键教学结论有人审 | 误把 recovery 当 improvement 会污染后续全部设计；必须核原始来源与反例 |
| 安全审计/对抗式复审 | 顶配推理模型，尽量独立于实现上下文 | K1 的跨字段旁路证明仅按键名检查不够；需结合全生命周期和真实请求验证 |
| 按确定规格实现局部代码 | 中档工程模型 | 适合修明确接口、组件状态和类型错误；身份/事务/泄漏边界交强模型复核 |
| 跨层集成与疑难修复 | 高档或顶配推理模型 | 路由、DTO、主体身份、DB、前端可能各自正确而组合错误 |
| 跑测试/收集日志/计数/比对 hash | 轻量模型或确定性脚本 | 规则明确时可机械执行；不得让执行模型自行把失败/404 改成可接受 |
| OCR 清洗/批量内容修订 | 轻量做候选与差异表；强模型审歧义，教师确认正式内容 | 批量统一表面很容易改错语义；machine 不能把自己的视觉判断升级为 teacher_verified |
| 文档撰写/规格整理 | 中档模型 | 按事实清单整理足够；涉及权限、能力结论或架构裁决仍由强模型审 |
| V2.3 这类架构设计 | 顶配推理模型 + 独立复审 | 身份/版本/污染/幂等一旦设计错，会让以后长期证据不可恢复；当前暂缓 |

升级信号：需求互相冲突、跨模块状态不一致、出现第二次修复、测试与真实界面矛盾、涉及身份/内容历史/能力结论时，升级到最强档并找反例。可安全降级的条件：规格明确、影响局部、结果能由独立脚本或真实行为验收，且执行者无权降低验收标准。

不要以“用了强模型”替代教师核验，也不要让同一个模型同时修改数据、重新定义验收口径并宣布通过。

## 盲区与待确认事项

这些问题影响下一次实现授权；不妨碍本轮审查完成。

1. **Pilot 到底是单人本机，还是多学生/局域网？** 这决定身份隔离需立即修复还是可暂按单用户边界处理。请提供实际访问范围，不需要任何密钥。
2. **V2.2 的错题集合何时允许知道？** 当前 Round 2 只出错题，无法与“任何阶段不得知道哪题错”同时成立。需要明确接受的阶段边界。
3. **原先 WO A–H 的原始批准规格在哪里？** 服务引用的总规划文件未找到。需补原工单或已批准要求，避免把实现细节当产品裁决。
4. **“零真实内容差异”由谁、在何版本上确认？** 需要可复现脚本、核验记录和 review actor；目前 baseline 仍写无 teacher verification。模型看 PDF 不能改称真人审核。
5. **内容权利的项目记录是否齐全？** 按用户送审材料的“自有版权”作为当前工作前提，不作相反断言；正式发布时仍需能追溯素材来源、授权范围和记录。此次不做法律判断。
6. **K4/K5/K10 的裁决是否已经得到用户确认？** Word 将 248960ms、全对直通、CET-6 范围写作已决策；代码支持前两项的现状，但仓库不能单独证明每项的批准过程。
7. **冻结是否允许定点纠错？** 当前 HEAD 已包括冻结后的安全修复和不兼容 Harvest。建议另设“现有功能落地修复”的明确边界与新验收基线，再由用户授权执行。
8. **如何定义这次成功？** 建议是两套材料的明确路径能操作、可恢复、数据可追溯、不会过度声称。不要要求用两套熟悉真题证明长期整体能力提升。

## 附录 A 项目的完整来龙去脉

### A1 从写作网站到 listening legacy

最初项目是 Vue/FastAPI 的英语自习室网站，已有写作批改，听力为占位。2026-08-19 一天内按 Phase 逐步增加题库、考试/练习、行为采集、复盘、训练、Profile、表达迁移及真实语料工具。后续版本不是把 legacy 删除后重建，而是多个路径并存、共享 router/repository/SQLite。

| 日期 | Commit | 阶段与实际加入内容 |
|---|---|---|
| 08-19 | 2f4dddc | Phase 0：导入原网站，作文批改与听力占位 |
| 08-19 | 7e1c303 | Phase 1：两套 CET-6 结构化 JSON/音频、API、套题列表与考试页 |
| 08-19 | 0a00cc9 | Phase 2：考试/练习模式、attempt、行为事件、断点续答 |
| 08-19 | dc5c950 | Phase 3：逐题复盘、五级提示、retry、自诊断与掌握度流转 |
| 08-19 | 6dfb3e3 | Phase 4：听写/语块/改写/干扰项训练、blind retest、错题本 |
| 08-19 | af304e9 | Phase 4.1：诊断 revision、训练 provenance、证据链加固与测试 |
| 08-19 | 5a80f35 | Phase 5A：规则化 Profile 证据引擎 |
| 08-19 | de55736 | Phase 5B：Profile UI、推荐卡片、证据回链 |
| 08-19 | f152004 | Phase 6：Expression Bridge，31 表达/62 场景及 TTS 资产 |
| 08-19 | f64ea7b | Phase 6.1：跨语境证据规则、教师审核/编辑/音频再生成 |
| 08-19 | 8c63117 | Phase 7：Corpus ingestion、许可 gate、ASR、切分、匹配、教师页面 |
| 08-20 | 5ab5bd3 | 教师改 transcript 联动 teacher_edited，保留 raw、重组 cleaned text |
| 08-20 | feee689 | Phase 7.5：语料来源、许可风险与自建录音策略文档 |
| 08-20 | 64b6a5d | Phase 7.6：AMI seed 工具、标签、10 张 task cards、录音授权草案 |
| 08-20 | 75ec174 | Phase 7.7：content/metadata revision 分离、授权链、教师匹配、录音工具包 |
| 08-21 | bd6cea8 | 酒店角色卡 Version B，纯文档 |
| 08-29 | fdc9c23 | 一次封入 V2.0b 数据、V2.1 Exam、V2.2 Continuous Practice 及验收包 |

其中“14 approved clips”等历史运行结果来自提交说明/报告；Git 不跟踪运行数据库，不能由提交本身证明这些记录在每台机器存在。

### A2 V2.0b 到 V2.2 的重建意义

V2.0b 解决题面/原文恢复与审核语义，建立 candidate、precheck、payload preview 和 baseline。当前是两套 CET-6、每套 25 题/7 Units，仍 machine_prechecked，未 teacher_verified，未学生发布。

V2.1 把试卷恢复成英文 A/B/C/D、audio_only 题干、一个 Unit 3–4 题同时可见；卷面不提前给答案、原文、中文或 evidence，音频与题号不做时间联动。专用 V2 ID 与 legacy 隔离。

V2.2 在两段 Conversation 1 上做 Continuous Practice：intro → option_preview → first_pass → round1 → blind_full_replay → round2 → result_final。首遍原速、无暂停/seek/replay 控件；中断无效并可完整重开；Round 1 全对有直通结果例外；二次成功仅为 recovery，Profile 不接收 cp_*。

`fdc9c23` 是 104 文件的大封版。Git 没有独立的 V2.0/V2.1 提交节点，不应伪造更细开发日期。验收标记 ENGINEERING_PILOT_ACCEPTED 仅为当时工程 Pilot，不是内容教师认证或正式发布。

### A3 用户随后主动调整教学路线

最初下一步曾叫“V2.3 Sentence Lab 全文逐句训练”。用户随后暂停设计和编码，要求审查“是否促进长期真实听力而不仅仅做对 CET”。形成学习模型 Audit 和 V1。

下一轮用户接受核心原则，并要求 V1.1 Calibration 和 V2.3 Minimal MVP：CET/general 分轨；新输入为长期训练主干；Sentence Lab 变为 selective probe；三池分离；recovery/reintegration/drill completion 均不等于 transfer；Profile 依赖跨材料、跨时间证据。

第三轮用户明确 V1.1 通过、MVP 总体方向通过，但仍禁止编码；要求 Data Semantics Hardening：exposure/evidence 分离、媒体/题目/标注版本分离、global/subject 状态分离、8–12 个小 Pilot fixtures、真实播放即污染 holdout、pilot_subject_id 最低身份。输出只到 READY_FOR_V2_3_ENGINEERING_DESIGN。

这些内容对应 `docs/V2_LISTENING_LEARNING_MODEL_AUDIT.md`、`V2_LISTENING_LEARNING_MODEL_V1.md`、`V2_LISTENING_LEARNING_MODEL_V1_1.md` 和 `V2_3_MINIMAL_MVP_SPEC.md`。本地文件时间集中在 08-30，09-04 才统一入 Git；文件时间只能辅助理解，不能替代提交历史。

最新 09-05 Word 总结又明确近期优先“两套真题精听体验落地”，V2.3 外部素材暂缓。用户在本次对话要求优先该 Word/Prompt，因此本报告按这一近期方向审核，保留此前教学原则和 V2.3 未来设计。

### A4 Claude 接手后留下的 12 个提交

原基线及之前 17 个提交作者为 ql3035-spec；之后 12 个为 CET Dev。结合用户说明，以下作为“Claude 接手期”审计；Git 没有 Claude/Anthropic 签名，不能认定每行内容都由 Claude 原创。例如 920b19e 是收编此前 Codex 文档。

| 日期时间 北京时间 | Commit | 实际工作 | 当前审查结论 |
|---|---|---|---|
| 09-04 05:49 | 49c0cf0 | transcript/OCR 修订、legacy 回填、两套 candidate 与 baseline 重封 | 有实际修订；派生 precheck/preview 不同步，重封未证明整条证据链一致 |
| 09-04 05:50 | 9450e30 | WO D–H 后端：lexicon/Stem/Dashboard 服务、7 张表、15 个端点、数据与测试 | 原型已实现；117/117 是提交声明 |
| 09-04 05:50 | ce90050 | WO D–H 前端：4 页面、6 组件、API/types/路由与 Harvest 集成 | 真实集成有断点，当前类型检查失败 |
| 09-04 05:50 | 920b19e | 收编接管审计、学习模型 Audit/V1/V1.1、V2.3 MVP spec | 文档归档，不是 V2.3 实现 |
| 09-04 05:51 | 2462b71 | 忽略备份、DB journal、两份环境交接草稿 | 改善 Git 清单；ignored 文件仍真实存在 |
| 09-04 05:56 | cbc78fc | K1 删除直接 round1_correct | 首修，随后发现旁路并深修 |
| 09-04 06:02 | f8cef7c | K2 event payload 字段白名单、event owner 绑定 | 部分缓解，非真实身份/全端点授权 |
| 09-04 06:08 | ba91f27 | K3 V2.2 题面/options/dimension snapshot、删题漂移检测 | 重答 pin 有效；全系统/最终维度历史仍不完整 |
| 09-04 22:39 | 754f36a | K1 并行数组旁路修复，显式 raise，旧 manifest 防护 | 最终结果旁路修复已落地；全生命周期承诺另需裁定 |
| 09-04 22:55 | 9fe1eb6 | httpx2 更正为 httpx，补 pytest/timeout | 123/123 为当时子集声明；当前环境失效 |
| 09-04 23:14 | 76c1d36 | K6 既有 V2.1 attempt 写入 gate；K9 metadata 读 baseline | 修复已提交；新 K6 测试存在 DB 隔离问题 |
| 09-05 00:53 | f064dcd | V2.3 engineering design 草案 | 只新增 300 行设计文档，明确非编码授权 |

忽略换行/空白后，fdc9c23..HEAD 为 49 个文件实质变化，而原始 diff 显示 73 个文件。9450e30 中 training_service/v2_practice_service 仅换行变化；真正的 V2.2 行为影响来自后续安全修复与前端 Harvest。不要把大段 EOL 重写当作大量新实现。

### A5 环境工作留下的痕迹

根目录还有 ignored 的 `修复沙盒_交接Codex.md` 和 `迁移WSL2_清空C盘_交接Codex.md`，记录 Claude 桌面沙盒对 junction 的限制、C/D 盘数据布局和 WSL2 迁移计划。它们是操作计划/历史说明，不证明迁移与清理已完成。本次没有执行里面任何命令，也没有审查整个电脑的应用状态。

## 附录 B 当前架构 路由 API 数据与测试索引

### B1 架构与 legacy

前端为 Vue 3/TypeScript/Vite；后端 FastAPI；听力统一 router 与 repository，JSON 内容和 SQLite 行为数据并存。main.py 同时保留写作批改，对 DeepSeek key 和写作 SDK 的导入耦合仍在。

三主轨为 legacy exams、V2.1 v2_full、V2.2 v2_practice/cp_*；另有 Expression/Corpus、Lexicon/Stem/Pacing/Dashboard。旧复盘、四种训练、Profile、Expression Bridge、教师审核与语料工具均还在，不是 V2.3 新功能。

### B2 当前注册路由

| 类别 | 路由 |
|---|---|
| 基础 | `/`、`/writing`、`/listening` |
| V2 | `/listening/v2/exams/:examId`、`/listening/v2/practice/:materialId` |
| Legacy 学生 | `/listening/exams/:examId`、`/listening/review/:attemptId`、`/listening/mistakes`、`/listening/profile` |
| 表达/语料 | `/listening/corpus`、`/listening/expressions`、`/listening/expressions/:expressionId` |
| 接手期新增 | `/listening/lexicon`、`/listening/pacing/:examId`、`/listening/stem-bank`、`/listening/dashboard` |
| 教师 | `/listening/teacher/expressions` 及 `/:expressionId`，`/listening/teacher/corpus` 及 `/:assetId` |

共 20 条注册路由；注册存在不等于当前已发布或页面可用。无 V2.3 路由。

### B3 Backend API

听力前缀 `/api/listening`，router 中当前 82 个 HTTP route decorators。Legacy 考试/attempt/复盘/训练/Profile、表达、教师 Expression/Corpus、学生 clips 保留。

V2.1：GET `/v2/exams`、`/v2/exams/{exam_id}/paper`、`/v2/exams/{exam_id}/audio`；attempt create/save/events/submit 复用通用接口。

V2.2：GET `/v2/practice/materials`、`/v2/practice/materials/{material_id}`、其 `/audio`；POST `/v2/practice/sessions`；GET `/v2/practice/sessions/find`、`/v2/practice/sessions/{session_id}`；POST session 的 `/events`、`/round1`、`/round2`。

新增 15 个 D–H 接口：

- Lexicon：POST `/lexicon/seed`；GET `/lexicon/session`、`/lexicon/phase0/status`、`/lexicon/phase0/entry-test`；POST `/lexicon/phase0/entry-test/complete`、`/lexicon/phase0/complete`、`/lexicon/attempt`。
- Harvest：GET `/lexicon/items`；POST `/lexicon/harvest`。
- Pacing：GET `/exams/{exam_id}/pacing`。
- Stem：GET `/stem-bank/stems`、`/stem-bank/session`、`/stem-bank/stats`；POST `/stem-bank/predict`。
- Dashboard：GET `/dashboard`。

### B4 实际 SQLite 状态

`backend/listening/data/listening.db` 被 Git ignore；本次只读计数如下。`listening_dev.db` 为 0 byte 遗留文件，不能用它判断实际学习数据。

| 表 | 行数 | 所属功能 |
|---|---:|---|
| attempts | 5 | Legacy/V2.1；含 k6_test 测试残留 |
| attempt_answers | 52 | 作答 |
| behavior_events | 185 | 行为 |
| diagnoses | 1 | 旧自诊断/标签 |
| training_results | 1 | 旧训练 |
| expression_attempts | 0 | 表达迁移 |
| corpus_assets | 2 | 语料资产 |
| corpus_clips | 45 | 15 approved、30 pending_teacher |
| cp_sessions / cp_responses / cp_events | 各 0 | V2.2 |
| lex_items / lex_audio_assets / lex_srs / lex_attempts | 各 0 | 词汇 |
| phase0_state / phase0_test_attempts | 各 0 | 词汇 Phase 0 |
| stem_predictions | 0 | 题型预测 |

共 18 张业务表。没有 v3_* 表。空表不证明功能完全没跑过，也不等于验收失败；但不能把当前 DB 当作已有完整用户链路的证据。

### B5 测试方法静态清单

| 文件 | test_* 方法数 |
|---|---:|
| test_aural_lexicon.py | 18 |
| test_e2e_flow.py | 17 |
| test_harvest_d3.py | 16 |
| test_pacing.py | 13 |
| test_stem_bank_dashboard.py | 22 |
| test_v21_exam.py | 14 |
| test_v22_practice.py | 24 |
| test_phase41_evidence_chain.py | 5 |
| test_phase50_profile.py | 7 |
| test_phase60_expression_bridge.py | 5 |
| test_phase61_transfer.py | 6 |
| test_phase70_corpus.py | 6 |
| test_phase76_seed_corpus.py | 6 |
| test_phase77_recording_pilot.py | 5 |
| 合计 | 164 |

历史 71/71 对应旧 baseline；接手期 117/123/124 的口径与文件集合不同。今后验收必须附 commit、命令、测试收集清单、隔离 DB 和结果，不能仅给总数。

### B6 可复用资产

可以复用统一 fetch 错误处理、白名单 DTO 思路、区间播放器基础、registry、独立 session/response/event 模式、corpus 许可与版本治理模式。复用前应评估当前缺口。

四种 legacy 训练组件可用于当前两套材料的学习修复，但不能未经评审直接继承“错题 → 答案证据句 → 精听”定位路径；学生定位失败仍不得被自动告知答案区间。RangePlayer 是 V2.2 固定区间连续播放组件，送审稿把它称为“卡壳分段重听”并不准确，不能当成已完成自由句级训练的证明。

将来 V2.3 不能直接把 Lexicon、Stem、同材料训练或旧 Profile 的结果灌入独立 transfer evidence。当前 Profile 不读 cp_*，但 V2.1 submitted attempt 仍可能进入 Profile 的总 attempt 计数；应区分计数污染与正式能力证据流入。

## 附录 C 给 Claude 的直接续接说明

请从当前 `main@f064dcd` 接手，先读本报告与用户最新送审 Word/Prompt，再按需读对应代码。不要 reset 回 fdc9c23；原 baseline 存在且为当前 HEAD 祖先，仓库共 29 提交、无 tag/remote/upstream。

当前近期主轨是“两套 CET-6 真题上的已有学习流程落地”，V2.3 暂缓。已有教学模型原则继续有效：CET/general 分轨；observation≠diagnosis；same-item recovery≠transfer；machine≠teacher_verified；不推断 working memory/attention/processing speed；正式 Profile 不接收 V2.2 evidence。

先承认现状：WO D–H 已有代码，但未获得本次端到端验收；当前前端有 5 个类型错误，Pacing 提交接口错误、学生 ID 分裂、词库未初始化、Stem 阶段与统计存在缺陷。V2.0b 重封六项 hash 自洽，但派生报告/preview 不同步。后端当前环境不可复跑，“124/124 全量绿”不可沿用。

本轮用户授权的是审核和交接文档。下一轮若用户要求修复，按第一部分 §4 的顺序定点实现、临时 DB 回归、真实页面验收；不得自行启动 V2.3、抓取新素材、搭建全文逐句长流程、开放学生 gate 或升级 teacher/profile 状态。

提交验收记录至少包含：commit、环境、操作路径、网络请求与答案落库证据、刷新恢复结果、内容版本/来源、测试集合与结果、剩余已知问题。不要把源代码存在、接口返回 200 或测试打印了勾号当作学习链路完成。

### 本报告与旧文档的关系

`CODEX_PROJECT_HANDOFF_AUDIT.md` 是 08-30、fdc9c23 的历史快照，保留不改写。`docs/CLAUDE_CONTINUATION_HANDOFF_2026-09-05.md` 是此前简版；本报告补入新附件优先级、真实类型检查结果、D–H 断点、派生数据漂移与完整时间线，当前续接以本报告为准。

工作树在本轮文档写入前只有此前简版交接未跟踪；本报告及文档标记也尚未提交。未作任何 Git commit。Git clean/dirty 应带观察时点，送审稿当时“0 未提交”不用于描述本轮新增文档后的状态。
