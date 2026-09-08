# student_id ↔ 登录打通：完整变更与验证

## 1. Summary

本次只覆盖接收 student_id 的端点：有效 cookie 优先账号 UUID，否则保留客户端匿名 ID。无匿名历史合并，不新增资源级访问控制。

- backend/listening/router.py：26 个端点（14 Query、12 body）接入可选认证。使用当前项目可导入的 `from auth.service ...`；附件的 `..auth` 不适用于现有顶层 listening 包。
- 使用 `Annotated[str | None, Depends(...)] = None`，兼容旧测试直接调用路由函数；缺失/无效 cookie 或认证异常依要求回退匿名。
- frontend/src/services/listeningEvents.ts：优先 currentUser.id，不覆盖 localStorage；保留原有 stu_… 匿名 ID 格式。
- 以下 12 个视图：一次性 studentId 改 computed；脚本使用 .value，模板自动解包，无训练流程或样式变化。
  - frontend/src/views/listening/ListeningMistakesView.vue
  - frontend/src/views/listening/ListeningStrictPacingView.vue
  - frontend/src/views/listening/ListeningExpressionsView.vue
  - frontend/src/views/listening/ListeningReviewView.vue
  - frontend/src/views/listening/StemBankView.vue
  - frontend/src/views/listening/ListeningExamView.vue
  - frontend/src/views/listening/ListeningProfileView.vue
  - frontend/src/views/listening/ListeningExamV2View.vue
  - frontend/src/views/listening/ExpressionTrainView.vue
  - frontend/src/views/listening/ListeningPracticeV2View.vue
  - frontend/src/views/listening/AuralLexiconView.vue
  - frontend/src/views/listening/ListeningDashboardView.vue

- backend/tests/test_student_auth.py：26 个端点双身份覆盖、真实 cookie/数据库集成、两设备登录续接、异常回退与关闭的 release gate。
- frontend/tests/studentIdentity.test.mjs：匿名持久化、账号切换/登出响应性、不覆盖匿名 ID。
- backend/tests/run_student_auth_regression.py：安全回归入口，自动设置临时 LISTENING_DB_PATH/AUTH_DB_PATH，并复制旧测试会编辑的表达 JSON/音频；禁止写真实 data 目录。
- 本说明：逐文件给出仅本次任务的完整 diff；排除之前已有的未提交视觉与认证修改。

## 2. 完整改动

### backend/listening/router.py

