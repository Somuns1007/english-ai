<template>
  <!--
    Strict Pacing Player (Work Order F)

    模拟真实 CET 考场体验：
    - 音频只能前进不能后退
    - 进入答题窗口后显示 13 秒倒计时
    - 倒计时归零自动锁定（留空）
    - 用户尝试倒退时记录 stem_replay_requested 事件
    - pacing_mode 以行为事件形式上报
  -->
  <div class="pacing-root">
    <!-- 顶栏 -->
    <div class="pacing-topbar">
      <span class="exam-label">{{ examTitle }}</span>
      <span class="q-progress">{{ lockedCount }} / {{ windows.length }} 题已锁定</span>
    </div>

    <!-- 音频控制（只能播放/暂停，不能拖动） -->
    <div class="audio-bar">
      <button class="play-btn" :disabled="phase === 'done'" @click="togglePlay">
        {{ playing ? '⏸ 暂停' : (phase === 'ready' ? '▶ 开始' : '▶ 继续') }}
      </button>
      <!-- 进度条（只读，不可拖动） -->
      <div class="progress-track" title="答题中禁止拖动音频">
        <div class="progress-fill" :style="{ width: progressPct + '%' }"></div>
      </div>
      <span class="time-label">{{ fmtTime(currentTime) }} / {{ fmtTime(duration) }}</span>
    </div>

    <!-- 当前激活题（答题窗口中） -->
    <div v-if="activeQ && phase !== 'done'" class="active-window">
      <div class="window-header">
        <span class="section-tag">{{ sectionLabel(activeQ.unit_id) }}</span>
        <span class="q-num">Q{{ activeQ.q }}</span>
        <div class="countdown-ring" :class="countdownUrgent ? 'urgent' : ''">
          <span class="countdown-num">{{ countdown }}</span>
          <span class="countdown-unit">秒</span>
        </div>
      </div>

      <div class="q-options">
        <button
          v-for="opt in currentOptions"
          :key="opt.label"
          class="opt-btn"
          :class="{
            selected: picks[activeQ.q] === opt.label,
            locked: isLocked(activeQ.q),
          }"
          :disabled="isLocked(activeQ.q)"
          @click="selectAnswer(activeQ.q, opt.label)"
        >
          <span class="opt-label">{{ opt.label }}</span>
          <span class="opt-text">{{ opt.text }}</span>
        </button>
      </div>
      <p v-if="isLocked(activeQ.q)" class="lock-msg">
        {{ picks[activeQ.q] ? `已选：${picks[activeQ.q]}` : '未作答（超时）' }}
      </p>
    </div>

    <!-- 等待下一题（音频播放中，未到窗口） -->
    <div v-else-if="phase === 'playing' && !activeQ" class="listening-hint">
      <p class="hint-txt">🎧 认真聆听……</p>
      <p v-if="nextQ" class="next-hint">
        下一题：Q{{ nextQ.q }}（约 {{ nextWindowIn }} 秒后）
      </p>
    </div>

    <!-- 完成 -->
    <div v-if="phase === 'done'" class="done-card">
      <p class="done-title">答题完成</p>
      <p class="done-sub">已作答 {{ answeredCount }} / {{ windows.length }} 题</p>
      <button class="submit-btn" :disabled="submitting" @click="submitAnswers">
        {{ submitting ? '提交中……' : '提交答案' }}
      </button>
      <p v-if="submitResult" class="submit-msg">
        得分：{{ submitResult.score }} / {{ windows.length }}
      </p>
    </div>

    <!-- 所有题目列表（题纸，始终可见） -->
    <div class="question-sheet">
      <p class="sheet-title">题目列表（可提前浏览选项）</p>
      <div
        v-for="w in windows"
        :key="w.q"
        class="sheet-q"
        :class="{
          active: activeQ?.q === w.q,
          locked: isLocked(w.q),
          unanswered: isLocked(w.q) && !picks[w.q],
        }"
      >
        <div class="sheet-q-header">
          <span class="sheet-q-num">Q{{ w.q }}</span>
          <span v-if="isLocked(w.q) && picks[w.q]" class="sheet-pick">{{ picks[w.q] }}</span>
          <span v-else-if="isLocked(w.q)" class="sheet-miss">—</span>
        </div>
        <div class="sheet-opts">
          <span
            v-for="opt in optionsFor(w.q)"
            :key="opt.label"
            class="sheet-opt"
            :class="{ chosen: picks[w.q] === opt.label && isLocked(w.q) }"
          >{{ opt.label }}. {{ opt.text }}</span>
        </div>
      </div>
    </div>

    <!-- 隐藏的 audio 元素 -->
    <audio
      ref="audioEl"
      :src="audioSrc"
      preload="metadata"
      @timeupdate="onTimeUpdate"
      @durationchange="onDurationChange"
      @ended="onEnded"
      @seeked="onSeeked"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

