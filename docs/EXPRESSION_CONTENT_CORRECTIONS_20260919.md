# 表达练习内容修订记录（2026-09-19）

## 范围与结果

针对学生反馈的“almost 遗漏导致题干与中文答案不对应”，检查现有 31 条表达、62 段新编场景和 186 道配套题。逐项检查英文正文、题干、正确选项及其他选项的对应关系，重点检查否定、数量、时间、人物、限定范围，以及题干擅自添加的地点/身份。

本轮修改 **39 段场景中的 49 道题、12 段对话正文、6 条表达释义**。其余 23 段保留，不为凑数量重写。对话正文变更的 12 段已重新生成 Edge TTS 音频，语音角色沿用原索引。

这是模型执行的内容修订与工程验证，不是教师审批，不是人工逐段听审。所有 review_status 保持 pending_teacher；真题 source_sentence、source_type、source_sentence_status 没有因本轮修改提高审核等级。

## 学生反馈与已有修改

- scn_annual_leave_colleague 的 almost 已在本轮开始前修正，本轮保留并加入回归测试，不冒领为新修复。
- scn_fair_chores 的正确人物分工在本轮开始前已修正；本轮保留 B 厨房 / A 卫生间，明确先后与每月轮换，并修订相邻选项。
- 表达文件中此前四条 source_sentence 修改完整保留，本轮没有改任何真题原句。
- 不修改现有个人作答数据库，不把旧记录重新判分。

## 重点修订示例

1. 酒店：星期六不是房型；改问星期六可订的房间类型。题干问“还有什么可订”，不把可订写成已完成预订。
2. 餐厅：明确“周六七点订满”，与“九点一刻还有位置”保持一致。
3. 布拉格行程：三天假配两晚住宿，更新对应选项。
4. 全包套餐：限定于列明的餐食和标准饮品，不把所有额外消费都说成免费。
5. 药物场景：删掉未明确药物时编造的“两小时间隔”和“吃新药当天停过敏药”，改成核对具体药物后再建议。
6. 生词题：配药、恢复精力、再次确认等含义题回到目标表达，不再把另一条细节当成词义。
7. 场景题：无录音依据时不强行断定电话、大学、办公室、同事、医生等身份地点；改问实际讨论的事项。
8. 年假时间：六月休假改为给“年内以后或急事”留假，避免没有交代的春节跨年关系。
9. 研究场景：去掉“一半岗位不公开”“午睡二十分钟改善记忆”等无来源的精确断言。
10. 释义：city break 不规定固定 2–4 天；职场 get ahead 不仅指升职；全包和配药说明语境范围。

## 62 段检查清单

scene 表示情境/话题题，meaning 表示表达含义/作用题，key_info 表示具体信息题。

