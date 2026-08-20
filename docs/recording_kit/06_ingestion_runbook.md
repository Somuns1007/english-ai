# 真人录音 Ingestion Runbook

> 录音到达 `backend/listening/data/_incoming_recordings/` 后，按本流程走。
> 原则：**真人录音与公开语料走同一条流水线，没有捷径。**
> 唯一区别：上传时 `permission_status=owned` 且必须带授权链字段。

## 0. 前置检查（缺一不进库）

- [ ] `04_consent_log.md` 有本段录音的记录行
- [ ] 授权协议已签署，商用/AI 处理勾选状态与登记表一致
- [ ] 文件名符合命名规范

## 1. 上传（带授权链）

```bash
TOKEN=<教师口令>
curl -X POST "http://localhost:8000/api/listening/teacher/corpus/assets\
?title=Hotel full booking dialogue v1 (self-recorded)\
&source_name=Self-recorded pilot (consent CONSENT-2026-0001)\
&license=self_recorded\
&permission_status=owned\
&consent_id=CONSENT-2026-0001\
&speaker_ids=SPK_A,SPK_B\
&commercial_permission=true\
&editing_permission=true\
&ai_processing_permission=true\
&recorded_at=2026-08-21" \
  -H "X-Teacher-Token: $TOKEN" \
  -F "file=@backend/listening/data/_incoming_recordings/hotel_v1_20260821_take1.wav"
```

系统行为：`permission_status=owned` 但缺 `consent_id` 的素材**无法被批准**，
也不会出现在学生端——这是硬门控，不是约定。

## 2. ASR → 切分 → 匹配（与 AMI 相同的端点）

```bash
curl -X POST .../teacher/corpus/assets/{asset_id}/run-asr        -H "X-Teacher-Token: $TOKEN"
curl -X POST .../teacher/corpus/assets/{asset_id}/run-segmentation -H "X-Teacher-Token: $TOKEN"
curl -X POST .../teacher/corpus/assets/{asset_id}/run-matching     -H "X-Teacher-Token: $TOKEN"
```

## 3. 教师审核（教师页面操作）

1. 对照音频修正 transcript（改 transcript 会 bump `content_revision` 并回落待审——
   这是刻意设计：内容变了必须重审；只调标签只 bump `metadata_revision`）。
2. 选教学价值高的片段建 clip（多人轮次完整、含目标交际功能的片段优先）。
3. 打标签：scenario_tags / communicative_function / difficulty / accent /
   speaker_count / speech_rate / listening_features。
4. Expression 匹配：
   - 规则命中（exact/target_surface/related）以 candidate 出现，逐条确认或否决；
   - 真人说了功能等价但用词不同的表达（对照 `05_card_evaluation.md` 收集的原话），
     用「添加匹配」手动建立 `communicative_equivalent`（必须填原话 matched_text + note）。
   - **Phase 7.7 不使用任何 LLM 自动建立关联。**
5. 批准 clip → 批准 asset（5 条质检自查：音质/上下文/自然度/难度/迁移价值）。

## 4. 验收核对

- 学生端 `/listening/corpus` 出现新 clip，attribution 显示
  "Self-recorded pilot (consent CONSENT-2026-XXXX)"。
- 授权登记、clip、expression 关联三者能对上号。

## 撤回处理

录音者在撤回期内行使撤回权：教师将 asset `permission_status` 改为 `unverified`
（自动回落待审、学生端立即不可见），随后删除音频文件与 clips，
并在 consent log 备注撤回日期。
