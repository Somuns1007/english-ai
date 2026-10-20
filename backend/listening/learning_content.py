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
  ],
  "cet4_202606_set2_u1": [
    {
      "transfer": "介绍一位亲人时，试着用两个并列动作说出生时间和居住经历。",
      "structure": "was born 和 spent 是并列的两件事；living in... 补充说明她这段时间住在哪里。",
      "anchor": "[1]Nancy Gifford was born months after the end of the First World War and spent 102 years living in her three-bedroom house in the Somerset Village of Street.",
      "listening": "先听出出生时间和居住时长，再把后面的地点接上。",
      "gloss": "南希在第一次世界大战结束几个月后出生，并在萨默塞特郡斯特里特村的三居室房子里住了102年。",
      "id": "C4S2U1D01"
    },
    {
      "transfer": "说一件现在要做的事，再用 having done 补充之前的经历。",
      "structure": "主句是 She is now putting it on the market；having lived... 补充她此前的居住经历。",
      "anchor": "She is now putting it on the market, having lived in it through the Second World War and the invention of television.",
      "listening": "听到 having lived 后，继续听她住过的历史时期，别把它当成新的主句。",
      "gloss": "她现在正把房子挂牌出售；在此之前，她一直住在那里，经历了二战和电视的发明。",
      "id": "C4S2U1D02"
    }
  ],
  "cet4_202606_set2_u2": [
    {
      "transfer": "介绍一位完成挑战的人，并用 by doing 说他是怎么做到的。",
      "structure": "who survived... 修饰 a man；by eating... 说明他靠什么维持生存。",
      "anchor": "The navy rescued a man who survived 24 days floating in the sea on a boat by eating tomato sauce and vegetable powder.",
      "listening": "先抓住被救的人，再听 24 days 和 by 后面的生存方式。",
      "gloss": "海军救起了一名男子；他在海上漂了24天，靠番茄酱和蔬菜粉活了下来。",
      "id": "C4S2U2D01"
    },
    {
      "transfer": "讲一次意外，用 when 和 while 交代事情发生时你正在做什么。",
      "structure": "told 后接一整段陈述；when 和 while 分别交代海流把船带走及他当时正在修船的时间关系。",
      "anchor": "The man told authorities that his experience began in December when currents swept the sailboat out to sea while he was making repairs.",
      "listening": "听到 when currents swept... 时，把它接到 his experience began，不要丢掉 while 后的修船背景。",
      "gloss": "男子告诉当局，他的经历始于12月：修船时，海流把帆船带到了外海。",
      "id": "C4S2U2D02"
    }
  ],
  "cet4_202606_set2_u3": [
    {
      "transfer": "说明一项安排时，依次交代计划、目的和原因。",
      "structure": "is set to close 表计划关闭；to make up for... 表目的；caused by... 说明预算减少的原因。",
      "anchor": "[5]The board of Denver public schools is set to close several elementary and middle schools to make up for a decreased budget caused by declining enrollment.",
      "listening": "按“关闭学校—弥补预算—招生下降”这条链听，不必先记住学校名称。",
      "gloss": "丹佛公立学校董事会准备关闭几所学校，以弥补因入学人数下降而减少的预算。",
      "id": "C4S2U3D01"
    },
    {
      "transfer": "列出两类不同标准时，用 as well as 连接，并说清各自的附加条件。",
      "structure": "with fewer than 215 students 和 with fewer than 275 students... 是由 as well as 连接的两类标准。",
      "anchor": "The school board approved criteria to close schools with fewer than 215 students, as well as schools with fewer than 275 students and a projected decline in enrollment.",
      "listening": "两个数字对应不同条件；第二类还带有预计招生下降这一条件。",
      "gloss": "学校董事会批准了关闭学校的标准：学生少于215人的学校，以及少于275人且预计招生继续下降的学校。",
      "id": "C4S2U3D02"
    }
  ],
  "cet4_202606_set2_u4": [
    {
      "transfer": "描述一件最近反复尝试的事，用 I've been trying to... 开头。",
      "structure": "I've been trying to... 表示到现在为止一直在尝试；for the musical... 和 on the evening... 依次补充订票对象与日期。",
      "anchor": "[8]I’ve been trying to book tickets for the musical Cats in London on the evening of May the 28th.",
      "listening": "先抓 I've been trying to book tickets，再听演出和日期。",
      "gloss": "我一直想订5月28日晚伦敦音乐剧《猫》的票。",
      "id": "C4S2U4D01"
    },
    {
      "transfer": "向别人说明首选方案不可用，再用 but 提出可行替代。",
      "structure": "前半句 all the tickets... are sold out 说明限制；but 后给出另一个可选座位。",
      "anchor": "Actually, [10]all the tickets at the front are already sold out anyway, but I can offer you two upstairs near the middle.",
      "listening": "听到 but 就准备接收替代方案，不要只记住前排已经售罄。",
      "gloss": "前排的票已经卖完了，不过我可以给你楼上靠中间的两个座位。",
      "id": "C4S2U4D02"
    }
  ],
  "cet4_202606_set2_u5": [
    {
      "transfer": "说一次你通过记录或观察才意识到的习惯。",
      "structure": "that recorded... 修饰 app；how much time... 是 recorded 的内容；and 后转到说话人发现的结果。",
      "anchor": "[13]Well, I downloaded an app that recorded how much time I spent on my phone, and I was shocked to realize I was using my phone an average of eight hours a day.",
      "listening": "先听应用记录了什么，再听 shocked to realize 后的平均使用时长。",
      "gloss": "我下载了一个记录手机使用时间的应用，惊讶地发现自己平均每天用手机八小时。",
      "id": "C4S2U5D01"
    },
    {
      "transfer": "解释自己为什么觉得某件事很难做到，用 That's why I don't see how...。",
      "structure": "why 引出原因；I don't see how... 表“我想不出怎么能……”，里面还有 how 引导的从句。",
      "anchor": "That is really why I don’t see how anyone could live without a mobile phone.",
      "listening": "不要把 don't see how 误解成没看见；这里表达的是难以想象。",
      "gloss": "这正是我想不出有人怎么能不用手机生活的原因。",
      "id": "C4S2U5D02"
    }
  ],
  "cet4_202606_set2_u6": [
    {
      "transfer": "介绍图表时，先说数据来源，再用 shows 说出变化和时间。",
      "structure": "主语是 A three-month moving average...；shows 后才是统计结果；when 补充达到高点的时间。",
      "anchor": "A three-month moving average of annual wage increases from the Atlanta Federal Reserve Bank’s wage tracker shows that US job switchers got the highest wage increase last July, when the measure touched 8.5 percent.",
      "listening": "长主语听完再找 shows，不要把机构名称听成句子的动作。",
      "gloss": "一项三个月移动平均数据显示，换工作者的工资涨幅在去年7月达到最高点，当时为8.5%。",
      "id": "C4S2U6D01"
    },
    {
      "transfer": "表达带保留的判断时，用 likely，再补充支持判断的现象。",
      "structure": "because 说明就业市场可能降温的原因；even a shortage... 表即使缺工也没扭转后面的趋势；分号连接补充说明。",
      "anchor": "[18]The labor market is likely cooling, because even a shortage of workers isn’t overcoming the historic imbalance between employers and employees in the US; the volume of income that workers take home as a proportion of what the US economy produces is still falling.",
      "listening": "先听 likely cooling 这一判断，再听 even 引出的让步和分号后的收入占比。",
      "gloss": "就业市场可能在降温，因为即使缺少工人也没扭转劳资之间长期失衡的局面；劳动收入占经济产出的比例仍在下降。",
      "id": "C4S2U6D02"
    }
  ],
  "cet4_202606_set2_u7": [
    {
      "transfer": "介绍一种便利做法后，用 but 说明它可能带来的代价。",
      "structure": "破折号之间解释 highly processed foods；but 后转向研究发现的健康代价。",
      "anchor": "Highly processed foods—the kinds made with lots of sugar, fat and salt—make up as much as sixty percent of the average American diet, [19]but a new study shows that their low price and convenience come at a cost to health.",
      "listening": "先听食物的定义和占比，再把 but 后面的信息当作重点转折。",
      "gloss": "高度加工食品占美国人平均饮食很大一部分，但一项新研究指出，便宜和方便可能有健康代价。",
      "id": "C4S2U7D01"
    },
    {
      "transfer": "解释一件事为什么来不及时，用 not give... enough time to...。",
      "structure": "if you're eating more quickly 是条件；you're not giving... enough time to... 表没有留足时间；后面两个 that 从句说明大脑收到什么信号。",
      "anchor": "One theory is that if you’re eating more quickly, you’re not giving your gut enough time to signal to your brain that you’ve had enough calories and that you’re full.",
      "listening": "先听进食速度，再追踪“肠道发信号—大脑收到信号”这条顺序。",
      "gloss": "一种理论认为，吃得太快时，肠道还没来得及告诉大脑已经吃够了。",
      "id": "C4S2U7D02"
    }
  ],
  "cet4_202606_set2_u8": [
    {
      "transfer": "比较两种解释时，先说常见看法，再用 but 和 could 提出另一种可能。",
      "structure": "This is generally attributed to... 介绍常见解释；but 后说新研究的不同看法；could 保留不确定性。",
      "anchor": "This is generally attributed to backward thinking and conservative values, but new research shows that such differences could be linked to differences in the preferences of males and females.",
      "listening": "听到 but 后留意观点转折，保留 could 的“可能”，别听成已证明的因果关系。",
      "gloss": "人们通常把这种差异归因于旧观念和保守价值观，但新研究认为，它也可能与个人偏好有关。",
      "id": "C4S2U8D01"
    },
    {
      "transfer": "讲研究发现时，保留“研究观察到”的范围，不据此判断某个具体的人。",
      "structure": "分号连接两个观察结果；as early as... 强调出现得早；and 连接后面的两种倾向。",
      "anchor": "These differences appear as early as six years old; girls that age already show more interest in helping and caring for others than boys do, and they already exhibit a greater orientation toward family versus career.",
      "listening": "听清研究描述的是群体观察，不要把它套用到每一个孩子身上。",
      "gloss": "研究说这些差异早在六岁时就可能出现，并描述了受研究儿童的兴趣倾向。",
      "id": "C4S2U8D02"
    }
  ]
}''')
CONTENT = json.loads(r'''{
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
  },
  "cet4_202606_set2_u1": {
    "title": "百岁老人出售旧居",
    "vocabulary": [
      {
        "id": "C4S2U1V01",
        "anchor": "putting it on the market",
        "example": "They plan to put the apartment on the market next month. 他们计划下个月把公寓挂牌出售。",
        "gloss": "固定短语；把房产等挂牌出售。",
        "surface": "put on the market"
      },
      {
        "id": "C4S2U1V02",
        "anchor": "priced at some 170,000 pounds",
        "example": "The second-hand bike is priced at 80 pounds. 这辆二手自行车标价八十英镑。",
        "gloss": "搭配；标价为某个金额。some 在金额前表示大约。",
        "surface": "be priced at"
      },
      {
        "id": "C4S2U1V03",
        "anchor": "According to the estate agent",
        "example": "According to the notice, the library closes at six. 根据通知，图书馆六点关门。",
        "gloss": "介词短语；根据某人或某来源的信息。",
        "surface": "according to"
      },
      {
        "id": "C4S2U1V04",
        "anchor": "much of the house remains the same",
        "example": "The street has changed, but the old shop remains the same. 这条街变了，但那家老店仍和以前一样。",
        "gloss": "搭配；保持原样、没有变化。",
        "surface": "remain the same"
      },
      {
        "id": "C4S2U1V05",
        "anchor": "having lived in it through",
        "example": "She lived through several changes at work. 她经历了工作上的几次变化。",
        "gloss": "短语动词；经历一段时期或某件事。",
        "surface": "live through"
      },
      {
        "id": "C4S2U1V06",
        "anchor": "moving to a nursing home",
        "example": "His grandmother moved to a nursing home near her family. 他的祖母搬进了家人附近的养老院。",
        "gloss": "动词搭配；搬到养老院居住。",
        "surface": "move to a nursing home"
      }
    ]
  },
  "cet4_202606_set2_u2": {
    "title": "海上获救经历",
    "vocabulary": [
      {
        "id": "C4S2U2V01",
        "anchor": "key to his rescue",
        "example": "Clear directions were key to finding the venue. 清楚的指引是找到会场的关键。",
        "gloss": "搭配；对某结果至关重要，后接名词或动名词。",
        "surface": "key to"
      },
      {
        "id": "C4S2U2V02",
        "anchor": "making repairs",
        "example": "The workers are making repairs to the bridge. 工人们正在修理这座桥。",
        "gloss": "动词搭配；进行修理。",
        "surface": "make repairs"
      },
      {
        "id": "C4S2U2V03",
        "anchor": "prevent it from sinking",
        "example": "A lid can prevent the water from spilling. 盖子可以防止水洒出来。",
        "gloss": "句型；prevent something from doing something，防止某事发生。",
        "surface": "prevent ... from"
      },
      {
        "id": "C4S2U2V04",
        "anchor": "without success",
        "example": "We searched for the missing file without success. 我们找过那个丢失的文件，但没找到。",
        "gloss": "固定表达；尝试了但没有成功。",
        "surface": "without success"
      },
      {
        "id": "C4S2U2V05",
        "anchor": "swept the sailboat out to sea",
        "example": "A strong wind swept the small boat out to sea. 一阵大风把小船吹到了外海。",
        "gloss": "动词搭配；被风或水流带到海上。",
        "surface": "sweep ... out to sea"
      },
      {
        "id": "C4S2U2V06",
        "anchor": "send a distress signal",
        "example": "The crew sent a distress signal when the engine failed. 发动机故障后，船员发出了求救信号。",
        "gloss": "动词搭配；发出求救信号。",
        "surface": "send a distress signal"
      }
    ]
  },
  "cet4_202606_set2_u3": {
    "title": "学校预算与招生变化",
    "vocabulary": [
      {
        "id": "C4S2U3V01",
        "anchor": "make up for a decreased budget",
        "example": "Extra donations helped make up for the shortfall. 额外捐款帮助弥补了资金缺口。",
        "gloss": "短语动词；弥补不足或损失。",
        "surface": "make up for"
      },
      {
        "id": "C4S2U3V02",
        "anchor": "declining enrollment",
        "example": "The course was cancelled because of declining enrollment. 这门课程因报名人数下降而取消。",
        "gloss": "名词短语；入学或报名人数下降。",
        "surface": "declining enrollment"
      },
      {
        "id": "C4S2U3V03",
        "anchor": "a projected decline in enrollment",
        "example": "The plan is based on a projected decline in demand. 这项计划基于对需求下降的预测。",
        "gloss": "名词短语；预计会出现的下降，projected 表预测而非既成事实。",
        "surface": "a projected decline"
      },
      {
        "id": "C4S2U3V04",
        "anchor": "stay out of debt",
        "example": "They set a budget to stay out of debt. 他们制定预算以避免负债。",
        "gloss": "固定搭配；避免陷入债务。",
        "surface": "stay out of debt"
      },
      {
        "id": "C4S2U3V05",
        "anchor": "is set to close",
        "example": "The library is set to close for repairs next month. 图书馆定于下个月闭馆维修。",
        "gloss": "固定搭配；预计或计划要做某事。",
        "surface": "be set to"
      },
      {
        "id": "C4S2U3V06",
        "anchor": "per-pupil funding",
        "example": "The report compares per-pupil funding across schools. 这份报告比较了各校的生均经费。",
        "gloss": "名词短语；按每名学生计算的经费。",
        "surface": "per-pupil funding"
      }
    ]
  },
  "cet4_202606_set2_u4": {
    "title": "电话预订音乐剧门票",
    "vocabulary": [
      {
        "id": "C4S2U4V01",
        "anchor": "take the payment over the phone",
        "example": "The hotel can take payment over the phone. 酒店可以通过电话收款。",
        "gloss": "搭配；通过电话收取款项。",
        "surface": "take payment over the phone"
      },
      {
        "id": "C4S2U4V02",
        "anchor": "on a business trip",
        "example": "My colleague is away on a business trip this week. 我的同事本周出差了。",
        "gloss": "固定短语；在出差途中。",
        "surface": "on a business trip"
      },
      {
        "id": "C4S2U4V03",
        "anchor": "can sell out",
        "example": "Popular workshops can sell out within a day. 热门工作坊可能一天内就报满。",
        "gloss": "短语动词；票、商品或名额售罄。",
        "surface": "sell out"
      },
      {
        "id": "C4S2U4V04",
        "anchor": "reserve those for you",
        "example": "I can reserve a table for you at seven. 我可以帮你预订七点的桌位。",
        "gloss": "动词搭配；为某人预留或预订某物。",
        "surface": "reserve ... for you"
      },
      {
        "id": "C4S2U4V05",
        "anchor": "accept my card payment",
        "example": "Does this shop accept card payments? 这家店收银行卡付款吗？",
        "gloss": "动词搭配；接受刷卡付款。",
        "surface": "accept a card payment"
      },
      {
        "id": "C4S2U4V06",
        "anchor": "scared of heights",
        "example": "She is scared of heights, so she avoided the glass bridge. 她恐高，所以没走那座玻璃桥。",
        "gloss": "固定搭配；害怕高处。",
        "surface": "be scared of heights"
      }
    ]
  },
  "cet4_202606_set2_u5": {
    "title": "减少手机使用",
    "vocabulary": [
      {
        "id": "C4S2U5V01",
        "anchor": "haven’t turned it back on",
        "example": "I turned the lamp off and forgot to turn it back on. 我关掉台灯后忘了再打开。",
        "gloss": "短语动词；把已关闭的设备重新打开。",
        "surface": "turn ... back on"
      },
      {
        "id": "C4S2U5V02",
        "anchor": "I was shocked to realize",
        "example": "I was shocked to realize how late it was. 我惊讶地发现时间已经这么晚了。",
        "gloss": "句型；惊讶地意识到某件事。",
        "surface": "be shocked to realize"
      },
      {
        "id": "C4S2U5V03",
        "anchor": "pay in cash",
        "example": "You can pay in cash or by card. 你可以付现金，也可以刷卡。",
        "gloss": "固定搭配；用现金付款。",
        "surface": "pay in cash"
      },
      {
        "id": "C4S2U5V04",
        "anchor": "don’t have any choice but to",
        "example": "The train was cancelled, so we had no choice but to wait. 火车取消了，我们只好等。",
        "gloss": "固定句型；别无选择，只能做某事。",
        "surface": "have no choice but to"
      },
      {
        "id": "C4S2U5V05",
        "anchor": "an average of eight hours a day",
        "example": "He walks an average of five kilometers a day. 他平均每天走五公里。",
        "gloss": "数量表达；平均每天达到某个量。",
        "surface": "an average of ... a day"
      },
      {
        "id": "C4S2U5V06",
        "anchor": "spending too much time on social media",
        "example": "I spend too much time on emails in the morning. 我早上花太多时间处理邮件。",
        "gloss": "动词搭配；在某件事上花太多时间。",
        "surface": "spend too much time on"
      }
    ]
  },
  "cet4_202606_set2_u6": {
    "title": "换工作与薪资趋势",
    "vocabulary": [
      {
        "id": "C4S2U6V01",
        "anchor": "a three-month moving average",
        "example": "The chart shows a moving average of monthly sales. 图表显示月销售额的移动平均值。",
        "gloss": "统计表达；滚动计算一段时期的平均值。",
        "surface": "moving average"
      },
      {
        "id": "C4S2U6V02",
        "anchor": "gone up and down",
        "example": "The temperature has gone up and down all week. 这一周气温一直有升有降。",
        "gloss": "固定表达；上下波动。",
        "surface": "go up and down"
      },
      {
        "id": "C4S2U6V03",
        "anchor": "On average",
        "example": "On average, the trip takes forty minutes. 平均而言，这段行程需要四十分钟。",
        "gloss": "固定表达；平均来说，并非每个个体都如此。",
        "surface": "on average"
      },
      {
        "id": "C4S2U6V04",
        "anchor": "as a proportion of",
        "example": "We measured transport costs as a proportion of total spending. 我们将交通费用按总支出的占比来衡量。",
        "gloss": "介词短语；作为某个整体的比例。",
        "surface": "as a proportion of"
      },
      {
        "id": "C4S2U6V05",
        "anchor": "the gap is now closing",
        "example": "The gap between the two teams is closing. 两支队伍的差距正在缩小。",
        "gloss": "名词和动词搭配；差距正在缩小。",
        "surface": "the gap is closing"
      },
      {
        "id": "C4S2U6V06",
        "anchor": "wage growth is slowing down",
        "example": "Price growth is slowing down this year. 今年价格上涨的速度正在放缓。",
        "gloss": "动词短语；增长速度正在放慢，不等于已经下降。",
        "surface": "growth is slowing down"
      }
    ]
  },
  "cet4_202606_set2_u7": {
    "title": "深加工食品与饮食研究",
    "vocabulary": [
      {
        "id": "C4S2U7V01",
        "anchor": "even though both diets had the same amounts",
        "example": "She kept walking even though it was raining. 尽管下着雨，她仍继续走。",
        "gloss": "让步连接词；即使、尽管，提示后文与预期不同。",
        "surface": "even though"
      },
      {
        "id": "C4S2U7V02",
        "anchor": "independent of those nutrients",
        "example": "The committee made a decision independent of the sponsor. 委员会独立于赞助方作出了决定。",
        "gloss": "形容词搭配；不依赖于、不受某因素左右。",
        "surface": "independent of"
      },
      {
        "id": "C4S2U7V03",
        "anchor": "tends to be softer",
        "example": "The weather tends to be cooler near the coast. 海边的天气往往更凉爽。",
        "gloss": "动词搭配；通常会、有某种倾向，不表示每次都如此。",
        "surface": "tend to"
      },
      {
        "id": "C4S2U7V04",
        "anchor": "By the time the brain gets that signal",
        "example": "By the time we arrived, the meeting had started. 我们到达时，会议已经开始了。",
        "gloss": "时间连接结构；到某个时间点时，常强调另一件事已发生。",
        "surface": "by the time"
      },
      {
        "id": "C4S2U7V05",
        "anchor": "come at a cost to health",
        "example": "The convenience comes at a cost to privacy. 这种便利是以隐私为代价的。",
        "gloss": "固定搭配；某种好处伴随着代价。",
        "surface": "come at a cost to"
      },
      {
        "id": "C4S2U7V06",
        "anchor": "a higher risk of cancer and obesity",
        "example": "Long hours outdoors can mean a higher risk of sunburn. 长时间待在户外可能增加晒伤风险。",
        "gloss": "名词搭配；某种情况发生的风险更高。",
        "surface": "a higher risk of"
      }
    ]
  },
  "cet4_202606_set2_u8": {
    "title": "家庭分工与个人偏好研究",
    "vocabulary": [
      {
        "id": "C4S2U8V01",
        "anchor": "could be linked to",
        "example": "The delay could be linked to heavy traffic. 这次延误可能与交通拥堵有关。",
        "gloss": "被动搭配；可能与某事有关，could 保留不确定性。",
        "surface": "be linked to"
      },
      {
        "id": "C4S2U8V02",
        "anchor": "primary responsibility for such tasks",
        "example": "The editor has primary responsibility for the final draft. 编辑对终稿负主要责任。",
        "gloss": "名词搭配；对某事承担主要责任。",
        "surface": "primary responsibility for"
      },
      {
        "id": "C4S2U8V03",
        "anchor": "do not mean dissatisfaction",
        "example": "A quiet response does not mean dissatisfaction. 回应安静并不表示不满意。",
        "gloss": "句型；某现象并不必然意味着某结论。",
        "surface": "does not mean"
      },
      {
        "id": "C4S2U8V04",
        "anchor": "a greater orientation toward family versus career",
        "example": "The course has a practical orientation toward teamwork. 这门课更侧重团队合作的实际运用。",
        "gloss": "名词搭配；更偏向某一方向或目标。这里只学习表达，不把群体描述用于判断个人。",
        "surface": "an orientation toward"
      },
      {
        "id": "C4S2U8V05",
        "anchor": "Keep in mind, however",
        "example": "Keep in mind, however, that the shop closes early on Sundays. 不过要记住，这家店周日关门早。",
        "gloss": "提醒表达；不过，要记住某个补充条件。",
        "surface": "keep in mind"
      },
      {
        "id": "C4S2U8V06",
        "anchor": "as early as six years old",
        "example": "Some children begin swimming as early as four years old. 有些孩子四岁就开始学游泳。",
        "gloss": "时间表达；早在某个年龄或时间。",
        "surface": "as early as"
      }
    ]
  }
}''')
