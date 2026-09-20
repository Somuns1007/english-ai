"""Reviewed-source anchors and machine-authored learning notes; no exam answer keys.

Rights: project owner declared ownership in the implementation request (2026-09-10).
This declaration is not teacher verification. Set 1 is deliberately excluded.
"""
import json

CONTENT_REVISION = 1
GUIDANCE = json.loads(r'''{
  "cet6_202606_set2_u7": [
    {
      "transfer": "用 already / not yet 描述自己某项技能的当前状态，不给孩子贴发展标签。",
      "structure": "old enough to... 与 but have not yet...；两条件共同限定阶段。",
      "anchor": "The 24-month time frame comes at an age when youngsters are old enough to appreciate poetic lyrics and snappy tunes, but have not yet started to be embarrassed by their mother and father's preferences.",
      "listening": "保留“已经／还没有”，不只记一个年龄数字。",
      "gloss": "孩子已经能够欣赏歌词和曲调，同时还没有开始因父母的偏好而感到难为情；这是材料对某时间段的描述。",
      "id": "S2U7D01"
    },
    {
      "transfer": "用不强迫的方式向朋友推荐一首歌，并允许对方不喜欢。",
      "structure": "not to A, but instead B；while 表同时发生，不是此处的让步关系。",
      "anchor": "Dr. Egermann advises parents not to push their favourite music too hard on their children, but instead play it as background music while the child is playing.",
      "listening": "把“反对的方法”和“替代方法”分开说清。",
      "gloss": "材料中专家建议不要强迫孩子接受父母喜欢的音乐，而是在孩子玩耍时作为背景音乐播放。",
      "id": "S2U7D02"
    }
  ],
  "cet6_202606_set2_u2": [
    {
      "transfer": "只练咨询表达，不让学生或模型判断实际药物是否可以合用。",
      "structure": "主句 came in；inquiring... 描述目的或伴随动作；that... 修饰前一种药；she was already taking 修饰另一种药。",
      "anchor": "A patient came in inquiring about a medication that had a potential interaction with another medication she was already taking.",
      "listening": "把“一种／另一种／已经服用”关系说清，不先要求抄出整句。",
      "gloss": "患者来咨询一种药物，它可能与她已经在服用的另一种药物发生相互作用。",
      "id": "S2U2D01"
    },
    {
      "transfer": "说一次帮助他人后感到有成就感的经历；英文困难可先用中文构思。",
      "structure": "Some 限定范围；reported 限定证据来源；which 回指所述改善。",
      "anchor": "Some have reported seeing improvements in their health, which is really rewarding to see.",
      "listening": "复述时保留“部分”“报告”，不能说成方案已经被证明对所有人有效。",
      "gloss": "部分患者报告健康有所改善，看到这一点让说话人感到有成就感。",
      "id": "S2U2D02"
    }
  ],
  "cet6_202606_set2_u3": [
    {
      "transfer": "表达某一天自己如何在两项任务中排优先级，不要求认同材料的群体概括。",
      "structure": "place A above B 表优先级；两个动名词结构分别是 A 与 B。",
      "anchor": "They often place fulfilling obligations to others above focusing on their own interests.",
      "listening": "先辨出 above 两边，再解释 often 的范围；不把倾向说成没有个人兴趣。",
      "gloss": "材料说他们往往把履行对他人的义务放在关注自身兴趣之前。",
      "id": "S2U3D01"
    },
    {
      "transfer": "练习表达“两个情境的结果不同”，不自动生成文化能力画像。",
      "structure": "this correlation 回指前文；not the same 修饰强度，而不是直接否定关联存在。",
      "anchor": "But the strength of this correlation wasn't the same across cultures.",
      "listening": "遮字复述“不相同的是什么”，再决定是否收藏 correlation。",
      "gloss": "这种关联的强度在不同文化背景下并不相同。",
      "id": "S2U3D02"
    }
  ],
  "cet6_202606_set2_u1": [
    {
      "transfer": "用 either...or... 描述一次选时间或选地点的困难。",
      "structure": "either A or B；两项都构成障碍，而非一个好方案、一个坏方案。",
      "anchor": "Everything is either wildly expensive or already fully booked.",
      "listening": "先说出两个并列项，再按需听写 fully booked。是否有连读，待听核后再标注。",
      "gloss": "能找到的选择要么贵得离谱，要么已经订满。",
      "id": "S2U1D01"
    },
    {
      "transfer": "改用温和、非婚姻冲突的情境表达“考虑到某人不喜欢什么，换一个安排”。",
      "structure": "Considering 给背景；if I tried / I would 表假设；that 回指前文的登高活动。",
      "anchor": "Considering [4] Jane is terrified of heights, I think if I tried to make her do that, I would come back divorced.",
      "listening": "先区分事实背景与假设后果，不把夸张语气当已经发生的离婚。",
      "gloss": "考虑到 Jane 恐高，男士夸张地说，如果强迫她去做，回来可能就离婚了。",
      "id": "S2U1D02"
    }
  ],
  "cet6_202606_set2_u5": [
    {
      "transfer": "为下次学习选择一个可完成的目标，其他任务允许延后。",
      "structure": "However 修正或限制前文；only...when... 表条件；保留“材料称”，不变成本系统的普遍科学承诺。",
      "anchor": "However, follow-up research has discovered implementation intentions only work when you focus on one thing at a time.",
      "listening": "先说条件，再说方法；不要因为听到 work 就遗漏 only。",
      "gloss": "材料称后续研究发现，这种具体计划在一次专注一件事时才有效。",
      "id": "S2U5D01"
    },
    {
      "transfer": "学生给自己的练习设一个可调整的时间安排，不做“21天必成功”的承诺。",
      "structure": "The time... 作主语；depends on 表取决于；including 列举而非完整清单。",
      "anchor": "The time it takes to build a habit depends on many factors, including how difficult the habit is, your genetics and more.",
      "listening": "复述时保留“多种因素”，不把某个外部常见天数补进原文。",
      "gloss": "形成习惯需要多久取决于多种因素，材料没有给统一时间。",
      "id": "S2U5D02"
    }
  ],
  "cet6_202606_set2_u4": [
    {
      "transfer": "用 give rise to 描述普通生活中一种变化及其结果。",
      "structure": "Those changes 回指前文过程；give rise to 表产生；that... 描述可见性。",
      "anchor": "Those changes then give rise to complex patterns at a larger scale that people can see.",
      "listening": "用“微观变化→可见图案”复述，再回听验证指代。",
      "gloss": "前面所说的变化随后在更大尺度上产生人们能看见的复杂图案。",
      "id": "S2U4D01"
    },
    {
      "transfer": "练“我们看到了某现象，但还不能确定原因或作用”的谨慎表达。",
      "structure": "not always 不是一概不知道；one 指 purpose，而不是 pattern。",
      "anchor": "But scientists do not always know the purpose of a pattern, or even if there is one.",
      "listening": "撤字后说出 one 的指代，再解释句子保留了什么不确定性。",
      "gloss": "科学家并不总知道图案的用途，甚至不一定知道它是否有用途。",
      "id": "S2U4D02"
    }
  ],
  "cet6_202606_set2_u6": [
    {
      "transfer": "描述两个系统可能受不同因素影响，不要求学生讲正确的天体物理知识。",
      "structure": "But on Earth 对照前文；被动结构突出影响来源。",
      "anchor": "But on Earth, the overall temperature of the planet is dominated by the distribution of gases in our atmosphere.",
      "listening": "听后只填“对象—主要因素”，避免把冥王星的假说套给地球。",
      "gloss": "材料说地球整体温度主要受大气中气体分布影响。",
      "id": "S2U6D01"
    },
    {
      "transfer": "用“我们观察到……，但还需要……验证”表达一个日常小判断。",
      "structure": "just a good guess 限定结论；based on A and B / not C 区分依据。",
      "anchor": "But right now, this is just a good guess, based on data from New Horizons and a sophisticated computer model, not direct observations of the haze's composition.",
      "listening": "听出数据、模型、直接观测三类信息的关系，不听到 model 就说已经证明。",
      "gloss": "在材料所述当时，它仍是依据数据和复杂计算机模型提出的推测，而不是对雾霾成分的直接观测结论。",
      "id": "S2U6D02"
    }
  ]
}''')
CONTENT = json.loads(r'''
{
  "cet6_202606_set2_u5": {
    "title": "具体计划与习惯行动",
    "vocabulary": [
      {
        "id": "S2U5V01",
        "anchor": "somewhat counter-intuitive",
        "example": "The solution seems counterintuitive at first. 这个解决办法起初似乎违反直觉。",
        "gloss": "形容词；与直觉相反。词卡可用规范词形 counterintuitive，但锚点保留来源拼法并建立映射。",
        "surface": "counter-intuitive"
      },
      {
        "id": "S2U5V02",
        "anchor": "stick with your habits",
        "example": "I want to stick with a manageable routine. 我想坚持一套做得到的日常安排。",
        "gloss": "短语动词；坚持。不要按胶水的字面意思解释。",
        "surface": "stick with"
      },
      {
        "id": "S2U5V03",
        "anchor": "implementation intentions",
        "example": "My plan specifies when and where I will practise. 我的计划明确了何时、何地练习。",
        "gloss": "专门术语；材料用来称呼写明何时、何地、如何行动的具体计划。理解即可，不默认要求拼写。",
        "surface": "implementation intentions"
      },
      {
        "id": "S2U5V04",
        "anchor": "a lot of conscious effort",
        "example": "At first, checking the schedule took conscious effort. 起初，查看日程需要有意识地提醒自己。",
        "gloss": "名词短语；有意识的努力。与自动化对比，但不据此测量学生认知能力。",
        "surface": "conscious effort"
      },
      {
        "id": "S2U5V05",
        "anchor": "more or less automatic",
        "example": "The outline is more or less complete. 提纲基本完成了。",
        "gloss": "固定表达；大体上、差不多。此处不是比较“更多还是更少”。",
        "surface": "more or less"
      },
      {
        "id": "S2U5V06",
        "anchor": "some tipping point",
        "example": "The discussion reached a tipping point after the new evidence. 新证据出现后，讨论到了一个转折点。",
        "gloss": "名词短语；发生关键变化的临界点。本段未给一个适用于所有人的固定天数。",
        "surface": "tipping point"
      }
    ]
  },
  "cet6_202606_set2_u1": {
    "title": "结婚纪念日旅行计划",
    "vocabulary": [
      {
        "id": "S2U1V01",
        "anchor": "book a city break",
        "example": "We are planning a city break in autumn. 我们计划秋天去城市短途度假。",
        "gloss": "名词短语；到城市进行的短途度假，不是城市中休息片刻。常见于旅行语境。",
        "surface": "city break"
      },
      {
        "id": "S2U1V02",
        "anchor": "the anniversary is looming",
        "example": "The deadline is looming, so we need a decision. 截止日期临近，我们需要作出决定。",
        "gloss": "动词；日期正在逼近，语境中带紧迫感。搭配 a deadline is looming。",
        "surface": "loom"
      },
      {
        "id": "S2U1V03",
        "anchor": "scrambling to find accommodation",
        "example": "We scrambled to find a replacement speaker. 我们急忙寻找替补发言人。",
        "gloss": "动词结构；匆忙、费力地设法做某事。此处不是攀爬。",
        "surface": "scramble to"
      },
      {
        "id": "S2U1V04",
        "anchor": "offset the cost",
        "example": "Sharing transport can offset some of the cost. 共乘交通工具可以抵消一部分费用。",
        "gloss": "动词；抵消、补偿部分成本。并不自动意味着完全免费。",
        "surface": "offset"
      },
      {
        "id": "S2U1V05",
        "anchor": "are all inclusive",
        "example": "We asked what the all-inclusive package covered. 我们询问了全包套餐包含哪些项目。",
        "gloss": "形容词结构；费用包含套餐范围内项目；本材料随后解释食物和饮料。不得推广成任何附加消费都免费。",
        "surface": "all inclusive"
      },
      {
        "id": "S2U1V06",
        "anchor": "absolutely thrilled to bits",
        "example": "I was thrilled to bits when the tickets arrived. 票送到时，我特别高兴。",
        "gloss": "非正式表达，尤见英式用法；非常高兴。作为整块学，不拆解 bits 的字面义。",
        "surface": "thrilled to bits"
      }
    ]
  },
  "cet6_202606_set2_u7": {
    "title": "儿童音乐偏好与家庭影响",
    "vocabulary": [
      {
        "id": "S2U7V01",
        "anchor": "have a small window",
        "example": "We have a small window to change the booking. 我们只有很短的时间可以修改预订。",
        "gloss": "比喻性名词短语；有限的机会或时间窗口。不是房间窗户。",
        "surface": "a small window"
      },
      {
        "id": "S2U7V02",
        "anchor": "time is of the essence",
        "example": "We need to respond today; time is of the essence. 我们今天需要回复，时间很关键。",
        "gloss": "固定表达；时间至关重要，需要及时行动。本稿只讲日常语境，不作法律条款解读。",
        "surface": "time is of the essence"
      },
      {
        "id": "S2U7V03",
        "anchor": "gravitate away from their parents' choices",
        "example": "My interests gradually gravitated away from competitive games. 我的兴趣逐渐不再偏向竞技游戏。",
        "gloss": "动词结构；逐渐远离某种选择或倾向。注意 away from 的方向，与 toward 对照在揭示后学习。",
        "surface": "gravitate away from"
      },
      {
        "id": "S2U7V04",
        "anchor": "receptive to their musical suggestions",
        "example": "The group was receptive to a different approach. 小组愿意考虑不同的方法。",
        "gloss": "形容词搭配；愿意接受某建议或想法。不是已经完全接受。",
        "surface": "receptive to"
      },
      {
        "id": "S2U7V05",
        "anchor": "fostering good taste",
        "example": "Shared activities can foster friendship. 共同活动可以促进友谊。",
        "gloss": "动词；培养、促进。这里是培养欣赏趣味，不是食物味觉。",
        "surface": "foster"
      },
      {
        "id": "S2U7V06",
        "anchor": "bond with others",
        "example": "The project helped us bond with our classmates. 这个项目帮助我们与同学建立更亲近的联系。",
        "gloss": "动词搭配；与他人建立亲近联系。与经济中的债券名词义区分。",
        "surface": "bond with"
      }
    ]
  },
  "cet6_202606_set2_u6": {
    "title": "冥王星大气与研究假说",
    "vocabulary": [
      {
        "id": "S2U6V01",
        "anchor": "distant dwarf planet",
        "example": "The article describes a distant dwarf planet. 文章描述了一颗遥远的矮行星。",
        "gloss": "名词短语；矮行星。专业类别只需在本段中识别。",
        "surface": "dwarf planet"
      },
      {
        "id": "S2U6V02",
        "anchor": "haze in Pluto's atmosphere",
        "example": "A layer of haze obscured the hills. 一层薄霾遮住了群山。",
        "gloss": "名词；霾、薄雾状悬浮层。不要默认与地球污染烟雾成分相同。",
        "surface": "haze"
      },
      {
        "id": "S2U6V03",
        "anchor": "scattering light from the Sun",
        "example": "The model shows how particles scatter light. 模型展示颗粒怎样散射光线。",
        "gloss": "动词；散射、使分散。这里描述光线变化，不是简单遮住同义替换。",
        "surface": "scatter"
      },
      {
        "id": "S2U6V04",
        "anchor": "is dominated by the distribution of gases",
        "example": "The conversation was dominated by questions about cost. 讨论主要围绕费用问题展开。",
        "gloss": "被动结构；主要受某因素影响。本句需要跟踪是哪颗行星。",
        "surface": "be dominated by"
      },
      {
        "id": "S2U6V05",
        "anchor": "the haze's composition",
        "example": "The team examined the material's composition. 团队研究了材料的组成。",
        "gloss": "名词；组成、成分。不是作文或作曲义。",
        "surface": "composition"
      },
      {
        "id": "S2U6V06",
        "anchor": "validates their bright idea",
        "example": "More observations are needed to validate the model. 需要更多观测来检验模型。",
        "gloss": "动词；验证、为某想法提供支持。未发生的检验不能改写成已证实。",
        "surface": "validate"
      }
    ]
  },
  "cet6_202606_set2_u4": {
    "title": "自然图案如何形成",
    "vocabulary": [
      {
        "id": "S2U4V01",
        "anchor": "intricate patterns",
        "example": "The artist drew an intricate pattern. 艺术家画了一个精细复杂的图案。",
        "gloss": "形容词；复杂精细的。不是单纯混乱。",
        "surface": "intricate"
      },
      {
        "id": "S2U4V02",
        "anchor": "come down to what's happening",
        "example": "The choice comes down to time and cost. 这个选择归根结底取决于时间和成本。",
        "gloss": "短语；归结为、关键在于。此处不是从高处下来。",
        "surface": "come down to"
      },
      {
        "id": "S2U4V03",
        "anchor": "materials undergo processes",
        "example": "The design underwent several changes. 设计经历了几次修改。",
        "gloss": "动词；经历某过程或变化。搭配 undergo a change。",
        "surface": "undergo"
      },
      {
        "id": "S2U4V04",
        "anchor": "give rise to complex patterns",
        "example": "Small changes can give rise to unexpected results. 小变化可能产生意外结果。",
        "gloss": "固定表达；引起、产生。跟踪原因与结果方向。",
        "surface": "give rise to"
      },
      {
        "id": "S2U4V05",
        "anchor": "molecules begin clustering together",
        "example": "The visitors clustered together near the entrance. 游客聚集在入口附近。",
        "gloss": "动词结构；聚集在一起。cluster 也可作名词，当前先学动作。",
        "surface": "cluster together"
      },
      {
        "id": "S2U4V06",
        "anchor": "generate a pattern by coincidence",
        "example": "We chose the same topic by coincidence. 我们碰巧选了同一个主题。",
        "gloss": "介词短语；偶然、巧合地。不是有意设计的同义表达。",
        "surface": "by coincidence"
      }
    ]
  },
  "cet6_202606_set2_u3": {
    "title": "热情与文化背景",
    "vocabulary": [
      {
        "id": "S2U3V01",
        "anchor": "thought of in a positive light",
        "example": "The interview presented the project in a positive light. 访谈从积极角度介绍了这个项目。",
        "gloss": "固定表达；从积极角度看待。不是照明条件。",
        "surface": "in a positive light"
      },
      {
        "id": "S2U3V02",
        "anchor": "been overstated",
        "example": "We should not overstate the benefits of one tool. 我们不应夸大一种工具的好处。",
        "gloss": "动词；夸大。overstated 不等于 completely false。",
        "surface": "overstate"
      },
      {
        "id": "S2U3V03",
        "anchor": "individualistic cultures",
        "example": "The article compares individualistic and collectivistic values. 文章比较强调个人与集体的价值取向。",
        "gloss": "形容词；强调个人自主或个人目标的。不要直接译为自私。",
        "surface": "individualistic"
      },
      {
        "id": "S2U3V04",
        "anchor": "collectivistic cultures",
        "example": "The researcher discussed collectivistic traditions. 研究者讨论了集体取向的传统。",
        "gloss": "形容词；强调群体关系或集体义务的。与个体真实行为不能简单画等号。",
        "surface": "collectivistic"
      },
      {
        "id": "S2U3V05",
        "anchor": "fulfilling obligations to others",
        "example": "We need time to fulfill our existing obligations. 我们需要时间履行已有义务。",
        "gloss": "动词搭配；履行对他人的义务。搭配 fulfill an obligation。",
        "surface": "fulfill obligations"
      },
      {
        "id": "S2U3V06",
        "anchor": "positively correlated with academic achievements",
        "example": "The report asks whether attendance correlates with performance. 报告探讨出勤是否与表现相关。",
        "gloss": "动词结构；与某事相关联。正相关不是因果证明，也不是每个人都如此。",
        "surface": "correlate with"
      }
    ]
  },
  "cet6_202606_set2_u2": {
    "title": "药师交流与用药管理",
    "vocabulary": [
      {
        "id": "S2U2V01",
        "anchor": "filling prescriptions",
        "example": "The pharmacist is filling a prescription. 药师正在按处方配药。",
        "gloss": "动词搭配；按处方配药。此处不是医生开具处方，也不是填写表格。",
        "surface": "fill prescriptions"
      },
      {
        "id": "S2U2V02",
        "anchor": "a potential interaction",
        "example": "She asked the pharmacist about a possible drug interaction. 她向药师询问可能的药物相互作用。",
        "gloss": "名词；这里指药物相互作用。日常也有互动义，先掌握当前语境。",
        "surface": "interaction"
      },
      {
        "id": "S2U2V03",
        "anchor": "double-check with her doctor",
        "example": "Please double-check the date with the organizer. 请向组织者再次核实日期。",
        "gloss": "动词；再核实。搭配 double-check something with someone。",
        "surface": "double-check"
      },
      {
        "id": "S2U2V04",
        "anchor": "ended up switching",
        "example": "We ended up moving the meeting online. 我们最后把会议改成了线上会议。",
        "gloss": "动词短语；最后发生、最终变成某结果。搭配 end up doing something。",
        "surface": "end up"
      },
      {
        "id": "S2U2V05",
        "anchor": "taking them as prescribed",
        "example": "She asked what “as prescribed” meant on the form. 她询问表格上的“遵医嘱”是什么意思。",
        "gloss": "结构；按处方或医嘱用药。学习此词义不代表网站可以判断具体服药方式。",
        "surface": "as prescribed"
      },
      {
        "id": "S2U2V06",
        "anchor": "Medication non-adherence",
        "example": "The report discusses medication non-adherence. 报告讨论了未遵医嘱用药的问题。",
        "gloss": "名词；未按约定或医嘱执行，此处是用药依从性问题。不要仅解释为忘记，原因可能多样。",
        "surface": "non-adherence"
      }
    ]
  }
}
''')