```diff
--- a/backend/listening/router.py
+++ b/backend/listening/router.py
@@ -2,9 +2,9 @@
 """听力模块 API 路由。所有端点挂载在 /api/listening 前缀下。"""
 import os
 from pathlib import Path
+from typing import Annotated, Optional
-from typing import Optional
 
+from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Query, UploadFile
-from fastapi import APIRouter, Depends, Header, HTTPException, Query, UploadFile
 from fastapi.responses import FileResponse
 from pydantic import BaseModel
 
@@ -30,11 +30,23 @@
     RetryIn,
     TrainingResultIn,
 )
+from auth.service import get_user_by_token as _auth_get_user
+
 from .repository import exam_repo, load_tag_dictionary, student_repo
 
 router = APIRouter(prefix="/api/listening", tags=["listening"])
 
 
+def _optional_student_id(token: str | None = Cookie(default=None)) -> str | None:
+    """有效登录优先使用账号 UUID；缺失或验证异常按约定回退匿名流程。"""
+    if not token:
+        return None
+    try:
+        return _auth_get_user(token).id
+    except Exception:
+        return None
+
+
 def require_teacher(
     x_teacher_token: Optional[str] = Header(None),
     token: Optional[str] = Query(None),
@@ -54,7 +66,8 @@
 
 
 @router.get("/exams")
+def list_exams(student_id: str = Query("anonymous"), auth_id: Annotated[str | None, Depends(_optional_student_id)] = None):
+    student_id = auth_id if auth_id is not None else student_id
-def list_exams(student_id: str = Query("anonymous")):
     return {"data": [s.model_dump() for s in service.exam_summaries(student_id)]}
 
 
@@ -90,12 +103,13 @@
 
 
 @router.post("/attempts")
+def create_attempt(body: AttemptCreate, auth_id: Annotated[str | None, Depends(_optional_student_id)] = None):
+    effective_id = auth_id if auth_id is not None else body.student_id
-def create_attempt(body: AttemptCreate):
     if v2_exam_service.is_v2_exam(body.exam_id) and not v2_exam_service.gate_allows():
         raise HTTPException(status_code=403, detail="该套题尚未发布")
     if not exam_repo.get(body.exam_id) and not v2_exam_service.is_v2_exam(body.exam_id):
         raise HTTPException(status_code=404, detail="套题不存在")
+    attempt = student_repo.create_attempt(effective_id, body.exam_id, body.mode)
-    attempt = student_repo.create_attempt(body.student_id, body.exam_id, body.mode)
     return {"data": attempt}
 
 
@@ -104,8 +118,10 @@
     exam_id: str = Query(...),
     mode: str = Query("practice_mode"),
     student_id: str = Query("anonymous"),
+    auth_id: Annotated[str | None, Depends(_optional_student_id)] = None,
 ):
     """刷新恢复: 查找未提交 attempt 并带回已保存答案。"""
+    student_id = auth_id if auth_id is not None else student_id
     attempt = student_repo.find_in_progress_attempt(student_id, exam_id, mode)
     if not attempt:
         return {"data": None}
@@ -113,15 +129,16 @@
 
 
 @router.post("/attempts/{attempt_id}/events")
+def post_behavior_events(attempt_id: str, body: BehaviorEventBatch, auth_id: Annotated[str | None, Depends(_optional_student_id)] = None):
-def post_behavior_events(attempt_id: str, body: BehaviorEventBatch):
     """行为事件批量上报。只记录, 不据此自动判定学生错因。"""
+    effective_id = auth_id if auth_id is not None else body.student_id
     attempt = student_repo.get_attempt(attempt_id)
     if not attempt:
         raise HTTPException(status_code=404, detail="作答记录不存在")
     # K6 fix: gate 关闭后, 已存在的 V2 attempt 也不得继续写入
     if v2_exam_service.is_v2_exam(attempt["exam_id"]) and not v2_exam_service.gate_allows():
         raise HTTPException(status_code=403, detail="该套题尚未发布")
+    saved = student_repo.add_behavior_events(effective_id, attempt_id, body.events)
-    saved = student_repo.add_behavior_events(body.student_id, attempt_id, body.events)
     return {"data": {"saved": saved}}
 
 
@@ -220,7 +237,8 @@
 
 
 @router.post("/diagnoses")
+def save_diagnosis(body: DiagnosisIn, auth_id: Annotated[str | None, Depends(_optional_student_id)] = None):
+    effective_id = auth_id if auth_id is not None else body.student_id
-def save_diagnosis(body: DiagnosisIn):
     attempt = student_repo.get_attempt(body.attempt_id)
     if not attempt:
         raise HTTPException(status_code=404, detail="作答记录不存在")
@@ -228,7 +246,7 @@
     # 系统推测以 /candidates 接口的行为证据版为准, 诊断记录只保存
     # 学生自判(student_tags)与最终确认(final_tags), 保持分层。
     result = student_repo.upsert_diagnosis(
+        effective_id,
-        body.student_id,
         body.attempt_id,
         body.question_id,
         body.student_tags,
@@ -239,12 +257,13 @@
 
 
 @router.post("/training-results")
+def save_training_result(body: TrainingResultIn, auth_id: Annotated[str | None, Depends(_optional_student_id)] = None):
-def save_training_result(body: TrainingResultIn):
     """训练结果落库。证据链字段由服务端权威判定, 不信任客户端上报:
     - diagnosis_id/diagnosis_revision: 绑定"当前有效诊断"(而非客户端传的旧值)
     - provenance: 由题目数据判定(teacher_calibrated / generated_unverified)
     - trigger_tags: 快照当前训练计划中触发了该训练类型的错因
     """
+    effective_id = auth_id if auth_id is not None else body.student_id
     diagnosis_id = body.diagnosis_id
     diagnosis_revision = None
     provenance = None
@@ -267,7 +286,7 @@
                     if t["type"] == body.training_type
                 })
     result = student_repo.add_training_result(
+        effective_id,
-        body.student_id,
         body.question_id,
         body.training_type,
         body.pre_result,
@@ -295,7 +314,9 @@
     section: str = Query(None),
     trained: bool = Query(None),
     retested: bool = Query(None),
+    auth_id: Annotated[str | None, Depends(_optional_student_id)] = None,
 ):
+    student_id = auth_id if auth_id is not None else student_id
     return {
         "data": service.list_mistakes(
             student_id, mastery=mastery, tag=tag,
@@ -389,19 +410,22 @@
 
 
 @router.get("/profile")
+def get_profile(student_id: str = Query("anonymous"), auth_id: Annotated[str | None, Depends(_optional_student_id)] = None):
-def get_profile(student_id: str = Query("anonymous")):
     """Phase 5A 证据画像: cause 聚合 → confidence/current_risk/cause_mastery
     → skill 聚合 → trend → 规则化推荐。全部规则计算, 可反查 evidence_refs。"""
+    student_id = auth_id if auth_id is not None else student_id
     return {"data": profile_service.build_profile(student_id)}
 
 
 @router.get("/profile/causes")
+def get_profile_causes(student_id: str = Query("anonymous"), auth_id: Annotated[str | None, Depends(_optional_student_id)] = None):
+    student_id = auth_id if auth_id is not None else student_id
-def get_profile_causes(student_id: str = Query("anonymous")):
     return {"data": profile_service.build_cause_profile(student_id)}
 
 
 @router.get("/profile/skills")
+def get_profile_skills(student_id: str = Query("anonymous"), auth_id: Annotated[str | None, Depends(_optional_student_id)] = None):
+    student_id = auth_id if auth_id is not None else student_id
-def get_profile_skills(student_id: str = Query("anonymous")):
     causes = profile_service.build_cause_profile(student_id)
     return {"data": profile_service.build_skill_profile(causes)}
 
@@ -418,8 +442,9 @@
 
 
 @router.get("/expressions")
+def list_expressions(student_id: str = Query("anonymous"), auth_id: Annotated[str | None, Depends(_optional_student_id)] = None):
-def list_expressions(student_id: str = Query("anonymous")):
     """表达卡片列表(含该学生进度)。表达全部 source_type=official_exam, 可追溯。"""
+    student_id = auth_id if auth_id is not None else student_id
     return {"data": expression_service.list_expressions(student_id)}
 
 
@@ -449,8 +474,9 @@
 
 
 @router.get("/expressions/{expression_id}")
+def get_expression(expression_id: str, student_id: str = Query("anonymous"), auth_id: Annotated[str | None, Depends(_optional_student_id)] = None):
-def get_expression(expression_id: str, student_id: str = Query("anonymous")):
     """表达详情 + 场景列表。场景不含 text 与答案(先听不看文本)。"""
+    student_id = auth_id if auth_id is not None else student_id
     data = expression_service.expression_detail(expression_id, student_id)
     if not data:
         raise HTTPException(status_code=404, detail="表达不存在")
@@ -467,11 +493,12 @@
 
 
 @router.post("/expressions/scenarios/{scenario_id}/submit")
+def submit_scenario(scenario_id: str, body: ExpressionSubmitIn, auth_id: Annotated[str | None, Depends(_optional_student_id)] = None):
-def submit_scenario(scenario_id: str, body: ExpressionSubmitIn):
     """提交三题作答: 服务端判分, 落 expression_attempts 证据表, 返回揭示内容。"""
+    effective_id = auth_id if auth_id is not None else body.student_id
     result = expression_service.submit_scenario(
         scenario_id,
+        effective_id,
-        body.student_id,
         body.answers,
         body.listen_count_before_submit,
         body.reveal_used,
@@ -919,11 +946,12 @@
 
 
 @router.post("/v2/practice/sessions")
+def v2_practice_create_session(body: _CpSessionCreate, auth_id: Annotated[str | None, Depends(_optional_student_id)] = None):
-def v2_practice_create_session(body: _CpSessionCreate):
     """创建 session: pin 内容 revision/hash + round2 选项顺序。"""
+    effective_id = auth_id if auth_id is not None else body.student_id
     if not v2_exam_service.gate_allows():
         raise HTTPException(status_code=403, detail="该练习尚未发布")
+    session = v2_practice_service.create_session(effective_id, body.material_id)
-    session = v2_practice_service.create_session(body.student_id, body.material_id)
     if session is None:
         raise HTTPException(status_code=404, detail="材料不存在")
     return {"data": {"session_id": session["id"], "stage": session["stage"]}}
@@ -932,8 +960,10 @@
 @router.get("/v2/practice/sessions/find")
 def v2_practice_find_session(
     material_id: str = Query(...), student_id: str = Query("anonymous"),
+    auth_id: Annotated[str | None, Depends(_optional_student_id)] = None,
 ):
     """刷新恢复: 找该学生在该材料上最近的 session。"""
+    student_id = auth_id if auth_id is not None else student_id
     if not v2_exam_service.gate_allows():
         raise HTTPException(status_code=403, detail="该练习尚未发布")
     session = v2_practice_service.find_session(student_id, material_id)
@@ -954,13 +984,14 @@
 
 
 @router.post("/v2/practice/sessions/{session_id}/events")
+def v2_practice_events(session_id: str, body: _CpEventBatch, auth_id: Annotated[str | None, Depends(_optional_student_id)] = None):
-def v2_practice_events(session_id: str, body: _CpEventBatch):
     """行为事件批量上报(白名单事件类型; 只记录事实)。"""
+    effective_id = auth_id if auth_id is not None else body.student_id
     if not v2_exam_service.gate_allows():
         raise HTTPException(status_code=403, detail="该练习尚未发布")
     try:
         result = v2_practice_service.record_events(
+            session_id, effective_id, [e.model_dump() for e in body.events])
-            session_id, body.student_id, [e.model_dump() for e in body.events])
     except PermissionError as exc:
         raise HTTPException(status_code=403, detail=str(exc))
     if result is None:
@@ -1040,29 +1071,33 @@
 
 
 @router.get("/lexicon/session")
+def lexicon_daily_session(student_id: str = Query(...), auth_id: Annotated[str | None, Depends(_optional_student_id)] = None):
-def lexicon_daily_session(student_id: str = Query(...)):
     """今日词汇会话：到期复习 + 新词引入。Phase 0 期间配额加重。"""
+    student_id = auth_id if auth_id is not None else student_id
     return {"data": aural_lexicon_service.get_daily_session(student_id)}
 
 
 @router.get("/lexicon/phase0/status")
+def lexicon_phase0_status(student_id: str = Query(...), auth_id: Annotated[str | None, Depends(_optional_student_id)] = None):
-def lexicon_phase0_status(student_id: str = Query(...)):
     """获取 Phase 0 状态（含 exam_practice_allowed 字段）。"""
+    student_id = auth_id if auth_id is not None else student_id
     return {"data": aural_lexicon_service.get_phase0_status(student_id)}
 
 
 @router.get("/lexicon/phase0/entry-test")
+def lexicon_entry_test(student_id: str = Query(...), auth_id: Annotated[str | None, Depends(_optional_student_id)] = None):
-def lexicon_entry_test(student_id: str = Query(...)):
     """获取入口听觉词汇测试词条（40条随机抽样）。"""
+    student_id = auth_id if auth_id is not None else student_id
     return {"data": aural_lexicon_service.start_entry_test(student_id)}
 
 
 @router.post("/lexicon/phase0/entry-test/complete")
+def lexicon_entry_test_complete(body: _EntryTestResultsIn, auth_id: Annotated[str | None, Depends(_optional_student_id)] = None):
-def lexicon_entry_test_complete(body: _EntryTestResultsIn):
     """提交入口测试结果，决定是否进入 Phase 0。
 
     DTO 约束: results 只接受 item_id + is_correct，无 listening ability 字段。
     """
+    effective_id = auth_id if auth_id is not None else body.student_id
     # Validate: no forbidden ability fields in results
     for res in body.results:
         forbidden = {"understanding_stable", "ability_improved", "diagnosis",
@@ -1073,29 +1108,31 @@
                 detail=f"禁止字段: {forbidden} (DTO 白名单违规)"
             )
     result = aural_lexicon_service.complete_entry_test(
+        effective_id, body.results, body.threshold
-        body.student_id, body.results, body.threshold
     )
     return {"data": result}
 
 
 @router.post("/lexicon/phase0/complete")
+def lexicon_phase0_complete(body: _Phase0CompleteIn, auth_id: Annotated[str | None, Depends(_optional_student_id)] = None):
-def lexicon_phase0_complete(body: _Phase0CompleteIn):
     """Phase 0 复测达标，标记完成，开放六级练习。"""
+    effective_id = auth_id if auth_id is not None else body.student_id
     result = aural_lexicon_service.complete_phase0(
+        effective_id, body.retest_score
-        body.student_id, body.retest_score
     )
     return {"data": result}
 
 
 @router.post("/lexicon/attempt")
+def lexicon_record_attempt(body: _LexAttemptIn, auth_id: Annotated[str | None, Depends(_optional_student_id)] = None):
-def lexicon_record_attempt(body: _LexAttemptIn):
     """记录词汇 attempt，更新 SRS 调度。
 
     响应只含 attempt_id + lexical_item_recognized（无 ability 结论）。
     """
+    effective_id = auth_id if auth_id is not None else body.student_id
     try:
         result = aural_lexicon_service.record_attempt(
+            student_id=effective_id,
-            student_id=body.student_id,
             item_id=body.item_id,
             task_type=body.task_type,
             is_correct=body.is_correct,
@@ -1134,16 +1171,17 @@
 
 
 @router.post("/lexicon/harvest")
+def lexicon_harvest(body: _HarvestIn, auth_id: Annotated[str | None, Depends(_optional_student_id)] = None):
-def lexicon_harvest(body: _HarvestIn):
     """听后采集：将词条加入 SRS 队列。
 
     D3 红线：gate_type='exam_attempt' 要求 submitted_at IS NOT NULL；
              gate_type='cp_session'  要求 stage='result_final'。
     响应无 ability 结论字段。
     """
+    effective_id = auth_id if auth_id is not None else body.student_id
     try:
         result = aural_lexicon_service.harvest_word(
+            student_id=effective_id,
-            student_id=body.student_id,
             item_id=body.item_id,
             gate_type=body.gate_type,
             gate_id=body.gate_id,
@@ -1189,14 +1227,15 @@
 
 
 @router.post("/stem-bank/predict")
+def stem_bank_predict(body: _PredictionIn, auth_id: Annotated[str | None, Depends(_optional_student_id)] = None):
-def stem_bank_predict(body: _PredictionIn):
     """提交题型预测 + 答案选择，返回正确答案与 is_correct。
 
     此端点是唯一返回 correct_answer 的路径。
     """
+    effective_id = auth_id if auth_id is not None else body.student_id
     try:
         result = stem_bank_service.record_prediction(
+            student_id=effective_id,
-            student_id=body.student_id,
             question_no=body.question_no,
             predicted_type=body.predicted_type,
             selected_answer=body.selected_answer,
@@ -1207,8 +1246,9 @@
 
 
 @router.get("/stem-bank/stats")
+def stem_bank_stats(student_id: str = Query(...), auth_id: Annotated[str | None, Depends(_optional_student_id)] = None):
-def stem_bank_stats(student_id: str = Query(...)):
     """学生各题型预测准确率统计（无 ability 结论文案）。"""
+    student_id = auth_id if auth_id is not None else student_id
     return {"data": stem_bank_service.get_student_stats(student_id)}
 
 
@@ -1217,9 +1257,10 @@
 # ══════════════════════════════════════════════════════════════════════
 
 @router.get("/dashboard")
+def student_dashboard(student_id: str = Query(...), auth_id: Annotated[str | None, Depends(_optional_student_id)] = None):
-def student_dashboard(student_id: str = Query(...)):
     """聚合仪表盘数据（Phase 0 状态、今日词汇、题型统计、近期答题）。
 
     Copy 规范：所有字段为事实数字，无 ability 结论文案。
     """
+    student_id = auth_id if auth_id is not None else student_id
     return {"data": dashboard_service.get_dashboard(student_id)}
```

