# Set2 听后词汇表达与难句学习稿

日期：2026-09-10。状态：内部教学内容草稿，待审核；不等于 teacher_verified 或允许发布。

## 使用范围与来源

本稿覆盖当前网站第2套7个单元，优先作为后续学习闭环试点的内容基础。使用用户 Word 的“结合语境解释”思路，但当前材料不是 Word 中的食堂等材料，不直接搬用其中词条和题目对应关系。

- V2 exam_id：`cet6_202606_set2_v2`。
- 来源：`backend/listening/data/v2_full/cet6_202606_set2.candidate.json`，`units[].transcript.cleaned_text`。
- 源文件 SHA256：`d344f8f960f711990f9999f2b22689f69c468ab2bc7691c4734fcfe840df6f39`；各单元 transcript revision 为2。
- 源音频：`audio/cet6_202606_set2.m4a`。本稿未听核音频，不提供假定切片时间戳、逐词音标或实际连读判定。
- 共42个词汇表达、14个难句练习，覆盖7单元；是重点学习稿，不是全文逐句校对完成的成品。
- 当前只有 U1 在 Continuous Practice Pilot 中有材料定义；U2—U7 的逐段盲听、检测题、边界与解锁需另行审核，不把本稿当作7个已可运行的 CP 单元。
- source 目前 `machine_prechecked` 且有 `internal_annotation_only` 标志；Set2 是拟优先训练材料，不等于本稿可以直接公开。所有展示须先解决来源许可、内容审核与 release 条件。

## 学习卡与复习卡的区别

学习卡默认显示本句义、音频和一个关键提醒；搭配、新编例句、句子结构按需展开。复习卡默认先播声音，不先显示词面、中文或语义分类。学生尝试后揭示，记录“这次识别／仍需复习”，不生成听力能力分数。

表中原文锚点用于内部核对，不可在盲听前展示。新编例句及任务是教学创作，不是原文、官方试题或独立 transfer evidence。同词或同句的新 TTS 音频仍是熟悉内容。所有难句的提问和释义也只在后置学习阶段使用。

## U1 结婚纪念日旅行计划

来源：`cet6_202606_set2_u1`；transcript hash：`34fb929e01028be7521ed94731b8fb47a83bcf97c50d1480775af65449f81a14`。

内部主线：男士计划旅行，住宿难订，女士提出分段住宿建议；随后讨论一项可能不适合同行者的活动。重点是跟踪“问题—建议—限制”，不要听前展示这段摘要。

### 词汇与表达

| ID与表达 | 原文锚点 | 本句义与使用提醒 | 新编例句及中文 |
|---|---|---|---|
| S2U1V01 city break | book a city break | 名词短语；到城市进行的短途度假，不是城市中休息片刻。常见于旅行语境。 | We are planning a city break in autumn. 我们计划秋天去城市短途度假。 |
| S2U1V02 loom | the anniversary is looming | 动词；日期正在逼近，语境中带紧迫感。搭配 a deadline is looming。 | The deadline is looming, so we need a decision. 截止日期临近，我们需要作出决定。 |
| S2U1V03 scramble to | scrambling to find accommodation | 动词结构；匆忙、费力地设法做某事。此处不是攀爬。 | We scrambled to find a replacement speaker. 我们急忙寻找替补发言人。 |
| S2U1V04 offset | offset the cost | 动词；抵消、补偿部分成本。并不自动意味着完全免费。 | Sharing transport can offset some of the cost. 共乘交通工具可以抵消一部分费用。 |
| S2U1V05 all inclusive | are all inclusive | 形容词结构；费用包含套餐范围内项目；本材料随后解释食物和饮料。不得推广成任何附加消费都免费。 | We asked what the all-inclusive package covered. 我们询问了全包套餐包含哪些项目。 |
| S2U1V06 thrilled to bits | absolutely thrilled to bits | 非正式表达，尤见英式用法；非常高兴。作为整块学，不拆解 bits 的字面义。 | I was thrilled to bits when the tickets arrived. 票送到时，我特别高兴。 |

可选识别项：annual leave（年假）、accommodation（住宿）、spiral staircase（螺旋楼梯）、logistical nightmare（安排起来非常棘手的事情）。这些不是学生必须收藏的额外卡片。

### 难句练习

