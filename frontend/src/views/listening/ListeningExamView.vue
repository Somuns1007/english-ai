<template>
  <div class="exam-page">
    <div class="exam-container">
      <div class="topbar">
        <button class="back-button" @click="goBack">
          ← 返回听力首页
        </button>
        <span v-if="stage === 'running'" class="mode-badge">
          {{ mode === 'exam_mode' ? '考试模式' : '练习模式' }}
        </span>
      </div>

      <div v-if="loading" class="state-card">
        <p>正在加载套题……</p>
      </div>

      <div v-else-if="errorMessage" class="state-card error">
        <p>{{ errorMessage }}</p>
        <button class="retry-button" @click="loadExam">重试</button>
      </div>

      <!-- 入口: 模式选择 -->
      <template v-else-if="stage === 'intro' && examDetail">
        <section class="hero">
          <p class="eyebrow">{{ examDetail.exam_type.toUpperCase() }} Listening</p>
          <h1>{{ examDetail.title }}</h1>
          <p class="description">
            {{ examDetail.question_count }} 题 ·
            {{ examDetail.duration_ms ? formatDuration(examDetail.duration_ms) : '时长未知' }}
          </p>
        </section>

        <section v-if="inProgress" class="resume-card">
          <p>
            检测到你有一份未提交的{{ inProgress.attempt.mode === 'exam_mode' ? '考试' : '练习' }}
            记录（{{ inProgress.answers.length }} 题已作答）。
          </p>
          <div class="resume-actions">
            <button class="primary-btn" @click="resumeAttempt">
              继续上次作答
            </button>
            <button class="ghost-btn" @click="inProgress = null">
              重新开始
            </button>
          </div>
        </section>

        <section class="mode-grid">
          <div class="mode-card" @click="start('exam_mode')">
            <h2>考试模式</h2>
            <p>模拟真实考试：音频不可拖动、不可重播，提交前不显示答案。</p>
            <span class="go">开始考试 →</span>
          </div>
          <div class="mode-card" @click="start('practice_mode')">
            <h2>练习模式</h2>
            <p>自由控制音频进度与重播，作答过程同样被完整记录。</p>
            <span class="go">开始练习 →</span>
          </div>
        </section>
      </template>

      <!-- 作答中 -->
      <template v-else-if="stage === 'running'">
        <AudioPlayer
          :src="audioUrl(examId)"
          :mode="mode"
          @audio-event="onAudioEvent"
        />

        <div class="progress-info">
          <span>第 {{ currentIndex + 1 }} / {{ flatQuestions.length }} 题</span>
          <span>已作答 {{ answeredCount }} 题</span>
        </div>

        <QuestionCard
          v-if="currentQuestion"
          :question="currentQuestion"
          :model-value="answers[currentQuestion.id]?.finalAnswer ?? null"
          @update:model-value="onSelect"
        />

        <div class="nav-row">
          <button
            class="nav-btn"
            :disabled="currentIndex === 0"
            @click="gotoQuestion(currentIndex - 1)"
          >
            ← 上一题
          </button>
          <button
            class="nav-btn"
            :disabled="currentIndex >= flatQuestions.length - 1"
            @click="gotoQuestion(currentIndex + 1)"
          >
            下一题 →
          </button>
        </div>

        <div class="q-grid">
          <button
            v-for="(q, i) in flatQuestions"
            :key="q.id"
            class="q-dot"
            :class="{
              current: i === currentIndex,
              answered: !!answers[q.id]?.finalAnswer
            }"
            @click="gotoQuestion(i)"
          >
            {{ q.number }}
          </button>
        </div>

        <div class="submit-row">
          <p v-if="unansweredCount > 0" class="submit-hint">
            还有 {{ unansweredCount }} 题未作答
          </p>
          <button
            class="primary-btn"
            :disabled="submitting"
            @click="confirmSubmit"
          >
            {{ submitting ? '正在提交…' : '提交试卷' }}
          </button>
        </div>
      </template>

      <!-- 提交结果 -->
      <section v-else-if="stage === 'submitted' && submitResult" class="state-card">
        <p class="eyebrow">Submitted</p>
        <h2 class="result-score">
          {{ submitResult.score }} / {{ submitResult.question_count }}
        </h2>
        <p class="result-note">
          作答已保存。逐题诊断与复盘将在下一阶段开放。
        </p>
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
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AudioPlayer from '../../components/listening/AudioPlayer.vue'
import QuestionCard from '../../components/listening/QuestionCard.vue'
import {
  audioUrl,
  createAttempt,
  fetchExamQuestions,
  findInProgressAttempt,
  saveAnswer,
  submitAttempt
} from '../../services/listeningApi'
import { eventCollector, getStudentId } from '../../services/listeningEvents'
import type {
  ExamMode,
  InProgressAttempt,
  PublicQuestion,
  SubmitResult,
  UnitWithQuestions
} from '../../types/listening'

