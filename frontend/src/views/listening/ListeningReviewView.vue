<template>
  <div class="review-page">
    <div class="review-container">
      <div class="topbar">
        <button class="back-button" @click="$router.push('/listening')">
          ← 返回听力首页
        </button>
      </div>

      <div v-if="loading" class="state-card"><p>正在加载复盘……</p></div>
      <div v-else-if="errorMessage" class="state-card error">
        <p>{{ errorMessage }}</p>
      </div>

      <template v-else-if="overview">
        <section class="hero">
          <p class="eyebrow">Review</p>
          <h1>{{ overview.title }}</h1>
          <p class="description">
            得分 {{ overview.attempt.score }} / {{ overview.question_count }} ·
            答错 {{ wrongCount }} 题 ·
            建议流程：再听一遍 → 重答 → 逐级提示 → 自判错因 → 查看解析
          </p>
        </section>

        <AudioPlayer
          :src="audioUrl(overview.exam_id)"
          mode="practice_mode"
          @audio-event="onAudioEvent"
        />
        <p class="player-note">
          复听为整段播放（题目级时间戳待校准），请自行留意相关段落。
        </p>

        <section
          v-for="group in overview.units"
          :key="group.unit.id"
          class="unit-block"
        >
          <p class="unit-title">
            Section {{ group.unit.section }} · {{ group.unit.title }}
          </p>

          <div
            v-for="q in group.questions"
            :key="q.question_id"
            class="q-card"
            :class="{ wrong: !q.is_correct, open: openId === q.question_id }"
          >
            <button class="q-summary" @click="toggle(q.question_id)">
              <span class="q-no">Q{{ q.number }}</span>
              <span
                class="q-result"
                :class="q.is_correct ? 'right' : 'wrong'"
              >
                {{ q.is_correct ? '✓ 答对' : '✗ 答错' }}
              </span>
              <span class="q-answers">
                首答 {{ q.first_answer || '—' }} → 终答
                {{ q.final_answer || '—' }}
                <template v-if="q.change_count">
                  （改 {{ q.change_count }} 次）
                </template>
              </span>
              <span class="mastery" :class="q.mastery">
                {{ masteryLabel(q.mastery) }}
              </span>
            </button>

            <div v-if="openId === q.question_id" class="q-detail">
              <p v-if="q.question_text" class="q-text">
                {{ q.question_text }}
              </p>
              <p v-if="q.question_text_zh" class="q-text-zh">
                {{ q.question_text_zh }}
              </p>

              <!-- 第 1 步: 重答 -->
              <div v-if="!q.is_correct" class="step-block">
                <p class="step-title">① 再听一遍上面的音频，然后重新作答</p>
                <div class="retry-options">
                  <button
                    v-for="opt in q.options"
                    :key="opt.label"
                    class="retry-option"
                    :class="{
                      picked: retryPick[q.question_id] === opt.label,
                      hit:
                        retryResult[q.question_id]?.is_correct &&
                        retryPick[q.question_id] === opt.label,
                      miss:
                        retryResult[q.question_id] &&
                        !retryResult[q.question_id].is_correct &&
                        retryPick[q.question_id] === opt.label
                    }"
                    @click="doRetry(q, opt.label)"
                  >
                    {{ opt.label }}
                  </button>
                </div>
                <p
                  v-if="retryResult[q.question_id]"
                  class="retry-feedback"
                  :class="{ ok: retryResult[q.question_id].is_correct }"
                >
                  {{
                    retryResult[q.question_id].is_correct
                      ? '重答正确！现在可以继续查看提示，弄清第一次为什么错。'
                      : '还是不对，别着急——用下面的分级提示一步步来。'
                  }}
                </p>
              </div>

              <!-- 第 2 步: 分级提示 -->
              <div class="step-block">
                <p class="step-title">
                  ② 分级提示（逐级解锁，Level 5 才会显示答案与解析）
                </p>
                <HintStepper
                  :attempt-id="attemptId"
                  :question-id="q.question_id"
                  :unlocked-level="q.max_hint_level"
                  @unlocked="onHintUnlocked(q, $event)"
                />
              </div>

              <!-- 第 3 步: 错因诊断 -->
              <div v-if="!q.is_correct" class="step-block">
                <p class="step-title">③ 错因诊断</p>
                <DiagnosisPanel
                  :attempt-id="attemptId"
                  :question-id="q.question_id"
                  :student-id="studentId"
                  :initial-student-tags="q.diagnosis.student_tags"
                  :initial-final-tags="q.diagnosis.final_tags"
                  @saved="reloadOverview"
                />
              </div>

              <!-- 第 4 步: 对症训练与裸听复测 -->
              <div v-if="!q.is_correct" class="step-block">
                <p class="step-title">
                  ④ 对症训练与裸听复测（由已确认错因或高置信候选驱动）
                </p>
                <TrainingPanel
                  :attempt-id="attemptId"
                  :question-id="q.question_id"
                  :student-id="studentId"
                  @progress="reloadOverview"
                />
              </div>
            </div>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import AudioPlayer from '../../components/listening/AudioPlayer.vue'
import DiagnosisPanel from '../../components/listening/DiagnosisPanel.vue'
import HintStepper from '../../components/listening/HintStepper.vue'
import TrainingPanel from '../../components/listening/TrainingPanel.vue'
import {
  audioUrl,
  fetchReviewOverview,
  retryQuestion
} from '../../services/listeningApi'
import { eventCollector, getStudentId } from '../../services/listeningEvents'
import type { ReviewOverview, ReviewQuestion } from '../../types/listening'

const route = useRoute()
const attemptId = route.params.attemptId as string
const studentId = getStudentId()