### frontend/src/services/listeningEvents.ts

```diff
--- a/frontend/src/services/listeningEvents.ts
+++ b/frontend/src/services/listeningEvents.ts
@@ -1,5 +1,6 @@
 // 行为事件采集器: 前端队列 + 定时批量上报 + 页面隐藏时兜底
 // 原则: 只做客观记录; 事件即使丢失也不影响作答本身(作答走 saveAnswer)
+import { currentUser } from './authApi'
 import type { BehaviorEvent } from '../types/listening'
 import { postBehaviorEvents } from './listeningApi'
 
@@ -58,8 +59,9 @@
 
 export const eventCollector = new EventCollector()
 
+/** 登录时使用账号 UUID；否则保留原匿名 ID，登录/登出均不覆盖 localStorage。 */
-/** 生成/读取匿名学生 ID(持久在 localStorage, 服务端数据仍存 SQLite) */
 export function getStudentId(): string {
+  if (currentUser.value?.id) return currentUser.value.id
   const key = 'aq_listening_student_id'
   let id = localStorage.getItem(key)
   if (!id) {
```

### frontend/src/views/listening/ListeningMistakesView.vue

```diff
--- a/frontend/src/views/listening/ListeningMistakesView.vue
+++ b/frontend/src/views/listening/ListeningMistakesView.vue
@@ -123,7 +123,7 @@
 import { fetchMistakes, fetchTagDictionary } from '../../services/listeningApi'
 import { getStudentId } from '../../services/listeningEvents'
 
+const studentId = computed(() => getStudentId())
-const studentId = getStudentId()
 
 const loading = ref(true)
 const errorMessage = ref('')
@@ -165,7 +165,7 @@
   loading.value = true
   errorMessage.value = ''
   try {
+    mistakes.value = await fetchMistakes(studentId.value, {
-    mistakes.value = await fetchMistakes(studentId, {
       mastery: filters.mastery || undefined,
       section: filters.section || undefined,
       tag: filters.tag || undefined,
```