// ── Props / Emits ─────────────────────────────────────────────────────

export interface PacingWindow {
  q: number
  unit_id: string
  section_type: string
  stem_start_s: number
  window_start_s: number
  window_end_s: number
  window_duration_s: number
}

export interface QuestionOption {
  label: string   // A B C D
  text: string
}

export interface QuestionData {
  question_id: string
  number: number
  options: QuestionOption[]
}

const props = defineProps<{
  examId: string
  examTitle: string
  audioSrc: string
  attemptId: string
  studentId: string
  windows: PacingWindow[]
  questions: QuestionData[]   // matched by number → w.q
}>()

const emit = defineEmits<{
  (e: 'submitted', payload: { score: number; attemptId: string }): void
}>()

// ── State ─────────────────────────────────────────────────────────────

const audioEl = ref<HTMLAudioElement | null>(null)
const playing = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const phase = ref<'ready' | 'playing' | 'done'>('ready')
const picks = ref<Record<number, string>>({})      // q → selected label
const lockedQs = ref<Set<number>>(new Set())        // qs that are time-locked
const activeQ = ref<PacingWindow | null>(null)      // currently in-window question
const countdown = ref(13)
const submitting = ref(false)
const submitResult = ref<{ score: number } | null>(null)

let countdownTimer: ReturnType<typeof setInterval> | null = null
let lastSeekTime = 0   // guard against legitimate seeks vs user scrub

// ── Computed ──────────────────────────────────────────────────────────

const progressPct = computed(() =>
  duration.value > 0 ? (currentTime.value / duration.value) * 100 : 0
)

const lockedCount = computed(() => lockedQs.value.size)
const answeredCount = computed(() =>
  [...lockedQs.value].filter((q) => picks.value[q]).length
)

const countdownUrgent = computed(() => countdown.value <= 5)

const nextQ = computed<PacingWindow | null>(() => {
  const t = currentTime.value
  return (
    props.windows.find(
      (w) => w.window_start_s > t && !lockedQs.value.has(w.q)
    ) ?? null
  )
})

const nextWindowIn = computed(() => {
  if (!nextQ.value) return 0
  return Math.max(0, Math.round(nextQ.value.window_start_s - currentTime.value))
})

const currentOptions = computed<QuestionOption[]>(() => {
  if (!activeQ.value) return []
  return optionsFor(activeQ.value.q)
})

// ── Helpers ───────────────────────────────────────────────────────────

function optionsFor(qNum: number): QuestionOption[] {
  const q = props.questions.find((q) => q.number === qNum)
  return q?.options ?? []
}

function isLocked(qNum: number): boolean {
  return lockedQs.value.has(qNum)
}

function sectionLabel(unitId: string): string {
  const map: Record<string, string> = {
    conversation_1: 'Conversation 1',
    conversation_2: 'Conversation 2',
    passage_1: 'Passage 1',
    passage_2: 'Passage 2',
    lecture_1: 'Lecture 1',
    lecture_2: 'Lecture 2',
    lecture_3: 'Lecture 3',
  }
  return map[unitId] ?? unitId
}