const loading = ref(true)
const errorMessage = ref('')
const overview = ref<ReviewOverview | null>(null)
const openId = ref<string | null>(null)
const retryPick = ref<Record<string, string>>({})
const retryResult = ref<Record<string, { is_correct: boolean }>>({})
/** 复盘页内音频事件的题目上下文(用户正在展开的题) */
const contextQuestionId = ref<string | null>(null)

const wrongCount = computed(() => {
  if (!overview.value) return 0
  return overview.value.units
    .flatMap((u) => u.questions)
    .filter((q) => !q.is_correct).length
})

function masteryLabel(m: string): string {
  const labels: Record<string, string> = {
    unreviewed: '未复盘',
    reviewing: '复盘中',
    improved: '已改进',
    mastered: '已掌握',
    not_mistake: '—'
  }
  return labels[m] || m
}

async function loadOverview() {
  loading.value = true
  errorMessage.value = ''
  try {
    overview.value = await fetchReviewOverview(attemptId)
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : '复盘加载失败'
  } finally {
    loading.value = false
  }
}

async function reloadOverview() {
  overview.value = await fetchReviewOverview(attemptId)
}

function toggle(questionId: string) {
  openId.value = openId.value === questionId ? null : questionId
  contextQuestionId.value = openId.value
}

async function doRetry(q: ReviewQuestion, label: string) {
  retryPick.value[q.question_id] = label
  try {
    const result = await retryQuestion(attemptId, q.question_id, label)
    retryResult.value[q.question_id] = result
    await reloadOverview()
  } catch (error) {
    window.alert(error instanceof Error ? error.message : '重答提交失败')
  }
}

function onHintUnlocked(q: ReviewQuestion, level: number) {
  q.max_hint_level = Math.max(q.max_hint_level, level)
}

function onAudioEvent(
  eventType: 'audio_play' | 'audio_pause' | 'audio_seek' | 'audio_replay' | 'audio_ended',
  payload: Record<string, unknown>
) {
  eventCollector.track({
    event_type: eventType,
    question_id: contextQuestionId.value,
    payload
  })
}

onMounted(async () => {
  await loadOverview()
  // 复盘页的行为(复听/展开)同样计入该 attempt 的证据链
  eventCollector.start(attemptId, studentId)
})

onBeforeUnmount(() => {
  eventCollector.flush(true)
  eventCollector.stop()
})
</script>

<style scoped>
.review-page {
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

.review-container {
  max-width: 980px;
  margin: 0 auto;
}

.topbar {
  margin-bottom: 32px;
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

.eyebrow {
  margin: 0 0 12px;
  color: #e8a75c;
  font-size: 12px;
  letter-spacing: 4px;
  text-transform: uppercase;
}

.hero h1 {
  margin: 0;
  font-size: clamp(26px, 4vw, 36px);
  letter-spacing: 2px;
}

.description {
  margin-top: 12px;
  color: rgba(242, 239, 233, 0.55);
  font-size: 14px;
  line-height: 1.8;
}

.player-note {
  margin: 8px 0 0;
  font-size: 12px;
  color: rgba(242, 239, 233, 0.35);
}

.unit-block {
  margin-top: 28px;
}

.unit-title {
  font-size: 13px;
  letter-spacing: 2px;
  color: #e8a75c;
  margin: 0 0 12px;
}

.q-card {
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 16px;
  margin-bottom: 10px;
  overflow: hidden;
}

.q-card.wrong {
  border-color: rgba(232, 144, 122, 0.3);
}

.q-summary {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  background: transparent;
  border: none;
  color: inherit;
  font-size: 13.5px;
  cursor: pointer;
  text-align: left;
}

.q-no {
  font-weight: 700;
  color: #e8a75c;
  min-width: 34px;
}

.q-result.right {
  color: #7fd8a4;
}

.q-result.wrong {
  color: #e8907a;
}

.q-answers {
  flex: 1;
  color: rgba(242, 239, 233, 0.55);
  font-size: 13px;
}

.mastery {
  font-size: 11.5px;
  border-radius: 999px;
  padding: 2px 10px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: rgba(242, 239, 233, 0.5);
}

.mastery.improved {
  border-color: rgba(126, 184, 232, 0.5);
  color: #7eb8e8;
}

.mastery.mastered {
  border-color: rgba(127, 216, 164, 0.5);
  color: #7fd8a4;
}

.mastery.reviewing {
  border-color: rgba(232, 167, 92, 0.5);
  color: #e8a75c;
}

.q-detail {
  padding: 6px 22px 22px;
  border-top: 1px solid rgba(255, 255, 255, 0.07);
}

.q-text {
  font-size: 15px;
  line-height: 1.7;
  margin: 14px 0 4px;
}

.q-text-zh {
  font-size: 13px;
  color: rgba(242, 239, 233, 0.5);
  margin: 0 0 6px;
}

.step-block {
  margin-top: 16px;
}

.step-title {
  font-size: 13px;
  color: rgba(242, 239, 233, 0.65);
  letter-spacing: 1px;
  margin: 0 0 10px;
}

.retry-options {
  display: flex;
  gap: 10px;
}

.retry-option {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.05);
  color: #f2efe9;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
}

.retry-option.picked {
  border-color: #e8a75c;
}

.retry-option.hit {
  background: rgba(127, 216, 164, 0.2);
  border-color: #7fd8a4;
  color: #7fd8a4;
}

.retry-option.miss {
  background: rgba(232, 144, 122, 0.15);
  border-color: #e8907a;
  color: #e8907a;
}

.retry-feedback {
  margin-top: 10px;
  font-size: 13px;
  color: #e8907a;
  line-height: 1.7;
}

.retry-feedback.ok {
  color: #7fd8a4;
}

.state-card {
  margin-top: 36px;
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
</style>