### frontend/src/views/listening/ListeningStrictPacingView.vue

```diff
--- a/frontend/src/views/listening/ListeningStrictPacingView.vue
+++ b/frontend/src/views/listening/ListeningStrictPacingView.vue
@@ -52,7 +52,7 @@
 </template>
 
 <script setup lang="ts">
+import { computed, onMounted, ref } from 'vue'
-import { onMounted, ref } from 'vue'
 import { useRoute, useRouter } from 'vue-router'
 import StrictPacingPlayer, {
   type PacingWindow,
@@ -69,7 +69,7 @@
 const route = useRoute()
 const router = useRouter()
 const examId = route.params.examId as string
+const studentId = computed(() => getStudentId())
-const studentId = getStudentId()
 
 // ── State ─────────────────────────────────────────────────────────────
 type Phase = 'loading' | 'intro' | 'playing' | 'done' | 'error'
@@ -131,7 +131,7 @@
 async function startSession() {
   try {
     // Use exam_mode — pacing distinction tracked via behavior event in player
+    const attempt = await createAttempt(examId, 'exam_mode', studentId.value)
-    const attempt = await createAttempt(examId, 'exam_mode', studentId)
     attemptId.value = attempt.id
     phase.value = 'playing'
   } catch (e: unknown) {
```

### frontend/src/views/listening/ListeningExpressionsView.vue

```diff
--- a/frontend/src/views/listening/ListeningExpressionsView.vue
+++ b/frontend/src/views/listening/ListeningExpressionsView.vue
@@ -77,13 +77,13 @@
 </template>
 
 <script setup lang="ts">
+import { computed, onMounted, ref } from 'vue'
-import { onMounted, ref } from 'vue'
 import { useRouter } from 'vue-router'
 import { fetchExpressions, type ExpressionCard } from '../../services/listeningApi'
 import { getStudentId } from '../../services/listeningEvents'
 
 const router = useRouter()
+const studentId = computed(() => getStudentId())
-const studentId = getStudentId()
 
 const expressions = ref<ExpressionCard[]>([])
 const loading = ref(true)
@@ -93,7 +93,7 @@
   loading.value = true
   errorMessage.value = ''
   try {
+    expressions.value = await fetchExpressions(studentId.value)
-    expressions.value = await fetchExpressions(studentId)
   } catch (error) {
     errorMessage.value =
       error instanceof Error ? error.message : '表达加载失败, 请稍后重试。'
```

### frontend/src/views/listening/ListeningReviewView.vue

```diff
--- a/frontend/src/views/listening/ListeningReviewView.vue
+++ b/frontend/src/views/listening/ListeningReviewView.vue
@@ -186,7 +186,7 @@
 
 const route = useRoute()
 const attemptId = route.params.attemptId as string
+const studentId = computed(() => getStudentId())
-const studentId = getStudentId()
 
 const loading = ref(true)
 const errorMessage = ref('')
@@ -296,7 +296,7 @@
 onMounted(async () => {
   await loadOverview()
   // 复盘页的行为(复听/展开)同样计入该 attempt 的证据链
+  eventCollector.start(attemptId, studentId.value)
-  eventCollector.start(attemptId, studentId)
 })
 
 onBeforeUnmount(() => {
```

### frontend/src/views/listening/StemBankView.vue

```diff
--- a/frontend/src/views/listening/StemBankView.vue
+++ b/frontend/src/views/listening/StemBankView.vue
@@ -131,11 +131,11 @@
 </template>
 
 <script setup lang="ts">
+import { computed, onMounted, ref, watch } from 'vue'
-import { onMounted, ref, watch } from 'vue'
 import OptionPredictionTrainer, { type StemItem } from '../../components/listening/OptionPredictionTrainer.vue'
 import { getStudentId } from '../../services/listeningEvents'
 
+const studentId = computed(() => getStudentId())
-const studentId = getStudentId()
 
 // ── Constants ─────────────────────────────────────────────────────────
 
@@ -201,7 +201,7 @@
 
 async function loadStats() {
   try {
+    const res = await fetch(`/api/listening/stem-bank/stats?student_id=${studentId.value}`)
-    const res = await fetch(`/api/listening/stem-bank/stats?student_id=${studentId}`)
     if (res.ok) stats.value = (await res.json()).data
   } catch { /* non-critical */ }
 }
```

### frontend/src/views/listening/ListeningExamView.vue

