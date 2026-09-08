<template>
  <div class="exam-page">
    <div class="exam-container">
      <div class="topbar">
        <button class="back-button" @click="goBack">← 返回听力首页</button>
        <span v-if="stage === 'running'" class="mode-badge">
          {{ mode === 'exam_mode' ? '考试模式' : '练习模式' }}
        </span>
      </div>

      <div v-if="loading" class="state-card">
        <p>正在加载试卷……</p>
      </div>

      <div v-else-if="errorMessage" class="state-card error">
        <p>{{ errorMessage }}</p>
        <button class="retry-button" @click="loadPaper">重试</button>
      </div>

      <!-- 入口 -->
      <template v-else-if="stage === 'intro' && paper">
        <section class="hero">
          <p class="eyebrow">CET-6 Listening</p>
          <h1>{{ examTitle }}</h1>
          <p class="description">
            {{ totalQuestions }} 题 · {{ paper.units.length }} 个听力材料 ·
            题目由音频朗读，卷面只有选项
          </p>
        </section>

        <section v-if="inProgress" class="resume-card">
          <p>
            检测到你有一份未提交的作答记录（{{ inProgress.answers.length }} 题已作答）。
          </p>
          <div class="resume-actions">
            <button class="primary-btn" @click="resumeAttempt">继续上次作答</button>
            <button class="ghost-btn" @click="inProgress = null">重新开始</button>
          </div>
        </section>

        <section class="mode-grid">
          <div class="mode-card" @click="start('exam_mode')">
            <h2>考试模式</h2>
            <p>按真实考试流程：听完整套音频，完成全部题目后统一提交。</p>
            <span class="go">开始考试 →</span>
          </div>
          <div class="mode-card" @click="start('practice_mode')">
            <h2>练习模式</h2>
            <p>流程相同，作答行为同样被完整记录，用于日常练习。</p>
            <span class="go">开始练习 →</span>
          </div>
        </section>
      </template>

      <!-- 作答中 -->
      <template v-else-if="stage === 'running' && paper">
        <AudioPlayer
          :src="paper.audio.url"
          :mode="mode"
          controls="full"
          @audio-event="onAudioEvent"
        />

        <div class="unit-nav">
          <button
            class="nav-btn"
            :disabled="currentUnitIndex === 0"
            @click="gotoUnit(currentUnitIndex - 1)"
          >
            ← 上一组
          </button>
          <div class="unit-indicator">
            <span>Unit {{ currentUnitIndex + 1 }} / {{ paper.units.length }}</span>
            <span v-if="currentUnit?.question_range" class="unit-range">
              Questions {{ currentUnit.question_range[0] }}–{{ currentUnit.question_range[1] }}
            </span>
          </div>
          <button
            class="nav-btn"
            :disabled="currentUnitIndex >= paper.units.length - 1"
            @click="gotoUnit(currentUnitIndex + 1)"
          >
            下一组 →
          </button>
        </div>

        <UnitQuestionGroup
          v-if="currentUnit"
          :key="currentUnit.unit_id"
          :unit="currentUnit"
          :answers="selectedAnswers"
          @select="onSelect"
        />

        <div class="submit-row">
          <p v-if="unansweredCount > 0" class="submit-hint">
            还有 {{ unansweredCount }} 题未作答
          </p>
          <button class="primary-btn" :disabled="submitting" @click="showSubmitConfirm = true">
            {{ submitting ? '正在提交…' : '提交试卷' }}
          </button>
        </div>

        <!-- 提交确认: 只告知未作答数量, 不提示任何对错信息 -->
        <div
          v-if="showSubmitConfirm"
          class="modal-mask"
          @click.self="showSubmitConfirm = false"
        >
          <div class="modal-card">
            <p v-if="unansweredCount > 0" class="modal-text">
              还有 {{ unansweredCount }} 道题未作答。
            </p>
            <p v-else class="modal-text">确定提交试卷吗？</p>
            <div class="modal-actions">
              <button class="ghost-btn" @click="showSubmitConfirm = false">
                继续作答
              </button>
              <button class="primary-btn" @click="doSubmit">
                仍然提交
              </button>
            </div>
          </div>
        </div>
      </template>

      <!-- 提交结果(仅成绩摘要; 逐题复盘属于后续阶段) -->
      <section v-else-if="stage === 'submitted' && submitResult" class="state-card">
        <p class="eyebrow">Submitted</p>
        <h2 class="result-score">
          {{ submitResult.score }} / {{ submitResult.question_count }}
        </h2>
        <p class="result-note">作答已保存。逐题复盘将在后续阶段开放。</p>
        <div class="resume-actions">
          <button class="primary-btn" @click="$router.push('/listening')">
            返回听力首页
          </button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * V2.1 Exam Mode(audio_only)。
 *
 * 信息条件(与真实 CET 听力一致):
 *   学生只能看到题号 + A/B/C/D 英文选项; 题干由音频朗读。
 *   页面不存在"当前音频对应哪道题"的任何提示, 播放器与题号无映射。
 *
 * 交互模型:
 *   核心单位是 Unit(一个材料 + 该材料全部 3–4 题同时可见)。
 *   音频为整套连续播放, 允许 play/pause/seek/replay(现实容错, 只记录事实)。
 *   全部 7 个 Unit 完成后统一提交; 提交前不提示对错。
 */
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AudioPlayer from '../../components/listening/AudioPlayer.vue'
import UnitQuestionGroup from '../../components/listening/UnitQuestionGroup.vue'
import {
  createAttempt,
  fetchV2Paper,
  findInProgressAttempt,
  saveAnswer,
  submitAttempt
} from '../../services/listeningApi'
import { eventCollector, getStudentId } from '../../services/listeningEvents'
import type {
  ExamMode,
  InProgressAttempt,
  SubmitResult,
  V2Paper,
  V2PaperUnit
} from '../../types/listening'