| 场景 ID | 本轮处理 | 修改的题目 | 音频 | 修订理由/说明 |
| --- | --- | --- | --- | --- |
| scn_fully_booked_hotel | 修订 | key_info | 已重新生成 | 房型问法；可订不等于已订 |
| scn_fully_booked_restaurant | 修订 | meaning | 已重新生成 | 限定订满时段，消除与九点一刻有位的矛盾 |
| scn_city_break_travel_agency | 修订 | key_info | 已重新生成 | 三天假与三晚行程不自洽，改两晚 |
| scn_city_break_phone_friend | 修订 | scene | 沿用原录音 | 无电话依据，改问话题 |
| scn_annual_leave_hr | 保留 | — | 沿用原录音 | 本轮文字核对未发现需要修改的对应性错误；不是教师终审结论 |
| scn_annual_leave_colleague | 保留 | — | 沿用原录音 | 本轮文字核对未发现需要修改的对应性错误；不是教师终审结论 |
| scn_scramble_housing | 保留 | — | 沿用原录音 | 本轮文字核对未发现需要修改的对应性错误；不是教师终审结论 |
| scn_scramble_conference | 修订 | scene | 沿用原录音 | 不把参展自动认作出差 |
| scn_offset_roommate | 保留 | — | 沿用原录音 | 本轮文字核对未发现需要修改的对应性错误；不是教师终审结论 |
| scn_offset_carpool | 保留 | — | 沿用原录音 | 本轮文字核对未发现需要修改的对应性错误；不是教师终审结论 |
| scn_all_inclusive_hotel | 修订 | meaning | 已重新生成 | 全包限定于套餐，去掉任何饮食都免费的绝对说法 |
| scn_all_inclusive_agency | 修订 | scene、meaning | 沿用原录音 | 无明确旅行社地点；套餐范围具体化 |
| scn_query_venue | 保留 | — | 沿用原录音 | 本轮文字核对未发现需要修改的对应性错误；不是教师终审结论 |
| scn_query_university | 修订 | scene | 沿用原录音 | 去除无依据的校园位置 |
| scn_thrilled_gift | 修订 | scene | 沿用原录音 | 选项同类且互斥 |
| scn_thrilled_job | 保留 | — | 沿用原录音 | 本轮文字核对未发现需要修改的对应性错误；不是教师终审结论 |
| scn_get_ahead_review | 保留 | — | 沿用原录音 | 本轮文字核对未发现需要修改的对应性错误；不是教师终审结论 |
| scn_get_ahead_mentor | 保留 | — | 沿用原录音 | 本轮文字核对未发现需要修改的对应性错误；不是教师终审结论 |
| scn_expand_network_alumni | 修订 | scene、key_info | 已重新生成 | 去掉无依据的一半岗位统计；不假定两人都会参加 |
| scn_expand_network_conference | 修订 | meaning | 沿用原录音 | 减少业务网络与人脉网络重叠 |
| scn_take_on_manager | 修订 | scene | 沿用原录音 | 改问可确定的任务，不猜办公地点 |
| scn_take_on_student | 修订 | scene | 沿用原录音 | 以内容替代无依据地点 |
| scn_quality_time_family | 保留 | — | 沿用原录音 | 本轮文字核对未发现需要修改的对应性错误；不是教师终审结论 |
| scn_quality_time_study | 修订 | scene | 沿用原录音 | 问题与答案类别统一 |
| scn_beyond_resp_interview | 保留 | — | 沿用原录音 | 本轮文字核对未发现需要修改的对应性错误；不是教师终审结论 |
| scn_beyond_resp_volunteer | 修订 | scene | 沿用原录音 | 去除活动已结束及办公室位置的臆测 |
| scn_help_out_move | 保留 | — | 沿用原录音 | 本轮文字核对未发现需要修改的对应性错误；不是教师终审结论 |
| scn_help_out_neighbor | 保留 | — | 沿用原录音 | 本轮文字核对未发现需要修改的对应性错误；不是教师终审结论 |
| scn_divide_up_groupproject | 修订 | scene | 沿用原录音 | 不假定校园地点 |
| scn_divide_up_charity | 修订 | meaning | 沿用原录音 | 含义题回到目标表达 |
| scn_dole_out_meeting | 保留 | — | 沿用原录音 | 本轮文字核对未发现需要修改的对应性错误；不是教师终审结论 |
| scn_dole_out_volunteer | 修订 | meaning | 沿用原录音 | 不把原因细节算作词义识别 |
| scn_bulk_of_project | 修订 | scene | 沿用原录音 | 报告不必然是同事；问确切话题 |
| scn_bulk_of_moving | 保留 | — | 沿用原录音 | 本轮文字核对未发现需要修改的对应性错误；不是教师终审结论 |
| scn_fair_chores | 修订 | scene、key_info | 沿用原录音 | 保留已修正人物关系；不臆断合租；干扰项围绕角色与周期 |
| scn_fair_shifts | 保留 | — | 沿用原录音 | 本轮文字核对未发现需要修改的对应性错误；不是教师终审结论 |
| scn_feel_presentation | 修订 | scene | 沿用原录音 | 不猜地点，聚焦交际任务 |
| scn_feel_registration | 修订 | scene、meaning | 沿用原录音 | 不限定大学；词义题考委婉提议 |
| scn_prescription_pharmacy | 保留 | — | 沿用原录音 | 本轮文字核对未发现需要修改的对应性错误；不是教师终审结论 |
| scn_prescription_phone | 修订 | meaning | 沿用原录音 | 纠正词义题类型 |
| scn_interaction_pharmacist | 修订 | key_info | 已重新生成 | 删除无依据具体服药间隔 |
| scn_interaction_doctor | 修订 | meaning、key_info | 已重新生成 | 删除无依据停药安排 |
| scn_doublecheck_supplement | 修订 | scene、key_info | 已重新生成 | 删除对多数人安全的无依据保证；不臆断说话人职业 |
| scn_doublecheck_insurance | 修订 | meaning | 沿用原录音 | 含义题不再用报销条件替代 |
| scn_timeoff_colleague | 修订 | scene | 沿用原录音 | 不把可能的同事关系当作必然 |
| scn_timeoff_friend | 修订 | scene、key_info | 沿用原录音 | 避免将计划去海边误说成休息结束之后 |
| scn_recharge_weekend | 修订 | scene | 沿用原录音 | 题干与选项维度一致，去掉未明示同事身份 |
| scn_recharge_holiday | 修订 | meaning | 沿用原录音 | 纠正词义题 |
| scn_putoff_essay | 修订 | scene | 沿用原录音 | 用确切话题替代地点推断 |
| scn_putoff_dentist | 修订 | key_info | 已重新生成 | 未预约不说推迟已有预约；纠正蛀牙变成治疗的表达 |
| scn_spaceout_study | 修订 | scene | 沿用原录音 | 关系不确定，改问可确定主题 |
| scn_spaceout_meetings | 保留 | — | 沿用原录音 | 本轮文字核对未发现需要修改的对应性错误；不是教师终审结论 |
| scn_useup_hr | 修订 | key_info | 已重新生成 | 消除六月与春节的未说明时间关系 |
| scn_useup_travel | 保留 | — | 沿用原录音 | 本轮文字核对未发现需要修改的对应性错误；不是教师终审结论 |
| scn_oldhabits_doctor | 保留 | — | 沿用原录音 | 本轮文字核对未发现需要修改的对应性错误；不是教师终审结论 |
| scn_oldhabits_friend | 修订 | scene、key_info | 沿用原录音 | 去掉戒断诊断用语，话题题与细节题分开 |
| scn_comeacross_article | 修订 | scene、key_info | 已重新生成 | 删除无来源研究结论，保留文章主题；不猜办公室地点 |
| scn_comeacross_study | 修订 | key_info | 已重新生成 | 删除未经核实的精确研究结论，不虚构二十分钟效果 |
| scn_harm_supplements | 修订 | scene、key_info | 沿用原录音 | 原文未明示医生身份，不以题干补出职业 |
| scn_harm_meetings | 保留 | — | 沿用原录音 | 本轮文字核对未发现需要修改的对应性错误；不是教师终审结论 |
| scn_wct_food | 保留 | — | 沿用原录音 | 本轮文字核对未发现需要修改的对应性错误；不是教师终审结论 |
| scn_wct_deadlines | 保留 | — | 沿用原录音 | 本轮文字核对未发现需要修改的对应性错误；不是教师终审结论 |