```diff
--- a/frontend/src/views/listening/ListeningExamView.vue
+++ b/frontend/src/views/listening/ListeningExamView.vue
@@ -186,7 +186,7 @@
 const route = useRoute()
 const router = useRouter()
 const examId = route.params.examId as string
+const studentId = computed(() => getStudentId())
-const studentId = getStudentId()
 
 const loading = ref(true)
 const errorMessage = ref('')
@@ -249,7 +249,7 @@
 
 async function checkInProgress() {
   for (const m of ['exam_mode', 'practice_mode'] as ExamMode[]) {
+    const found = await findInProgressAttempt(examId, m, studentId.value)
-    const found = await findInProgressAttempt(examId, m, studentId)
     if (found) {
       inProgress.value = found
       return
@@ -259,7 +259,7 @@
 
 function start(selectedMode: ExamMode) {
   mode.value = selectedMode
+  createAttempt(examId, selectedMode, studentId.value)
-  createAttempt(examId, selectedMode, studentId)
     .then((attempt) => {
       attemptId.value = attempt.id
       beginRunning()
@@ -293,7 +293,7 @@
 
 function beginRunning() {
   stage.value = 'running'
+  eventCollector.start(attemptId.value!, studentId.value)
-  eventCollector.start(attemptId.value!, studentId)
   enterQuestion(0)
 }
 
```

### frontend/src/views/listening/ListeningProfileView.vue

```diff
--- a/frontend/src/views/listening/ListeningProfileView.vue
+++ b/frontend/src/views/listening/ListeningProfileView.vue
@@ -309,7 +309,7 @@
 import { getStudentId } from '../../services/listeningEvents'
 
 const router = useRouter()
+const studentId = computed(() => getStudentId())
-const studentId = getStudentId()
 
 const loading = ref(true)
 const errorMessage = ref('')
@@ -428,7 +428,7 @@
 
 onMounted(async () => {
   try {
+    profile.value = await fetchProfile(studentId.value)
-    profile.value = await fetchProfile(studentId)
   } catch (error) {
     errorMessage.value =
       error instanceof Error ? error.message : '画像加载失败'
```

### frontend/src/views/listening/ListeningExamV2View.vue

```diff
--- a/frontend/src/views/listening/ListeningExamV2View.vue
+++ b/frontend/src/views/listening/ListeningExamV2View.vue
@@ -185,7 +185,7 @@
 const route = useRoute()
 const router = useRouter()
 const examId = route.params.examId as string
+const studentId = computed(() => getStudentId())
-const studentId = getStudentId()
 
 const loading = ref(true)
 const errorMessage = ref('')
@@ -249,7 +249,7 @@
 
 async function checkInProgress() {
   for (const m of ['exam_mode', 'practice_mode'] as ExamMode[]) {
+    const found = await findInProgressAttempt(examId, m, studentId.value)
-    const found = await findInProgressAttempt(examId, m, studentId)
     if (found) {
       inProgress.value = found
       return
@@ -259,7 +259,7 @@
 
 function start(selectedMode: ExamMode) {
   mode.value = selectedMode
+  createAttempt(examId, selectedMode, studentId.value)
-  createAttempt(examId, selectedMode, studentId)
     .then((attempt) => {
       attemptId.value = attempt.id
       beginRunning(restoreUnitIndex())
@@ -300,7 +300,7 @@
 
 function beginRunning(unitIndex: number) {
   stage.value = 'running'
+  eventCollector.start(attemptId.value!, studentId.value)
-  eventCollector.start(attemptId.value!, studentId)
   enterUnit(unitIndex)
 }
 
```

### frontend/src/views/listening/ExpressionTrainView.vue

```diff
--- a/frontend/src/views/listening/ExpressionTrainView.vue
+++ b/frontend/src/views/listening/ExpressionTrainView.vue
@@ -163,7 +163,7 @@
 import { getStudentId } from '../../services/listeningEvents'
 
 const route = useRoute()
+const studentId = computed(() => getStudentId())
-const studentId = getStudentId()
 
 const detail = ref<ExpressionDetail | null>(null)
 const loading = ref(true)
@@ -285,7 +285,7 @@
   try {
     const durationMs = firstPlayAt.value ? Date.now() - firstPlayAt.value : 0
     result.value = await submitExpressionScenario(currentScenario.value.scenario_id, {
+      student_id: studentId.value,
-      student_id: studentId,
       answers: { ...answers.value },
       listen_count_before_submit: listenCount.value,
       reveal_used: revealUsed.value,
@@ -322,7 +322,7 @@
   errorMessage.value = ''
   try {
     const id = String(route.params.expressionId)
+    detail.value = await fetchExpressionDetail(id, studentId.value)
-    detail.value = await fetchExpressionDetail(id, studentId)
     await switchScenario(0)
   } catch (error) {
     errorMessage.value =
```

### frontend/src/views/listening/ListeningPracticeV2View.vue

```diff
--- a/frontend/src/views/listening/ListeningPracticeV2View.vue
+++ b/frontend/src/views/listening/ListeningPracticeV2View.vue
@@ -207,7 +207,7 @@
 
 const route = useRoute()
 const materialId = route.params.materialId as string
+const studentId = computed(() => getStudentId())
-const studentId = getStudentId()
 
 const FOCUS_TYPES = ['人物', '动作行为', '原因', '态度', '时间地点']
 
@@ -247,7 +247,7 @@
     ...e,
     client_at: new Date().toISOString()
   }))
+  await postV2PracticeEvents(sessionId.value, stamped, studentId.value, keepalive)
-  await postV2PracticeEvents(sessionId.value, stamped, studentId, keepalive)
 }
 
 async function enterPreview() {
@@ -322,11 +322,11 @@
 onMounted(async () => {
   try {
     bundle.value = await fetchV2PracticeBundle(materialId)
+    const found = await findV2PracticeSession(materialId, studentId.value)
-    const found = await findV2PracticeSession(materialId, studentId)
     if (found) {
       sessionId.value = found.session_id
     } else {
+      const created = await createV2PracticeSession(materialId, studentId.value)
-      const created = await createV2PracticeSession(materialId, studentId)
       sessionId.value = created.session_id
     }
     await refreshState()
```

### frontend/src/views/listening/AuralLexiconView.vue