interface AnswerState {
  firstAnswer: string | null
  firstAnswerAt: string | null
  finalAnswer: string | null
  lastAnswerAt: string | null
  changeCount: number
}

const route = useRoute()
const router = useRouter()
const examId = route.params.examId as string
const studentId = computed(() => getStudentId())

const loading = ref(true)
const errorMessage = ref('')
const stage = ref<'intro' | 'running' | 'submitted'>('intro')
const paper = ref<V2Paper | null>(null)
const mode = ref<ExamMode>('exam_mode')
const attemptId = ref<string | null>(null)
const inProgress = ref<InProgressAttempt | null>(null)
const submitting = ref(false)
const submitResult = ref<SubmitResult | null>(null)
const showSubmitConfirm = ref(false)

const currentUnitIndex = ref(0)
const answers = reactive<Record<string, AnswerState>>({})

const examTitles: Record<string, string> = {
  cet6_202606_set1_v2: '2026 年 6 月大学英语六级真题(第 1 套)',
  cet6_202606_set2_v2: '2026 年 6 月大学英语六级真题(第 2 套)'
}
const examTitle = computed(() => examTitles[examId] || 'CET Listening')

const currentUnit = computed<V2PaperUnit | null>(
  () => paper.value?.units[currentUnitIndex.value] || null
)
const totalQuestions = computed(
  () => paper.value?.units.reduce((n, u) => n + u.questions.length, 0) ?? 0
)
const selectedAnswers = computed<Record<string, string | null>>(() => {
  const out: Record<string, string | null> = {}
  for (const [qid, st] of Object.entries(answers)) out[qid] = st.finalAnswer
  return out
})
const answeredCount = computed(
  () => Object.values(answers).filter((a) => a.finalAnswer).length
)
const unansweredCount = computed(() => totalQuestions.value - answeredCount.value)

let unitEnteredAt = 0

function nowIso(): string {
  return new Date().toISOString()
}

function unitStorageKey(): string {
  return `v2_exam_unit_${attemptId.value}`
}

