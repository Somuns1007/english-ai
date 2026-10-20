"""Reviewed-source anchors and machine-authored learning notes; no exam answer keys.

Rights: project owner declared ownership in the implementation request (2026-09-10).
This declaration is not teacher verification. CET-4 Set 1 has its own reviewed-source draft.
"""
import json
from pathlib import Path

CONTENT_REVISION = 5
GUIDANCE = json.loads(r'''{
  "cet6_202606_set2_u7": [
    {
      "transfer": "用 already / not yet 描述自己某项技能的当前状态，不给孩子贴发展标签。",
      "structure": "old enough to... 与 but have not yet...；两条件共同限定阶段。",
      "anchor": "The 24-month time frame comes at an age when youngsters are old enough to appreciate poetic lyrics and snappy tunes, but have not yet started to be embarrassed by their mother and father's preferences.",
      "listening": "保留“已经／还没有”，不只记一个年龄数字。",
      "gloss": "孩子已经能够欣赏歌词和曲调，同时还没有开始因父母的偏好而感到难为情；这是材料对某时间段的描述。",
      "id": "S2U7D01",
      "pattern": "At this stage, the children are old enough to ___, but not yet ready to ___.",
      "examples": [
        "At this stage, the children are old enough to choose a book, but not yet ready to read it alone. 到这个阶段，孩子可以自己挑书，但还没准备好独自阅读。",
        "At this stage, the children are old enough to walk to class, but not yet ready to travel alone. 到这个阶段，孩子可以自己走去教室，但还没准备好独自出远门。"
      ],
      "pitfalls": [
        "old enough to 与 not yet ready to 表两种不同程度；不能只凭年龄断定个人能力。"
      ]
    },
    {
      "transfer": "用不强迫的方式向朋友推荐一首歌，并允许对方不喜欢。",
      "structure": "not to A, but instead B；while 表同时发生，不是此处的让步关系。",
      "anchor": "Dr. Egermann advises parents not to push their favourite music too hard on their children, but instead play it as background music while the child is playing.",
      "listening": "把“反对的方法”和“替代方法”分开说清。",
      "gloss": "材料中专家建议不要强迫孩子接受父母喜欢的音乐，而是在孩子玩耍时作为背景音乐播放。",
      "id": "S2U7D02",
      "pattern": "I would advise people not to ___, but instead to ___.",
      "examples": [
        "I would advise people not to rush, but instead to practise daily. 我会建议大家别着急，而是每天练习。",
        "I would advise people not to queue here, but instead to use the side entrance. 我会建议大家别在这里排队，改用侧门。"
      ],
      "pitfalls": [
        "advise someone not to A, but instead to B 两边用动词原形；别漏掉第二个 to。"
      ]
    }
  ],
  "cet6_202606_set2_u2": [
    {
      "transfer": "只练咨询表达，不让学生或模型判断实际药物是否可以合用。",
      "structure": "主句 came in；inquiring... 描述目的或伴随动作；that... 修饰前一种药；she was already taking 修饰另一种药。",
      "anchor": "A patient came in inquiring about a medication that had a potential interaction with another medication she was already taking.",
      "listening": "把“一种／另一种／已经服用”关系说清，不先要求抄出整句。",
      "gloss": "患者来咨询一种药物，它可能与她已经在服用的另一种药物发生相互作用。",
      "id": "S2U2D01",
      "pattern": "A visitor came in asking about ___ that might affect ___.",
      "examples": [
        "A visitor came in asking about a road closure that might affect the bus route. 一位访客来问道路封闭会不会影响公交路线。",
        "A visitor came in asking about a timetable change that might affect the tour. 一位访客来问时刻表变化会不会影响参观。"
      ],
      "pitfalls": [
        "that 从句修饰前面的变化或事件；might 表可能，不是已经确定。"
      ]
    },
    {
      "transfer": "说一次帮助他人后感到有成就感的经历；英文困难可先用中文构思。",
      "structure": "Some 限定范围；reported 限定证据来源；which 回指所述改善。",
      "anchor": "Some have reported seeing improvements in their health, which is really rewarding to see.",
      "listening": "复述时保留“部分”“报告”，不能说成方案已经被证明对所有人有效。",
      "gloss": "部分患者报告健康有所改善，看到这一点让说话人感到有成就感。",
      "id": "S2U2D02",
      "pattern": "Some have reported ___, which is encouraging to hear.",
      "examples": [
        "Some have reported shorter waits, which is encouraging to hear. 有人说等候时间缩短了，听到这消息让人鼓舞。",
        "Some have reported better access, which is encouraging to hear. 有人说使用更方便了，听到这消息让人鼓舞。"
      ],
      "pitfalls": [
        "Some 限定报告者范围；which 回指前面整件事，不要扩展成所有人都如此。"
      ]
    }
  ],
  "cet6_202606_set2_u3": [
    {
      "transfer": "表达某一天自己如何在两项任务中排优先级，不要求认同材料的群体概括。",
      "structure": "place A above B 表优先级；两个动名词结构分别是 A 与 B。",
      "anchor": "They often place fulfilling obligations to others above focusing on their own interests.",
      "listening": "先辨出 above 两边，再解释 often 的范围；不把倾向说成没有个人兴趣。",
      "gloss": "材料说他们往往把履行对他人的义务放在关注自身兴趣之前。",
      "id": "S2U3D01",
      "pattern": "They often place ___ above ___.",
      "examples": [
        "They often place safety above speed. 他们常把安全放在速度之前。",
        "They often place teamwork above personal recognition. 他们常把团队合作看得比个人表扬更重要。"
      ],
      "pitfalls": [
        "place A above B 是优先考虑 A；语序反过来意思就变了。"
      ]
    },
    {
      "transfer": "练习表达“两个情境的结果不同”，不自动生成文化能力画像。",
      "structure": "this correlation 回指前文；not the same 修饰强度，而不是直接否定关联存在。",
      "anchor": "But the strength of this correlation wasn't the same across cultures.",
      "listening": "遮字复述“不相同的是什么”，再决定是否收藏 correlation。",
      "gloss": "这种关联的强度在不同文化背景下并不相同。",
      "id": "S2U3D02",
      "pattern": "But the strength of this link wasn't the same across ___.",
      "examples": [
        "But the strength of this link wasn't the same across different schools. 但这种联系的强弱在不同学校并不一样。",
        "But the strength of this link wasn't the same across age groups. 但这种联系的强弱在不同年龄组并不一样。"
      ],
      "pitfalls": [
        "not the same 修饰联系的强度，不等于说联系完全不存在。"
      ]
    }
  ],
  "cet6_202606_set2_u1": [
    {
      "transfer": "用 either...or... 描述一次选时间或选地点的困难。",
      "structure": "either A or B；两项都构成障碍，而非一个好方案、一个坏方案。",
      "anchor": "Everything is either wildly expensive or already fully booked.",
      "listening": "先抓 either...or... 的两项，再听 fully booked；发音现象可参照该句下方的规则提示并自行重听。",
      "gloss": "能找到的选择要么贵得离谱，要么已经订满。",
      "id": "S2U1D01",
      "pattern": "Everything is either ___ or ___.",
      "examples": [
        "Everything is either too expensive or already booked. 每样东西要么太贵，要么早被订完。",
        "Everything is either too far away or closed today. 每个地方要么太远，要么今天不营业。"
      ],
      "pitfalls": [
        "either A or B 两边要保持语法平行；这里不是在提供可选的好方案。"
      ]
    },
    {
      "transfer": "改用温和、非婚姻冲突的情境表达“考虑到某人不喜欢什么，换一个安排”。",
      "structure": "Considering 给背景；if I tried / I would 表假设；that 回指前文的登高活动。",
      "anchor": "Considering [4] Jane is terrified of heights, I think if I tried to make her do that, I would come back divorced.",
      "listening": "先区分事实背景与假设后果，不把夸张语气当已经发生的离婚。",
      "gloss": "考虑到 Jane 恐高，男士夸张地说，如果强迫她去做，回来可能就离婚了。",
      "id": "S2U1D02",
      "pattern": "Considering ___, I think we should ___.",
      "examples": [
        "Considering the rain, I think we should stay inside. 考虑到下雨，我觉得我们应该待在室内。",
        "Considering the late hour, I think we should call tomorrow. 考虑到时间很晚，我觉得我们明天再打电话。"
      ],
      "pitfalls": [
        "Considering 后接名词或从句；不要把假设建议说成已经发生的事实。"
      ]
    }
  ],
  "cet6_202606_set2_u5": [
    {
      "transfer": "为下次学习选择一个可完成的目标，其他任务允许延后。",
      "structure": "However 修正或限制前文；only...when... 表条件；保留“材料称”，不变成本系统的普遍科学承诺。",
      "anchor": "However, follow-up research has discovered implementation intentions only work when you focus on one thing at a time.",
      "listening": "先说条件，再说方法；不要因为听到 work 就遗漏 only。",
      "gloss": "材料称后续研究发现，这种具体计划在一次专注一件事时才有效。",
      "id": "S2U5D01",
      "pattern": "However, this approach only works when you focus on ___.",
      "examples": [
        "However, this approach only works when you focus on one task at a time. 不过，这种做法只有在你一次专注一项任务时才有效。",
        "However, this approach only works when you focus on a clear goal. 不过，这种做法只有在你专注明确目标时才有效。"
      ],
      "pitfalls": [
        "only works when 是条件限制；不要省略 only 后把说法扩大成普遍保证。"
      ]
    },
    {
      "transfer": "学生给自己的练习设一个可调整的时间安排，不做“21天必成功”的承诺。",
      "structure": "The time... 作主语；depends on 表取决于；including 列举而非完整清单。",
      "anchor": "The time it takes to build a habit depends on many factors, including how difficult the habit is, your genetics and more.",
      "listening": "复述时保留“多种因素”，不把某个外部常见天数补进原文。",
      "gloss": "形成习惯需要多久取决于多种因素，材料没有给统一时间。",
      "id": "S2U5D02",
      "pattern": "The time it takes to ___ depends on many factors, including ___.",
      "examples": [
        "The time it takes to learn a language depends on many factors, including how often you practise. 学语言要花多久取决于很多因素，包括练习频率。",
        "The time it takes to repair the hall depends on many factors, including how much damage there is. 修好礼堂要花多久取决于很多因素，包括损坏程度。"
      ],
      "pitfalls": [
        "including 是举例，不表示列出的因素就是全部因素。"
      ]
    }
  ],
  "cet6_202606_set2_u4": [
    {
      "transfer": "用 give rise to 描述普通生活中一种变化及其结果。",
      "structure": "Those changes 回指前文过程；give rise to 表产生；that... 描述可见性。",
      "anchor": "Those changes then give rise to complex patterns at a larger scale that people can see.",
      "listening": "用“微观变化→可见图案”复述，再回听验证指代。",
      "gloss": "前面所说的变化随后在更大尺度上产生人们能看见的复杂图案。",
      "id": "S2U4D01",
      "pattern": "Those changes can give rise to ___ that people can see.",
      "examples": [
        "Those changes can give rise to new patterns that people can see. 这些变化可能产生人们看得见的新图案。",
        "Those changes can give rise to small cracks that people can see. 这些变化可能造成人们看得见的细小裂纹。"
      ],
      "pitfalls": [
        "give rise to 后接结果；that people can see 修饰结果，不是原因。"
      ]
    },
    {
      "transfer": "练“我们看到了某现象，但还不能确定原因或作用”的谨慎表达。",
      "structure": "not always 不是一概不知道；one 指 purpose，而不是 pattern。",
      "anchor": "But scientists do not always know the purpose of a pattern, or even if there is one.",
      "listening": "撤字后说出 one 的指代，再解释句子保留了什么不确定性。",
      "gloss": "科学家并不总知道图案的用途，甚至不一定知道它是否有用途。",
      "id": "S2U4D02",
      "pattern": "But we do not always know the purpose of ___, or even if there is one.",
      "examples": [
        "But we do not always know the purpose of a repeated symbol, or even if there is one. 但我们未必知道重复符号的用途，甚至未必知道它有没有用途。",
        "But we do not always know the purpose of a design, or even if there is one. 但我们未必知道某个设计的用途，甚至未必知道它有没有用途。"
      ],
      "pitfalls": [
        "one 指 purpose；not always 不是“永远不知道”。"
      ]
    }
  ],
  "cet6_202606_set2_u6": [
    {
      "transfer": "描述两个系统可能受不同因素影响，不要求学生讲正确的天体物理知识。",
      "structure": "But on Earth 对照前文；被动结构突出影响来源。",
      "anchor": "But on Earth, the overall temperature of the planet is dominated by the distribution of gases in our atmosphere.",
      "listening": "听后只填“对象—主要因素”，避免把冥王星的假说套给地球。",
      "gloss": "材料说地球整体温度主要受大气中气体分布影响。",
      "id": "S2U6D01",
      "pattern": "But here, ___ is dominated by ___.",
      "examples": [
        "But here, the schedule is dominated by staff availability. 不过这里的日程主要受人员是否有空影响。",
        "But here, the discussion is dominated by cost concerns. 不过这里的讨论主要围绕费用问题。"
      ],
      "pitfalls": [
        "被动式 be dominated by 后接影响来源；注意主语是受影响者。"
      ]
    },
    {
      "transfer": "用“我们观察到……，但还需要……验证”表达一个日常小判断。",
      "structure": "just a good guess 限定结论；based on A and B / not C 区分依据。",
      "anchor": "But right now, this is just a good guess, based on data from New Horizons and a sophisticated computer model, not direct observations of the haze's composition.",
      "listening": "听出数据、模型、直接观测三类信息的关系，不听到 model 就说已经证明。",
      "gloss": "在材料所述当时，它仍是依据数据和复杂计算机模型提出的推测，而不是对雾霾成分的直接观测结论。",
      "id": "S2U6D02",
      "pattern": "Right now, this is just a guess based on ___, not ___.",
      "examples": [
        "Right now, this is just a guess based on a few photos, not a full inspection. 目前这只是根据几张照片作出的猜测，并非完整检查的结论。",
        "Right now, this is just a guess based on early feedback, not final results. 目前这只是根据早期反馈作出的猜测，并非最终结果。"
      ],
      "pitfalls": [
        "just a guess 保留不确定性；based on 的两个依据用 not 分开，不能写成已证实。"
      ]
    }
  ],
  "cet4_202606_set2_u1": [
    {
      "transfer": "介绍一位亲人时，试着用两个并列动作说出生时间和居住经历。",
      "structure": "was born 和 spent 是并列的两件事；living in... 补充说明她这段时间住在哪里。",
      "anchor": "[1]Nancy Gifford was born months after the end of the First World War and spent 102 years living in her three-bedroom house in the Somerset Village of Street.",
      "listening": "先听出出生时间和居住时长，再把后面的地点接上。",
      "gloss": "南希在第一次世界大战结束几个月后出生，并在萨默塞特郡斯特里特村的三居室房子里住了102年。",
      "id": "C4S2U1D01",
      "pattern": "___ was born in ___ and spent most of her life in the same town.",
      "examples": [
        "Maya was born in York and spent most of her life in the same town. 玛雅出生在约克，一生大部分时间都住在那里。",
        "Lina was born in Bath and spent most of her life in the same town. 莉娜出生在巴斯，一生大部分时间都住在那里。"
      ],
      "pitfalls": [
        "并列动词 was born 和 spent 要保持时态一致；出生地前用 in。"
      ]
    },
    {
      "transfer": "说一件现在要做的事，再用 having done 补充之前的经历。",
      "structure": "主句是 She is now putting it on the market；having lived... 补充她此前的居住经历。",
      "anchor": "She is now putting it on the market, having lived in it through the Second World War and the invention of television.",
      "listening": "听到 having lived 后，继续听她住过的历史时期，别把它当成新的主句。",
      "gloss": "她现在正把房子挂牌出售；在此之前，她一直住在那里，经历了二战和电视的发明。",
      "id": "C4S2U1D02",
      "pattern": "I'm putting ___ on the market, having lived there for years.",
      "examples": [
        "I'm putting my flat on the market, having lived there for years. 我住了多年，现在要把公寓挂牌出售。",
        "I'm putting my house on the market, having lived there for years. 我住了多年，现在要把房子挂牌出售。"
      ],
      "pitfalls": [
        "having lived 表示先前的经历；不能用它表达尚未发生的居住。"
      ]
    }
  ],
  "cet4_202606_set2_u2": [
    {
      "transfer": "介绍一位完成挑战的人，并用 by doing 说他是怎么做到的。",
      "structure": "who survived... 修饰 a man；by eating... 说明他靠什么维持生存。",
      "anchor": "The navy rescued a man who survived 24 days floating in the sea on a boat by eating tomato sauce and vegetable powder.",
      "listening": "先抓住被救的人，再听 24 days 和 by 后面的生存方式。",
      "gloss": "海军救起了一名男子；他在海上漂了24天，靠番茄酱和蔬菜粉活了下来。",
      "id": "C4S2U2D01",
      "pattern": "The team helped ___, who had spent ___ waiting for help.",
      "examples": [
        "The team helped a hiker, who had spent hours waiting for help. 队员帮助了一位等候救援数小时的徒步者。",
        "The team helped a driver, who had spent the night waiting for help. 队员帮助了一位等了整夜的司机。"
      ],
      "pitfalls": [
        "who 指前面的被帮助者；不要把从句误接到 team 上。"
      ]
    },
    {
      "transfer": "讲一次意外，用 when 和 while 交代事情发生时你正在做什么。",
      "structure": "told 后接一整段陈述；when 和 while 分别交代海流把船带走及他当时正在修船的时间关系。",
      "anchor": "The man told authorities that his experience began in December when currents swept the sailboat out to sea while he was making repairs.",
      "listening": "听到 when currents swept... 时，把它接到 his experience began，不要丢掉 while 后的修船背景。",
      "gloss": "男子告诉当局，他的经历始于12月：修船时，海流把帆船带到了外海。",
      "id": "C4S2U2D02",
      "pattern": "The trouble began when ___ happened while we were traveling.",
      "examples": [
        "The trouble began when a tire burst while we were traveling. 我们出行时轮胎爆了，麻烦就从那时开始。",
        "The trouble began when the engine stopped while we were traveling. 我们路上发动机停了，麻烦就从那时开始。"
      ],
      "pitfalls": [
        "when 说事件发生点，while 说同时持续的背景；不要把两者机械互换。"
      ]
    }
  ],
  "cet4_202606_set2_u3": [
    {
      "transfer": "说明一项安排时，依次交代计划、目的和原因。",
      "structure": "is set to close 表计划关闭；to make up for... 表目的；caused by... 说明预算减少的原因。",
      "anchor": "[5]The board of Denver public schools is set to close several elementary and middle schools to make up for a decreased budget caused by declining enrollment.",
      "listening": "按“关闭学校—弥补预算—招生下降”这条链听，不必先记住学校名称。",
      "gloss": "丹佛公立学校董事会准备关闭几所学校，以弥补因入学人数下降而减少的预算。",
      "id": "C4S2U3D01",
      "pattern": "The club is set to ___ to make up for a budget shortfall.",
      "examples": [
        "The club is set to raise fees to make up for a budget shortfall. 社团计划涨费以弥补预算缺口。",
        "The club is set to cancel the trip to make up for a budget shortfall. 社团计划取消旅行以弥补预算缺口。"
      ],
      "pitfalls": [
        "be set to 后接动词原形；to make up for 表目的，不表示结果已经实现。"
      ]
    },
    {
      "transfer": "列出两类不同标准时，用 as well as 连接，并说清各自的附加条件。",
      "structure": "with fewer than 215 students 和 with fewer than 275 students... 是由 as well as 连接的两类标准。",
      "anchor": "The school board approved criteria to close schools with fewer than 215 students, as well as schools with fewer than 275 students and a projected decline in enrollment.",
      "listening": "两个数字对应不同条件；第二类还带有预计招生下降这一条件。",
      "gloss": "学校董事会批准了关闭学校的标准：学生少于215人的学校，以及少于275人且预计招生继续下降的学校。",
      "id": "C4S2U3D02",
      "pattern": "The plan covers ___, as well as ___.",
      "examples": [
        "The plan covers day classes, as well as weekend workshops. 计划涵盖日间课程，也包括周末工作坊。",
        "The plan covers bus fares, as well as entrance fees. 计划涵盖公交费，也包括门票。"
      ],
      "pitfalls": [
        "as well as 表“以及”，不要把后面一项误读成前一项的例外。"
      ]
    }
  ],
  "cet4_202606_set2_u4": [
    {
      "transfer": "描述一件最近反复尝试的事，用 I've been trying to... 开头。",
      "structure": "I've been trying to... 表示到现在为止一直在尝试；for the musical... 和 on the evening... 依次补充订票对象与日期。",
      "anchor": "[8]I’ve been trying to book tickets for the musical Cats in London on the evening of May the 28th.",
      "listening": "先抓 I've been trying to book tickets，再听演出和日期。",
      "gloss": "我一直想订5月28日晚伦敦音乐剧《猫》的票。",
      "id": "C4S2U4D01",
      "pattern": "I've been trying to book ___ for ___.",
      "examples": [
        "I've been trying to book concert tickets for Friday evening. 我一直想订周五晚的音乐会门票。",
        "I've been trying to book a room for Saturday night. 我一直想订周六晚的房间。"
      ],
      "pitfalls": [
        "have been trying 表持续到现在的尝试；for 后接所订的时间，不是动作的原因。"
      ]
    },
    {
      "transfer": "向别人说明首选方案不可用，再用 but 提出可行替代。",
      "structure": "前半句 all the tickets... are sold out 说明限制；but 后给出另一个可选座位。",
      "anchor": "Actually, [10]all the tickets at the front are already sold out anyway, but I can offer you two upstairs near the middle.",
      "listening": "听到 but 就准备接收替代方案，不要只记住前排已经售罄。",
      "gloss": "前排的票已经卖完了，不过我可以给你楼上靠中间的两个座位。",
      "id": "C4S2U4D02",
      "pattern": "The ___ are sold out, but I can offer you ___.",
      "examples": [
        "The front seats are sold out, but I can offer you seats in the back. 前排座位卖完了，但我可以给你后排座位。",
        "The morning slots are sold out, but I can offer you an afternoon appointment. 上午时段满了，但我可以给你下午的预约。"
      ],
      "pitfalls": [
        "sold out 说售罄；but 后通常给出仍可选择的替代方案。"
      ]
    }
  ],
  "cet4_202606_set2_u5": [
    {
      "transfer": "说一次你通过记录或观察才意识到的习惯。",
      "structure": "that recorded... 修饰 app；how much time... 是 recorded 的内容；and 后转到说话人发现的结果。",
      "anchor": "[13]Well, I downloaded an app that recorded how much time I spent on my phone, and I was shocked to realize I was using my phone an average of eight hours a day.",
      "listening": "先听应用记录了什么，再听 shocked to realize 后的平均使用时长。",
      "gloss": "我下载了一个记录手机使用时间的应用，惊讶地发现自己平均每天用手机八小时。",
      "pattern": "I was shocked to realize I spent ___ a day on ___.",
      "examples": [
        "I was shocked to realize I spent two hours a day on email. 我惊讶地发现自己每天花两小时处理邮件。",
        "I was shocked to realize I spent an hour a day on my commute. 我惊讶地发现自己每天通勤要花一小时。"
      ],
      "pitfalls": [
        "spend 后面先接时间，再用 on 接活动或事物；不要说 spend two hours for email。"
      ],
      "id": "C4S2U5D01"
    },
    {
      "transfer": "解释自己为什么觉得某件事很难做到，用 That's why I don't see how...。",
      "structure": "why 引出原因；I don't see how... 表“我想不出怎么能……”，里面还有 how 引导的从句。",
      "anchor": "That is really why I don’t see how anyone could live without a mobile phone.",
      "listening": "不要把 don't see how 误解成没看见；这里表达的是难以想象。",
      "gloss": "这正是我想不出有人怎么能不用手机生活的原因。",
      "pattern": "I don’t see how ___ could work without ___.",
      "examples": [
        "I don’t see how the team could work without a shared calendar. 我想不出团队不用共享日历怎么开展工作。",
        "I don’t see how this printer could work without a new cartridge. 我想不出这台打印机不换墨盒怎么运作。"
      ],
      "pitfalls": [
        "这里的 see how 是“想得出办法”，不是用眼睛“看见”；后面要接完整从句。"
      ],
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
      "id": "C4S2U6D01",
      "pattern": "The latest figures show that ___ rose in ___.",
      "examples": [
        "The latest figures show that sales rose in June. 最新数据显示六月销售额上升。",
        "The latest figures show that wages rose in March. 最新数据显示三月工资上涨。"
      ],
      "pitfalls": [
        "figures 是数据，show that 后接完整从句；不要把 rose 当名词“玫瑰”。"
      ]
    },
    {
      "transfer": "表达带保留的判断时，用 likely，再补充支持判断的现象。",
      "structure": "because 说明就业市场可能降温的原因；even a shortage... 表即使缺工也没扭转后面的趋势；分号连接补充说明。",
      "anchor": "[18]The labor market is likely cooling, because even a shortage of workers isn’t overcoming the historic imbalance between employers and employees in the US; the volume of income that workers take home as a proportion of what the US economy produces is still falling.",
      "listening": "先听 likely cooling 这一判断，再听 even 引出的让步和分号后的收入占比。",
      "gloss": "就业市场可能在降温，因为即使缺少工人也没扭转劳资之间长期失衡的局面；劳动收入占经济产出的比例仍在下降。",
      "id": "C4S2U6D02",
      "pattern": "The ___ is likely slowing, because ___.",
      "examples": [
        "The housing market is likely slowing, because fewer homes sold this month. 房地产市场可能在放缓，因为本月成交房屋减少了。",
        "The local economy is likely slowing, because new orders have fallen. 当地经济可能在放缓，因为新订单减少了。"
      ],
      "pitfalls": [
        "likely 表推测，不可写成确定结论；because 后面要接完整原因从句。"
      ]
    }
  ],
  "cet4_202606_set2_u7": [
    {
      "transfer": "介绍一种便利做法后，用 but 说明它可能带来的代价。",
      "structure": "破折号之间解释 highly processed foods；but 后转向研究发现的健康代价。",
      "anchor": "Highly processed foods—the kinds made with lots of sugar, fat and salt—make up as much as sixty percent of the average American diet, [19]but a new study shows that their low price and convenience come at a cost to health.",
      "listening": "先听食物的定义和占比，再把 but 后面的信息当作重点转折。",
      "gloss": "高度加工食品占美国人平均饮食很大一部分，但一项新研究指出，便宜和方便可能有健康代价。",
      "id": "C4S2U7D01",
      "pattern": "___ may be convenient, but it can come at a cost to ___.",
      "examples": [
        "Fast delivery may be convenient, but it can come at a cost to the environment. 快速配送虽方便，却可能给环境带来代价。",
        "Working late may be convenient, but it can come at a cost to sleep. 加班虽方便安排，却可能牺牲睡眠。"
      ],
      "pitfalls": [
        "but 标出转折；come at a cost to 后接受损的一方或事物。"
      ]
    },
    {
      "transfer": "解释一件事为什么来不及时，用 not give... enough time to...。",
      "structure": "if you're eating more quickly 是条件；you're not giving... enough time to... 表没有留足时间；后面两个 that 从句说明大脑收到什么信号。",
      "anchor": "One theory is that if you’re eating more quickly, you’re not giving your gut enough time to signal to your brain that you’ve had enough calories and that you’re full.",
      "listening": "先听进食速度，再追踪“肠道发信号—大脑收到信号”这条顺序。",
      "gloss": "一种理论认为，吃得太快时，肠道还没来得及告诉大脑已经吃够了。",
      "id": "C4S2U7D02",
      "pattern": "If you ___ too quickly, you may not give yourself enough time to ___.",
      "examples": [
        "If you answer too quickly, you may not give yourself enough time to check. 回答太快可能不给自己留够检查时间。",
        "If you leave too quickly, you may not give yourself enough time to pack. 离开太匆忙可能来不及收拾。"
      ],
      "pitfalls": [
        "if 从句用一般现在时表达条件；give ... time to 后接动词原形。"
      ]
    }
  ],
  "cet4_202606_set2_u8": [
    {
      "transfer": "比较两种解释时，先说常见看法，再用 but 和 could 提出另一种可能。",
      "structure": "This is generally attributed to... 介绍常见解释；but 后说新研究的不同看法；could 保留不确定性。",
      "anchor": "This is generally attributed to backward thinking and conservative values, but new research shows that such differences could be linked to differences in the preferences of males and females.",
      "listening": "听到 but 后留意观点转折，保留 could 的“可能”，别听成已证明的因果关系。",
      "gloss": "人们通常把这种差异归因于旧观念和保守价值观，但新研究认为，它也可能与个人偏好有关。",
      "id": "C4S2U8D01",
      "pattern": "This is often attributed to ___, but new evidence suggests ___.",
      "examples": [
        "This is often attributed to bad weather, but new evidence suggests a scheduling problem. 人们常将此归因于坏天气，但新证据指向排期问题。",
        "This is often attributed to low demand, but new evidence suggests a supply issue. 人们常将此归因于需求低，但新证据指向供应问题。"
      ],
      "pitfalls": [
        "be attributed to 说常见解释；suggests 保留证据仍待判断的语气。"
      ]
    },
    {
      "transfer": "讲研究发现时，保留“研究观察到”的范围，不据此判断某个具体的人。",
      "structure": "分号连接两个观察结果；as early as... 强调出现得早；and 连接后面的两种倾向。",
      "anchor": "These differences appear as early as six years old; girls that age already show more interest in helping and caring for others than boys do, and they already exhibit a greater orientation toward family versus career.",
      "listening": "听清研究描述的是群体观察，不要把它套用到每一个孩子身上。",
      "gloss": "研究说这些差异早在六岁时就可能出现，并描述了受研究儿童的兴趣倾向。",
      "id": "C4S2U8D02",
      "pattern": "These differences appear as early as ___; they are visible in ___.",
      "examples": [
        "These differences appear as early as week one; they are visible in attendance records. 这些差异第一周就出现了，出勤记录里能看到。",
        "These differences appear as early as spring; they are visible in the garden. 这些差异早在春天就出现了，在花园里可以看到。"
      ],
      "pitfalls": [
        "as early as 强调出现时间早；分号两边都要是完整句子。"
      ]
    }
  ]
}''')