```diff
--- a/frontend/src/views/listening/AuralLexiconView.vue
+++ b/frontend/src/views/listening/AuralLexiconView.vue
@@ -129,7 +129,7 @@
 // 旧版用 'aq_student_id'，与事件采集/V2.2/StemBank 的 student_id 不一致，已修正。
 import { getStudentId } from '../../services/listeningEvents'
 
+const studentId = computed(() => getStudentId())
-const studentId = getStudentId()
 
 // ── Stage 状态机 ──────────────────────────────────────────────────────
 type Stage = 'loading' | 'error' | 'entry_test' | 'entry_result' | 'session' | 'forced_exit'
@@ -209,7 +209,7 @@
 async function init() {
   stage.value = 'loading'
   try {
+    const status = await fetchPhase0Status(studentId.value)
-    const status = await fetchPhase0Status(studentId)
     phase0Status.value = status
 
     if (status.status === 'not_started') {
@@ -228,7 +228,7 @@
 
 // ── 入口测试 ──────────────────────────────────────────────────────────
 async function loadEntryTest() {
+  const data = await fetchEntryTestItems(studentId.value)
-  const data = await fetchEntryTestItems(studentId)
   entryItems.value   = data.items
   entryIdx.value     = 0
   entryResults.value = []
@@ -257,9 +257,9 @@
   clearInterval(entryTimerInterval.value!)
   if (entryResults.value.length === 0) { await loadSession(); return }
   try {
+    const res = await submitEntryTestResults(studentId.value, entryResults.value)
-    const res = await submitEntryTestResults(studentId, entryResults.value)
     entryScore.value  = res.entry_score
+    phase0Status.value = await fetchPhase0Status(studentId.value)
-    phase0Status.value = await fetchPhase0Status(studentId)
     stage.value = 'entry_result'
   } catch {
     await loadSession()   // 提交失败降级直接进词汇
@@ -268,7 +268,7 @@
 
 // ── 每日会话 ──────────────────────────────────────────────────────────
 async function loadSession() {
+  const data = await fetchLexSession(studentId.value)
-  const data = await fetchLexSession(studentId)
   const all  = [...data.due_review, ...data.new_items]
   sessionItems.value   = shuffle(all)
   sessionIdx.value     = 0
@@ -298,7 +298,7 @@
   if (payload.is_correct) sessionCorrect.value++
 
   // 上报（fire-and-forget，不阻塞 UI）
+  recordLexAttempt(studentId.value, item.item_id, currentTaskType.value, payload.is_correct)
-  recordLexAttempt(studentId, item.item_id, currentTaskType.value, payload.is_correct)
     .catch(() => {/* 静默失败 */})
 
   sessionIdx.value++
```

### frontend/src/views/listening/ListeningDashboardView.vue

```diff
--- a/frontend/src/views/listening/ListeningDashboardView.vue
+++ b/frontend/src/views/listening/ListeningDashboardView.vue
@@ -206,7 +206,7 @@
 import { getStudentId } from '../../services/listeningEvents'
 import StudyIcon from '../../components/listening/StudyIcon.vue'
 
+const studentId = computed(() => getStudentId())
-const studentId = getStudentId()
 
 // ── Types ─────────────────────────────────────────────────────────────
 
@@ -257,7 +257,7 @@
   loading.value = true
   err.value = ''
   try {
+    const res = await fetch(`/api/listening/dashboard?student_id=${studentId.value}`)
-    const res = await fetch(`/api/listening/dashboard?student_id=${studentId}`)
     if (!res.ok) throw new Error(`HTTP ${res.status}`)
     data.value = (await res.json()).data
   } catch (e: unknown) {
```

### backend/tests/test_student_auth.py（新增，全文）