async function loadPaper() {
  loading.value = true
  errorMessage.value = ''
  try {
    paper.value = await fetchV2Paper(examId)
    await checkInProgress()
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : '试卷加载失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

async function checkInProgress() {
  for (const m of ['exam_mode', 'practice_mode'] as ExamMode[]) {
    const found = await findInProgressAttempt(examId, m, studentId.value)
    if (found) {
      inProgress.value = found
      return
    }
  }
}

function start(selectedMode: ExamMode) {
  mode.value = selectedMode
  createAttempt(examId, selectedMode, studentId.value)
    .then((attempt) => {
      attemptId.value = attempt.id
      beginRunning(restoreUnitIndex())
    })
    .catch((error) => {
      errorMessage.value =
        error instanceof Error ? error.message : '无法创建作答记录'
    })
}

function resumeAttempt() {
  if (!inProgress.value) return
  const { attempt, answers: saved } = inProgress.value
  mode.value = attempt.mode as ExamMode
  attemptId.value = attempt.id
  for (const a of saved) {
    if (a.final_answer) {
      answers[a.question_id] = {
        firstAnswer: a.first_answer,
        firstAnswerAt: a.first_answer_at,
        finalAnswer: a.final_answer,
        lastAnswerAt: a.last_answer_at,
        changeCount: a.change_count
      }
    }
  }
  inProgress.value = null
  beginRunning(restoreUnitIndex())
}

/** 刷新/重进后回到上次停留的 Unit(纯 UI 状态, 不入行为数据) */
function restoreUnitIndex(): number {
  const raw = localStorage.getItem(unitStorageKey())
  const idx = raw ? Number(raw) : 0
  const max = (paper.value?.units.length ?? 1) - 1
  return Number.isFinite(idx) ? Math.min(Math.max(idx, 0), max) : 0
}

function beginRunning(unitIndex: number) {
  stage.value = 'running'
  eventCollector.start(attemptId.value!, studentId.value)
  enterUnit(unitIndex)
}

function enterUnit(index: number) {
  currentUnitIndex.value = index
  unitEnteredAt = Date.now()
  localStorage.setItem(unitStorageKey(), String(index))
  const u = currentUnit.value
  if (u) {
    eventCollector.track({
      event_type: 'unit_enter',
      payload: { unit_id: u.unit_id }
    })
  }
}

function leaveCurrentUnit() {
  const u = currentUnit.value
  if (!u || !unitEnteredAt) return
  eventCollector.track({
    event_type: 'unit_leave',
    payload: { unit_id: u.unit_id, dwell_ms: Date.now() - unitEnteredAt }
  })
  unitEnteredAt = 0
}

function gotoUnit(index: number) {
  if (index === currentUnitIndex.value) return
  leaveCurrentUnit()
  enterUnit(index)
}

function onSelect(questionId: string, _number: number, label: string) {
  const st = (answers[questionId] ||= {
    firstAnswer: null,
    firstAnswerAt: null,
    finalAnswer: null,
    lastAnswerAt: null,
    changeCount: 0
  })
  if (!st.firstAnswer) {
    st.firstAnswer = label
    st.firstAnswerAt = nowIso()
    eventCollector.track({
      event_type: 'answer_select',
      question_id: questionId,
      payload: { value: label }
    })
  } else if (st.finalAnswer !== label) {
    st.changeCount += 1
    eventCollector.track({
      event_type: 'answer_change',
      question_id: questionId,
      payload: { from: st.finalAnswer, to: label, change_count: st.changeCount }
    })
  } else {
    return
  }
  st.finalAnswer = label
  st.lastAnswerAt = nowIso()
  persistAnswer(questionId)
}

function persistAnswer(questionId: string) {
  const st = answers[questionId]
  if (!attemptId.value || !st) return
  saveAnswer(attemptId.value, questionId, {
    first_answer: st.firstAnswer,
    final_answer: st.finalAnswer,
    first_answer_at: st.firstAnswerAt,
    last_answer_at: st.lastAnswerAt,
    change_count: st.changeCount,
    dwell_ms: 0 // Unit 组视图下不再按单题计时; 停留时间见 unit_enter/leave 事件
  }).catch((error) => console.warn('答案保存失败:', error))
}

function onAudioEvent(
  eventType: 'audio_play' | 'audio_pause' | 'audio_seek' | 'audio_replay' | 'audio_ended',
  payload: Record<string, unknown>
) {
  // 音频事件只携带当前展示的 Unit 上下文(纯事实, 不代表"当前题")
  eventCollector.track({
    event_type: eventType,
    payload: { ...payload, viewing_unit_id: currentUnit.value?.unit_id ?? null }
  })
}

async function doSubmit() {
  if (!attemptId.value || submitting.value) return
  showSubmitConfirm.value = false
  submitting.value = true
  try {
    leaveCurrentUnit()
    await Promise.all(
      Object.keys(answers)
        .filter((qid) => answers[qid].finalAnswer)
        .map((qid) =>
          saveAnswer(attemptId.value!, qid, {
            first_answer: answers[qid].firstAnswer,
            final_answer: answers[qid].finalAnswer,
            first_answer_at: answers[qid].firstAnswerAt,
            last_answer_at: answers[qid].lastAnswerAt,
            change_count: answers[qid].changeCount,
            dwell_ms: 0
          })
        )
    )
    eventCollector.track({ event_type: 'submit', payload: {} })
    eventCollector.flush()
    submitResult.value = await submitAttempt(attemptId.value)
    stage.value = 'submitted'
    eventCollector.stop()
    localStorage.removeItem(unitStorageKey())
  } catch (error) {
    window.alert(error instanceof Error ? error.message : '提交失败，请稍后重试。')
  } finally {
    submitting.value = false
  }
}

function goBack() {
  if (stage.value === 'running') {
    if (!window.confirm('作答进度已自动保存，确定返回首页吗？')) return
    leaveCurrentUnit()
    eventCollector.flush(true)
    eventCollector.stop()
  }
  router.push('/listening')
}

onMounted(loadPaper)

onBeforeUnmount(() => {
  if (stage.value === 'running') {
    leaveCurrentUnit()
    eventCollector.flush(true)
  }
  eventCollector.stop()
})
</script>

<style scoped>
.exam-page {
  min-height: 100vh;
  background: #06070c;
  color: #f2efe9;
  padding: 32px 24px 90px;
  font-family:
    -apple-system,
    BlinkMacSystemFont,
    'PingFang SC',
    'Microsoft YaHei',
    sans-serif;
}

.exam-container {
  max-width: 860px;
  margin: 0 auto;
  display: grid;
  gap: 22px;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.back-button {
  border: none;
  background: transparent;
  color: rgba(242, 239, 233, 0.55);
  font-size: 14px;
  cursor: pointer;
  padding: 0;
}

.back-button:hover {
  color: #e8a75c;
}

.mode-badge {
  font-size: 12px;
  letter-spacing: 2px;
  color: #e8a75c;
  border: 1px solid rgba(232, 167, 92, 0.3);
  border-radius: 999px;
  padding: 3px 12px;
}

.eyebrow {
  margin: 0 0 12px;
  color: #e8a75c;
  font-size: 12px;
  letter-spacing: 4px;
  text-transform: uppercase;
}

.hero h1 {
  margin: 0;
  font-size: clamp(24px, 4vw, 34px);
  letter-spacing: 1px;
}

.description {
  margin-top: 12px;
  color: rgba(242, 239, 233, 0.55);
  font-size: 14px;
}

.mode-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 18px;
}

.mode-card {
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 18px;
  padding: 24px;
  cursor: pointer;
  transition:
    transform 0.25s,
    border-color 0.25s;
}

.mode-card:hover {
  transform: translateY(-2px);
  border-color: rgba(232, 167, 92, 0.35);
}

.mode-card h2 {
  margin: 0 0 8px;
  font-size: 18px;
}

.mode-card p {
  margin: 0;
  font-size: 13px;
  line-height: 1.8;
  color: rgba(242, 239, 233, 0.55);
}

.go {
  display: inline-block;
  margin-top: 14px;
  font-size: 13px;
  letter-spacing: 2px;
  color: #e8a75c;
}

.resume-card {
  background: rgba(232, 167, 92, 0.08);
  border: 1px solid rgba(232, 167, 92, 0.25);
  border-radius: 16px;
  padding: 16px 20px;
  font-size: 14px;
}

.resume-actions {
  margin-top: 12px;
  display: flex;
  gap: 12px;
  justify-content: center;
}

.primary-btn {
  border: none;
  border-radius: 12px;
  padding: 11px 24px;
  background: #e8a75c;
  color: #17120c;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
}

.primary-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.ghost-btn {
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  padding: 11px 24px;
  background: transparent;
  color: rgba(242, 239, 233, 0.65);
  font-size: 14px;
  cursor: pointer;
}

.unit-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.unit-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  font-size: 13px;
  color: rgba(242, 239, 233, 0.6);
}

.unit-range {
  font-size: 12px;
  color: rgba(242, 239, 233, 0.4);
}

.nav-btn {
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  padding: 9px 18px;
  background: rgba(255, 255, 255, 0.05);
  color: rgba(242, 239, 233, 0.75);
  font-size: 13px;
  cursor: pointer;
}

.nav-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.submit-row {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 16px;
}

.submit-hint {
  margin: 0;
  font-size: 13px;
  color: rgba(242, 239, 233, 0.4);
}

.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal-card {
  background: #14151c;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 18px;
  padding: 28px 32px;
  max-width: 360px;
  width: calc(100% - 48px);
  text-align: center;
}

.modal-text {
  margin: 0 0 20px;
  font-size: 15px;
  color: rgba(242, 239, 233, 0.85);
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.state-card {
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 20px;
  padding: 40px;
  text-align: center;
  color: rgba(242, 239, 233, 0.6);
}

.state-card.error {
  border-color: rgba(232, 144, 122, 0.4);
}

.retry-button {
  margin-top: 16px;
  border: none;
  border-radius: 12px;
  padding: 10px 22px;
  background: #e8a75c;
  color: #17120c;
  font-weight: 600;
  cursor: pointer;
}

.result-score {
  margin: 10px 0;
  font-size: 44px;
  color: #e8a75c;
}

.result-note {
  font-size: 14px;
  color: rgba(242, 239, 233, 0.5);
}
</style>