## 音频与旧版本保护

- 音频文件使用新文件名，12 个旧文件全部保留，没有覆盖或删除。
- audio_index.json 更新对应文件、生成时间、正文 SHA256、音频 SHA256 和内容版本。
- 12 段新音频通过 PyAV 完整解码检查，时长约 15.8–29.3 秒；这证明文件能解码，不证明发音、重音、停顿已人工审核。
- 修改前的三份数据原样保存于：
  - backend/listening/data/expressions/history/20260919_before/expressions.json
  - backend/listening/data/expressions/history/20260919_before/scenarios.json
  - backend/listening/data/expressions/history/20260919_before/audio_index.json
- 修订的场景 revision 从 1 增至 2，旧成绩继续保留原记录版本。
- 学生页面携带版本获取音频、揭示和提交；旧页面缺版本或版本不一致时返回 409，要求刷新，不保存此次成绩。
- 教师音频链接也带版本，避免审核页因新保护而无法播放。
- 本轮没有改变答案字母的位置，因此未进行选项随机重排。

## 验证记录

- 全量隔离测试：270 passed in 40.11s。
- 前端 npm run build：退出码 0。
- 新增 9 个测试实例覆盖原句保留、31/62/186 结构、修改场景版本、答案位置不变、音频/正文哈希、旧音频保留、almost/日期/人物限定、医疗改写，以及旧页面拒绝提交、新页面可获取音频与提交。
- 真实 backend/listening/data/listening.db 的 SHA256：
  AEDEB601197E859E3ECA5E41DCB809288352FCEECDE6E4F5648F7B6B19628DC0
  与本轮开始一致。
- 测试采用既有隔离运行器 backend/tests/run_student_auth_regression.py，不在真实库上写入。
- 未提交 Git，未部署线上，未修改 .env、Nginx、发布开关或教师认证实现。

## 文件范围

- 内容：expressions.json、scenarios.json、audio_index.json、12 个新 MP3、3 份历史快照。
- 衔接：expression_service.py 的公开场景增加版本；router.py 增加版本核对。
- 前端：listeningApi.ts、ExpressionTrainView.vue、TeacherExpressionDetailView.vue 仅衔接版本与错误提示，没有重做页面。
- 验证：backend/tests/test_expression_content_revision.py。
- 文档：本文件。

## 没有把哪些问题算作已解决

本次聚焦“原文—题干—选项—答案对应”，不是此前四项工程方案的整体执行：

- 答案位置仍为 A=51、B=116、C=18、D=1，未重排；同样没有宣称最长选项捷径已消除。
- 学生页提前显示词义和场景标签的问题，及“三题全对=迁移成功”的措辞，未在此次内容数据修订中改造。
- 默认隐藏未审核内容的统一审核门尚未新增，生产审核策略仍需要单独实施。
- 单人朗读整段对话的限制仍存在，没有改为 A/B 双人分角色音频。
- 31 条来源逐句对 PDF 的独立核验、完整人工听审均未执行，不据此改成 teacher_verified / approved。
- 未重新训练或重算学生能力画像，也没有证明泛化学习效果。

上线时需要后端、前端、三个内容文件和 12 个新音频一起发布，不能只替换题库；不得上传本机测试数据库。先完成独立内容复核及发布决策，旧页面需刷新后作答。