```python
"""Listening identity integration: real JWT/cookie checks with isolated account/student stores."""
import ast
from pathlib import Path
import inspect
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from auth.router import router as auth_router
from listening import router as api
from listening.repository import StudentRepository


@pytest.fixture(scope="module")
def app():
    application = FastAPI()
    application.include_router(auth_router)
    application.include_router(api.router)
    return application


@pytest.fixture
def setup(tmp_path, monkeypatch, app):
    monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "auth.db"))
    monkeypatch.setenv("AUTH_JWT_SECRET", "isolated-student-auth-test-secret-32-bytes")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "true")
    repo = StudentRepository(tmp_path / "listening.db")
    monkeypatch.setattr(api, "student_repo", repo)
    with TestClient(app, base_url="https://testserver") as client:
        yield client, repo, app
    app.dependency_overrides.clear()


def sign_in(client):
    data = {"email": "identity@example.com", "password": "test-password-123"}
    headers = {"X-Auth-Request": "1"}
    created = client.post("/api/auth/register", json=data, headers=headers)
    assert created.status_code == 201
    assert client.post("/api/auth/login", json=data, headers=headers).status_code == 200
    return created.json()["id"]


def test_anonymous_and_authenticated_persistence(setup, monkeypatch):
    client, repo, app = setup
    # Only availability is stubbed; attempt creation and JWT verification are real.
    monkeypatch.setattr(api.exam_repo, "get", lambda _: object())
    monkeypatch.setattr(api.v2_exam_service, "is_v2_exam", lambda _: False)
    payload = {"student_id": "alice", "exam_id": "identity-fixture", "mode": "exam_mode"}
    anonymous = client.post("/api/listening/attempts", json=payload).json()["data"]
    assert repo.get_attempt(anonymous["id"])["student_id"] == "alice"
    user_id = sign_in(client)
    owned = client.post("/api/listening/attempts", json=payload).json()["data"]
    assert repo.get_attempt(owned["id"])["student_id"] == user_id
    # Simulated second device: separate cookie jar, same account login.
    with TestClient(app, base_url="https://testserver") as device2:
        assert device2.post("/api/auth/login", json={"email": "identity@example.com", "password": "test-password-123"},
                            headers={"X-Auth-Request": "1"}).status_code == 200
        found = device2.get("/api/listening/attempts/in-progress", params={
            "student_id": "some-other-device", "exam_id": "identity-fixture", "mode": "exam_mode"})
        assert found.json()["data"]["attempt"]["id"] == owned["id"]
    assert client.post("/api/auth/logout", headers={"X-Auth-Request": "1"}).status_code == 204
    assert client.post("/api/listening/attempts", json=payload).json()["data"]["student_id"] == "alice"


@pytest.mark.parametrize("failure", [None, "broken-token", "backend-error"])
def test_optional_auth_fallback(setup, monkeypatch, failure):
    client, _, _ = setup
    if failure:
        client.cookies.set("token", failure)
    if failure == "backend-error":
        monkeypatch.setattr(api, "_auth_get_user", Mock(side_effect=RuntimeError("unavailable")))
    spy = Mock(return_value={})
    monkeypatch.setattr(api.dashboard_service, "get_dashboard", spy)
    assert client.get("/api/listening/dashboard?student_id=alice").status_code == 200
    spy.assert_called_once_with("alice")


QUERY_CASES = [
    ("/exams", "service", "exam_summaries", [], 0),
    ("/attempts/in-progress?exam_id=x", "student_repo", "find_in_progress_attempt", None, 0),
    ("/mistakes", "service", "list_mistakes", [], 0),
    ("/profile", "profile_service", "build_profile", {}, 0),
    ("/profile/causes", "profile_service", "build_cause_profile", {}, 0),
    ("/profile/skills", "profile_service", "build_cause_profile", [], 0),
    ("/expressions", "expression_service", "list_expressions", [], 0),
    ("/expressions/x", "expression_service", "expression_detail", {"id": "x"}, 1),
    ("/v2/practice/sessions/find?material_id=x", "v2_practice_service", "find_session", None, 0),
    ("/lexicon/session", "aural_lexicon_service", "get_daily_session", {}, 0),
    ("/lexicon/phase0/status", "aural_lexicon_service", "get_phase0_status", {}, 0),
    ("/lexicon/phase0/entry-test", "aural_lexicon_service", "start_entry_test", {}, 0),
    ("/stem-bank/stats", "stem_bank_service", "get_student_stats", {}, 0),
    ("/dashboard", "dashboard_service", "get_dashboard", {}, 0),
]


@pytest.mark.parametrize("case", QUERY_CASES, ids=[c[0] for c in QUERY_CASES])
@pytest.mark.parametrize("authenticated", [False, True])
def test_all_query_endpoints(setup, monkeypatch, case, authenticated):
    client, _, app = setup
    app.dependency_overrides[api._optional_student_id] = lambda: "USER-UUID-123" if authenticated else None
    monkeypatch.setattr(api.v2_exam_service, "gate_allows", lambda: True)
    monkeypatch.setattr(api.profile_service, "build_skill_profile", lambda _: {})
    path, module, method, result, index = case
    spy = Mock(return_value=result)
    monkeypatch.setattr(getattr(api, module), method, spy)
    response = client.get("/api/listening" + path + ("&" if "?" in path else "?") + "student_id=alice")
    assert response.status_code == 200, response.text
    assert spy.call_args.args[index] == ("USER-UUID-123" if authenticated else "alice")


BODY_CASES = [
    ("/attempts", {"exam_id": "x"}, "student_repo", "create_attempt", {}, 0),
    ("/attempts/a/events", {"events": []}, "student_repo", "add_behavior_events", 0, 0),
    ("/diagnoses", {"attempt_id": "a", "question_id": "q"}, "student_repo", "upsert_diagnosis", {}, 0),
    ("/training-results", {"question_id": "q", "training_type": "dictation"}, "student_repo", "add_training_result", {}, 0),
    ("/expressions/scenarios/x/submit", {}, "expression_service", "submit_scenario", {}, 1),
    ("/v2/practice/sessions", {"material_id": "x"}, "v2_practice_service", "create_session", {"id": "s", "stage": "first_pass"}, 0),
    ("/v2/practice/sessions/s/events", {"events": []}, "v2_practice_service", "record_events", {}, 1),
    ("/lexicon/phase0/entry-test/complete", {"results": []}, "aural_lexicon_service", "complete_entry_test", {}, 0),
    ("/lexicon/phase0/complete", {"retest_score": 1}, "aural_lexicon_service", "complete_phase0", {}, 0),
    ("/lexicon/attempt", {"item_id": "x", "task_type": "hear_identify", "is_correct": True}, "aural_lexicon_service", "record_attempt", {}, "student_id"),
    ("/lexicon/harvest", {"item_id": "x", "gate_type": "exam_attempt", "gate_id": "a"}, "aural_lexicon_service", "harvest_word", {}, "student_id"),
    ("/stem-bank/predict", {"question_no": 1}, "stem_bank_service", "record_prediction", {}, "student_id"),
]


@pytest.mark.parametrize("case", BODY_CASES, ids=[c[0] for c in BODY_CASES])
@pytest.mark.parametrize("authenticated", [False, True])
def test_all_body_endpoints(setup, monkeypatch, case, authenticated):
    client, _, app = setup
    app.dependency_overrides[api._optional_student_id] = lambda: "USER-UUID-123" if authenticated else None
    monkeypatch.setattr(api.v2_exam_service, "gate_allows", lambda: True)
    monkeypatch.setattr(api.v2_exam_service, "is_v2_exam", lambda _: False)
    monkeypatch.setattr(api.exam_repo, "get", lambda _: object())
    monkeypatch.setattr(api.student_repo, "get_attempt", lambda _: {"exam_id": "x"})
    path, payload, module, method, result, index = case
    spy = Mock(return_value=result)
    monkeypatch.setattr(getattr(api, module), method, spy)
    response = client.post("/api/listening" + path, json={**payload, "student_id": "alice"})
    assert response.status_code == 200, response.text
    args = spy.call_args.kwargs if isinstance(index, str) else spy.call_args.args
    assert args[index] == ("USER-UUID-123" if authenticated else "alice")


def test_no_student_endpoint_missing_dependency():
    tree = ast.parse(Path(api.__file__).read_text(encoding="utf-8"))
    found = 0
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or not node.decorator_list:
            continue
        has_id = any(a.arg == "student_id" for a in node.args.args) or any(
            isinstance(n, ast.Attribute) and n.attr == "student_id" for n in ast.walk(node))
        if has_id:
            found += 1
            assert any(a.arg == "auth_id" for a in node.args.args), node.name
            # Legacy tests call route functions directly, bypassing dependency injection.
            assert inspect.signature(getattr(api, node.name)).parameters["auth_id"].default is None
    assert found == 26


def test_release_gate_remains_closed(setup, monkeypatch):
    client, _, _ = setup
    monkeypatch.delenv("ALLOW_UNRELEASED_LISTENING_V2", raising=False)
    assert api.v2_exam_service.student_release_allowed() is False
    sign_in(client)
    assert client.post("/api/listening/v2/practice/sessions", json={"student_id": "alice", "material_id": "x"}).status_code == 403
```

### frontend/tests/studentIdentity.test.mjs（新增，全文）

```javascript
// Identity unit tests: compile the actual TypeScript in memory; never touch browser storage.
import { readFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import vm from 'node:vm'
import test from 'node:test'
import assert from 'node:assert/strict'
import ts from 'typescript'
import { computed, readonly, ref } from 'vue'

const require = createRequire(import.meta.url)
const source = readFileSync(new URL('../src/services/listeningEvents.ts', import.meta.url), 'utf8')
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText

function fixture(stored) {
  const account = ref(null)
  const values = new Map(stored ? [['aq_listening_student_id', stored]] : [])
  let writes = 0
  const context = {
    exports: {},
    require(name) {
      if (name === './authApi') return { currentUser: readonly(account) }
      if (name === './listeningApi') return { postBehaviorEvents: () => Promise.resolve() }
      return require(name)
    },
    crypto: { randomUUID: () => '00000000-1111-4222-8333-444444444444' },
    localStorage: {
      getItem: key => values.get(key) ?? null,
      setItem: (key, value) => { writes++; values.set(key, value) },
    },
  }
  vm.runInNewContext(compiled, context)
  return { account, values, getStudentId: context.exports.getStudentId, writes: () => writes }
}

test('existing anonymous ID survives login, account switching and logout', () => {
  const f = fixture('stu_existing')
  const id = computed(() => f.getStudentId())
  assert.equal(id.value, 'stu_existing')
  f.account.value = { id: 'account-a' }
  assert.equal(id.value, 'account-a')
  f.account.value = { id: 'account-b' }
  assert.equal(id.value, 'account-b')
  f.account.value = null
  assert.equal(id.value, 'stu_existing')
  assert.equal(f.writes(), 0)
})

test('new anonymous visitor uses the unchanged persistent ID format', () => {
  const f = fixture()
  assert.equal(f.getStudentId(), 'stu_000000001111')
  assert.equal(f.getStudentId(), 'stu_000000001111')
  assert.equal(f.writes(), 1)
})

test('authenticated visitor does not create or overwrite an anonymous ID', () => {
  const f = fixture()
  f.account.value = { id: 'account-a' }
  assert.equal(f.getStudentId(), 'account-a')
  assert.equal(f.values.size, 0)
  assert.equal(f.writes(), 0)
})
```