**S2U1D01 原句**：Everything is either wildly expensive or already fully booked.

- 揭示前任务：说话人遇到的是哪两类选择困境？
- 揭示后释义：能找到的选择要么贵得离谱，要么已经订满。
- 结构：either A or B；两项都构成障碍，而非一个好方案、一个坏方案。
- 听辨任务：先说出两个并列项，再按需听写 fully booked。是否有连读，待听核后再标注。
- 迁移：用 either...or... 描述一次选时间或选地点的困难。

**S2U1D02 原句**：Considering [4] Jane is terrified of heights, I think if I tried to make her do that, I would come back divorced.

- 显示层须移除内部标记 `[4]`，但源文保持原样并留审计映射。
- 揭示前任务：男士是在报告已经发生的事，还是用假设表达担忧？
- 揭示后释义：考虑到 Jane 恐高，男士夸张地说，如果强迫她去做，回来可能就离婚了。
- 结构：Considering 给背景；if I tried / I would 表假设；that 回指前文的登高活动。
- 听辨任务：先区分事实背景与假设后果，不把夸张语气当已经发生的离婚。
- 迁移：改用温和、非婚姻冲突的情境表达“考虑到某人不喜欢什么，换一个安排”。

### 一次可结束的学习任务

完成 CP 后，学生先用中文概括当前问题；自己选一句困难处。默认只完成一次关系复述和一张声音卡即可退出，想深入再学第二句。跟读建议句或新编例句；表达任务是为朋友提出一个低成本出游方案。延迟复习只问问题与方案，不再记忆原题选项。

## U2 药师交流与用药管理

来源：`cet6_202606_set2_u2`；transcript hash：`b8ae47396c58ff6aef5eb5cfbf3a5817919913a94767792b90db60989fd23bb7`。

内部主线：两位药师交流患者咨询、与医生核实、用药管理及提醒服务。这里训练说话人和事件跟踪，不提供用药建议；药物问题应交给专业人员处理。

### 词汇与表达

| ID与表达 | 原文锚点 | 本句义与使用提醒 | 新编例句及中文 |
|---|---|---|---|
| S2U2V01 fill prescriptions | filling prescriptions | 动词搭配；按处方配药。此处不是医生开具处方，也不是填写表格。 | The pharmacist is filling a prescription. 药师正在按处方配药。 |
| S2U2V02 interaction | a potential interaction | 名词；这里指药物相互作用。日常也有互动义，先掌握当前语境。 | She asked the pharmacist about a possible drug interaction. 她向药师询问可能的药物相互作用。 |
| S2U2V03 double-check | double-check with her doctor | 动词；再核实。搭配 double-check something with someone。 | Please double-check the date with the organizer. 请向组织者再次核实日期。 |
| S2U2V04 end up | ended up switching | 动词短语；最后发生、最终变成某结果。搭配 end up doing something。 | We ended up moving the meeting online. 我们最后把会议改成了线上会议。 |
| S2U2V05 as prescribed | taking them as prescribed | 结构；按处方或医嘱用药。学习此词义不代表网站可以判断具体服药方式。 | She asked what “as prescribed” meant on the form. 她询问表格上的“遵医嘱”是什么意思。 |
| S2U2V06 non-adherence | Medication non-adherence | 名词；未按约定或医嘱执行，此处是用药依从性问题。不要仅解释为忘记，原因可能多样。 | The report discusses medication non-adherence. 报告讨论了未遵医嘱用药的问题。 |

可选识别项：pharmaceutical expertise（药学专业知识）、chronic conditions（慢性疾病）、side effects（副作用）。不要求每位学生准确拼写所有专业词。

### 难句练习

**S2U2D01 原句**：A patient came in inquiring about a medication that had a potential interaction with another medication she was already taking.

- 揭示前任务：这里涉及一种药还是两种？哪一种是原来就在服用的？
- 揭示后释义：患者来咨询一种药物，它可能与她已经在服用的另一种药物发生相互作用。
- 结构：主句 came in；inquiring... 描述目的或伴随动作；that... 修饰前一种药；she was already taking 修饰另一种药。
- 听辨任务：把“一种／另一种／已经服用”关系说清，不先要求抄出整句。
- 迁移：只练咨询表达，不让学生或模型判断实际药物是否可以合用。