function fmtTime(s: number): string {
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m}:${sec.toString().padStart(2, '0')}`
}

// ── Audio controls ────────────────────────────────────────────────────

function togglePlay() {
  const el = audioEl.value
  if (!el) return
  if (playing.value) {
    el.pause()
    playing.value = false
  } else {
    el.play()
    playing.value = true
    if (phase.value === 'ready') {
      phase.value = 'playing'
      logPacingMode()
    }
  }
}

function onDurationChange() {
  duration.value = audioEl.value?.duration ?? 0
}

function onEnded() {
  playing.value = false
  // Lock any still-open window
  if (activeQ.value) lockCurrentWindow()
  phase.value = 'done'
}

// Forward-only guard: if user scrubs backward, log stem_replay_requested + cancel
function onSeeked() {
  const el = audioEl.value
  if (!el) return
  if (el.currentTime < lastSeekTime - 0.5) {
    // backward seek detected
    el.currentTime = lastSeekTime
    logStemReplayRequested()
  }
  lastSeekTime = el.currentTime
}

function onTimeUpdate() {
  const el = audioEl.value
  if (!el) return
  currentTime.value = el.currentTime
  lastSeekTime = el.currentTime
  tickWindows(el.currentTime)
}

// ── Window detection ──────────────────────────────────────────────────

function tickWindows(t: number) {
  // If already in a window, let countdown handle it
  if (activeQ.value) return

  const w = props.windows.find(
    (w) => t >= w.window_start_s && t < w.window_end_s && !lockedQs.value.has(w.q)
  )
  if (w) enterWindow(w)
}

function enterWindow(w: PacingWindow) {
  activeQ.value = w
  const remaining = Math.max(
    0,
    Math.ceil(w.window_end_s - (audioEl.value?.currentTime ?? w.window_start_s))
  )
  countdown.value = Math.min(13, remaining)
  startCountdown()
}

function startCountdown() {
  stopCountdown()
  countdownTimer = setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) lockCurrentWindow()
  }, 1000)
}

function stopCountdown() {
  if (countdownTimer !== null) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
}

function lockCurrentWindow() {
  if (!activeQ.value) return
  stopCountdown()
  lockedQs.value = new Set([...lockedQs.value, activeQ.value.q])
  activeQ.value = null
  countdown.value = 13
  // Check if all done
  if (lockedQs.value.size >= props.windows.length) {
    phase.value = 'done'
    audioEl.value?.pause()
    playing.value = false
  }
}

function selectAnswer(qNum: number, label: string) {
  if (isLocked(qNum)) return
  picks.value = { ...picks.value, [qNum]: label }
  // Immediately lock after selection
  lockCurrentWindow()
}

// ── Submit ────────────────────────────────────────────────────────────

async function submitAnswers() {
  submitting.value = true
  try {
    // Submit each answer
    for (const w of props.windows) {
      const q = props.questions.find((q) => q.number === w.q)
      if (!q) continue
      await fetch(`/api/listening/attempts/${props.attemptId}/answers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: props.studentId,
          question_id: q.question_id,
          answer: picks.value[w.q] ?? '',
          is_final: true,
        }),
      })
    }
    // Submit attempt
    const res = await fetch(`/api/listening/attempts/${props.attemptId}/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ student_id: props.studentId }),
    })
    if (res.ok) {
      const data = await res.json()
      submitResult.value = { score: data.data?.score ?? 0 }
      emit('submitted', { score: data.data?.score ?? 0, attemptId: props.attemptId })
    }
  } finally {
    submitting.value = false
  }
}

// ── Behavior event logging ─────────────────────────────────────────────

async function logPacingMode() {
  await fetch(`/api/listening/attempts/${props.attemptId}/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      student_id: props.studentId,
      events: [{
        event_type: 'pacing_mode_entered',
        question_id: null,
        payload: { pacing_mode: 'strict', exam_id: props.examId },
        client_at: new Date().toISOString(),
      }],
    }),
  }).catch(() => {/* non-critical */})
}