# Rule-based listening cues. These describe likely pronunciation patterns,
# not verified observations of the recording. Batch authoring waits for review
# of the CET-4 unit 5 sample.
SOUND_NOTES = json.loads(r'''{
  "cet4_202606_set2_u5": [
    {
      "id": "C4S2U5P01",
      "segment_id": "cet4_202606_set2_u5_seg001",
      "anchor": "you answered",
      "type": "连读",
      "pair": [
        "you",
        "answered"
      ],
      "note": "you 的元音接 answered 开头的元音，两个词之间通常不会明显停顿；听时留意 answered。"
    },
    {
      "id": "C4S2U5P02",
      "segment_id": "cet4_202606_set2_u5_seg002",
      "anchor": "turned off",
      "type": "连读",
      "pair": [
        "turned",
        "off"
      ],
      "note": "turned 末尾的 /d/ 接 off 开头的元音，通常会连着说；别把 off 漏掉。"
    },
    {
      "id": "C4S2U5P10",
      "segment_id": "cet4_202606_set2_u5_seg002",
      "anchor": "back on",
      "type": "连读",
      "pair": [
        "back",
        "on"
      ],
      "note": "back 末尾的 /k/ 接 on 开头的元音，通常会连在一起；这两个词表示重新打开。"
    },
    {
      "id": "C4S2U5P03",
      "segment_id": "cet4_202606_set2_u5_seg003",
      "anchor": "would you",
      "type": "同化",
      "pair": [
        "would",
        "you"
      ],
      "note": "would 的 /d/ 遇到 you 开头的 /j/，连说时可能发生同化；听时结合整句判断。"
    },
    {
      "id": "C4S2U5P04",
      "segment_id": "cet4_202606_set2_u5_seg004",
      "anchor": "spent on",
      "type": "喉塞化",
      "pair": [
        "spent",
        "on"
      ],
      "note": "spent 末尾的 /t/ 遇到 on 的元音，在一些口音里可能喉塞化；不要以为少了 spent。"
    },
    {
      "id": "C4S2U5P05",
      "segment_id": "cet4_202606_set2_u5_seg005",
      "anchor": "and into",
      "type": "连读",
      "pair": [
        "and",
        "into"
      ],
      "note": "and 末尾的 /d/ 接 into 的元音，通常会连着说；注意后面还有 into the night。"
    },
    {
      "id": "C4S2U5P06",
      "segment_id": "cet4_202606_set2_u5_seg006",
      "anchor": "time on",
      "type": "连读",
      "pair": [
        "time",
        "on"
      ],
      "note": "time 末尾的 /m/ 接 on 的元音，通常会连在一起；听时抓住 on 后的 social media。"
    },
    {
      "id": "C4S2U5P07",
      "segment_id": "cet4_202606_set2_u5_seg007",
      "anchor": "shopping online",
      "type": "连读",
      "pair": [
        "shopping",
        "online"
      ],
      "note": "shopping 末尾的辅音接 online 开头的元音，通常会连着说；不要漏掉 online。"
    },
    {
      "id": "C4S2U5P08",
      "segment_id": "cet4_202606_set2_u5_seg008",
      "anchor": "pay in",
      "type": "连读",
      "pair": [
        "pay",
        "in"
      ],
      "note": "pay 和 in 的元音相接，通常不会明显停顿；听时留意后面的 cash。"
    },
    {
      "id": "C4S2U5P09",
      "segment_id": "cet4_202606_set2_u5_seg009",
      "anchor": "great for",
      "type": "失爆",
      "pair": [
        "great",
        "for"
      ],
      "note": "great 末尾的 /t/ 后接 for 的辅音，通常可以只做闭塞而不明显爆破。"
    }
  ],
  "cet6_202606_set2_u1": [
    {
      "id": "S2U1P01",
      "segment_id": "cet6_202606_set2_u1_seg002",
      "anchor": "wedding anniversary",
      "type": "连读",
      "pair": [
        "wedding",
        "anniversary"
      ],
      "note": "wedding 的末音接 anniversary 开头的元音，连说时通常少有停顿；听时把两个词分开理解。",
      "legacy_question_number": 1
    },
    {
      "id": "S2U1P02",
      "segment_id": "cet6_202606_set2_u1_seg004",
      "anchor": "find accommodation",
      "type": "连读",
      "pair": [
        "find",
        "accommodation"
      ],
      "note": "find 的末音接 accommodation 开头的元音，连说时通常少有停顿；听时把两个词分开理解。",
      "legacy_question_number": 2
    },
    {
      "id": "S2U1P03",
      "segment_id": "cet6_202606_set2_u1_seg005",
      "anchor": "couple of",
      "type": "连读",
      "pair": [
        "couple",
        "of"
      ],
      "note": "couple 的末音接 of 开头的元音，连说时通常少有停顿；听时把两个词分开理解。",
      "legacy_question_number": 3
    },
    {
      "id": "S2U1P04",
      "segment_id": "cet6_202606_set2_u1_seg008",
      "anchor": "terrified of",
      "type": "连读",
      "pair": [
        "terrified",
        "of"
      ],
      "note": "terrified 的末音接 of 开头的元音，连说时通常少有停顿；听时把两个词分开理解。",
      "legacy_question_number": 4
    },
    {
      "id": "S2U1P05",
      "segment_id": "cet6_202606_set2_u1_seg001",
      "anchor": "Are",
      "type": "弱读",
      "word": "Are",
      "weak": "/ə/",
      "note": "Are 是虚词，连续语流中常可弱读为 /ə/；听时注意不要漏掉。"
    },
    {
      "id": "S2U1P06",
      "segment_id": "cet6_202606_set2_u1_seg003",
      "anchor": "cosmopolitan",
      "type": "闪音",
      "word": "cosmopolitan",
      "note": "cosmopolitan 中间的 /t/ 或 /d/ 位于非重读元音前，在美音中可能读成闪音。"
    },
    {
      "id": "S2U1P07",
      "segment_id": "cet6_202606_set2_u1_seg006",
      "anchor": "city",
      "type": "闪音",
      "word": "city",
      "note": "city 中间的 /t/ 或 /d/ 位于非重读元音前，在美音中可能读成闪音。"
    },
    {
      "id": "S2U1P08",
      "segment_id": "cet6_202606_set2_u1_seg007",
      "anchor": "but you",
      "type": "同化",
      "pair": [
        "but",
        "you"
      ],
      "note": "but 末尾的辅音遇到 you 开头的 /j/，连说时可能同化；结合整句判断。"
    }
  ],
  "cet6_202606_set2_u2": [
    {
      "id": "S2U2P01",
      "segment_id": "cet6_202606_set2_u2_seg002",
      "anchor": "talking to",
      "type": "弱读",
      "word": "to",
      "weak": "/tə/",
      "note": "to 是虚词，连续语流中常可弱读为 /tə/；听时注意不要漏掉。",
      "legacy_question_number": 5
    },
    {
      "id": "S2U2P02",
      "segment_id": "cet6_202606_set2_u2_seg005",
      "anchor": "ended up",
      "type": "连读",
      "pair": [
        "ended",
        "up"
      ],
      "note": "ended 的末音接 up 开头的元音，连说时通常少有停顿；听时把两个词分开理解。",
      "legacy_question_number": 6
    },
    {
      "id": "S2U2P03",
      "segment_id": "cet6_202606_set2_u2_seg010",
      "anchor": "working on",
      "type": "连读",
      "pair": [
        "working",
        "on"
      ],
      "note": "working 的末音接 on 开头的元音，连说时通常少有停顿；听时把两个词分开理解。",
      "legacy_question_number": 7
    },
    {
      "id": "S2U2P04",
      "segment_id": "cet6_202606_set2_u2_seg015",
      "anchor": "adherence is",
      "type": "连读",
      "pair": [
        "adherence",
        "is"
      ],
      "note": "adherence 的末音接 is 开头的元音，连说时通常少有停顿；听时把两个词分开理解。",
      "legacy_question_number": 8
    },
    {
      "id": "S2U2P05",
      "segment_id": "cet6_202606_set2_u2_seg001",
      "anchor": "it going",
      "type": "失爆",
      "pair": [
        "it",
        "going"
      ],
      "note": "it 末尾的爆破音后面紧接 going 的辅音，通常不会明显爆破；留意后一个词。"
    },
    {
      "id": "S2U2P06",
      "segment_id": "cet6_202606_set2_u2_seg003",
      "anchor": "about a",
      "type": "喉塞化",
      "pair": [
        "about",
        "a"
      ],
      "note": "about 末尾的 /t/ 后接 a 开头的元音，在一些口音中可能喉塞化。"
    },
    {
      "id": "S2U2P07",
      "segment_id": "cet6_202606_set2_u2_seg004",
      "anchor": "did you",
      "type": "同化",
      "pair": [
        "did",
        "you"
      ],
      "note": "did 末尾的辅音遇到 you 开头的 /j/，连说时可能同化；结合整句判断。"
    },
    {
      "id": "S2U2P08",
      "segment_id": "cet6_202606_set2_u2_seg006",
      "anchor": "great. You",
      "type": "同化",
      "pair": [
        "great",
        "You"
      ],
      "note": "great 末尾的辅音遇到 You 开头的 /j/，连说时可能同化；结合整句判断。"
    },
    {
      "id": "S2U2P09",
      "segment_id": "cet6_202606_set2_u2_seg007",
      "anchor": "Totally",
      "type": "闪音",
      "word": "Totally",
      "note": "Totally 中间的 /t/ 或 /d/ 位于非重读元音前，在美音中可能读成闪音。"
    },
    {
      "id": "S2U2P10",
      "segment_id": "cet6_202606_set2_u2_seg008",
      "anchor": "opposite is",
      "type": "喉塞化",
      "pair": [
        "opposite",
        "is"
      ],
      "note": "opposite 末尾的 /t/ 后接 is 开头的元音，在一些口音中可能喉塞化。"
    },
    {
      "id": "S2U2P11",
      "segment_id": "cet6_202606_set2_u2_seg009",
      "anchor": "get their",
      "type": "失爆",
      "pair": [
        "get",
        "their"
      ],
      "note": "get 末尾的爆破音后面紧接 their 的辅音，通常不会明显爆破；留意后一个词。"
    },
    {
      "id": "S2U2P12",
      "segment_id": "cet6_202606_set2_u2_seg011",
      "anchor": "That",
      "type": "弱读",
      "word": "That",
      "weak": "/ðət/",
      "note": "That 是虚词，连续语流中常可弱读为 /ðət/；听时注意不要漏掉。"
    },
    {
      "id": "S2U2P13",
      "segment_id": "cet6_202606_set2_u2_seg012",
      "anchor": "medications",
      "type": "闪音",
      "word": "medications",
      "note": "medications 中间的 /t/ 或 /d/ 位于非重读元音前，在美音中可能读成闪音。"
    },
    {
      "id": "S2U2P14",
      "segment_id": "cet6_202606_set2_u2_seg013",
      "anchor": "great to",
      "type": "失爆",
      "pair": [
        "great",
        "to"
      ],
      "note": "great 末尾的爆破音后面紧接 to 的辅音，通常不会明显爆破；留意后一个词。"
    },
    {
      "id": "S2U2P15",
      "segment_id": "cet6_202606_set2_u2_seg014",
      "anchor": "Yes, absolutely",
      "type": "连读",
      "pair": [
        "Yes",
        "absolutely"
      ],
      "note": "Yes 的末音接 absolutely 开头的元音，连说时通常少有停顿；听时把两个词分开理解。"
    },
    {
      "id": "S2U2P16",
      "segment_id": "cet6_202606_set2_u2_seg016",
      "anchor": "but I'm",
      "type": "喉塞化",
      "pair": [
        "but",
        "I'm"
      ],
      "note": "but 末尾的 /t/ 后接 I'm 开头的元音，在一些口音中可能喉塞化。"
    }
  ],
  "cet6_202606_set2_u3": [
    {
      "id": "S2U3P01",
      "segment_id": "cet6_202606_set2_u3_seg002",
      "anchor": "likely to",
      "type": "弱读",
      "word": "to",
      "weak": "/tə/",
      "note": "to 是虚词，连续语流中常可弱读为 /tə/；听时注意不要漏掉。",
      "legacy_question_number": 9
    },
    {
      "id": "S2U3P02",
      "segment_id": "cet6_202606_set2_u3_seg003",
      "anchor": "less important",
      "type": "连读",
      "pair": [
        "less",
        "important"
      ],
      "note": "less 的末音接 important 开头的元音，连说时通常少有停顿；听时把两个词分开理解。",
      "legacy_question_number": 10
    },
    {
      "id": "S2U3P03",
      "segment_id": "cet6_202606_set2_u3_seg008",
      "anchor": "effect of",
      "type": "喉塞化",
      "pair": [
        "effect",
        "of"
      ],
      "note": "effect 末尾的 /t/ 后接 of 开头的元音，在一些口音中可能喉塞化。",
      "legacy_question_number": 11
    },
    {
      "id": "S2U3P04",
      "segment_id": "cet6_202606_set2_u3_seg001",
      "anchor": "at least",
      "type": "失爆",
      "pair": [
        "at",
        "least"
      ],
      "note": "at 末尾的爆破音后面紧接 least 的辅音，通常不会明显爆破；留意后一个词。"
    },
    {
      "id": "S2U3P05",
      "segment_id": "cet6_202606_set2_u3_seg004",
      "anchor": "motivated",
      "type": "闪音",
      "word": "motivated",
      "note": "motivated 中间的 /t/ 或 /d/ 位于非重读元音前，在美音中可能读成闪音。"
    },
    {
      "id": "S2U3P06",
      "segment_id": "cet6_202606_set2_u3_seg005",
      "anchor": "are",
      "type": "弱读",
      "word": "are",
      "weak": "/ə/",
      "note": "are 是虚词，连续语流中常可弱读为 /ə/；听时注意不要漏掉。"
    },
    {
      "id": "S2U3P07",
      "segment_id": "cet6_202606_set2_u3_seg006",
      "anchor": "data",
      "type": "闪音",
      "word": "data",
      "note": "data 中间的 /t/ 或 /d/ 位于非重读元音前，在美音中可能读成闪音。"
    },
    {
      "id": "S2U3P08",
      "segment_id": "cet6_202606_set2_u3_seg007",
      "anchor": "enjoyment and",
      "type": "喉塞化",
      "pair": [
        "enjoyment",
        "and"
      ],
      "note": "enjoyment 末尾的 /t/ 后接 and 开头的元音，在一些口音中可能喉塞化。"
    },
    {
      "id": "S2U3P09",
      "segment_id": "cet6_202606_set2_u3_seg009",
      "anchor": "mathematics",
      "type": "闪音",
      "word": "mathematics",
      "note": "mathematics 中间的 /t/ 或 /d/ 位于非重读元音前，在美音中可能读成闪音。"
    }
  ],
  "cet6_202606_set2_u4": [
    {
      "id": "S2U4P01",
      "segment_id": "cet6_202606_set2_u4_seg003",
      "anchor": "arrangement of",
      "type": "喉塞化",
      "pair": [
        "arrangement",
        "of"
      ],
      "note": "arrangement 末尾的 /t/ 后接 of 开头的元音，在一些口音中可能喉塞化。",
      "legacy_question_number": 12
    },
    {
      "id": "S2U4P02",
      "segment_id": "cet6_202606_set2_u4_seg004",
      "anchor": "materials undergo",
      "type": "连读",
      "pair": [
        "materials",
        "undergo"
      ],
      "note": "materials 的末音接 undergo 开头的元音，连说时通常少有停顿；听时把两个词分开理解。",
      "legacy_question_number": 13
    },
    {
      "id": "S2U4P03",
      "segment_id": "cet6_202606_set2_u4_seg005",
      "anchor": "delicate frozen",
      "type": "失爆",
      "pair": [
        "delicate",
        "frozen"
      ],
      "note": "delicate 末尾的爆破音后面紧接 frozen 的辅音，通常不会明显爆破；留意后一个词。",
      "legacy_question_number": 14
    },
    {
      "id": "S2U4P04",
      "segment_id": "cet6_202606_set2_u4_seg008",
      "anchor": "generate a",
      "type": "喉塞化",
      "pair": [
        "generate",
        "a"
      ],
      "note": "generate 末尾的 /t/ 后接 a 开头的元音，在一些口音中可能喉塞化。",
      "legacy_question_number": 15
    },
    {
      "id": "S2U4P05",
      "segment_id": "cet6_202606_set2_u4_seg001",
      "anchor": "does",
      "type": "弱读",
      "word": "does",
      "weak": "/dəz/",
      "note": "does 是虚词，连续语流中常可弱读为 /dəz/；听时注意不要漏掉。"
    },
    {
      "id": "S2U4P06",
      "segment_id": "cet6_202606_set2_u4_seg002",
      "anchor": "patterns",
      "type": "闪音",
      "word": "patterns",
      "note": "patterns 中间的 /t/ 或 /d/ 位于非重读元音前，在美音中可能读成闪音。"
    },
    {
      "id": "S2U4P07",
      "segment_id": "cet6_202606_set2_u4_seg006",
      "anchor": "bent shape",
      "type": "失爆",
      "pair": [
        "bent",
        "shape"
      ],
      "note": "bent 末尾的爆破音后面紧接 shape 的辅音，通常不会明显爆破；留意后一个词。"
    },
    {
      "id": "S2U4P08",
      "segment_id": "cet6_202606_set2_u4_seg007",
      "anchor": "the",
      "type": "弱读",
      "word": "the",
      "weak": "/ðə/",
      "note": "the 是虚词，连续语流中常可弱读为 /ðə/；听时注意不要漏掉。"
    }
  ],
  "cet6_202606_set2_u5": [
    {
      "id": "S2U5P01",
      "segment_id": "cet6_202606_set2_u5_seg003",
      "anchor": "Making a",
      "type": "连读",
      "pair": [
        "Making",
        "a"
      ],
      "note": "Making 的末音接 a 开头的元音，连说时通常少有停顿；听时把两个词分开理解。",
      "legacy_question_number": 16
    },
    {
      "id": "S2U5P02",
      "segment_id": "cet6_202606_set2_u5_seg007",
      "anchor": "filled out",
      "type": "连读",
      "pair": [
        "filled",
        "out"
      ],
      "note": "filled 的末音接 out 开头的元音，连说时通常少有停顿；听时把两个词分开理解。",
      "legacy_question_number": 17
    },
    {
      "id": "S2U5P03",
      "segment_id": "cet6_202606_set2_u5_seg009",
      "anchor": "focus on",
      "type": "连读",
      "pair": [
        "focus",
        "on"
      ],
      "note": "focus 的末音接 on 开头的元音，连说时通常少有停顿；听时把两个词分开理解。",
      "legacy_question_number": 18
    },
    {
      "id": "S2U5P04",
      "segment_id": "cet6_202606_set2_u5_seg001",
      "anchor": "included",
      "type": "闪音",
      "word": "included",
      "note": "included 中间的 /t/ 或 /d/ 位于非重读元音前，在美音中可能读成闪音。"
    },
    {
      "id": "S2U5P05",
      "segment_id": "cet6_202606_set2_u5_seg002",
      "anchor": "and you",
      "type": "同化",
      "pair": [
        "and",
        "you"
      ],
      "note": "and 末尾的辅音遇到 you 开头的 /j/，连说时可能同化；结合整句判断。"
    },
    {
      "id": "S2U5P06",
      "segment_id": "cet6_202606_set2_u5_seg004",
      "anchor": "As you'll",
      "type": "同化",
      "pair": [
        "As",
        "you'll"
      ],
      "note": "As 末尾的辅音遇到 you'll 开头的 /j/，连说时可能同化；结合整句判断。"
    },
    {
      "id": "S2U5P07",
      "segment_id": "cet6_202606_set2_u5_seg005",
      "anchor": "that you",
      "type": "同化",
      "pair": [
        "that",
        "you"
      ],
      "note": "that 末尾的辅音遇到 you 开头的 /j/，连说时可能同化；结合整句判断。"
    },
    {
      "id": "S2U5P08",
      "segment_id": "cet6_202606_set2_u5_seg006",
      "anchor": "asked people",
      "type": "失爆",
      "pair": [
        "asked",
        "people"
      ],
      "note": "asked 末尾的爆破音后面紧接 people 的辅音，通常不会明显爆破；留意后一个词。"
    },
    {
      "id": "S2U5P09",
      "segment_id": "cet6_202606_set2_u5_seg008",
      "anchor": "has",
      "type": "弱读",
      "word": "has",
      "weak": "/əz/",
      "note": "has 是虚词，连续语流中常可弱读为 /əz/；听时注意不要漏掉。"
    },
    {
      "id": "S2U5P10",
      "segment_id": "cet6_202606_set2_u5_seg010",
      "anchor": "is, your",
      "type": "同化",
      "pair": [
        "is",
        "your"
      ],
      "note": "is 末尾的辅音遇到 your 开头的 /j/，连说时可能同化；结合整句判断。"
    }
  ],
  "cet6_202606_set2_u6": [
    {
      "id": "S2U6P01",
      "segment_id": "cet6_202606_set2_u6_seg003",
      "anchor": "haze in",
      "type": "连读",
      "pair": [
        "haze",
        "in"
      ],
      "note": "haze 的末音接 in 开头的元音，连说时通常少有停顿；听时把两个词分开理解。",
      "legacy_question_number": 19
    },
    {
      "id": "S2U6P02",
      "segment_id": "cet6_202606_set2_u6_seg007",
      "anchor": "gases in",
      "type": "连读",
      "pair": [
        "gases",
        "in"
      ],
      "note": "gases 的末音接 in 开头的元音，连说时通常少有停顿；听时把两个词分开理解。",
      "legacy_question_number": 20
    },
    {
      "id": "S2U6P03",
      "segment_id": "cet6_202606_set2_u6_seg013",
      "anchor": "light from",
      "type": "失爆",
      "pair": [
        "light",
        "from"
      ],
      "note": "light 末尾的爆破音后面紧接 from 的辅音，通常不会明显爆破；留意后一个词。",
      "legacy_question_number": 21
    },
    {
      "id": "S2U6P04",
      "segment_id": "cet6_202606_set2_u6_seg001",
      "anchor": "was",
      "type": "弱读",
      "word": "was",
      "weak": "/wəz/",
      "note": "was 是虚词，连续语流中常可弱读为 /wəz/；听时注意不要漏掉。"
    },
    {
      "id": "S2U6P05",
      "segment_id": "cet6_202606_set2_u6_seg002",
      "anchor": "at a",
      "type": "喉塞化",
      "pair": [
        "at",
        "a"
      ],
      "note": "at 末尾的 /t/ 后接 a 开头的元音，在一些口音中可能喉塞化。"
    },
    {
      "id": "S2U6P06",
      "segment_id": "cet6_202606_set2_u6_seg004",
      "anchor": "study",
      "type": "闪音",
      "word": "study",
      "note": "study 中间的 /t/ 或 /d/ 位于非重读元音前，在美音中可能读成闪音。"
    },
    {
      "id": "S2U6P07",
      "segment_id": "cet6_202606_set2_u6_seg005",
      "anchor": "computer",
      "type": "闪音",
      "word": "computer",
      "note": "computer 中间的 /t/ 或 /d/ 位于非重读元音前，在美音中可能读成闪音。"
    },
    {
      "id": "S2U6P08",
      "segment_id": "cet6_202606_set2_u6_seg006",
      "anchor": "solid particles",
      "type": "失爆",
      "pair": [
        "solid",
        "particles"
      ],
      "note": "solid 末尾的爆破音后面紧接 particles 的辅音，通常不会明显爆破；留意后一个词。"
    },
    {
      "id": "S2U6P09",
      "segment_id": "cet6_202606_set2_u6_seg008",
      "anchor": "can",
      "type": "弱读",
      "word": "can",
      "weak": "/kən/",
      "note": "can 是虚词，连续语流中常可弱读为 /kən/；听时注意不要漏掉。"
    },
    {
      "id": "S2U6P10",
      "segment_id": "cet6_202606_set2_u6_seg009",
      "anchor": "erupt, emitting",
      "type": "喉塞化",
      "pair": [
        "erupt",
        "emitting"
      ],
      "note": "erupt 末尾的 /t/ 后接 emitting 开头的元音，在一些口音中可能喉塞化。"
    },
    {
      "id": "S2U6P11",
      "segment_id": "cet6_202606_set2_u6_seg010",
      "anchor": "that of",
      "type": "喉塞化",
      "pair": [
        "that",
        "of"
      ],
      "note": "that 末尾的 /t/ 后接 of 开头的元音，在一些口音中可能喉塞化。"
    },
    {
      "id": "S2U6P12",
      "segment_id": "cet6_202606_set2_u6_seg011",
      "anchor": "floating",
      "type": "闪音",
      "word": "floating",
      "note": "floating 中间的 /t/ 或 /d/ 位于非重读元音前，在美音中可能读成闪音。"
    },
    {
      "id": "S2U6P13",
      "segment_id": "cet6_202606_set2_u6_seg012",
      "anchor": "test their",
      "type": "失爆",
      "pair": [
        "test",
        "their"
      ],
      "note": "test 末尾的爆破音后面紧接 their 的辅音，通常不会明显爆破；留意后一个词。"
    }
  ],
  "cet6_202606_set2_u7": [
    {
      "id": "S2U7P01",
      "segment_id": "cet6_202606_set2_u7_seg001",
      "anchor": "have a",
      "type": "连读",
      "pair": [
        "have",
        "a"
      ],
      "note": "have 的末音接 a 开头的元音，连说时通常少有停顿；听时把两个词分开理解。",
      "legacy_question_number": 22
    },
    {
      "id": "S2U7P02",
      "segment_id": "cet6_202606_set2_u7_seg004",
      "anchor": "influenced by",
      "type": "失爆",
      "pair": [
        "influenced",
        "by"
      ],
      "note": "influenced 末尾的爆破音后面紧接 by 的辅音，通常不会明显爆破；留意后一个词。",
      "legacy_question_number": 23
    },
    {
      "id": "S2U7P03",
      "segment_id": "cet6_202606_set2_u7_seg008",
      "anchor": "variety of",
      "type": "连读",
      "pair": [
        "variety",
        "of"
      ],
      "note": "variety 的末音接 of 开头的元音，连说时通常少有停顿；听时把两个词分开理解。",
      "legacy_question_number": 24
    },
    {
      "id": "S2U7P04",
      "segment_id": "cet6_202606_set2_u7_seg011",
      "anchor": "going to",
      "type": "弱读",
      "word": "to",
      "weak": "/tə/",
      "note": "to 是虚词，连续语流中常可弱读为 /tə/；听时注意不要漏掉。",
      "legacy_question_number": 25
    },
    {
      "id": "S2U7P05",
      "segment_id": "cet6_202606_set2_u7_seg002",
      "anchor": "out a",
      "type": "喉塞化",
      "pair": [
        "out",
        "a"
      ],
      "note": "out 末尾的 /t/ 后接 a 开头的元音，在一些口音中可能喉塞化。"
    },
    {
      "id": "S2U7P06",
      "segment_id": "cet6_202606_set2_u7_seg003",
      "anchor": "important",
      "type": "闪音",
      "word": "important",
      "note": "important 中间的 /t/ 或 /d/ 位于非重读元音前，在美音中可能读成闪音。"
    },
    {
      "id": "S2U7P07",
      "segment_id": "cet6_202606_set2_u7_seg005",
      "anchor": "of",
      "type": "弱读",
      "word": "of",
      "weak": "/əv/",
      "note": "of 是虚词，连续语流中常可弱读为 /əv/；听时注意不要漏掉。"
    },
    {
      "id": "S2U7P08",
      "segment_id": "cet6_202606_set2_u7_seg006",
      "anchor": "shared their",
      "type": "失爆",
      "pair": [
        "shared",
        "their"
      ],
      "note": "shared 末尾的 /d/ 后面紧接 their 的辅音，通常不会明显爆破；留意 their。"
    },
    {
      "id": "S2U7P09",
      "segment_id": "cet6_202606_set2_u7_seg007",
      "anchor": "reporting",
      "type": "闪音",
      "word": "reporting",
      "note": "reporting 中间的 /t/ 或 /d/ 位于非重读元音前，在美音中可能读成闪音。"
    },
    {
      "id": "S2U7P10",
      "segment_id": "cet6_202606_set2_u7_seg009",
      "anchor": "include the",
      "type": "失爆",
      "pair": [
        "include",
        "the"
      ],
      "note": "include 末尾的爆破音后面紧接 the 的辅音，通常不会明显爆破；留意后一个词。"
    },
    {
      "id": "S2U7P11",
      "segment_id": "cet6_202606_set2_u7_seg010",
      "anchor": "to",
      "type": "弱读",
      "word": "to",
      "weak": "/tə/",
      "note": "to 是虚词，连续语流中常可弱读为 /tə/；听时注意不要漏掉。"
    }
  ],
  "cet4_202606_set2_u1": [
    {
      "id": "C4S2U1P01",
      "segment_id": "cet4_202606_set2_u1_seg001",
      "anchor": "old woman",
      "type": "失爆",
      "pair": [
        "old",
        "woman"
      ],
      "note": "old 末尾的爆破音后面紧接 woman 的辅音，通常不会明显爆破；留意后一个词。"
    },
    {
      "id": "C4S2U1P02",
      "segment_id": "cet4_202606_set2_u1_seg002",
      "anchor": "months after",
      "type": "连读",
      "pair": [
        "months",
        "after"
      ],
      "note": "months 末尾的 /s/ 接 after 开头的元音，通常会连着说；留意出生时间。"
    },
    {
      "id": "C4S2U1P03",
      "segment_id": "cet4_202606_set2_u1_seg003",
      "anchor": "it on",
      "type": "喉塞化",
      "pair": [
        "it",
        "on"
      ],
      "note": "it 末尾的 /t/ 后接 on 开头的元音，在一些口音中可能喉塞化。"
    },
    {
      "id": "C4S2U1P04",
      "segment_id": "cet4_202606_set2_u1_seg004",
      "anchor": "the",
      "type": "弱读",
      "word": "the",
      "weak": "/ðə/",
      "note": "the 是虚词，连续语流中常可弱读为 /ðə/；听时注意不要漏掉。"
    },
    {
      "id": "C4S2U1P05",
      "segment_id": "cet4_202606_set2_u1_seg005",
      "anchor": "According",
      "type": "闪音",
      "word": "According",
      "note": "According 中间的 /t/ 或 /d/ 位于非重读元音前，在美音中可能读成闪音。"
    },
    {
      "id": "C4S2U1P06",
      "segment_id": "cet4_202606_set2_u1_seg006",
      "anchor": "estate agent",
      "type": "喉塞化",
      "pair": [
        "estate",
        "agent"
      ],
      "note": "estate 末尾的 /t/ 后接 agent 开头的元音，在一些口音中可能喉塞化。"
    },
    {
      "id": "C4S2U1P07",
      "segment_id": "cet4_202606_set2_u1_seg007",
      "anchor": "Except for",
      "type": "失爆",
      "pair": [
        "Except",
        "for"
      ],
      "note": "Except 末尾的爆破音后面紧接 for 的辅音，通常不会明显爆破；留意后一个词。"
    },
    {
      "id": "C4S2U1P08",
      "segment_id": "cet4_202606_set2_u1_seg008",
      "anchor": "the",
      "type": "弱读",
      "word": "the",
      "weak": "/ðə/",
      "note": "the 是虚词，连续语流中常可弱读为 /ðə/；听时注意不要漏掉。"
    }
  ],
  "cet4_202606_set2_u2": [
    {
      "id": "C4S2U2P01",
      "segment_id": "cet4_202606_set2_u2_seg001",
      "anchor": "floating",
      "type": "闪音",
      "word": "floating",
      "note": "floating 中间的 /t/ 或 /d/ 位于非重读元音前，在美音中可能读成闪音。"
    },
    {
      "id": "C4S2U2P02",
      "segment_id": "cet4_202606_set2_u2_seg002",
      "anchor": "wrote the",
      "type": "失爆",
      "pair": [
        "wrote",
        "the"
      ],
      "note": "wrote 末尾的爆破音后面紧接 the 的辅音，通常不会明显爆破；留意后一个词。"
    },
    {
      "id": "C4S2U2P03",
      "segment_id": "cet4_202606_set2_u2_seg003",
      "anchor": "sailboat out",
      "type": "喉塞化",
      "pair": [
        "sailboat",
        "out"
      ],
      "note": "sailboat 末尾的 /t/ 后接 out 开头的元音，在一些口音中可能喉塞化。"
    },
    {
      "id": "C4S2U2P04",
      "segment_id": "cet4_202606_set2_u2_seg004",
      "anchor": "water",
      "type": "闪音",
      "word": "water",
      "note": "water 中间的 /t/ 或 /d/ 位于非重读元音前，在美音中可能读成闪音。"
    },
    {
      "id": "C4S2U2P05",
      "segment_id": "cet4_202606_set2_u2_seg005",
      "anchor": "to",
      "type": "弱读",
      "word": "to",
      "weak": "/tə/",
      "note": "to 是虚词，连续语流中常可弱读为 /tə/；听时注意不要漏掉。"
    },
    {
      "id": "C4S2U2P06",
      "segment_id": "cet4_202606_set2_u2_seg006",
      "anchor": "passed again",
      "type": "喉塞化",
      "pair": [
        "passed",
        "again"
      ],
      "note": "passed 末尾的 /t/ 后接 again 开头的元音，在一些口音中可能喉塞化。"
    },
    {
      "id": "C4S2U2P07",
      "segment_id": "cet4_202606_set2_u2_seg007",
      "anchor": "sailboat was",
      "type": "失爆",
      "pair": [
        "sailboat",
        "was"
      ],
      "note": "sailboat 末尾的爆破音后面紧接 was 的辅音，通常不会明显爆破；留意后一个词。"
    },
    {
      "id": "C4S2U2P08",
      "segment_id": "cet4_202606_set2_u2_seg008",
      "anchor": "was",
      "type": "弱读",
      "word": "was",
      "weak": "/wəz/",
      "note": "was 是虚词，连续语流中常可弱读为 /wəz/；听时注意不要漏掉。"
    }
  ],
  "cet4_202606_set2_u3": [
    {
      "id": "C4S2U3P01",
      "segment_id": "cet4_202606_set2_u3_seg001",
      "anchor": "middle",
      "type": "闪音",
      "word": "middle",
      "note": "middle 中间的 /t/ 或 /d/ 位于非重读元音前，在美音中可能读成闪音。"
    },
    {
      "id": "C4S2U3P02",
      "segment_id": "cet4_202606_set2_u3_seg002",
      "anchor": "announced in",
      "type": "喉塞化",
      "pair": [
        "announced",
        "in"
      ],
      "note": "announced 末尾的 /t/ 后接 in 开头的元音，在一些口音中可能喉塞化。"
    },
    {
      "id": "C4S2U3P03",
      "segment_id": "cet4_202606_set2_u3_seg003",
      "anchor": "approved criteria",
      "type": "失爆",
      "pair": [
        "approved",
        "criteria"
      ],
      "note": "approved 末尾的爆破音后面紧接 criteria 的辅音，通常不会明显爆破；留意后一个词。"
    },
    {
      "id": "C4S2U3P04",
      "segment_id": "cet4_202606_set2_u3_seg004",
      "anchor": "middle",
      "type": "闪音",
      "word": "middle",
      "note": "middle 中间的 /t/ 或 /d/ 位于非重读元音前，在美音中可能读成闪音。"
    },
    {
      "id": "C4S2U3P05",
      "segment_id": "cet4_202606_set2_u3_seg005",
      "anchor": "that",
      "type": "弱读",
      "word": "that",
      "weak": "/ðət/",
      "note": "that 是虚词，连续语流中常可弱读为 /ðət/；听时注意不要漏掉。"
    },
    {
      "id": "C4S2U3P06",
      "segment_id": "cet4_202606_set2_u3_seg006",
      "anchor": "but in",
      "type": "喉塞化",
      "pair": [
        "but",
        "in"
      ],
      "note": "but 末尾的 /t/ 后接 in 开头的元音，在一些口音中可能喉塞化。"
    },
    {
      "id": "C4S2U3P07",
      "segment_id": "cet4_202606_set2_u3_seg007",
      "anchor": "district said",
      "type": "失爆",
      "pair": [
        "district",
        "said"
      ],
      "note": "district 末尾的爆破音后面紧接 said 的辅音，通常不会明显爆破；留意后一个词。"
    }
  ],
  "cet4_202606_set2_u4": [
    {
      "id": "C4S2U4P01",
      "segment_id": "cet4_202606_set2_u4_seg001",
      "anchor": "Theater",
      "type": "闪音",
      "word": "Theater",
      "note": "Theater 中间的 /t/ 或 /d/ 位于非重读元音前，在美音中可能读成闪音。"
    },
    {
      "id": "C4S2U4P02",
      "segment_id": "cet4_202606_set2_u4_seg002",
      "anchor": "to",
      "type": "弱读",
      "word": "to",
      "weak": "/tə/",
      "note": "to 是虚词，连续语流中常可弱读为 /tə/；听时注意不要漏掉。"
    },
    {
      "id": "C4S2U4P03",
      "segment_id": "cet4_202606_set2_u4_seg003",
      "anchor": "it and",
      "type": "喉塞化",
      "pair": [
        "it",
        "and"
      ],
      "note": "it 末尾的 /t/ 后接 and 开头的元音，在一些口音中可能喉塞化。"
    },
    {
      "id": "C4S2U4P04",
      "segment_id": "cet4_202606_set2_u4_seg004",
      "anchor": "husband usually",
      "type": "同化",
      "pair": [
        "husband",
        "usually"
      ],
      "note": "husband 末尾的辅音遇到 usually 开头的 /j/，连说时可能同化；结合整句判断。"
    },
    {
      "id": "C4S2U4P05",
      "segment_id": "cet4_202606_set2_u4_seg005",
      "anchor": "indeed, madam",
      "type": "失爆",
      "pair": [
        "indeed",
        "madam"
      ],
      "note": "indeed 末尾的爆破音后面紧接 madam 的辅音，通常不会明显爆破；留意后一个词。"
    },
    {
      "id": "C4S2U4P06",
      "segment_id": "cet4_202606_set2_u4_seg006",
      "anchor": "the",
      "type": "弱读",
      "word": "the",
      "weak": "/ðə/",
      "note": "the 是虚词，连续语流中常可弱读为 /ðə/；听时注意不要漏掉。"
    },
    {
      "id": "C4S2U4P07",
      "segment_id": "cet4_202606_set2_u4_seg007",
      "anchor": "that you",
      "type": "同化",
      "pair": [
        "that",
        "you"
      ],
      "note": "that 末尾的辅音遇到 you 开头的 /j/，连说时可能同化；结合整句判断。"
    },
    {
      "id": "C4S2U4P08",
      "segment_id": "cet4_202606_set2_u4_seg008",
      "anchor": "and you",
      "type": "同化",
      "pair": [
        "and",
        "you"
      ],
      "note": "and 末尾的辅音遇到 you 开头的 /j/，连说时可能同化；结合整句判断。"
    },
    {
      "id": "C4S2U4P09",
      "segment_id": "cet4_202606_set2_u4_seg009",
      "anchor": "and your",
      "type": "同化",
      "pair": [
        "and",
        "your"
      ],
      "note": "and 末尾的辅音遇到 your 开头的 /j/，连说时可能同化；结合整句判断。"
    }
  ],
  "cet4_202606_set2_u6": [
    {
      "id": "C4S2U6P01",
      "segment_id": "cet4_202606_set2_u6_seg001",
      "anchor": "Last year",
      "type": "同化",
      "pair": [
        "Last",
        "year"
      ],
      "note": "Last 末尾的辅音遇到 year 开头的 /j/，连说时可能同化；结合整句判断。"
    },
    {
      "id": "C4S2U6P02",
      "segment_id": "cet4_202606_set2_u6_seg002",
      "anchor": "Federal",
      "type": "闪音",
      "word": "Federal",
      "note": "Federal 中间的 /t/ 或 /d/ 位于非重读元音前，在美音中可能读成闪音。"
    },
    {
      "id": "C4S2U6P03",
      "segment_id": "cet4_202606_set2_u6_seg003",
      "anchor": "it has",
      "type": "失爆",
      "pair": [
        "it",
        "has"
      ],
      "note": "it 末尾的爆破音后面紧接 has 的辅音，通常不会明显爆破；留意后一个词。"
    },
    {
      "id": "C4S2U6P04",
      "segment_id": "cet4_202606_set2_u6_seg004",
      "anchor": "and",
      "type": "弱读",
      "word": "and",
      "weak": "/ən/",
      "note": "and 是虚词，连续语流中常可弱读为 /ən/；听时注意不要漏掉。"
    },
    {
      "id": "C4S2U6P05",
      "segment_id": "cet4_202606_set2_u6_seg005",
      "anchor": "was usually",
      "type": "同化",
      "pair": [
        "was",
        "usually"
      ],
      "note": "was 末尾的辅音遇到 usually 开头的 /j/，连说时可能同化；结合整句判断。"
    },
    {
      "id": "C4S2U6P06",
      "segment_id": "cet4_202606_set2_u6_seg006",
      "anchor": "widened",
      "type": "闪音",
      "word": "widened",
      "note": "widened 中间的 /t/ 或 /d/ 位于非重读元音前，在美音中可能读成闪音。"
    },
    {
      "id": "C4S2U6P07",
      "segment_id": "cet4_202606_set2_u6_seg007",
      "anchor": "get an",
      "type": "喉塞化",
      "pair": [
        "get",
        "an"
      ],
      "note": "get 末尾的 /t/ 后接 an 开头的元音，在一些口音中可能喉塞化。"
    },
    {
      "id": "C4S2U6P08",
      "segment_id": "cet4_202606_set2_u6_seg008",
      "anchor": "reached or",
      "type": "喉塞化",
      "pair": [
        "reached",
        "or"
      ],
      "note": "reached 末尾的 /t/ 后接 or 开头的元音，在一些口音中可能喉塞化。"
    },
    {
      "id": "C4S2U6P09",
      "segment_id": "cet4_202606_set2_u6_seg009",
      "anchor": "shortage",
      "type": "闪音",
      "word": "shortage",
      "note": "shortage 中间的 /t/ 或 /d/ 位于非重读元音前，在美音中可能读成闪音。"
    }
  ],
  "cet4_202606_set2_u7": [
    {
      "id": "C4S2U7P01",
      "segment_id": "cet4_202606_set2_u7_seg001",
      "anchor": "diet, [19]but",
      "type": "失爆",
      "pair": [
        "diet",
        "but"
      ],
      "note": "diet 末尾的爆破音后面紧接 but 的辅音，通常不会明显爆破；留意后一个词。"
    },
    {
      "id": "C4S2U7P02",
      "segment_id": "cet4_202606_set2_u7_seg002",
      "anchor": "that",
      "type": "弱读",
      "word": "that",
      "weak": "/ðət/",
      "note": "that 是虚词，连续语流中常可弱读为 /ðət/；听时注意不要漏掉。"
    },
    {
      "id": "C4S2U7P03",
      "segment_id": "cet4_202606_set2_u7_seg003",
      "anchor": "gained two",
      "type": "失爆",
      "pair": [
        "gained",
        "two"
      ],
      "note": "gained 末尾的爆破音后面紧接 two 的辅音，通常不会明显爆破；留意后一个词。"
    },
    {
      "id": "C4S2U7P04",
      "segment_id": "cet4_202606_set2_u7_seg004",
      "anchor": "wasn’t a",
      "type": "喉塞化",
      "pair": [
        "wasn’t",
        "a"
      ],
      "note": "wasn’t 末尾的 /t/ 后接 a 开头的元音，在一些口音中可能喉塞化。"
    },
    {
      "id": "C4S2U7P05",
      "segment_id": "cet4_202606_set2_u7_seg005",
      "anchor": "didn’t",
      "type": "闪音",
      "word": "didn’t",
      "note": "didn’t 中间的 /t/ 或 /d/ 位于非重读元音前，在美音中可能读成闪音。"
    },
    {
      "id": "C4S2U7P06",
      "segment_id": "cet4_202606_set2_u7_seg006",
      "anchor": "the",
      "type": "弱读",
      "word": "the",
      "weak": "/ðə/",
      "note": "the 是虚词，连续语流中常可弱读为 /ðə/；听时注意不要漏掉。"
    },
    {
      "id": "C4S2U7P07",
      "segment_id": "cet4_202606_set2_u7_seg007",
      "anchor": "study",
      "type": "闪音",
      "word": "study",
      "note": "study 中间的 /t/ 或 /d/ 位于非重读元音前，在美音中可能读成闪音。"
    },
    {
      "id": "C4S2U7P08",
      "segment_id": "cet4_202606_set2_u7_seg008",
      "anchor": "it easier",
      "type": "喉塞化",
      "pair": [
        "it",
        "easier"
      ],
      "note": "it 末尾的 /t/ 后接 easier 开头的元音，在一些口音中可能喉塞化。"
    },
    {
      "id": "C4S2U7P09",
      "segment_id": "cet4_202606_set2_u7_seg009",
      "anchor": "that you’ve",
      "type": "同化",
      "pair": [
        "that",
        "you’ve"
      ],
      "note": "that 末尾的辅音遇到 you’ve 开头的 /j/，连说时可能同化；结合整句判断。"
    },
    {
      "id": "C4S2U7P10",
      "segment_id": "cet4_202606_set2_u7_seg010",
      "anchor": "that signal",
      "type": "失爆",
      "pair": [
        "that",
        "signal"
      ],
      "note": "that 末尾的爆破音后面紧接 signal 的辅音，通常不会明显爆破；留意后一个词。"
    }
  ],
  "cet4_202606_set2_u8": [
    {
      "id": "C4S2U8P01",
      "segment_id": "cet4_202606_set2_u8_seg001",
      "anchor": "to",
      "type": "弱读",
      "word": "to",
      "weak": "/tə/",
      "note": "to 是虚词，连续语流中常可弱读为 /tə/；听时注意不要漏掉。"
    },
    {
      "id": "C4S2U8P02",
      "segment_id": "cet4_202606_set2_u8_seg002",
      "anchor": "attributed",
      "type": "闪音",
      "word": "attributed",
      "note": "attributed 中间的 /t/ 或 /d/ 位于非重读元音前，在美音中可能读成闪音。"
    },
    {
      "id": "C4S2U8P03",
      "segment_id": "cet4_202606_set2_u8_seg003",
      "anchor": "looked at",
      "type": "喉塞化",
      "pair": [
        "looked",
        "at"
      ],
      "note": "looked 末尾的 /t/ 后接 at 开头的元音，在一些口音中可能喉塞化。"
    },
    {
      "id": "C4S2U8P04",
      "segment_id": "cet4_202606_set2_u8_seg004",
      "anchor": "liked yard",
      "type": "同化",
      "pair": [
        "liked",
        "yard"
      ],
      "note": "liked 末尾的辅音遇到 yard 开头的 /j/，连说时可能同化；结合整句判断。"
    },
    {
      "id": "C4S2U8P05",
      "segment_id": "cet4_202606_set2_u8_seg005",
      "anchor": "leaned toward",
      "type": "失爆",
      "pair": [
        "leaned",
        "toward"
      ],
      "note": "leaned 末尾的爆破音后面紧接 toward 的辅音，通常不会明显爆破；留意后一个词。"
    },
    {
      "id": "C4S2U8P06",
      "segment_id": "cet4_202606_set2_u8_seg006",
      "anchor": "that",
      "type": "弱读",
      "word": "that",
      "weak": "/ðət/",
      "note": "that 是虚词，连续语流中常可弱读为 /ðət/；听时注意不要漏掉。"
    },
    {
      "id": "C4S2U8P07",
      "segment_id": "cet4_202606_set2_u8_seg007",
      "anchor": "that as",
      "type": "喉塞化",
      "pair": [
        "that",
        "as"
      ],
      "note": "that 末尾的 /t/ 后接 as 开头的元音，在一些口音中可能喉塞化。"
    },
    {
      "id": "C4S2U8P08",
      "segment_id": "cet4_202606_set2_u8_seg008",
      "anchor": "study’s",
      "type": "闪音",
      "word": "study’s",
      "note": "study’s 中间的 /t/ 或 /d/ 位于非重读元音前，在美音中可能读成闪音。"
    },
    {
      "id": "C4S2U8P09",
      "segment_id": "cet4_202606_set2_u8_seg009",
      "anchor": "The authors",
      "type": "连读",
      "pair": [
        "The",
        "authors"
      ],
      "note": "The 的末音接 authors 开头的元音，连说时通常少有停顿；听时把两个词分开理解。"
    },
    {
      "id": "C4S2U8P10",
      "segment_id": "cet4_202606_set2_u8_seg010",
      "anchor": "six years",
      "type": "同化",
      "pair": [
        "six",
        "years"
      ],
      "note": "six 末尾的辅音遇到 years 开头的 /j/，连说时可能同化；结合整句判断。"
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
        "surface": "counter-intuitive",
        "collocations": [
          "a counterintuitive result 反直觉的结果",
          "seem counterintuitive at first 起初似乎反直觉"
        ],
        "more_examples": [
          "It sounds counterintuitive, but the shorter route took longer. 听着有违直觉，但较短路线花的时间反而更长。",
          "The finding was counterintuitive to many readers. 这个发现让许多读者觉得出乎意料。"
        ],
        "pitfalls": [
          "来源拼法 counter-intuitive 与常见规范拼法 counterintuitive 是同一词。"
        ]
      },
      {
        "id": "S2U5V02",
        "anchor": "stick with your habits",
        "example": "I want to stick with a manageable routine. 我想坚持一套做得到的日常安排。",
        "gloss": "短语动词；坚持。不要按胶水的字面意思解释。",
        "surface": "stick with",
        "collocations": [
          "stick with a plan 坚持计划",
          "stick with a routine 保持惯常安排"
        ],
        "more_examples": [
          "I decided to stick with the afternoon class. 我决定继续上下午的课。",
          "She stuck with her reading plan for a month. 她坚持阅读计划一个月。"
        ],
        "pitfalls": [
          "stick with 在此是“坚持”，不要按粘贴的字面义理解。"
        ]
      },
      {
        "id": "S2U5V03",
        "anchor": "implementation intentions",
        "example": "My plan specifies when and where I will practise. 我的计划明确了何时、何地练习。",
        "gloss": "专门术语；材料用来称呼写明何时、何地、如何行动的具体计划。理解即可，不默认要求拼写。",
        "surface": "implementation intentions",
        "collocations": [
          "form implementation intentions 制定具体行动计划",
          "write down implementation intentions 写下具体行动计划"
        ],
        "more_examples": [
          "The workshop asked us to specify when and where we would practise. 工作坊让我们写明何时何地练习。",
          "Her plan named a time and place for the new routine. 她的计划写明了新习惯的时间和地点。"
        ],
        "pitfalls": [
          "这是研究语境里的术语；重点理解“何时何地做”，不必照字面译作“实施意图”。"
        ]
      },
      {
        "id": "S2U5V04",
        "anchor": "a lot of conscious effort",
        "example": "At first, checking the schedule took conscious effort. 起初，查看日程需要有意识地提醒自己。",
        "gloss": "名词短语；有意识的努力。与自动化对比，但不据此测量学生认知能力。",
        "surface": "conscious effort",
        "collocations": [
          "require conscious effort 需要有意识的努力",
          "make a conscious effort to listen 有意识地努力倾听"
        ],
        "more_examples": [
          "It took conscious effort to check my notes each evening. 每晚检查笔记需要我刻意提醒自己。",
          "I made a conscious effort to arrive earlier. 我有意识地争取早点到。"
        ],
        "pitfalls": [
          "conscious 在这里修饰主动注意，不等于“道德良心上的”。"
        ]
      },
      {
        "id": "S2U5V05",
        "anchor": "more or less automatic",
        "example": "The outline is more or less complete. 提纲基本完成了。",
        "gloss": "固定表达；大体上、差不多。此处不是比较“更多还是更少”。",
        "surface": "more or less",
        "collocations": [
          "more or less ready 基本准备好了",
          "more or less the same 差不多一样"
        ],
        "more_examples": [
          "The new timetable is more or less final. 新时间表基本定了。",
          "We have more or less finished the display. 展板我们差不多做完了。"
        ],
        "pitfalls": [
          "more or less 在此是“大致”，不要拆成数量上的“更多或更少”。"
        ]
      },
      {
        "id": "S2U5V06",
        "anchor": "some tipping point",
        "example": "The discussion reached a tipping point after the new evidence. 新证据出现后，讨论到了一个转折点。",
        "gloss": "名词短语；发生关键变化的临界点。本段未给一个适用于所有人的固定天数。",
        "surface": "tipping point",
        "collocations": [
          "reach a tipping point 到达转折点",
          "a tipping point in the discussion 讨论的转折点"
        ],
        "more_examples": [
          "The project reached a tipping point when more volunteers joined. 更多志愿者加入后，项目迎来转折点。",
          "A new bus route could be a tipping point for the area. 新公交线路可能成为这个地区的转折点。"
        ],
        "pitfalls": [
          "tipping point 是关键转折，不必然有统一的固定天数。"
        ]
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
        "surface": "city break",
        "collocations": [
          "plan a city break 计划城市短途游",
          "book a city break 预订城市短途游"
        ],
        "more_examples": [
          "We took a city break in Bristol over the weekend. 周末我们去布里斯托尔短途旅行。",
          "A city break can fit into a long weekend. 城市短途游可以安排在长周末。"
        ],
        "pitfalls": [
          "city break 是短途旅行，不是工作中的“休息”。"
        ]
      },
      {
        "id": "S2U1V02",
        "anchor": "the anniversary is looming",
        "example": "The deadline is looming, so we need a decision. 截止日期临近，我们需要作出决定。",
        "gloss": "动词；日期正在逼近，语境中带紧迫感。搭配 a deadline is looming。",
        "surface": "loom",
        "collocations": [
          "a deadline is looming 截止日期临近",
          "exams are looming 考试快到了"
        ],
        "more_examples": [
          "The opening night is looming, so we need to rehearse. 首演快到了，我们得排练。",
          "With the holiday looming, hotels are filling up. 假期临近，酒店客房快订满了。"
        ],
        "pitfalls": [
          "loom 在这里暗含临近带来的压力，不等于普通的 come。"
        ]
      },
      {
        "id": "S2U1V03",
        "anchor": "scrambling to find accommodation",
        "example": "We scrambled to find a replacement speaker. 我们急忙寻找替补发言人。",
        "gloss": "动词结构；匆忙、费力地设法做某事。此处不是攀爬。",
        "surface": "scramble to",
        "collocations": [
          "scramble to find a seat 急忙找座位",
          "scramble to finish on time 赶着按时完成"
        ],
        "more_examples": [
          "We scrambled to replace the broken projector. 我们急忙找设备替换坏掉的投影仪。",
          "They scrambled to book a room before the conference. 他们赶在会议前匆忙订房。"
        ],
        "pitfalls": [
          "scramble to 后接动词原形；此处不是手脚并用地爬。"
        ]
      },
      {
        "id": "S2U1V04",
        "anchor": "offset the cost",
        "example": "Sharing transport can offset some of the cost. 共乘交通工具可以抵消一部分费用。",
        "gloss": "动词；抵消、补偿部分成本。并不自动意味着完全免费。",
        "surface": "offset",
        "collocations": [
          "offset travel costs 抵消旅行费用",
          "offset part of the expense 抵消部分开支"
        ],
        "more_examples": [
          "Sharing a taxi helped offset the fare. 拼车抵消了一部分车费。",
          "The grant will offset some printing costs. 补助会抵消部分印刷费。"
        ],
        "pitfalls": [
          "offset 只表示抵消一定成本，除非另有说明，不等于全部免费。"
        ]
      },
      {
        "id": "S2U1V05",
        "anchor": "are all inclusive",
        "example": "We asked what the all-inclusive package covered. 我们询问了全包套餐包含哪些项目。",
        "gloss": "形容词结构；费用包含套餐范围内项目；本材料随后解释食物和饮料。不得推广成任何附加消费都免费。",
        "surface": "all inclusive",
        "collocations": [
          "an all-inclusive resort 全包式度假村",
          "an all-inclusive price 全包价格"
        ],
        "more_examples": [
          "We checked whether the all-inclusive rate covered dinner. 我们确认全包价格是否含晚餐。",
          "Their all-inclusive package includes meals but not excursions. 他们的全包套餐含餐食，但不含短途游。"
        ],
        "pitfalls": [
          "all-inclusive 的包含范围取决于套餐条款，不能推断所有项目都免费。"
        ]
      },
      {
        "id": "S2U1V06",
        "anchor": "absolutely thrilled to bits",
        "example": "I was thrilled to bits when the tickets arrived. 票送到时，我特别高兴。",
        "gloss": "非正式表达，尤见英式用法；非常高兴。作为整块学，不拆解 bits 的字面义。",
        "surface": "thrilled to bits",
        "collocations": [
          "be thrilled to bits about the news 对消息高兴极了",
          "feel thrilled to bits 欣喜若狂"
        ],
        "more_examples": [
          "I was thrilled to bits when my friends visited. 朋友来访让我高兴坏了。",
          "She was thrilled to bits with her new role. 新职位让她特别高兴。"
        ],
        "pitfalls": [
          "这是非正式表达，整体表示很高兴；不要把 bits 按“碎片”翻译。"
        ]
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
        "surface": "a small window",
        "collocations": [
          "a small window of opportunity 短暂的机会窗口",
          "have a small window to act 只有很短时间行动"
        ],
        "more_examples": [
          "We have a small window to change the reservation. 我们只有很短时间可以修改预订。",
          "There was a small window to submit the form. 提交表格的时间窗口很短。"
        ],
        "pitfalls": [
          "window 是机会或时间的比喻，不是房间里的窗户。"
        ]
      },
      {
        "id": "S2U7V02",
        "anchor": "time is of the essence",
        "example": "We need to respond today; time is of the essence. 我们今天需要回复，时间很关键。",
        "gloss": "固定表达；时间至关重要，需要及时行动。本稿只讲日常语境，不作法律条款解读。",
        "surface": "time is of the essence",
        "collocations": [
          "time is of the essence now 现在时间很关键",
          "say time is of the essence 强调时间紧迫"
        ],
        "more_examples": [
          "We should leave soon; time is of the essence. 我们应尽快出发，时间很关键。",
          "With the deadline tomorrow, time is of the essence. 明天就到截止日期了，时间很紧。"
        ],
        "pitfalls": [
          "整体表示必须及时行动，不要逐字译为“时间是本质”。"
        ]
      },
      {
        "id": "S2U7V03",
        "anchor": "gravitate away from their parents' choices",
        "example": "My interests gradually gravitated away from competitive games. 我的兴趣逐渐不再偏向竞技游戏。",
        "gloss": "动词结构；逐渐远离某种选择或倾向。注意 away from 的方向，与 toward 对照在揭示后学习。",
        "surface": "gravitate away from",
        "collocations": [
          "gravitate away from an old habit 渐渐摆脱旧习惯",
          "gravitate away from a choice 逐渐不再倾向某选择"
        ],
        "more_examples": [
          "I gradually gravitated away from late-night study. 我逐渐不再习惯熬夜学习。",
          "The group gravitated away from the original design. 小组渐渐不再采用原设计。"
        ],
        "pitfalls": [
          "away from 表远离；toward 才是趋向，方向不能弄反。"
        ]
      },
      {
        "id": "S2U7V04",
        "anchor": "receptive to their musical suggestions",
        "example": "The group was receptive to a different approach. 小组愿意考虑不同的方法。",
        "gloss": "形容词搭配；愿意接受某建议或想法。不是已经完全接受。",
        "surface": "receptive to",
        "collocations": [
          "be receptive to feedback 愿意听取反馈",
          "be receptive to new ideas 愿意接受新想法"
        ],
        "more_examples": [
          "The team was receptive to suggestions from visitors. 团队愿意听取访客建议。",
          "She seemed receptive to a change of schedule. 她似乎愿意考虑调整日程。"
        ],
        "pitfalls": [
          "receptive to 是愿意考虑，不表示已经完全采纳。"
        ]
      },
      {
        "id": "S2U7V05",
        "anchor": "fostering good taste",
        "example": "Shared activities can foster friendship. 共同活动可以促进友谊。",
        "gloss": "动词；培养、促进。这里是培养欣赏趣味，不是食物味觉。",
        "surface": "foster",
        "collocations": [
          "foster curiosity 培养好奇心",
          "foster a sense of trust 促进信任感"
        ],
        "more_examples": [
          "Reading together can foster curiosity about science. 一起阅读能培养对科学的好奇心。",
          "The club hopes to foster new friendships. 社团希望促进新的友谊。"
        ],
        "pitfalls": [
          "foster 在此是“促进、培养”，不是“寄养”的意思。"
        ]
      },
      {
        "id": "S2U7V06",
        "anchor": "bond with others",
        "example": "The project helped us bond with our classmates. 这个项目帮助我们与同学建立更亲近的联系。",
        "gloss": "动词搭配；与他人建立亲近联系。与经济中的债券名词义区分。",
        "surface": "bond with",
        "collocations": [
          "bond with classmates 与同学建立感情",
          "bond with a new team 与新团队建立联系"
        ],
        "more_examples": [
          "Cooking together helped us bond with our neighbors. 一起做饭让我们与邻居更亲近。",
          "The trip gave the group time to bond. 这次旅行给了小组成员培养感情的机会。"
        ],
        "pitfalls": [
          "bond with 是建立亲近关系；与名词 bond“债券”不同。"
        ]
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
        "surface": "dwarf planet",
        "collocations": [
          "a distant dwarf planet 遥远的矮行星",
          "study a dwarf planet 研究矮行星"
        ],
        "more_examples": [
          "The telescope observed a dwarf planet beyond Neptune. 望远镜观测到海王星之外的一颗矮行星。",
          "We read about a dwarf planet in science class. 科学课上我们读到了矮行星。"
        ],
        "pitfalls": [
          "dwarf planet 是天文学类别，不能只按字面理解成“小行星”。"
        ]
      },
      {
        "id": "S2U6V02",
        "anchor": "haze in Pluto's atmosphere",
        "example": "A layer of haze obscured the hills. 一层薄霾遮住了群山。",
        "gloss": "名词；霾、薄雾状悬浮层。不要默认与地球污染烟雾成分相同。",
        "surface": "haze",
        "collocations": [
          "a layer of haze 一层薄霾",
          "haze in the atmosphere 大气中的薄雾层"
        ],
        "more_examples": [
          "Haze made the distant buildings hard to see. 薄霾让远处建筑难以看清。",
          "A pale haze hung over the valley in the morning. 早晨山谷上方笼罩着淡淡的薄雾。"
        ],
        "pitfalls": [
          "haze 不一定由污染造成；应根据具体语境判断成分。"
        ]
      },
      {
        "id": "S2U6V03",
        "anchor": "scattering light from the Sun",
        "example": "The model shows how particles scatter light. 模型展示颗粒怎样散射光线。",
        "gloss": "动词；散射、使分散。这里描述光线变化，不是简单遮住同义替换。",
        "surface": "scatter",
        "collocations": [
          "scatter light 散射光线",
          "scatter in different directions 向不同方向散开"
        ],
        "more_examples": [
          "The glass surface scattered the light across the wall. 玻璃表面把光散射到墙上。",
          "The wind scattered leaves across the path. 风把树叶吹散在小路上。"
        ],
        "pitfalls": [
          "scatter 是使分散或散射，不等于完全遮挡。"
        ]
      },
      {
        "id": "S2U6V04",
        "anchor": "is dominated by the distribution of gases",
        "example": "The conversation was dominated by questions about cost. 讨论主要围绕费用问题展开。",
        "gloss": "被动结构；主要受某因素影响。本句需要跟踪是哪颗行星。",
        "surface": "be dominated by",
        "collocations": [
          "be dominated by one topic 由一个话题主导",
          "be dominated by weather patterns 主要受天气形态影响"
        ],
        "more_examples": [
          "The meeting was dominated by questions about timing. 会议讨论主要围绕时间安排。",
          "The landscape is dominated by a tall ridge. 一道高高的山脊是这片地貌的主要特征。"
        ],
        "pitfalls": [
          "be dominated by 后接主导因素，别颠倒被影响者与影响来源。"
        ]
      },
      {
        "id": "S2U6V05",
        "anchor": "the haze's composition",
        "example": "The team examined the material's composition. 团队研究了材料的组成。",
        "gloss": "名词；组成、成分。不是作文或作曲义。",
        "surface": "composition",
        "collocations": [
          "the chemical composition 化学成分",
          "examine the composition of a sample 检查样本成分"
        ],
        "more_examples": [
          "The label lists the composition of the fabric. 标签列出了布料成分。",
          "The team compared the composition of two samples. 团队比较了两个样本的组成。"
        ],
        "pitfalls": [
          "composition 在这里是组成成分，不是英语作文。"
        ]
      },
      {
        "id": "S2U6V06",
        "anchor": "validates their bright idea",
        "example": "More observations are needed to validate the model. 需要更多观测来检验模型。",
        "gloss": "动词；验证、为某想法提供支持。未发生的检验不能改写成已证实。",
        "surface": "validate",
        "collocations": [
          "validate a theory 验证理论",
          "validate a model with new data 用新数据验证模型"
        ],
        "more_examples": [
          "The team needs more measurements to validate its idea. 团队需要更多测量数据来验证想法。",
          "New observations may help validate the prediction. 新观测可能有助于验证预测。"
        ],
        "pitfalls": [
          "validate 是提供检验证据；尚待检验的猜想不能说成已被证实。"
        ]
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
        "surface": "intricate",
        "collocations": [
          "an intricate design 精细复杂的设计",
          "intricate details 精巧的细节"
        ],
        "more_examples": [
          "The scarf has an intricate woven pattern. 这条围巾有精细的编织图案。",
          "I needed time to understand the intricate instructions. 我需要时间理解复杂细致的说明。"
        ],
        "pitfalls": [
          "intricate 强调结构复杂精细，不等于 messy“杂乱”。"
        ]
      },
      {
        "id": "S2U4V02",
        "anchor": "come down to what's happening",
        "example": "The choice comes down to time and cost. 这个选择归根结底取决于时间和成本。",
        "gloss": "短语；归结为、关键在于。此处不是从高处下来。",
        "surface": "come down to",
        "collocations": [
          "come down to timing 归结为时机",
          "come down to a choice 关键在于选择"
        ],
        "more_examples": [
          "Our decision comes down to the cost of travel. 我们的决定归根结底取决于路费。",
          "It may come down to which room is available. 最后可能取决于哪间房有空。"
        ],
        "pitfalls": [
          "come down to 在这里是“归结为”，不是从楼上下来。"
        ]
      },
      {
        "id": "S2U4V03",
        "anchor": "materials undergo processes",
        "example": "The design underwent several changes. 设计经历了几次修改。",
        "gloss": "动词；经历某过程或变化。搭配 undergo a change。",
        "surface": "undergo",
        "collocations": [
          "undergo a change 经历变化",
          "undergo a review 接受审查"
        ],
        "more_examples": [
          "The old hall will undergo repairs next month. 旧礼堂下个月将进行维修。",
          "The draft underwent several revisions. 草稿经过了几轮修改。"
        ],
        "pitfalls": [
          "undergo 后面直接接过程名词，不加 through。"
        ]
      },
      {
        "id": "S2U4V04",
        "anchor": "give rise to complex patterns",
        "example": "Small changes can give rise to unexpected results. 小变化可能产生意外结果。",
        "gloss": "固定表达；引起、产生。跟踪原因与结果方向。",
        "surface": "give rise to",
        "collocations": [
          "give rise to a pattern 形成图案",
          "give rise to new questions 引出新问题"
        ],
        "more_examples": [
          "A small change in temperature gave rise to cracks. 温度的小变化导致了裂纹。",
          "The survey gave rise to a useful discussion. 调查引发了一场有益讨论。"
        ],
        "pitfalls": [
          "give rise to 表“导致”，原因在前、结果在后；to 是介词。"
        ]
      },
      {
        "id": "S2U4V05",
        "anchor": "molecules begin clustering together",
        "example": "The visitors clustered together near the entrance. 游客聚集在入口附近。",
        "gloss": "动词结构；聚集在一起。cluster 也可作名词，当前先学动作。",
        "surface": "cluster together",
        "collocations": [
          "cluster together near a door 聚在门边",
          "particles cluster together 颗粒聚在一起"
        ],
        "more_examples": [
          "The students clustered together around the noticeboard. 学生围在公告栏旁。",
          "Tiny drops clustered together on the glass. 小水滴聚在玻璃上。"
        ],
        "pitfalls": [
          "cluster together 是聚集，不是整齐地排成一列。"
        ]
      },
      {
        "id": "S2U4V06",
        "anchor": "generate a pattern by coincidence",
        "example": "We chose the same topic by coincidence. 我们碰巧选了同一个主题。",
        "gloss": "介词短语；偶然、巧合地。不是有意设计的同义表达。",
        "surface": "by coincidence",
        "collocations": [
          "happen by coincidence 碰巧发生",
          "meet by coincidence 偶遇"
        ],
        "more_examples": [
          "We both brought the same book by coincidence. 我们碰巧都带了同一本书。",
          "They met at the station by coincidence. 他们在车站偶然相遇。"
        ],
        "pitfalls": [
          "by coincidence 指巧合，不暗示有人事先安排。"
        ]
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
        "surface": "in a positive light",
        "collocations": [
          "present someone in a positive light 从积极角度呈现某人",
          "see a plan in a positive light 积极看待计划"
        ],
        "more_examples": [
          "Her teacher described the project in a positive light. 老师积极评价了这个项目。",
          "The article casts the change in a positive light. 文章从积极角度呈现了这项改变。"
        ],
        "pitfalls": [
          "light 在此是比喻，不是照明；通常说 in a positive light。"
        ]
      },
      {
        "id": "S2U3V02",
        "anchor": "been overstated",
        "example": "We should not overstate the benefits of one tool. 我们不应夸大一种工具的好处。",
        "gloss": "动词；夸大。overstated 不等于 completely false。",
        "surface": "overstate",
        "collocations": [
          "overstate the benefits 夸大好处",
          "overstate the importance 夸大重要性"
        ],
        "more_examples": [
          "The brochure may overstate how easy the course is. 宣传册可能夸大了课程的容易程度。",
          "We should avoid overstating the results. 我们应避免夸大结果。"
        ],
        "pitfalls": [
          "overstate 是说得过头，不必然表示所说完全虚假。"
        ]
      },
      {
        "id": "S2U3V03",
        "anchor": "individualistic cultures",
        "example": "The article compares individualistic and collectivistic values. 文章比较强调个人与集体的价值取向。",
        "gloss": "形容词；强调个人自主或个人目标的。不要直接译为自私。",
        "surface": "individualistic",
        "collocations": [
          "individualistic values 个人取向的价值观",
          "an individualistic approach 强调个人选择的做法"
        ],
        "more_examples": [
          "The essay compares individualistic approaches to study. 文章比较了强调个人选择的学习方式。",
          "An individualistic plan may offer more freedom of choice. 强调个人选择的计划可能提供更多自主空间。"
        ],
        "pitfalls": [
          "individualistic 不等于 selfish；不要用一个形容词判断具体个人。"
        ]
      },
      {
        "id": "S2U3V04",
        "anchor": "collectivistic cultures",
        "example": "The researcher discussed collectivistic traditions. 研究者讨论了集体取向的传统。",
        "gloss": "形容词；强调群体关系或集体义务的。与个体真实行为不能简单画等号。",
        "surface": "collectivistic",
        "collocations": [
          "collectivistic values 集体取向的价值观",
          "a collectivistic approach 重视群体的做法"
        ],
        "more_examples": [
          "The course discusses collectivistic and individualistic ideas. 课程讨论集体取向与个人取向的观念。",
          "A collectivistic approach may emphasize shared decisions. 重视群体的做法可能更强调共同决策。"
        ],
        "pitfalls": [
          "collectivistic 描述一种取向，不能据此推断每个人的行为。"
        ]
      },
      {
        "id": "S2U3V05",
        "anchor": "fulfilling obligations to others",
        "example": "We need time to fulfill our existing obligations. 我们需要时间履行已有义务。",
        "gloss": "动词搭配；履行对他人的义务。搭配 fulfill an obligation。",
        "surface": "fulfill obligations",
        "collocations": [
          "fulfill an obligation 履行义务",
          "fulfill obligations to a team 履行对团队的义务"
        ],
        "more_examples": [
          "We must fulfill our commitments to the volunteers. 我们必须履行对志愿者的承诺。",
          "He planned his week to fulfill his family obligations. 他安排一周日程来履行家庭责任。"
        ],
        "pitfalls": [
          "fulfill obligations 是履行义务；不要与 full“装满”混用。"
        ]
      },
      {
        "id": "S2U3V06",
        "anchor": "positively correlated with academic achievements",
        "example": "The report asks whether attendance correlates with performance. 报告探讨出勤是否与表现相关。",
        "gloss": "动词结构；与某事相关联。正相关不是因果证明，也不是每个人都如此。",
        "surface": "correlate with",
        "collocations": [
          "correlate with attendance 与出勤相关",
          "correlate strongly with results 与结果高度相关"
        ],
        "more_examples": [
          "The study asks whether practice time correlates with confidence. 研究探讨练习时间是否与信心有关。",
          "Higher sales correlated with longer opening hours in the report. 报告中较高销售额与较长营业时间相关。"
        ],
        "pitfalls": [
          "correlate with 只表示相关，不自动证明因果。"
        ]
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
        "surface": "fill prescriptions",
        "collocations": [
          "fill a prescription at a pharmacy 在药房配药",
          "fill prescriptions for patients 为患者配药"
        ],
        "more_examples": [
          "The pharmacy can fill your prescription this afternoon. 药房今天下午可以按处方配药。",
          "He waited while the pharmacist filled his prescription. 药师配药时他在旁等待。"
        ],
        "pitfalls": [
          "药师 fill a prescription 是配药；医生开处方是 write a prescription。"
        ]
      },
      {
        "id": "S2U2V02",
        "anchor": "a potential interaction",
        "example": "She asked the pharmacist about a possible drug interaction. 她向药师询问可能的药物相互作用。",
        "gloss": "名词；这里指药物相互作用。日常也有互动义，先掌握当前语境。",
        "surface": "interaction",
        "collocations": [
          "a drug interaction 药物相互作用",
          "check for possible interactions 检查可能的相互作用"
        ],
        "more_examples": [
          "The pharmacist explained a possible interaction between the medicines. 药师解释了两种药可能的相互作用。",
          "The form asks about drug interactions. 表格询问药物相互作用。"
        ],
        "pitfalls": [
          "interaction 在这里指药物间的相互作用，不是日常社交“互动”。"
        ]
      },
      {
        "id": "S2U2V03",
        "anchor": "double-check with her doctor",
        "example": "Please double-check the date with the organizer. 请向组织者再次核实日期。",
        "gloss": "动词；再核实。搭配 double-check something with someone。",
        "surface": "double-check",
        "collocations": [
          "double-check the date 再核对日期",
          "double-check with the organizer 向组织者再确认"
        ],
        "more_examples": [
          "Please double-check the room number before you go. 出发前请再核对房间号。",
          "I double-checked the timetable with the office. 我向办公室再次确认了时间表。"
        ],
        "pitfalls": [
          "double-check 是再次核实；不必说 double-check again。"
        ]
      },
      {
        "id": "S2U2V04",
        "anchor": "ended up switching",
        "example": "We ended up moving the meeting online. 我们最后把会议改成了线上会议。",
        "gloss": "动词短语；最后发生、最终变成某结果。搭配 end up doing something。",
        "surface": "end up",
        "collocations": [
          "end up waiting 最后只好等着",
          "end up in another room 最后到了另一间房"
        ],
        "more_examples": [
          "We ended up taking the later train. 我们最后坐了晚一班火车。",
          "The discussion ended up taking two hours. 讨论最后持续了两个小时。"
        ],
        "pitfalls": [
          "end up 后接动作时用 -ing，不说 end up to do。"
        ]
      },
      {
        "id": "S2U2V05",
        "anchor": "taking them as prescribed",
        "example": "She asked what “as prescribed” meant on the form. 她询问表格上的“遵医嘱”是什么意思。",
        "gloss": "结构；按处方或医嘱用药。学习此词义不代表网站可以判断具体服药方式。",
        "surface": "as prescribed",
        "collocations": [
          "take medicine as prescribed 按医嘱服药",
          "follow the directions as prescribed 按处方说明操作"
        ],
        "more_examples": [
          "The leaflet says to use the medicine as prescribed. 说明书上说要按医嘱用药。",
          "She asked the pharmacist what “as prescribed” meant. 她问药师“遵医嘱”具体是什么意思。"
        ],
        "pitfalls": [
          "as prescribed 是按处方要求，不等于随意决定剂量；具体用法应问专业人员。"
        ]
      },
      {
        "id": "S2U2V06",
        "anchor": "Medication non-adherence",
        "example": "The report discusses medication non-adherence. 报告讨论了未遵医嘱用药的问题。",
        "gloss": "名词；未按约定或医嘱执行，此处是用药依从性问题。不要仅解释为忘记，原因可能多样。",
        "surface": "non-adherence",
        "collocations": [
          "medication non-adherence 未按医嘱用药",
          "discuss reasons for non-adherence 讨论未遵从的原因"
        ],
        "more_examples": [
          "The study examined several reasons for non-adherence. 研究探讨了多种未遵从的原因。",
          "The clinic asked how to reduce medication non-adherence. 诊所研究如何减少未按医嘱用药的情况。"
        ],
        "pitfalls": [
          "non-adherence 不一定是忘记，也不能仅凭词语推断个人原因。"
        ]
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
        "surface": "put on the market",
        "collocations": [
          "put a house on the market 把房子挂牌出售",
          "put a flat on the market 把公寓挂牌出售"
        ],
        "more_examples": [
          "They put their old house on the market after moving. 搬家后他们把旧房子挂牌出售。",
          "The owner may put the property on the market in spring. 房主可能春天将这处房产挂牌出售。"
        ],
        "pitfalls": [
          "on the market 在此指待售；不要误解为“在市场里”。"
        ]
      },
      {
        "id": "C4S2U1V02",
        "anchor": "priced at some 170,000 pounds",
        "example": "The second-hand bike is priced at 80 pounds. 这辆二手自行车标价八十英镑。",
        "gloss": "搭配；标价为某个金额。some 在金额前表示大约。",
        "surface": "be priced at",
        "collocations": [
          "be priced at 50 dollars 标价五十美元",
          "be priced at under 100 pounds 标价不到一百英镑"
        ],
        "more_examples": [
          "The workshop is priced at twenty dollars per person. 这场工作坊每人收费二十美元。",
          "These notebooks are priced at three pounds each. 这些笔记本每本标价三英镑。"
        ],
        "pitfalls": [
          "price 在这里用被动式 be priced at；金额前用 at，不用 for。"
        ]
      },
      {
        "id": "C4S2U1V03",
        "anchor": "According to the estate agent",
        "example": "According to the notice, the library closes at six. 根据通知，图书馆六点关门。",
        "gloss": "介词短语；根据某人或某来源的信息。",
        "surface": "according to",
        "collocations": [
          "according to the report 根据报告",
          "according to the schedule 根据时间表"
        ],
        "more_examples": [
          "According to the map, the station is two blocks away. 地图显示车站在两个街区外。",
          "According to our records, your booking is for Friday. 根据记录，您的预订是在周五。"
        ],
        "pitfalls": [
          "according to 后接消息来源；表达“依我看”通常不用 according to me。"
        ]
      },
      {
        "id": "C4S2U1V04",
        "anchor": "much of the house remains the same",
        "example": "The street has changed, but the old shop remains the same. 这条街变了，但那家老店仍和以前一样。",
        "gloss": "搭配；保持原样、没有变化。",
        "surface": "remain the same",
        "collocations": [
          "remain the same size 保持相同大小",
          "remain the same for years 多年不变"
        ],
        "more_examples": [
          "The price remained the same throughout the week. 整整一周价格都没有变化。",
          "Her phone number has remained the same since college. 从大学起她的电话号码就没变。"
        ],
        "pitfalls": [
          "remain 是系动词，这里直接接 the same，不加 be。"
        ]
      },
      {
        "id": "C4S2U1V05",
        "anchor": "having lived in it through",
        "example": "She lived through several changes at work. 她经历了工作上的几次变化。",
        "gloss": "短语动词；经历一段时期或某件事。",
        "surface": "live through",
        "collocations": [
          "live through a difficult year 度过艰难的一年",
          "live through major changes 经历重大变化"
        ],
        "more_examples": [
          "The neighborhood lived through a long period of construction. 这个街区经历了很长一段施工期。",
          "My parents lived through several moves when they were young. 我父母年轻时经历过几次搬家。"
        ],
        "pitfalls": [
          "live through 强调亲身经历一段时期，不等于 live in 某个地点。"
        ]
      },
      {
        "id": "C4S2U1V06",
        "anchor": "moving to a nursing home",
        "example": "His grandmother moved to a nursing home near her family. 他的祖母搬进了家人附近的养老院。",
        "gloss": "动词搭配；搬到养老院居住。",
        "surface": "move to a nursing home",
        "collocations": [
          "move to a nursing home near family 搬到家人附近的养老院",
          "decide to move to a nursing home 决定搬进养老院"
        ],
        "more_examples": [
          "After talking with her family, she chose to move to a nursing home. 和家人商量后，她决定搬进养老院。",
          "The couple moved to a nursing home with accessible rooms. 这对夫妇搬进了一家有无障碍房间的养老院。"
        ],
        "pitfalls": [
          "nursing home 指提供照护的居住机构，不是普通的“护士宿舍”。"
        ]
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
        "surface": "key to",
        "collocations": [
          "the key to success 成功的关键",
          "key to solving the problem 解决问题的关键"
        ],
        "more_examples": [
          "Regular feedback was key to improving the course. 定期反馈是改进课程的关键。",
          "A clear list is the key to staying organized. 清楚的清单是保持有条理的关键。"
        ],
        "pitfalls": [
          "to 在 key to 里是介词，后接动词时用 -ing：key to learning。"
        ]
      },
      {
        "id": "C4S2U2V02",
        "anchor": "making repairs",
        "example": "The workers are making repairs to the bridge. 工人们正在修理这座桥。",
        "gloss": "动词搭配；进行修理。",
        "surface": "make repairs",
        "collocations": [
          "make repairs to a roof 修理屋顶",
          "make urgent repairs 进行紧急维修"
        ],
        "more_examples": [
          "The school will make repairs to the heating system. 学校将维修供暖系统。",
          "We had to make repairs before opening the shop. 开店前我们得先修理。"
        ],
        "pitfalls": [
          "make repairs to 后接修理对象；不要说 make repairs for the roof。"
        ]
      },
      {
        "id": "C4S2U2V03",
        "anchor": "prevent it from sinking",
        "example": "A lid can prevent the water from spilling. 盖子可以防止水洒出来。",
        "gloss": "句型；prevent something from doing something，防止某事发生。",
        "surface": "prevent ... from",
        "collocations": [
          "prevent water from leaking 防止漏水",
          "prevent a delay from getting worse 防止延误加重"
        ],
        "more_examples": [
          "A cover prevents dust from collecting on the books. 盖子能防止书上积灰。",
          "Leaving earlier could prevent us from missing the bus. 早点出发可以避免我们错过公交车。"
        ],
        "pitfalls": [
          "prevent A from doing B 的 from 不能省；后面用 -ing。"
        ]
      },
      {
        "id": "C4S2U2V04",
        "anchor": "without success",
        "example": "We searched for the missing file without success. 我们找过那个丢失的文件，但没找到。",
        "gloss": "固定表达；尝试了但没有成功。",
        "surface": "without success",
        "collocations": [
          "search without success 寻找但未成功",
          "try without success 尝试但未成功"
        ],
        "more_examples": [
          "I tried to reset the printer without success. 我试着重置打印机，但没有成功。",
          "They looked for a quiet table without success. 他们想找张安静的桌子，却没找到。"
        ],
        "pitfalls": [
          "without success 修饰前面的尝试，不能直接替代 unsuccessful 作形容词。"
        ]
      },
      {
        "id": "C4S2U2V05",
        "anchor": "swept the sailboat out to sea",
        "example": "A strong wind swept the small boat out to sea. 一阵大风把小船吹到了外海。",
        "gloss": "动词搭配；被风或水流带到海上。",
        "surface": "sweep ... out to sea",
        "collocations": [
          "sweep a boat out to sea 把船冲到海上",
          "be swept out to sea 被冲到外海"
        ],
        "more_examples": [
          "The current swept the empty kayak out to sea. 水流把空皮划艇冲到了外海。",
          "A sudden wave swept their equipment out to sea. 一阵突来的海浪把他们的装备卷到了外海。"
        ],
        "pitfalls": [
          "sweep 在这里是“卷走”，不是“扫地”；out to sea 表离岸方向。"
        ]
      },
      {
        "id": "C4S2U2V06",
        "anchor": "send a distress signal",
        "example": "The crew sent a distress signal when the engine failed. 发动机故障后，船员发出了求救信号。",
        "gloss": "动词搭配；发出求救信号。",
        "surface": "send a distress signal",
        "collocations": [
          "send a distress signal by radio 通过无线电发求救信号",
          "receive a distress signal 收到求救信号"
        ],
        "more_examples": [
          "The hikers sent a distress signal when they lost their way. 徒步者迷路后发出了求救信号。",
          "The rescue team received a distress signal before dawn. 救援队天亮前收到求救信号。"
        ],
        "pitfalls": [
          "distress signal 是求救信号，不是普通的“心情不好”的消息。"
        ]
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
        "surface": "make up for",
        "collocations": [
          "make up for lost time 弥补耽误的时间",
          "make up for a shortfall 弥补缺口"
        ],
        "more_examples": [
          "We stayed late to make up for the missed rehearsal. 我们留下来排练，以弥补错过的那次彩排。",
          "A discount helped make up for the delivery delay. 折扣在一定程度上弥补了送货延误。"
        ],
        "pitfalls": [
          "make up for 后接要弥补的损失；不要与 make up“编造”混淆。"
        ]
      },
      {
        "id": "C4S2U3V02",
        "anchor": "declining enrollment",
        "example": "The course was cancelled because of declining enrollment. 这门课程因报名人数下降而取消。",
        "gloss": "名词短语；入学或报名人数下降。",
        "surface": "declining enrollment",
        "collocations": [
          "declining enrollment at a school 学校入学人数下降",
          "respond to declining enrollment 应对报名人数下降"
        ],
        "more_examples": [
          "The evening class closed after years of declining enrollment. 夜间课程因多年报名人数下降而停办。",
          "Declining enrollment prompted the club to combine two groups. 报名人数减少促使社团合并了两个小组。"
        ],
        "pitfalls": [
          "enrollment 在这里是人数或报名情况，不是某个学生的注册表。"
        ]
      },
      {
        "id": "C4S2U3V03",
        "anchor": "a projected decline in enrollment",
        "example": "The plan is based on a projected decline in demand. 这项计划基于对需求下降的预测。",
        "gloss": "名词短语；预计会出现的下降，projected 表预测而非既成事实。",
        "surface": "a projected decline",
        "collocations": [
          "a projected decline in sales 预计销售下降",
          "a projected decline next year 预计明年下降"
        ],
        "more_examples": [
          "The budget reflects a projected decline in ticket sales. 预算考虑了预计的票房下降。",
          "A projected decline in demand changed the team's plan. 预计需求下降让团队调整了计划。"
        ],
        "pitfalls": [
          "projected 是“预测的”，不能把它说成已经发生的 decline。"
        ]
      },
      {
        "id": "C4S2U3V04",
        "anchor": "stay out of debt",
        "example": "They set a budget to stay out of debt. 他们制定预算以避免负债。",
        "gloss": "固定搭配；避免陷入债务。",
        "surface": "stay out of debt",
        "collocations": [
          "stay out of debt by budgeting 靠预算避免负债",
          "help a family stay out of debt 帮助家庭避免负债"
        ],
        "more_examples": [
          "She tracks her spending to stay out of debt. 她记录开支，避免欠债。",
          "Buying a used laptop helped me stay out of debt. 买二手笔记本电脑帮我避免负债。"
        ],
        "pitfalls": [
          "stay out of debt 是避免欠债，不等于还清已有债务；后者可说 pay off debt。"
        ]
      },
      {
        "id": "C4S2U3V05",
        "anchor": "is set to close",
        "example": "The library is set to close for repairs next month. 图书馆定于下个月闭馆维修。",
        "gloss": "固定搭配；预计或计划要做某事。",
        "surface": "be set to",
        "collocations": [
          "be set to open next week 定于下周开业",
          "be set to begin at nine 定于九点开始"
        ],
        "more_examples": [
          "The exhibition is set to open on Monday. 展览定于周一开幕。",
          "The team is set to announce the results tomorrow. 团队预计明天公布结果。"
        ],
        "pitfalls": [
          "be set to 表计划或预期，后接动词原形；不保证事情已经发生。"
        ]
      },
      {
        "id": "C4S2U3V06",
        "anchor": "per-pupil funding",
        "example": "The report compares per-pupil funding across schools. 这份报告比较了各校的生均经费。",
        "gloss": "名词短语；按每名学生计算的经费。",
        "surface": "per-pupil funding",
        "collocations": [
          "increase per-pupil funding 提高生均经费",
          "compare per-pupil funding 比较生均经费"
        ],
        "more_examples": [
          "The district reviewed per-pupil funding across its schools. 学区审查了各校的生均经费。",
          "Per-pupil funding fell when the budget was cut. 预算削减后，生均经费下降了。"
        ],
        "pitfalls": [
          "per-pupil 是“每名学生的”，不要把它误读成全校总经费。"
        ]
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
        "surface": "take payment over the phone",
        "collocations": [
          "take payment over the phone by card 通过电话收取刷卡款项",
          "ask to take payment over the phone 请求电话付款"
        ],
        "more_examples": [
          "The travel desk can take payment over the phone. 旅行服务台可以通过电话收款。",
          "They took payment over the phone before confirming our seats. 他们电话收款后才确认我们的座位。"
        ],
        "pitfalls": [
          "take payment 是商家“收款”，顾客“付款”通常说 make a payment。"
        ]
      },
      {
        "id": "C4S2U4V02",
        "anchor": "on a business trip",
        "example": "My colleague is away on a business trip this week. 我的同事本周出差了。",
        "gloss": "固定短语；在出差途中。",
        "surface": "on a business trip",
        "collocations": [
          "be away on a business trip 因出差不在",
          "return from a business trip 出差回来"
        ],
        "more_examples": [
          "She is on a business trip in Manchester this week. 她这周去曼彻斯特出差。",
          "I met my colleague after his business trip. 同事出差回来后我见到了他。"
        ],
        "pitfalls": [
          "on a business trip 是出差；不要把 business 误解成在当地经营生意。"
        ]
      },
      {
        "id": "C4S2U4V03",
        "anchor": "can sell out",
        "example": "Popular workshops can sell out within a day. 热门工作坊可能一天内就报满。",
        "gloss": "短语动词；票、商品或名额售罄。",
        "surface": "sell out",
        "collocations": [
          "tickets sell out 门票售罄",
          "sell out within minutes 几分钟内售罄"
        ],
        "more_examples": [
          "The morning tour sold out before we booked. 我们预订前上午的参观名额就满了。",
          "These handmade mugs usually sell out quickly. 这些手工马克杯通常很快售罄。"
        ],
        "pitfalls": [
          "主语是票或商品时说 tickets sold out；商家卖光某物可说 sold out of tickets。"
        ]
      },
      {
        "id": "C4S2U4V04",
        "anchor": "reserve those for you",
        "example": "I can reserve a table for you at seven. 我可以帮你预订七点的桌位。",
        "gloss": "动词搭配；为某人预留或预订某物。",
        "surface": "reserve ... for you",
        "collocations": [
          "reserve a seat for you 为你留座",
          "reserve a room for a guest 为客人预留房间"
        ],
        "more_examples": [
          "I can reserve two seats for your group. 我可以为你们留两个座位。",
          "The hotel reserved a quiet room for us. 酒店为我们预留了安静的房间。"
        ],
        "pitfalls": [
          "reserve A for B 的 A 是被预留的东西，B 是受益人；不要把两者颠倒。"
        ]
      },
      {
        "id": "C4S2U4V05",
        "anchor": "accept my card payment",
        "example": "Does this shop accept card payments? 这家店收银行卡付款吗？",
        "gloss": "动词搭配；接受刷卡付款。",
        "surface": "accept a card payment",
        "collocations": [
          "accept card payments 接受刷卡付款",
          "accept a payment online 接受网上付款"
        ],
        "more_examples": [
          "The café accepts card payments after six. 这家咖啡馆六点后仍接受刷卡付款。",
          "Does the ticket office accept card payments? 售票处接受刷卡付款吗？"
        ],
        "pitfalls": [
          "accept payment 是收款方的动作，顾客付款说 pay by card。"
        ]
      },
      {
        "id": "C4S2U4V06",
        "anchor": "scared of heights",
        "example": "She is scared of heights, so she avoided the glass bridge. 她恐高，所以没走那座玻璃桥。",
        "gloss": "固定搭配；害怕高处。",
        "surface": "be scared of heights",
        "collocations": [
          "be scared of heights 恐高",
          "feel scared of heights in a tower 在高塔上感到恐高"
        ],
        "more_examples": [
          "He is scared of heights but still enjoys ground-floor museums. 他恐高，但仍喜欢参观一楼的博物馆。",
          "I felt scared of heights on the open staircase. 走在开放式楼梯上我有些恐高。"
        ],
        "pitfalls": [
          "scared of 后接名词或 -ing；不要说 scared to heights。"
        ]
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
        "surface": "turn ... back on",
        "collocations": [
          "turn the lights back on 重新开灯",
          "turn notifications back on 重新开启通知",
          "turn the Wi-Fi back on 重新打开无线网络"
        ],
        "more_examples": [
          "I turned the heater back on when it got cold. 天冷时我又打开了暖气。",
          "Please turn it back on after the meeting. 开完会请把它重新打开。"
        ],
        "pitfalls": [
          "宾语是代词时放在 turn 和 back on 之间：turn it back on，不能说 turn back on it。"
        ],
        "listening_trap": "back on 两词可能连在一起，听到时别漏掉 on。"
      },
      {
        "id": "C4S2U5V02",
        "anchor": "I was shocked to realize",
        "example": "I was shocked to realize how late it was. 我惊讶地发现时间已经这么晚了。",
        "gloss": "句型；惊讶地意识到某件事。",
        "surface": "be shocked to realize",
        "collocations": [
          "be shocked to realize the cost 惊讶地意识到花费",
          "be shocked to realize how much time has passed 惊讶地发现过了这么久"
        ],
        "more_examples": [
          "She was shocked to realize her ticket had expired. 她惊讶地发现自己的车票已经过期。",
          "We were shocked to realize the room was already booked. 我们惊讶地发现房间已经被订走了。"
        ],
        "pitfalls": [
          "shocked 后接 to realize，不能说 shocked for realize；realize 在这里是“意识到”，不是“实现”。"
        ]
      },
      {
        "id": "C4S2U5V03",
        "anchor": "pay in cash",
        "example": "You can pay in cash or by card. 你可以付现金，也可以刷卡。",
        "gloss": "固定搭配；用现金付款。",
        "surface": "pay in cash",
        "collocations": [
          "pay in cash at the counter 在柜台付现金",
          "pay for a meal in cash 用现金付餐费"
        ],
        "more_examples": [
          "The market stall only accepts cash, so I paid in cash. 这个市场摊位只收现金，所以我付了现金。",
          "Can I pay in cash for this notebook? 这本笔记本我能付现金吗？"
        ],
        "pitfalls": [
          "说“用现金付”用 in cash；说“刷卡付”常用 by card，不要把两个介词混用。"
        ]
      },
      {
        "id": "C4S2U5V04",
        "anchor": "don’t have any choice but to",
        "example": "The train was cancelled, so we had no choice but to wait. 火车取消了，我们只好等。",
        "gloss": "固定句型；别无选择，只能做某事。",
        "surface": "have no choice but to",
        "collocations": [
          "have no choice but to leave 别无选择只能离开",
          "have no choice but to postpone the meeting 只好推迟会议"
        ],
        "more_examples": [
          "The lift was broken, so we had no choice but to take the stairs. 电梯坏了，我们只好走楼梯。",
          "With no seats left, I had no choice but to stand. 没有空座位，我只好站着。"
        ],
        "pitfalls": [
          "but to 后接动词原形；不要写成 have no choice but doing。"
        ]
      },
      {
        "id": "C4S2U5V05",
        "anchor": "an average of eight hours a day",
        "example": "He walks an average of five kilometers a day. 他平均每天走五公里。",
        "gloss": "数量表达；平均每天达到某个量。",
        "surface": "an average of ... a day",
        "collocations": [
          "an average of six hours a day 平均每天六小时",
          "an average of three calls a day 平均每天三个电话"
        ],
        "more_examples": [
          "The library lends an average of fifty books a day. 图书馆平均每天借出五十本书。",
          "I drink an average of two cups of tea a day. 我平均每天喝两杯茶。"
        ],
        "pitfalls": [
          "an average of 后面接数量；a day 表示“每天”，不要把 an average 错写成 on average of。"
        ]
      },
      {
        "id": "C4S2U5V06",
        "anchor": "spending too much time on social media",
        "example": "I spend too much time on emails in the morning. 我早上花太多时间处理邮件。",
        "gloss": "动词搭配；在某件事上花太多时间。",
        "surface": "spend too much time on",
        "collocations": [
          "spend too much time on homework 在作业上花太多时间",
          "spend too much time on social media 在社交媒体上花太多时间"
        ],
        "more_examples": [
          "I spent too much time on the first question. 我在第一道题上花了太多时间。",
          "We spend too much time on minor details in meetings. 我们开会时在小细节上花了太多时间。"
        ],
        "pitfalls": [
          "spend time on 后接名词；若后接动作，通常说 spend time doing，而不是 spend time to do。"
        ]
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
        "surface": "moving average",
        "collocations": [
          "a three-month moving average 三个月移动平均值",
          "calculate a moving average 计算移动平均值"
        ],
        "more_examples": [
          "The dashboard displays a moving average of daily visits. 仪表盘显示每日访问量的移动平均值。",
          "We calculated a moving average to smooth out weekly changes. 我们算了移动平均值，以平滑每周波动。"
        ],
        "pitfalls": [
          "moving average 是一段时间内滚动计算的平均值，不是所有数据的一次总平均。"
        ]
      },
      {
        "id": "C4S2U6V02",
        "anchor": "gone up and down",
        "example": "The temperature has gone up and down all week. 这一周气温一直有升有降。",
        "gloss": "固定表达；上下波动。",
        "surface": "go up and down",
        "collocations": [
          "prices go up and down 价格上下波动",
          "go up and down throughout the year 全年起伏"
        ],
        "more_examples": [
          "Bus fares have gone up and down over the past decade. 过去十年公交票价时涨时跌。",
          "The number of visitors goes up and down with the weather. 游客人数随天气起伏。"
        ],
        "pitfalls": [
          "go up and down 说的是波动；不能只凭这个短语断定总体上涨。"
        ]
      },
      {
        "id": "C4S2U6V03",
        "anchor": "On average",
        "example": "On average, the trip takes forty minutes. 平均而言，这段行程需要四十分钟。",
        "gloss": "固定表达；平均来说，并非每个个体都如此。",
        "surface": "on average",
        "collocations": [
          "on average each week 平均每周",
          "on average across the group 全组平均来看"
        ],
        "more_examples": [
          "On average, each meeting lasts half an hour. 平均每次会议持续半小时。",
          "Students borrow three books a month on average. 学生平均每月借三本书。"
        ],
        "pitfalls": [
          "on average 是副词短语；不要说 on average of three books。"
        ]
      },
      {
        "id": "C4S2U6V04",
        "anchor": "as a proportion of",
        "example": "We measured transport costs as a proportion of total spending. 我们将交通费用按总支出的占比来衡量。",
        "gloss": "介词短语；作为某个整体的比例。",
        "surface": "as a proportion of",
        "collocations": [
          "costs as a proportion of income 成本占收入的比例",
          "spending as a proportion of the budget 开支占预算的比例"
        ],
        "more_examples": [
          "We tracked rent as a proportion of monthly income. 我们记录了房租占月收入的比例。",
          "The chart shows travel costs as a proportion of the total. 图表展示差旅费在总额中的占比。"
        ],
        "pitfalls": [
          "as a proportion of 后面接作为分母的整体，别把部分和整体倒过来。"
        ]
      },
      {
        "id": "C4S2U6V05",
        "anchor": "the gap is now closing",
        "example": "The gap between the two teams is closing. 两支队伍的差距正在缩小。",
        "gloss": "名词和动词搭配；差距正在缩小。",
        "surface": "the gap is closing",
        "collocations": [
          "the gap is closing slowly 差距正在缓慢缩小",
          "see the gap closing 看到差距缩小"
        ],
        "more_examples": [
          "The gap between online and in-person sales is closing. 线上与线下销售额的差距正在缩小。",
          "After several rounds, the score gap was closing. 几轮之后比分差距逐渐缩小。"
        ],
        "pitfalls": [
          "closing 表差距变小，不表示差距已经消失。"
        ]
      },
      {
        "id": "C4S2U6V06",
        "anchor": "wage growth is slowing down",
        "example": "Price growth is slowing down this year. 今年价格上涨的速度正在放缓。",
        "gloss": "动词短语；增长速度正在放慢，不等于已经下降。",
        "surface": "growth is slowing down",
        "collocations": [
          "sales growth is slowing down 销售增长在放缓",
          "growth is slowing down gradually 增长逐渐放缓"
        ],
        "more_examples": [
          "Visitor growth is slowing down this summer. 今年夏天游客增长速度正在放缓。",
          "The chart suggests that growth is slowing down, though it remains positive. 图表显示增长在放缓，但仍为正增长。"
        ],
        "pitfalls": [
          "增长放缓不等于数量下降；两者不能混用。"
        ]
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
        "surface": "even though",
        "collocations": [
          "even though it was late 尽管时间很晚",
          "even though the plan changed 尽管计划变了"
        ],
        "more_examples": [
          "We went for a walk even though it was chilly. 尽管有点冷，我们还是出去散了步。",
          "She joined the call even though she was busy. 她虽忙，还是参加了通话。"
        ],
        "pitfalls": [
          "even though 后接完整从句；不要只接一个名词。"
        ]
      },
      {
        "id": "C4S2U7V02",
        "anchor": "independent of those nutrients",
        "example": "The committee made a decision independent of the sponsor. 委员会独立于赞助方作出了决定。",
        "gloss": "形容词搭配；不依赖于、不受某因素左右。",
        "surface": "independent of",
        "collocations": [
          "independent of the outcome 不受结果左右",
          "remain independent of sponsors 保持不受赞助方影响"
        ],
        "more_examples": [
          "The review should be independent of the sales team. 评审应独立于销售团队。",
          "Her decision was independent of the prize money. 她的决定不受奖金影响。"
        ],
        "pitfalls": [
          "independent of 后接所不依赖的对象；不要把它和 dependent on 搞反。"
        ]
      },
      {
        "id": "C4S2U7V03",
        "anchor": "tends to be softer",
        "example": "The weather tends to be cooler near the coast. 海边的天气往往更凉爽。",
        "gloss": "动词搭配；通常会、有某种倾向，不表示每次都如此。",
        "surface": "tend to",
        "collocations": [
          "tend to arrive early 通常早到",
          "tend to be quieter 往往更安静"
        ],
        "more_examples": [
          "I tend to study better in the morning. 我通常早上学习效率更高。",
          "Small shops tend to close earlier on Sundays. 小店周日往往关门更早。"
        ],
        "pitfalls": [
          "tend to 是倾向，不等于 always；to 后接动词原形。"
        ]
      },
      {
        "id": "C4S2U7V04",
        "anchor": "By the time the brain gets that signal",
        "example": "By the time we arrived, the meeting had started. 我们到达时，会议已经开始了。",
        "gloss": "时间连接结构；到某个时间点时，常强调另一件事已发生。",
        "surface": "by the time",
        "collocations": [
          "by the time we arrived 到我们到达时",
          "by the time the show began 到演出开始时"
        ],
        "more_examples": [
          "By the time I reached the station, the train had left. 我到车站时火车已经开走了。",
          "The room was ready by the time the guests arrived. 客人到达时房间已准备好。"
        ],
        "pitfalls": [
          "by the time 引出时间从句；描述更早完成的动作常用过去完成时。"
        ]
      },
      {
        "id": "C4S2U7V05",
        "anchor": "come at a cost to health",
        "example": "The convenience comes at a cost to privacy. 这种便利是以隐私为代价的。",
        "gloss": "固定搭配；某种好处伴随着代价。",
        "surface": "come at a cost to",
        "collocations": [
          "come at a cost to sleep 以睡眠为代价",
          "convenience comes at a cost to privacy 便利以隐私为代价"
        ],
        "more_examples": [
          "Working late can come at a cost to family time. 工作到很晚可能挤占陪伴家人的时间。",
          "Fast delivery may come at a cost to the environment. 快速配送可能以环境为代价。"
        ],
        "pitfalls": [
          "come at a cost to 后接受到损失的对象；不是说“价格便宜”。"
        ]
      },
      {
        "id": "C4S2U7V06",
        "anchor": "a higher risk of cancer and obesity",
        "example": "Long hours outdoors can mean a higher risk of sunburn. 长时间待在户外可能增加晒伤风险。",
        "gloss": "名词搭配；某种情况发生的风险更高。",
        "surface": "a higher risk of",
        "collocations": [
          "a higher risk of delay 更高的延误风险",
          "face a higher risk of errors 面临更高的出错风险"
        ],
        "more_examples": [
          "Rushing the task creates a higher risk of mistakes. 赶任务会增加出错风险。",
          "The outdoor event faces a higher risk of cancellation in bad weather. 天气不好时，这场户外活动更可能取消。"
        ],
        "pitfalls": [
          "risk of 后面接名词或 -ing；不要说 risk to make mistakes。"
        ]
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
        "surface": "be linked to",
        "collocations": [
          "be linked to a delay 与延误有关",
          "be linked to changes in demand 与需求变化有关"
        ],
        "more_examples": [
          "The noise could be linked to roadworks nearby. 噪音可能与附近修路有关。",
          "The rise in orders may be linked to the new schedule. 订单增加可能与新时间表有关。"
        ],
        "pitfalls": [
          "be linked to 只表示有关联，不自动证明因果；to 是介词。"
        ]
      },
      {
        "id": "C4S2U8V02",
        "anchor": "primary responsibility for such tasks",
        "example": "The editor has primary responsibility for the final draft. 编辑对终稿负主要责任。",
        "gloss": "名词搭配；对某事承担主要责任。",
        "surface": "primary responsibility for",
        "collocations": [
          "take primary responsibility for training 主要负责培训",
          "have primary responsibility for a project 对项目负主要责任"
        ],
        "more_examples": [
          "She has primary responsibility for the event schedule. 她主要负责活动日程。",
          "Our office took primary responsibility for updating the guide. 我们办公室主要负责更新指南。"
        ],
        "pitfalls": [
          "responsibility for 后接所负责的事；不要说 responsibility of managing 在此替代 for managing。"
        ]
      },
      {
        "id": "C4S2U8V03",
        "anchor": "do not mean dissatisfaction",
        "example": "A quiet response does not mean dissatisfaction. 回应安静并不表示不满意。",
        "gloss": "句型；某现象并不必然意味着某结论。",
        "surface": "does not mean",
        "collocations": [
          "does not mean failure 并不意味着失败",
          "does not mean you agree 不代表你同意"
        ],
        "more_examples": [
          "A short reply does not mean the person is upset. 回复简短不意味着对方不高兴。",
          "A slow start does not mean the project will fail. 起步慢不代表项目一定失败。"
        ],
        "pitfalls": [
          "does not mean 后接名词或完整从句；别把可能性说成必然。"
        ]
      },
      {
        "id": "C4S2U8V04",
        "anchor": "a greater orientation toward family versus career",
        "example": "The course has a practical orientation toward teamwork. 这门课更侧重团队合作的实际运用。",
        "gloss": "名词搭配；更偏向某一方向或目标。这里只学习表达，不把群体描述用于判断个人。",
        "surface": "an orientation toward",
        "collocations": [
          "an orientation toward practice 偏重实践的取向",
          "an orientation toward teamwork 注重团队合作的取向"
        ],
        "more_examples": [
          "The workshop has an orientation toward hands-on learning. 工作坊更侧重动手学习。",
          "Their plan shows an orientation toward long-term maintenance. 他们的计划更注重长期维护。"
        ],
        "pitfalls": [
          "toward 后接名词或 -ing；orientation 这里是“取向”，不是入职说明会。"
        ]
      },
      {
        "id": "C4S2U8V05",
        "anchor": "Keep in mind, however",
        "example": "Keep in mind, however, that the shop closes early on Sundays. 不过要记住，这家店周日关门早。",
        "gloss": "提醒表达；不过，要记住某个补充条件。",
        "surface": "keep in mind",
        "collocations": [
          "keep in mind the deadline 记住截止日期",
          "keep in mind that plans can change 记住计划可能变化"
        ],
        "more_examples": [
          "Keep in mind that the café closes at five. 记住咖啡馆五点关门。",
          "We should keep in mind the cost of printing. 我们应记得考虑打印成本。"
        ],
        "pitfalls": [
          "keep in mind 后可接名词或 that 从句；不要逐字译成“放在脑中”。"
        ]
      },
      {
        "id": "C4S2U8V06",
        "anchor": "as early as six years old",
        "example": "Some children begin swimming as early as four years old. 有些孩子四岁就开始学游泳。",
        "gloss": "时间表达；早在某个年龄或时间。",
        "surface": "as early as",
        "collocations": [
          "as early as next week 最早下周",
          "as early as age five 早在五岁时"
        ],
        "more_examples": [
          "The tickets may go on sale as early as Friday. 门票最早可能周五开售。",
          "She started drawing maps as early as primary school. 她早在小学就开始画地图。"
        ],
        "pitfalls": [
          "as early as 强调时间早；不能把它当作 as soon as 的“只要……就”。"
        ]
      }
    ]
  }
}''')

_cet4_set1 = json.loads((Path(__file__).parent / "data/v2_full/cet4_202606_set1.learning_notes.json").read_text(encoding="utf-8"))
GUIDANCE.update(_cet4_set1["guidance"])
SOUND_NOTES.update(_cet4_set1["sound_notes"])
CONTENT.update(_cet4_set1["content"])