**S2U2D02 原句**：Some have reported seeing improvements in their health, which is really rewarding to see.

- 揭示前任务：这是所有患者都有改善，还是部分患者报告改善？
- 揭示后释义：部分患者报告健康有所改善，看到这一点让说话人感到有成就感。
- 结构：Some 限定范围；reported 限定证据来源；which 回指所述改善。
- 听辨任务：复述时保留“部分”“报告”，不能说成方案已经被证明对所有人有效。
- 迁移：说一次帮助他人后感到有成就感的经历；英文困难可先用中文构思。

### 一次可结束的学习任务

学生口头排“咨询—核实—后续变化”，不提前给出已填答案；任选 double-check 或 end up 收藏。若主要障碍是专业名词，揭示后理解即可，不把大量医学词汇听写当必修。跟读后练一句向专业人员请求核实的表达。

## U3 热情与文化背景

来源：`cet6_202606_set2_u3`；transcript hash：`d222f4a208df608256d986f458d5ddeb74b931e123a10ec98e774044ad037e5f`。

内部主线：材料介绍研究中热情与成绩关联的文化差异。强调材料的研究表述，不把个人按国家或文化标签诊断，也不据此要求学生选择人生目标。

### 词汇与表达

| ID与表达 | 原文锚点 | 本句义与使用提醒 | 新编例句及中文 |
|---|---|---|---|
| S2U3V01 in a positive light | thought of in a positive light | 固定表达；从积极角度看待。不是照明条件。 | The interview presented the project in a positive light. 访谈从积极角度介绍了这个项目。 |
| S2U3V02 overstate | been overstated | 动词；夸大。overstated 不等于 completely false。 | We should not overstate the benefits of one tool. 我们不应夸大一种工具的好处。 |
| S2U3V03 individualistic | individualistic cultures | 形容词；强调个人自主或个人目标的。不要直接译为自私。 | The article compares individualistic and collectivistic values. 文章比较强调个人与集体的价值取向。 |
| S2U3V04 collectivistic | collectivistic cultures | 形容词；强调群体关系或集体义务的。与个体真实行为不能简单画等号。 | The researcher discussed collectivistic traditions. 研究者讨论了集体取向的传统。 |
| S2U3V05 fulfill obligations | fulfilling obligations to others | 动词搭配；履行对他人的义务。搭配 fulfill an obligation。 | We need time to fulfill our existing obligations. 我们需要时间履行已有义务。 |
| S2U3V06 correlate with | positively correlated with academic achievements | 动词结构；与某事相关联。正相关不是因果证明，也不是每个人都如此。 | The report asks whether attendance correlates with performance. 报告探讨出勤是否与表现相关。 |

可选识别项：bolster（支持、加强）、subtle（细微、不那么明显）、motivation（动机）。

### 难句练习

**S2U3D01 原句**：They often place fulfilling obligations to others above focusing on their own interests.

- 揭示前任务：两件事的优先顺序是什么？
- 揭示后释义：材料说他们往往把履行对他人的义务放在关注自身兴趣之前。
- 结构：place A above B 表优先级；两个动名词结构分别是 A 与 B。
- 听辨任务：先辨出 above 两边，再解释 often 的范围；不把倾向说成没有个人兴趣。
- 迁移：表达某一天自己如何在两项任务中排优先级，不要求认同材料的群体概括。

**S2U3D02 原句**：But the strength of this correlation wasn't the same across cultures.

- 揭示前任务：材料是在否定所有关联，还是说关联强弱不同？
- 揭示后释义：这种关联的强度在不同文化背景下并不相同。
- 结构：this correlation 回指前文；not the same 修饰强度，而不是直接否定关联存在。
- 听辨任务：遮字复述“不相同的是什么”，再决定是否收藏 correlation。
- 迁移：练习表达“两个情境的结果不同”，不自动生成文化能力画像。

### 一次可结束的学习任务

用中文说明“作者有没有说热情毫无作用”；核对后保留证据强度。专业概念过多时先处理一对对比词，其他词暂存。输出任务是解释自己学习的一种动力，而不是评价某类人是否上进。

## U4 自然图案如何形成

来源：`cet6_202606_set2_u4`；transcript hash：`623f4cee9c5dfbdcc5b202bb1d2b9eba4bbacbec2669354a63623f2d061c1db7`。