### backend/tests/run_student_auth_regression.py（新增，全文）

```python
"""Run existing tests against disposable SQLite/JSON copies; production data is read-only."""
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

with tempfile.TemporaryDirectory(prefix="identity-tests-", ignore_cleanup_errors=True) as directory:
    isolated = Path(directory)
    os.environ["LISTENING_DB_PATH"] = str(isolated / "listening.db")
    os.environ["AUTH_DB_PATH"] = str(isolated / "auth.db")
    # Existing repository switch: only disposable test DBs sacrifice fsync durability.
    os.environ["LISTENING_UNSAFE_FAST_DB"] = "1"
    from listening import expression_service as expressions
    target = isolated / "expressions"
    shutil.copytree(expressions.EXPRESSIONS_DIR, target)
    expressions.EXPRESSIONS_DIR = target
    expressions.EXPRESSIONS_PATH = target / "expressions.json"
    expressions.SCENARIOS_PATH = target / "scenarios.json"
    expressions.AUDIO_INDEX_PATH = target / "audio_index.json"
    expressions.expression_repo.reload()
    # Legacy TTS helper uses its own constants; also keep its output off real data.
    try:
        from listening.tools import generate_scenario_audio as tts
        tts.DATA_DIR = isolated
        tts.SCENARIOS_PATH = expressions.SCENARIOS_PATH
        tts.AUDIO_INDEX_PATH = expressions.AUDIO_INDEX_PATH
        tts.AUDIO_DIR = target / "audio"
    except ModuleNotFoundError:
        pass

    def deny_real_data_writes(event, args):
        if event == "open":
            path, mode, flags = args
            writing = flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)
        elif event in {"os.remove", "os.rmdir", "os.mkdir", "os.rename"}:
            path, writing = args[0], True
        else:
            return
        if writing and isinstance(path, (str, bytes)):
            resolved = Path(os.fsdecode(path)).resolve()
            if resolved.is_relative_to(ROOT / "backend" / "listening" / "data"):
                raise RuntimeError(f"Test attempted to modify protected real data: {resolved}")
    sys.addaudithook(deny_real_data_writes)
    import pytest
    os.chdir(ROOT / "backend")
    raise SystemExit(pytest.main([*(sys.argv[1:] or ["tests", "-x"]), "-p", "no:cacheprovider",
                                 "--basetemp", str(isolated / "pytest")]))
```

## 3. 验证结果

安全复现命令（在项目根目录，使用已安装现有依赖的 Python 环境）：

```bash
python backend/tests/run_student_auth_regression.py tests -x -q
cd frontend
node --test tests/studentIdentity.test.mjs
npm run build
```

不要直接运行会备份后重写真实 JSON 的旧测试入口；附件中的 backend/listening/tests/ 实际不存在，实际目录为 backend/tests/。

最终回归：**237 passed in 16.28s**，包含 179 项原有测试和 58 项新增身份测试，无跳过。
前端身份单测 **3/3 通过**；`npm run build`（vue-tsc + Vite）通过。
旧测试直接调用路由函数时的 Depends 默认值兼容问题已通过 Annotated/default None 修复，并包含在最终通过的完整回归中。
测试执行使用项目已有的 `LISTENING_UNSAFE_FAST_DB=1`，仅针对临时库关闭 fsync，生产配置不变。
全部写入限定在临时 SQLite/表达数据副本；真实 listening.db SHA-256 前后均为
`AEDEB601197E859E3ECA5E41DCB809288352FCEECDE6E4F5648F7B6B19628DC0`。
`student_release_allowed` 实际读取仍为 false；没有部署线上。

## 4. 手工 curl 验证（Bash）

以下使用本地后端；本地 HTTP 测试需按 auth 文档配置 AUTH_COOKIE_SECURE=false 和 AUTH_JWT_SECRET。生产请换成实际 HTTPS 域名且保留 Secure=true。使用已注册的专用测试账号；这些命令会创建测试作答记录，不要在真实学生账号上随意运行。

```bash
BASE_URL='http://127.0.0.1:8000'
# ① 匿名请求：返回 data.student_id 应为 alice
curl -sS "$BASE_URL/api/listening/attempts" \
  -H 'Content-Type: application/json' \
  -d '{"student_id":"alice","exam_id":"cet6_202606_set2","mode":"exam_mode"}'

# 先登录：填写已注册的测试账号，cookie 写入本地文件（请妥善保管）
curl -sS -c auth-test.cookies "$BASE_URL/api/auth/login" \
  -H 'Content-Type: application/json' -H 'X-Auth-Request: 1' \
  -d '{"email":"你的测试邮箱","password":"你的测试密码"}'

# ② 登录态仍故意传 alice：返回 data.student_id 应为登录用户 UUID，而非 alice
curl -sS -b auth-test.cookies "$BASE_URL/api/listening/attempts" \
  -H 'Content-Type: application/json' \
  -d '{"student_id":"alice","exam_id":"cet6_202606_set2","mode":"exam_mode"}'

# 对照用户 id，确认与上一步 data.student_id 相同
curl -sS -b auth-test.cookies "$BASE_URL/api/auth/me"
```

## 5. 保持不变与安全边界

- 不修改 auth/、v2_practice_service.py、cp_*.py、data/*.json 或真实 listening.db；不新增外部依赖，不改 listeningApi.ts 默认参数。
- student_release_allowed 保持 false；测试内模拟门控放行不等于发布，也不写 baseline。
- 账号 UUID 会用于登录后新记录及查询，故跨设备可续接这些账号记录；旧匿名记录仍归原 localStorage ID，不自动迁移。
- 按附件要求，无效/过期 token 和认证内部异常都回退匿名。不能据此宣称整个系统完全防冒名：未登录客户端仍可自报 ID。
- 现有仅依赖 attempt_id/session_id 的读写接口（如保存答案、提交、复盘、CP round1/round2）未在本次新增所有权校验；它们不是附件所述接收 student_id 的端点。完整权限隔离需另行设计。
- computed 只确保后续取值更新，不自动清空已经加载的页面数据、迁移进行中的匿名 attempt 或取消旧事件队列。