interface ExamDetailBrief {
  id: string
  exam_type: string
  title: string
  question_count: number
  duration_ms: number | null
}

interface AnswerState {
  firstAnswer: string | null
  firstAnswerAt: string | null
  finalAnswer: string | null
  lastAnswerAt: string | null
  changeCount: number
  dwellMs: number
}

const route = useRoute()
const router = useRouter()
const examId = route.params.examId as string
const studentId = getStudentId()

const loading = ref(true)
const errorMessage = ref('')
const stage = ref<'intro' | 'running' | 'submitted'>('intro')
const examDetail = ref<ExamDetailBrief | null>(null)
const units = ref<UnitWithQuestions[]>([])
const mode = ref<ExamMode>('practice_mode')
const attemptId = ref<string | null>(null)
const inProgress = ref<InProgressAttempt | null>(null)
const submitting = ref(false)
const submitResult = ref<SubmitResult | null>(null)

const currentIndex = ref(0)
const answers = reactive<Record<string, AnswerState>>({})

const flatQuestions = computed<PublicQuestion[]>(() =>
  units.value.flatMap((u) => u.questions)
)
const currentQuestion = computed<PublicQuestion | null>(
  () => flatQuestions.value[currentIndex.value] || null
)
const answeredCount = computed(
  () => Object.values(answers).filter((a) => a.finalAnswer).length
)
const unansweredCount = computed(
  () => flatQuestions.value.length - answeredCount.value
)

let questionEnteredAt = 0

function nowIso(): string {
  return new Date().toISOString()
}

function formatDuration(ms: number): string {
  const s = Math.round(ms / 1000)
  return `${Math.floor(s / 60)} 分 ${String(s % 60).padStart(2, '0')} 秒`
}

async function loadExam() {
  loading.value = true
  errorMessage.value = ''
  try {
    const [detailRes, questionData] = await Promise.all([
      fetch(`/api/listening/exams/${encodeURIComponent(examId)}`).then((r) =>
        r.json()
      ),
      fetchExamQuestions(examId)
    ])
    examDetail.value = detailRes.data
    units.value = questionData
    await checkInProgress()
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : '套题加载失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

async function checkInProgress() {
  for (const m of ['exam_mode', 'practice_mode'] as ExamMode[]) {
    const found = await findInProgressAttempt(examId, m, studentId)
    if (found) {
      inProgress.value = found
      return
    }
  }
}

function start(selectedMode: ExamMode) {
  mode.value = selectedMode
  createAttempt(examId, selectedMode, studentId)
    .then((attempt) => {
      attemptId.value = attempt.id
      beginRunning()
    })
    .catch((error) => {
      errorMessage.value =
        error instanceof Error ? error.message : '无法创建作答记录'
    })
}

function resumeAttempt() {
  if (!inProgress.value) return
  const { attempt, answers: saved } = inProgress.value
  mode.value = attempt.mode
  attemptId.value = attempt.id
  for (const a of saved) {
    if (a.final_answer) {
      answers[a.question_id] = {
        firstAnswer: a.first_answer,
        firstAnswerAt: a.first_answer_at,
        finalAnswer: a.final_answer,
        lastAnswerAt: a.last_answer_at,
        changeCount: a.change_count,
        dwellMs: a.dwell_ms || 0
      }
    }
  }
  inProgress.value = null
  beginRunning()
}

function beginRunning() {
  stage.value = 'running'
  eventCollector.start(attemptId.value!, studentId)
  enterQuestion(0)
}

function enterQuestion(index: number) {
  currentIndex.value = index
  questionEnteredAt = Date.now()
  const q = currentQuestion.value
  if (q) {
    eventCollector.track({
      event_type: 'question_enter',
      question_id: q.id
    })
  }
}

function leaveCurrentQuestion() {
  const q = currentQuestion.value
  if (!q || !questionEnteredAt) return
  const dwell = Date.now() - questionEnteredAt
  const st = answers[q.id]
  if (st) {
    st.dwellMs += dwell
  }
  eventCollector.track({
    event_type: 'question_leave',
    question_id: q.id,
    payload: { dwell_ms: dwell }
  })
  questionEnteredAt = 0
}

function gotoQuestion(index: number) {
  if (index === currentIndex.value) return
  const leaving = currentQuestion.value
  leaveCurrentQuestion()
  if (leaving && answers[leaving.id]?.finalAnswer) {
    persistAnswer(leaving.id)
  }
  enterQuestion(index)
}

function onSelect(label: string) {
  const q = currentQuestion.value
  if (!q) return
  const st = (answers[q.id] ||= {
    firstAnswer: null,
    firstAnswerAt: null,
    finalAnswer: null,
    lastAnswerAt: null,
    changeCount: 0,
    dwellMs: 0
  })
  if (!st.firstAnswer) {
    st.firstAnswer = label
    st.firstAnswerAt = nowIso()
    eventCollector.track({
      event_type: 'answer_select',
      question_id: q.id,
      payload: { value: label }
    })
  } else if (st.finalAnswer !== label) {
    st.changeCount += 1
    eventCollector.track({
      event_type: 'answer_change',
      question_id: q.id,
      payload: { from: st.finalAnswer, to: label, change_count: st.changeCount }
    })
  } else {
    return
  }
  st.finalAnswer = label
  st.lastAnswerAt = nowIso()
  persistAnswer(q.id)
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
    dwell_ms: st.dwellMs
  }).catch((error) => console.warn('答案保存失败:', error))
}