内部主线：材料从可见图案谈到微观过程、外部条件和偶然性。自然科学表述只用于理解材料；不擅自修订原文中可能存在的抽取问题。

### 词汇与表达

| ID与表达 | 原文锚点 | 本句义与使用提醒 | 新编例句及中文 |
|---|---|---|---|
| S2U4V01 intricate | intricate patterns | 形容词；复杂精细的。不是单纯混乱。 | The artist drew an intricate pattern. 艺术家画了一个精细复杂的图案。 |
| S2U4V02 come down to | come down to what's happening | 短语；归结为、关键在于。此处不是从高处下来。 | The choice comes down to time and cost. 这个选择归根结底取决于时间和成本。 |
| S2U4V03 undergo | materials undergo processes | 动词；经历某过程或变化。搭配 undergo a change。 | The design underwent several changes. 设计经历了几次修改。 |
| S2U4V04 give rise to | give rise to complex patterns | 固定表达；引起、产生。跟踪原因与结果方向。 | Small changes can give rise to unexpected results. 小变化可能产生意外结果。 |
| S2U4V05 cluster together | molecules begin clustering together | 动词结构；聚集在一起。cluster 也可作名词，当前先学动作。 | The visitors clustered together near the entrance. 游客聚集在入口附近。 |
| S2U4V06 by coincidence | generate a pattern by coincidence | 介词短语；偶然、巧合地。不是有意设计的同义表达。 | We chose the same topic by coincidence. 我们碰巧选了同一个主题。 |

可选识别项：molecule（分子）、humidity（湿度）、imperfection（不完美之处、缺陷）。

### 难句练习

**S2U4D01 原句**：Those changes then give rise to complex patterns at a larger scale that people can see.

- 揭示前任务：哪些变化带来了什么可见结果？
- 揭示后释义：前面所说的变化随后在更大尺度上产生人们能看见的复杂图案。
- 结构：Those changes 回指前文过程；give rise to 表产生；that... 描述可见性。
- 听辨任务：用“微观变化→可见图案”复述，再回听验证指代。
- 迁移：用 give rise to 描述普通生活中一种变化及其结果。

**S2U4D02 原句**：But scientists do not always know the purpose of a pattern, or even if there is one.

- 揭示前任务：科学家不知道的是用途，还是还不能确定是否有用途？
- 揭示后释义：科学家并不总知道图案的用途，甚至不一定知道它是否有用途。
- 结构：not always 不是一概不知道；one 指 purpose，而不是 pattern。
- 听辨任务：撤字后说出 one 的指代，再解释句子保留了什么不确定性。
- 迁移：练“我们看到了某现象，但还不能确定原因或作用”的谨慎表达。

### 一次可结束的学习任务

只要能解释“看见的图案与微观过程相关，不能假定都有目的”，即可结束主线检查。声音卡选 give rise to；学生想深入再整理因果句。不要要求背完全部物理化学词汇。

## U5 具体计划与习惯行动

来源：`cet6_202606_set2_u5`；transcript hash：`3a5e325c00c53d44476e4df737e5c51ca3f5a9299c923515148e38b28a558057`。

内部主线：材料讨论明确行动计划、一次关注一个目标及习惯逐渐自动化。文中研究数值不能直接拿来保证本网站提升效果，也不能据此设统一习惯养成天数。

### 词汇与表达

| ID与表达 | 原文锚点 | 本句义与使用提醒 | 新编例句及中文 |
|---|---|---|---|
| S2U5V01 counter-intuitive | somewhat counter-intuitive | 形容词；与直觉相反。词卡可用规范词形 counterintuitive，但锚点保留来源拼法并建立映射。 | The solution seems counterintuitive at first. 这个解决办法起初似乎违反直觉。 |
| S2U5V02 stick with | stick with your habits | 短语动词；坚持。不要按胶水的字面意思解释。 | I want to stick with a manageable routine. 我想坚持一套做得到的日常安排。 |
| S2U5V03 implementation intentions | implementation intentions | 专门术语；材料用来称呼写明何时、何地、如何行动的具体计划。理解即可，不默认要求拼写。 | My plan specifies when and where I will practise. 我的计划明确了何时、何地练习。 |
| S2U5V04 conscious effort | a lot of conscious effort | 名词短语；有意识的努力。与自动化对比，但不据此测量学生认知能力。 | At first, checking the schedule took conscious effort. 起初，查看日程需要有意识地提醒自己。 |
| S2U5V05 more or less | more or less automatic | 固定表达；大体上、差不多。此处不是比较“更多还是更少”。 | The outline is more or less complete. 提纲基本完成了。 |
| S2U5V06 tipping point | some tipping point | 名词短语；发生关键变化的临界点。本段未给一个适用于所有人的固定天数。 | The discussion reached a tipping point after the new evidence. 新证据出现后，讨论到了一个转折点。 |

