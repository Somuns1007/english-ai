<template>
  <div class="sp-page">
    <div class="sp-container">
      <div class="topbar">
        <button class="back-button" @click="$router.push('/listening')">
          ← 返回听力首页
        </button>
        <span class="mode-tag">Strict Pacing · 仿真模式</span>
      </div>

      <div v-if="phase === 'loading'" class="state-card">
        <p>正在加载……</p>
      </div>

      <div v-else-if="phase === 'error'" class="state-card error">
        <p>{{ errorMsg }}</p>
      </div>

      <!-- 开始说明 -->
      <div v-else-if="phase === 'intro'" class="intro-card">
        <p class="eyebrow">CET 仿真模式</p>
        <h1>{{ examTitle }}</h1>
        <ul class="rules">
          <li>音频<strong>只能前进不能后退</strong>，模拟真实考场。</li>
          <li>听到每道题的题干后，系统进入 <strong>13 秒答题窗口</strong>并倒计时。</li>
          <li>窗口关闭后自动锁定（无论是否作答），不可再改。</li>
          <li>所有 25 题完成后点击"提交"，查看得分。</li>
          <li>如尝试倒退音频，系统记录 <em>stem_replay_requested</em> 事件（不强制停止）。</li>
        </ul>
        <button class="start-btn" @click="startSession">我准备好了，开始作答</button>
      </div>

      <!-- 播放器 -->
      <StrictPacingPlayer
        v-else-if="phase === 'playing' && attemptId && windows.length && questions.length"
        :exam-id="examId"
        :exam-title="examTitle"
        :audio-src="audioSrc"
        :attempt-id="attemptId"
        :student-id="studentId"
        :windows="windows"
        :questions="questions"
        @submitted="onSubmitted"
      />

      <!-- 完成跳转 -->
      <div v-else-if="phase === 'done'" class="state-card">
        <p>提交完成！正在跳转复盘页……</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import StrictPacingPlayer, {
  type PacingWindow,
  type QuestionData,
} from '../../components/listening/StrictPacingPlayer.vue'
import {
  audioUrl,
  createAttempt,
  fetchExamQuestions,
} from '../../services/listeningApi'
import { getStudentId } from '../../services/listeningEvents'
import type { UnitWithQuestions } from '../../types/listening'

const route = useRoute()
const router = useRouter()
const examId = route.params.examId as string
const studentId = getStudentId()

// ── State ─────────────────────────────────────────────────────────────
type Phase = 'loading' | 'intro' | 'playing' | 'done' | 'error'
const phase = ref<Phase>('loading')
const errorMsg = ref('')

const examTitle = ref('')
const audioSrc = ref('')
const windows = ref<PacingWindow[]>([])
const questions = ref<QuestionData[]>([])
const attemptId = ref('')

// ── Bootstrap ─────────────────────────────────────────────────────────
onMounted(async () => {
  try {
    // 1. Fetch pacing windows
    const pacingRes = await fetch(`/api/listening/exams/${encodeURIComponent(examId)}/pacing`)
    if (!pacingRes.ok) {
      throw new Error(
        pacingRes.status === 404
          ? 'この試験には Strict Pacing データがありません（封卷または未設定）'
          : `pacing fetch failed: ${pacingRes.status}`
      )
    }
    const pacingJson = await pacingRes.json()
    windows.value = pacingJson.data.windows as PacingWindow[]

    // 2. Fetch exam questions
    const units: UnitWithQuestions[] = await fetchExamQuestions(examId)
    examTitle.value = units[0]?.unit.exam_id
      ? units[0].unit.exam_id.replace(/_/g, ' ').toUpperCase()
      : examId

    // Flatten to QuestionData matching StrictPacingPlayer's interface
    questions.value = units.flatMap((u) =>
      u.questions.map((q) => ({
        question_id: q.id,
        number: q.number,
        options: q.options.map((o) => ({ label: o.label, text: o.text })),
      }))
    )

    // Also fetch exam title from exam detail
    const examDetail = await fetch(`/api/listening/exams/${encodeURIComponent(examId)}`)
    if (examDetail.ok) {
      const detailJson = await examDetail.json()
      examTitle.value = detailJson.data?.title ?? examTitle.value
    }

    audioSrc.value = audioUrl(examId)
    phase.value = 'intro'
  } catch (e: unknown) {
    errorMsg.value = e instanceof Error ? e.message : String(e)
    phase.value = 'error'
  }
})

// ── Start session: create attempt ─────────────────────────────────────
async function startSession() {
  try {
    // Use exam_mode — pacing distinction tracked via behavior event in player
    const attempt = await createAttempt(examId, 'exam_mode', studentId)
    attemptId.value = attempt.id
    phase.value = 'playing'
  } catch (e: unknown) {
    errorMsg.value = e instanceof Error ? e.message : '创建答题记录失败'
    phase.value = 'error'
  }
}

// ── On submission ─────────────────────────────────────────────────────
function onSubmitted(payload: { score: number; attemptId: string }) {
  phase.value = 'done'
  // Redirect to review after brief pause
  setTimeout(() => {
    router.push(`/listening/review/${payload.attemptId}`)
  }, 1500)
}
</script>

<style scoped>
.sp-page {
  min-height: 100vh;
  padding: 0 16px 48px;
}
.sp-container {
  max-width: 820px;
  margin: 0 auto;
  padding: 24px 0;
}
.topbar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 28px;
}
.back-button {
  background: none;
  border: none;
  color: rgba(242, 239, 233, 0.55);
  font-size: 14px;
  cursor: pointer;
  padding: 0;
}
.back-button:hover { color: rgba(242,239,233,0.85); }
.mode-tag {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: rgba(232,167,92,0.7);
  border: 1px solid rgba(232,167,92,0.2);
  border-radius: 20px;
  padding: 3px 10px;
}

/* intro card */
.intro-card {
  padding: 32px 0;
}
.eyebrow {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: rgba(242,239,233,0.35);
  margin: 0 0 10px;
}
h1 {
  font-size: 26px;
  font-weight: 700;
  color: rgba(242,239,233,0.92);
  margin: 0 0 24px;
}
.rules {
  padding: 0 0 0 20px;
  margin: 0 0 28px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.rules li {
  font-size: 14px;
  color: rgba(242,239,233,0.65);
  line-height: 1.6;
}
.rules strong { color: rgba(242,239,233,0.9); }
.rules em { color: rgba(232,167,92,0.8); font-style: normal; }
.start-btn {
  padding: 12px 28px;
  border-radius: 12px;
  border: 1px solid rgba(232,167,92,0.35);
  background: rgba(232,167,92,0.1);
  color: #e8a75c;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
}
.start-btn:hover { background: rgba(232,167,92,0.18); }

/* state cards */
.state-card {
  margin-top: 60px;
  background: rgba(255,255,255,0.045);
  border: 1px solid rgba(255,255,255,0.09);
  border-radius: 20px;
  padding: 40px;
  text-align: center;
  color: rgba(242,239,233,0.6);
}
.state-card.error { border-color: rgba(232,100,90,0.4); color: rgba(232,100,90,0.85); }
</style>