async function logStemReplayRequested() {
  const qNum = activeQ.value?.q ?? null
  const q = qNum ? props.questions.find((q) => q.number === qNum) : null
  await fetch(`/api/listening/attempts/${props.attemptId}/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      student_id: props.studentId,
      events: [{
        event_type: 'stem_replay_requested',
        question_id: q?.question_id ?? null,
        payload: {
          pacing_mode: 'strict',
          current_time_s: Math.round(currentTime.value),
          active_q: qNum,
        },
        client_at: new Date().toISOString(),
      }],
    }),
  }).catch(() => {/* non-critical */})
}

// ── Lifecycle ─────────────────────────────────────────────────────────

onBeforeUnmount(() => {
  stopCountdown()
  audioEl.value?.pause()
})
</script>

<style scoped>
.pacing-root {
  max-width: 780px;
  margin: 0 auto;
  padding: 0 0 48px;
}

/* topbar */
.pacing-topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.07);
  margin-bottom: 20px;
}
.exam-label { font-size: 13px; color: rgba(242,239,233,0.5); }
.q-progress { font-size: 13px; color: rgba(232,167,92,0.85); font-weight: 600; }

/* audio bar */
.audio-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}
.play-btn {
  padding: 8px 18px;
  border-radius: 10px;
  border: 1px solid rgba(232,167,92,0.35);
  background: rgba(232,167,92,0.08);
  color: #e8a75c;
  font-size: 14px;
  cursor: pointer;
  flex-shrink: 0;
}
.play-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.progress-track {
  flex: 1;
  height: 6px;
  background: rgba(255,255,255,0.08);
  border-radius: 3px;
  cursor: not-allowed;
}
.progress-fill {
  height: 100%;
  background: #e8a75c;
  border-radius: 3px;
  transition: width 0.5s linear;
}
.time-label { font-size: 12px; color: rgba(242,239,233,0.4); flex-shrink: 0; }

/* active window */
.active-window {
  background: rgba(232,167,92,0.07);
  border: 1px solid rgba(232,167,92,0.2);
  border-radius: 16px;
  padding: 20px 22px;
  margin-bottom: 20px;
}
.window-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.section-tag {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: rgba(242,239,233,0.4);
}
.q-num {
  font-size: 16px;
  font-weight: 700;
  color: #e8a75c;
}
.countdown-ring {
  margin-left: auto;
  display: flex;
  align-items: baseline;
  gap: 3px;
  padding: 4px 12px;
  border-radius: 20px;
  background: rgba(232,167,92,0.12);
  border: 1px solid rgba(232,167,92,0.25);
  transition: all 0.3s;
}
.countdown-ring.urgent {
  background: rgba(232,100,90,0.15);
  border-color: rgba(232,100,90,0.4);
}
.countdown-num {
  font-size: 22px;
  font-weight: 700;
  color: #e8a75c;
  line-height: 1;
}
.countdown-ring.urgent .countdown-num { color: #e8645a; }
.countdown-unit { font-size: 11px; color: rgba(242,239,233,0.5); }

.q-options { display: flex; flex-direction: column; gap: 8px; }
.opt-btn {
  display: flex;
  gap: 10px;
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.09);
  background: transparent;
  color: rgba(242,239,233,0.78);
  font-size: 14px;
  text-align: left;
  cursor: pointer;
  line-height: 1.5;
  transition: border-color 0.15s, background 0.15s;
}
.opt-btn:hover:not(:disabled) {
  border-color: rgba(232,167,92,0.35);
  background: rgba(232,167,92,0.07);
}
.opt-btn.selected {
  border-color: #e8a75c;
  background: rgba(232,167,92,0.12);
  color: #e8a75c;
}
.opt-btn.locked { cursor: not-allowed; opacity: 0.7; }
.opt-label { font-weight: 700; flex-shrink: 0; }
.lock-msg {
  margin: 10px 0 0;
  font-size: 13px;
  color: rgba(242,239,233,0.5);
}

/* listening hint */
.listening-hint {
  padding: 20px;
  text-align: center;
  margin-bottom: 20px;
}
.hint-txt { font-size: 18px; color: rgba(242,239,233,0.6); margin: 0 0 8px; }
.next-hint { font-size: 13px; color: rgba(242,239,233,0.35); margin: 0; }

/* done card */
.done-card {
  padding: 28px;
  background: rgba(100,200,140,0.07);
  border: 1px solid rgba(100,200,140,0.2);
  border-radius: 16px;
  text-align: center;
  margin-bottom: 24px;
}
.done-title { font-size: 18px; font-weight: 700; color: #64c88c; margin: 0 0 8px; }
.done-sub { font-size: 14px; color: rgba(242,239,233,0.55); margin: 0 0 16px; }
.submit-btn {
  padding: 10px 28px;
  border-radius: 12px;
  border: none;
  background: #64c88c;
  color: #0e1a14;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
}
.submit-btn:disabled { opacity: 0.5; cursor: wait; }
.submit-msg { margin: 12px 0 0; font-size: 15px; color: #64c88c; font-weight: 600; }

/* question sheet */
.question-sheet {
  margin-top: 28px;
  border-top: 1px solid rgba(255,255,255,0.06);
  padding-top: 20px;
}
.sheet-title {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: rgba(242,239,233,0.3);
  margin: 0 0 14px;
}
.sheet-q {
  padding: 10px 12px;
  border-radius: 8px;
  margin-bottom: 6px;
  border: 1px solid transparent;
  transition: border-color 0.2s;
}
.sheet-q.active { border-color: rgba(232,167,92,0.35); background: rgba(232,167,92,0.05); }
.sheet-q.locked { opacity: 0.75; }
.sheet-q.unanswered { opacity: 0.5; }
.sheet-q-header { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
.sheet-q-num { font-size: 12px; font-weight: 700; color: rgba(242,239,233,0.6); }
.sheet-pick { font-size: 12px; font-weight: 700; color: #64c88c; }
.sheet-miss { font-size: 12px; color: rgba(232,100,90,0.7); }
.sheet-opts { display: flex; flex-direction: column; gap: 2px; }
.sheet-opt { font-size: 12px; color: rgba(242,239,233,0.4); line-height: 1.5; }
.sheet-opt.chosen { color: #64c88c; font-weight: 600; }
</style>