可选识别项：vigorous（有力的、剧烈的）、control group（对照组）、committed（投入的）。

### 难句练习

**S2U5D01 原句**：However, follow-up research has discovered implementation intentions only work when you focus on one thing at a time.

- 揭示前任务：材料给前面的方法增加了什么条件？
- 揭示后释义：材料称后续研究发现，这种具体计划在一次专注一件事时才有效。
- 结构：However 修正或限制前文；only...when... 表条件；保留“材料称”，不变成本系统的普遍科学承诺。
- 听辨任务：先说条件，再说方法；不要因为听到 work 就遗漏 only。
- 迁移：为下次学习选择一个可完成的目标，其他任务允许延后。

**S2U5D02 原句**：The time it takes to build a habit depends on many factors, including how difficult the habit is, your genetics and more.

- 揭示前任务：材料是否给出了人人相同的养成时长？
- 揭示后释义：形成习惯需要多久取决于多种因素，材料没有给统一时间。
- 结构：The time... 作主语；depends on 表取决于；including 列举而非完整清单。
- 听辨任务：复述时保留“多种因素”，不把某个外部常见天数补进原文。
- 迁移：学生给自己的练习设一个可调整的时间安排，不做“21天必成功”的承诺。

### 一次可结束的学习任务

写下“我下次在什么时间、地点做哪一项短练习”，这是行动计划而不是能力证据。复习选 stick with 或 more or less；学生不需要把本文研究结果背作学习科学知识点。

## U6 冥王星大气与研究假说

来源：`cet6_202606_set2_u6`；transcript hash：`76345c1ad3e25fa2aad8e6c55b85474459c47da6af0c93888d2c9ae1f75c261b`。

内部主线：材料提出雾霾与低温相关的解释，比较地球与冥王星，并说明模型假说仍待观测检验。历史时间表按材料学习，不作为当前航天新闻。

**内容审核提示**：原文开头存在跨行断句，含飞越速度和将来发射的历史表述。本次不确认这些数值或时间的现实准确性；不拿它们制作必须精确判分的数值听写卡。修订须另核录音与原始资料，不能用当前知识擅改试题。

### 词汇与表达

| ID与表达 | 原文锚点 | 本句义与使用提醒 | 新编例句及中文 |
|---|---|---|---|
| S2U6V01 dwarf planet | distant dwarf planet | 名词短语；矮行星。专业类别只需在本段中识别。 | The article describes a distant dwarf planet. 文章描述了一颗遥远的矮行星。 |
| S2U6V02 haze | haze in Pluto's atmosphere | 名词；霾、薄雾状悬浮层。不要默认与地球污染烟雾成分相同。 | A layer of haze obscured the hills. 一层薄霾遮住了群山。 |
| S2U6V03 scatter | scattering light from the Sun | 动词；散射、使分散。这里描述光线变化，不是简单遮住同义替换。 | The model shows how particles scatter light. 模型展示颗粒怎样散射光线。 |
| S2U6V04 be dominated by | is dominated by the distribution of gases | 被动结构；主要受某因素影响。本句需要跟踪是哪颗行星。 | The conversation was dominated by questions about cost. 讨论主要围绕费用问题展开。 |
| S2U6V05 composition | the haze's composition | 名词；组成、成分。不是作文或作曲义。 | The team examined the material's composition. 团队研究了材料的组成。 |
| S2U6V06 validate | validates their bright idea | 动词；验证、为某想法提供支持。未发生的检验不能改写成已证实。 | More observations are needed to validate the model. 需要更多观测来检验模型。 |

可选识别项：atmosphere（大气）、estimate（估计）、sophisticated（复杂精密的）、notion（想法）。

### 难句练习

**S2U6D01 原句**：But on Earth, the overall temperature of the planet is dominated by the distribution of gases in our atmosphere.