function onAudioEvent(
  eventType: 'audio_play' | 'audio_pause' | 'audio_seek' | 'audio_replay' | 'audio_ended',
  payload: Record<string, unknown>
) {
  // 音频事件携带当前题目上下文(供后续定位复听分析); 不代表学生错因
  eventCollector.track({
    event_type: eventType,
    question_id: currentQuestion.value?.id ?? null,
    payload
  })
}

function confirmSubmit() {
  const message =
    unansweredCount.value > 0
      ? `还有 ${unansweredCount.value} 题未作答，确定提交吗？`
      : '确定提交试卷吗？提交后将进入诊断复盘。'
  if (window.confirm(message)) {
    doSubmit()
  }
}

async function doSubmit() {
  if (!attemptId.value || submitting.value) return
  submitting.value = true
  try {
    leaveCurrentQuestion()
    // 先落全部答案, 再冲事件, 最后判分
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
            dwell_ms: answers[qid].dwellMs
          })
        )
    )
    eventCollector.flush()
    submitResult.value = await submitAttempt(attemptId.value)
    stage.value = 'submitted'
    eventCollector.stop()
    // 提交后直接进入逐题复盘
    router.push(`/listening/review/${attemptId.value}`)
  } catch (error) {
    window.alert(
      error instanceof Error ? error.message : '提交失败，请稍后重试。'
    )
  } finally {
    submitting.value = false
  }
}

function goBack() {
  if (stage.value === 'running') {
    if (!window.confirm('作答进度已自动保存，确定返回首页吗？')) return
    leaveCurrentQuestion()
    const q = currentQuestion.value
    if (q && answers[q.id]?.finalAnswer) persistAnswer(q.id)
    eventCollector.flush(true)
    eventCollector.stop()
  }
  router.push('/listening')
}

onMounted(loadExam)

onBeforeUnmount(() => {
  if (stage.value === 'running') {
    leaveCurrentQuestion()
    eventCollector.flush(true)
  }
  eventCollector.stop()
})
</script>

<style scoped>
.exam-page {
  min-height: 100vh;
  background:
    radial-gradient(
      circle at 50% -10%,
      rgba(232, 167, 92, 0.12),
      transparent 34%
    ),
    #06070c;
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
  max-width: 980px;
  margin: 0 auto;
  display: grid;
  gap: 20px;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
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
  font-size: clamp(28px, 4vw, 40px);
  letter-spacing: 2px;
}

.description {
  margin-top: 14px;
  color: rgba(242, 239, 233, 0.55);
  font-size: 15px;
}

.mode-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-top: 12px;
}

.mode-card {
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 20px;
  padding: 28px;
  cursor: pointer;
  transition:
    transform 0.3s,
    border-color 0.3s;
}

.mode-card:hover {
  transform: translateY(-3px);
  border-color: rgba(232, 167, 92, 0.35);
}

.mode-card h2 {
  margin: 0 0 10px;
  font-size: 19px;
}

.mode-card p {
  margin: 0;
  font-size: 14px;
  line-height: 1.8;
  color: rgba(242, 239, 233, 0.55);
}

.go {
  display: inline-block;
  margin-top: 18px;
  font-size: 13px;
  letter-spacing: 2px;
  color: #e8a75c;
}

.resume-card {
  background: rgba(232, 167, 92, 0.08);
  border: 1px solid rgba(232, 167, 92, 0.25);
  border-radius: 16px;
  padding: 18px 22px;
  font-size: 14px;
  line-height: 1.7;
}

.resume-actions {
  margin-top: 12px;
  display: flex;
  gap: 12px;
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

.progress-info {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: rgba(242, 239, 233, 0.5);
}

.nav-row {
  display: flex;
  justify-content: space-between;
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

.q-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.q-dot {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.04);
  color: rgba(242, 239, 233, 0.6);
  font-size: 13px;
  cursor: pointer;
}

.q-dot.answered {
  border-color: rgba(232, 167, 92, 0.5);
  color: #e8a75c;
}

.q-dot.current {
  background: #e8a75c;
  color: #17120c;
  font-weight: 700;
}

.submit-row {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 16px;
  margin-top: 8px;
}

.submit-hint {
  margin: 0;
  font-size: 13px;
  color: rgba(242, 239, 233, 0.4);
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