- 揭示前任务：这句谈的是哪颗行星、什么主要因素？
- 揭示后释义：材料说地球整体温度主要受大气中气体分布影响。
- 结构：But on Earth 对照前文；被动结构突出影响来源。
- 听辨任务：听后只填“对象—主要因素”，避免把冥王星的假说套给地球。
- 迁移：描述两个系统可能受不同因素影响，不要求学生讲正确的天体物理知识。

**S2U6D02 原句**：But right now, this is just a good guess, based on data from New Horizons and a sophisticated computer model, not direct observations of the haze's composition.

- 揭示前任务：这个解释目前依据什么，还缺什么？
- 揭示后释义：在材料所述当时，它仍是依据数据和复杂计算机模型提出的推测，而不是对雾霾成分的直接观测结论。
- 结构：just a good guess 限定结论；based on A and B / not C 区分依据。
- 听辨任务：听出数据、模型、直接观测三类信息的关系，不听到 model 就说已经证明。
- 迁移：用“我们观察到……，但还需要……验证”表达一个日常小判断。

### 一次可结束的学习任务

不追求所有天文名词听写；优先区分“观察／解释／待验证”。学生用中文总结也算完成任务。若专业词负担太大，提供后置文字辅助后结束，不安排无穷次局部重播。

## U7 儿童音乐偏好与家庭影响

来源：`cet6_202606_set2_u7`；transcript hash：`a7a91e697b5590bce1d4fe8664a863fc57a4eaeef1a5ff039e79f65cf1487a67`。

内部主线：材料讨论父母影响儿童音乐偏好的时间范围、同伴影响与接触方式。年龄和调查比例属于材料所述研究，不转化为育儿诊断或固定成长规则。

### 词汇与表达

| ID与表达 | 原文锚点 | 本句义与使用提醒 | 新编例句及中文 |
|---|---|---|---|
| S2U7V01 a small window | have a small window | 比喻性名词短语；有限的机会或时间窗口。不是房间窗户。 | We have a small window to change the booking. 我们只有很短的时间可以修改预订。 |
| S2U7V02 time is of the essence | time is of the essence | 固定表达；时间至关重要，需要及时行动。本稿只讲日常语境，不作法律条款解读。 | We need to respond today; time is of the essence. 我们今天需要回复，时间很关键。 |
| S2U7V03 gravitate away from | gravitate away from their parents' choices | 动词结构；逐渐远离某种选择或倾向。注意 away from 的方向，与 toward 对照在揭示后学习。 | My interests gradually gravitated away from competitive games. 我的兴趣逐渐不再偏向竞技游戏。 |
| S2U7V04 receptive to | receptive to their musical suggestions | 形容词搭配；愿意接受某建议或想法。不是已经完全接受。 | The group was receptive to a different approach. 小组愿意考虑不同的方法。 |
| S2U7V05 foster | fostering good taste | 动词；培养、促进。这里是培养欣赏趣味，不是食物味觉。 | Shared activities can foster friendship. 共同活动可以促进友谊。 |
| S2U7V06 bond with | bond with others | 动词搭配；与他人建立亲近联系。与经济中的债券名词义区分。 | The project helped us bond with our classmates. 这个项目帮助我们与同学建立更亲近的联系。 |

可选识别项：adolescence（青春期）、peers（同龄人）、genres（体裁或风格类别）、lyrics（歌词）。

### 难句练习

**S2U7D01 原句**：The 24-month time frame comes at an age when youngsters are old enough to appreciate poetic lyrics and snappy tunes, but have not yet started to be embarrassed by their mother and father's preferences.

- 揭示前任务：材料如何描述这个阶段的两个同时存在的条件？
- 揭示后释义：孩子已经能够欣赏歌词和曲调，同时还没有开始因父母的偏好而感到难为情；这是材料对某时间段的描述。
- 结构：old enough to... 与 but have not yet...；两条件共同限定阶段。
- 听辨任务：保留“已经／还没有”，不只记一个年龄数字。
- 迁移：用 already / not yet 描述自己某项技能的当前状态，不给孩子贴发展标签。

**S2U7D02 原句**：Dr. Egermann advises parents not to push their favourite music too hard on their children, but instead play it as background music while the child is playing.

- 揭示前任务：建议少做什么、改做什么？
- 揭示后释义：材料中专家建议不要强迫孩子接受父母喜欢的音乐，而是在孩子玩耍时作为背景音乐播放。
- 结构：not to A, but instead B；while 表同时发生，不是此处的让步关系。
- 听辨任务：把“反对的方法”和“替代方法”分开说清。
- 迁移：用不强迫的方式向朋友推荐一首歌，并允许对方不喜欢。

### 一次可结束的学习任务

学生先概括“材料建议怎样接触音乐”；选择 receptive to 做声音卡。调查比例练习可选，必须同时明确对象与分母，不因数字写错就诊断记忆差。输出是推荐一种音乐并说明原因，不要求模仿文中的家长教育方式。

## 两张完整交互样卡

### 卡片 A offset the cost

- 来源：S2U1V04，词头 offset；必须绑定 U1 revision 与 hash。
- 首次盲听前：不展示该卡，不按此次材料推送该词头或例句。
- 学习态：播放经审核原句区间；先问“这里的 offset 大概是什么意思？”；可选“文字认识但声音没认出／意思不熟／都不确定”。
- 揭示态：说明是抵消或补偿成本，不等于完全消除费用；展示搭配和表内新编例句。
- 声音复习：不显示词头，播放词组或原句，让学生回想意义。已有上下文线索时记录为 context-supported，不冒充脱离语境识别。
- 输出练习：给一个普通活动节省费用的方案，用 offset 表达；若用其他自然表达也可完成沟通任务，不强制唯一措辞。
- 写入：词汇复习结果与表达产出分别记录；不得因为输出正确就标记 listening ability improved。

### 卡片 B time is of the essence

- 来源：S2U7V02；日常固定表达，不标成所有场景都适用的俚语。
- 学习态：在完成相应学习解锁后，听完整表达并尝试解释。
- 揭示态：时间很关键、需要及时行动；不逐个翻译 of / the / essence。
- 复习态：播放后用中文解释即可；第二种可选任务是换成自己的紧急安排说一句。
- 字符输入：拼写错误单独标记，不把中文解释正确但拼错 essence 自动判成“听不懂”。
- 缺音频：可查看文字详解，但标签为文字学习；不产生声音识别成功记录。

## 内容质量与发布前清单

1. 每条原文锚点归属正确，不把“同样的英语六级”当作同一套卷。表内新例句必须标为教学新编。
2. 不把候选文本中的题号标记、源解析或答案映射送入首听 DTO。
3. 逐句时间戳需独立审核。Set2 整套的作答静音保留用于考试；学习片段可在派生资源中排除指令和答题静音，但必须保留父音频映射及版本，不能覆盖整套源音频。
4. 本稿的任务提问与参考释义不是正式题目答案，但仍会泄露语义，必须在学习解锁后出现。
5. 选词优先服务学生实际困难；不是42条全部必背。已有词条应复用义项与来源关系，避免仅因新稿而重复创建 SRS 项。
6. 原文音频、释义、题目解析分别审核；内容有原文和商业出版物衍生限制，当前不得直接批量发布。
7. 当前 `student_release_allowed=false` 保持；学习任务默认 `profile_eligible=false`。重复材料仅记录复习／恢复／辅助后理解。
8. 专业材料存在历史事实、OCR与表达疑点时单独登记，不自动替换原文；未核验数字、专名不做严格自动判分。

## 词义抽查参考

这不是逐条词典审定。上述英文新例句为本稿创作，以下仅支持少数容易误读的固定表达，不能由此给全稿贴 teacher_verified。

- [Oxford Learner's Dictionaries：thrilled，含 thrilled to bits](https://www.oxfordlearnersdictionaries.com/definition/english/thrilled)：非正式表达的强烈高兴义。
- [Cambridge Dictionary：time is of the essence](https://dictionary.cambridge.org/dictionary/english/time-is-of-the-essence)：时间至关重要的表达。
- [Medical English：fill a prescription](https://www.medicalenglish.com/dictionary/fill-a-prescription)：药房配药语境，最终仍须英语内容审核。

如何接进当前系统，见 `LISTENING_FLOW_LEARNING_COMPLETION_DRAFT.md`。优先接通 U1，验收稳定后才扩到 U2—U7；不是先批量启用所有入口。
