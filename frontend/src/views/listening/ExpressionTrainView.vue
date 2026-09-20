<template>
  <div class="train-page">
    <div class="train-container">
      <div class="topbar">
        <button class="back-button" @click="$router.push('/listening/expressions')">
          ← 返回表达列表
        </button>
      </div>

      <div v-if="loading" class="state-card">
        <p>正在加载……</p>
      </div>

      <div v-else-if="errorMessage" class="state-card error">
        <p>{{ errorMessage }}</p>
        <button class="retry-button" @click="load">重试</button>
      </div>

      <template v-else-if="detail && currentScenario">
        <section class="hero">
          <p class="eyebrow">Expression Bridge</p>
          <h1>{{ detail.expression }}</h1>
          <p class="meaning">{{ detail.meaning }}</p>
          <p class="source">
            真题出处: {{ detail.source_exam_id }} · {{ detail.source_question_id?.split('_').pop() }}
            —— "{{ detail.source_sentence }}"
          </p>
        </section>

        <div class="scenario-nav">
          <button
            v-for="(s, i) in detail.scenarios"
            :key="s.scenario_id"
            class="scenario-tab"
            :class="{ active: i === scenarioIndex, done: s.last_attempt?.all_correct }"
            @click="switchScenario(i)"
          >
            场景 {{ i + 1 }} · {{ scenarioLabel(s.scenario) }}
          </button>
        </div>

        <section class="scenario-card">
          <div class="scenario-meta">
            <span class="tag">{{ scenarioLabel(currentScenario.scenario) }}</span>
            <span class="tag">{{ currentScenario.communicative_function }}</span>
            <span class="tag difficulty">{{ difficultyLabel(currentScenario.difficulty) }}</span>
            <span class="tag ai">AI 生成场景 · 待教师审核</span>
          </div>

          <!-- 第一步: 先听不看文本 -->
          <div class="listen-block">
            <p class="step-title">第一步 · 盲听(文本已隐藏)</p>
            <audio
              ref="audioEl"
              :src="scenarioAudioUrl(currentScenario.scenario_id, currentScenario.content_revision)"
              controls
              @play="onPlay"
            ></audio>
            <p class="listen-hint">
              已播放 {{ listenCount }} 次 · 合成语音({{ audioMeta?.voice_id || 'edge-tts' }})
            </p>
            <button
              v-if="!revealUsed && !submitted"
              class="giveup-button"
              @click="giveUpBlindListen"
            >
              实在听不懂, 放弃盲听看文本(会被记录)
            </button>
          </div>

          <!-- 放弃盲听后提前显示文本(目标表达已标出, 无答案) -->
          <div v-if="revealUsed && earlyReveal && !submitted" class="transcript-block early">
            <p class="step-title">文本(已放弃盲听, 已记录)</p>
            <p class="transcript" v-html="highlightedEarlyText"></p>
          </div>

          <!-- 第二步: 判断场景/含义/关键信息 -->
          <div class="questions-block">
            <p class="step-title">第二步 · 回答三个问题</p>
            <div
              v-for="key in questionKeys"
              :key="key"
              class="question"
            >
              <p class="question-text">
                <span class="q-label">{{ questionLabel(key) }}</span>
                {{ currentScenario.questions[key].question }}
              </p>
              <div class="options">
                <button
                  v-for="(text, label) in currentScenario.questions[key].options"
                  :key="label"
                  class="option"
                  :class="optionClass(key, String(label))"
                  :disabled="submitted"
                  @click="answers[key] = String(label)"
                >
                  <span class="option-label">{{ label }}</span>
                  <span>{{ text }}</span>
                </button>
              </div>
              <p v-if="submitted && result" class="verdict" :class="{ ok: result.correct[key] }">
                {{ result.correct[key] ? '✓ 正确' : `✗ 正确答案是 ${result.answers[key]}` }}
              </p>
            </div>

            <button
              v-if="!submitted"
              class="submit-button"
              :disabled="!allAnswered || submitting"
              @click="submit"
            >
              {{ submitting ? '提交中……' : '提交并揭示文本' }}
            </button>
          </div>

          <!-- 第三步: 揭示文本 + 标出目标表达 -->
          <div v-if="submitted && result" class="transcript-block">
            <p class="step-title">第三步 · 对照文本(目标表达已标出)</p>
            <p class="transcript" v-html="highlightedText"></p>
            <p class="target-note">
              目标表达: <strong>{{ result.target_expression }}</strong>
              —— {{ result.expression_meaning }}
            </p>
            <p v-if="result.related_expressions.length" class="related">
              同义表达: {{ result.related_expressions.join(' / ') }}
            </p>
            <p class="listen-hint">
              揭示后复听 {{ replayAfterReveal }} 次 · 看着文本再听一遍, 确认现在能听出来了
            </p>
            <div class="result-summary" :class="{ ok: result.correct.all }">
              {{ result.correct.all ? '三题全对, 迁移成功 ✓' : '还有判断失误, 建议复听后再看一遍文本' }}
            </div>
            <p class="evidence-line">
              本次证据强度: {{ result.evidence.strength }}({{ evidenceLevelLabel(result.evidence.level) }})
              · 审核权重 ×{{ verificationWeightText }}
              <span v-if="result.evidence.verification_level === 'pending_teacher'">
                —— 内容待教师审核, 仅作 provisional 证据
              </span>
            </p>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  fetchExpressionDetail,
  fetchScenarioAudioMeta,
  markExpressionReplay,
  revealScenarioEarly,
  scenarioAudioUrl,
  submitExpressionScenario,
  type AudioMeta,
  type EarlyReveal,
  type ExpressionDetail,
  type ExpressionSubmitResult
} from '../../services/listeningApi'
import { getStudentId } from '../../services/listeningEvents'

const route = useRoute()
const studentId = computed(() => getStudentId())

const detail = ref<ExpressionDetail | null>(null)
const loading = ref(true)
const errorMessage = ref('')

const scenarioIndex = ref(0)
const audioMeta = ref<AudioMeta | null>(null)

// 行为数据
const listenCount = ref(0)
const revealUsed = ref(false)
const replayAfterReveal = ref(0)
const firstPlayAt = ref<number | null>(null)

// 作答
const questionKeys = ['scene', 'meaning', 'key_info'] as const
type QuestionKey = (typeof questionKeys)[number]
const answers = ref<Record<QuestionKey, string>>({ scene: '', meaning: '', key_info: '' })
const submitted = ref(false)
const submitting = ref(false)
const result = ref<ExpressionSubmitResult | null>(null)

const currentScenario = computed(
  () => detail.value?.scenarios[scenarioIndex.value] ?? null
)

const allAnswered = computed(() =>
  questionKeys.every((k) => answers.value[k])
)

const highlightedText = computed(() => {
  if (!result.value) return ''
  return highlight(result.value.text, result.value.target_surface)
})

const highlightedEarlyText = computed(() => {
  if (!earlyReveal.value) return ''
  return highlight(earlyReveal.value.text, earlyReveal.value.target_surface)
})

// 放弃盲听后由服务端揭示的文本(不含答案)
const earlyReveal = ref<EarlyReveal | null>(null)

function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function highlight(text: string, surface: string): string {
  const escaped = escapeHtml(text)
  const idx = escaped.indexOf(escapeHtml(surface))
  if (idx === -1) return escaped.replace(/\n/g, '<br>')
  const s = escapeHtml(surface)
  return (
    escaped.slice(0, idx).replace(/\n/g, '<br>') +
    `<mark>${s}</mark>` +
    escaped.slice(idx + s.length).replace(/\n/g, '<br>')
  )
}

function scenarioLabel(key: string): string {
  const labels: Record<string, string> = {
    hotel: '酒店', airport: '机场', restaurant: '餐厅', phone_restaurant: '电话订位',
    hospital: '医院', pharmacy: '药房', workplace: '职场', campus: '校园',
    phone: '电话', social: '社交', housing: '住宿', travel_agency: '旅行社',
    volunteer_event: '志愿活动', health: '健康', job_interview: '面试'
  }
  return labels[key] || key
}

function difficultyLabel(d: string): string {
  return { easy: '简单', medium: '中等', hard: '较难' }[d] || d
}

function questionLabel(key: QuestionKey): string {
  return { scene: '场景', meaning: '含义', key_info: '关键信息' }[key]
}

function evidenceLevelLabel(level: string): string {
  return { none: '无', weak: '弱', medium: '中', strong: '强' }[level] || level
}

const verificationWeightText = computed(() => {
  const v = result.value?.evidence.verification_level
  return v === 'approved' ? '1.0(已审核)' : '0.5(待审核)'
})

function optionClass(key: QuestionKey, label: string) {
  const cls: Record<string, boolean> = { selected: answers.value[key] === label }
  if (submitted.value && result.value) {
    cls['is-answer'] = result.value.answers[key] === label
    cls['is-wrong'] = answers.value[key] === label && result.value.answers[key] !== label
  }
  return cls
}

function onPlay() {
  if (firstPlayAt.value === null) firstPlayAt.value = Date.now()
  if (!submitted.value) {
    listenCount.value += 1
  } else if (result.value) {
    replayAfterReveal.value += 1
    markExpressionReplay(result.value.attempt_id).catch(() => {})
  }
}

async function giveUpBlindListen() {
  if (!currentScenario.value || revealUsed.value) return
  try {
    earlyReveal.value = await revealScenarioEarly(currentScenario.value.scenario_id, currentScenario.value.content_revision)
    revealUsed.value = true
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '文本揭示失败, 请重试'
  }
}

async function submit() {
  if (!currentScenario.value || submitting.value) return
  submitting.value = true
  try {
    const durationMs = firstPlayAt.value ? Date.now() - firstPlayAt.value : 0
    result.value = await submitExpressionScenario(currentScenario.value.scenario_id, {
      student_id: studentId.value,
      content_revision: currentScenario.value.content_revision,
      answers: { ...answers.value },
      listen_count_before_submit: listenCount.value,
      reveal_used: revealUsed.value,
      duration_ms: durationMs
    })
    submitted.value = true
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '提交失败'
  } finally {
    submitting.value = false
  }
}

async function switchScenario(i: number) {
  scenarioIndex.value = i
  listenCount.value = 0
  revealUsed.value = false
  replayAfterReveal.value = 0
  firstPlayAt.value = null
  answers.value = { scene: '', meaning: '', key_info: '' }
  submitted.value = false
  result.value = null
  earlyReveal.value = null
  const s = detail.value?.scenarios[i]
  if (s?.has_audio) {
    audioMeta.value = await fetchScenarioAudioMeta(s.scenario_id).catch(() => null)
  } else {
    audioMeta.value = null
  }
}

async function load() {
  loading.value = true
  errorMessage.value = ''
  try {
    const id = String(route.params.expressionId)
    detail.value = await fetchExpressionDetail(id, studentId.value)
    await switchScenario(0)
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : '加载失败, 请稍后重试。'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.train-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at 50% -10%, rgba(232, 167, 92, 0.12), transparent 34%),
    #06070c;
  color: #f2efe9;
  padding: 32px 24px 90px;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.train-container {
  width: 100%;
  max-width: 820px;
  margin: 0 auto;
}

.topbar {
  margin-bottom: 40px;
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
  font-size: clamp(28px, 4vw, 40px);
  font-weight: 700;
}

.meaning {
  margin: 8px 0 0;
  color: rgba(242, 239, 233, 0.7);
}

.source {
  margin: 12px 0 0;
  font-size: 13px;
  color: rgba(242, 239, 233, 0.45);
  line-height: 1.7;
}

.scenario-nav {
  display: flex;
  gap: 10px;
  margin-top: 28px;
  flex-wrap: wrap;
}

.scenario-tab {
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: transparent;
  color: rgba(242, 239, 233, 0.6);
  border-radius: 999px;
  padding: 8px 16px;
  font-size: 13px;
  cursor: pointer;
}

.scenario-tab.active {
  border-color: #e8a75c;
  color: #e8a75c;
}

.scenario-tab.done {
  border-color: rgba(127, 216, 164, 0.4);
}

.scenario-card {
  margin-top: 24px;
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 20px;
  padding: 28px;
}

.scenario-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tag {
  font-size: 12px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 999px;
  padding: 3px 10px;
  color: rgba(242, 239, 233, 0.6);
}

.tag.difficulty {
  color: #e8a75c;
  border-color: rgba(232, 167, 92, 0.35);
}

.tag.ai {
  color: rgba(242, 239, 233, 0.35);
  border-style: dashed;
}

.step-title {
  margin: 24px 0 12px;
  font-size: 13px;
  letter-spacing: 2px;
  color: #e8a75c;
}

.listen-block audio {
  width: 100%;
}

.listen-hint {
  margin-top: 8px;
  font-size: 12px;
  color: rgba(242, 239, 233, 0.4);
}

.giveup-button {
  margin-top: 12px;
  border: 1px dashed rgba(232, 144, 122, 0.5);
  background: transparent;
  color: rgba(232, 144, 122, 0.85);
  border-radius: 10px;
  padding: 8px 14px;
  font-size: 12px;
  cursor: pointer;
}

.question {
  margin-top: 20px;
}

.question-text {
  margin: 0 0 10px;
  font-size: 15px;
  line-height: 1.7;
}

.q-label {
  display: inline-block;
  margin-right: 8px;
  font-size: 11px;
  color: #e8a75c;
  border: 1px solid rgba(232, 167, 92, 0.3);
  border-radius: 6px;
  padding: 1px 6px;
  vertical-align: 2px;
}

.options {
  display: grid;
  gap: 8px;
}

.option {
  display: flex;
  gap: 10px;
  align-items: baseline;
  text-align: left;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.03);
  color: rgba(242, 239, 233, 0.8);
  border-radius: 12px;
  padding: 10px 14px;
  font-size: 14px;
  cursor: pointer;
  transition: border-color 0.2s;
}

.option:hover:not(:disabled) {
  border-color: rgba(232, 167, 92, 0.4);
}

.option.selected {
  border-color: #e8a75c;
  background: rgba(232, 167, 92, 0.08);
}

.option.is-answer {
  border-color: #7fd8a4;
  background: rgba(127, 216, 164, 0.08);
}

.option.is-wrong {
  border-color: #e8907a;
  background: rgba(232, 144, 122, 0.08);
}

.option:disabled {
  cursor: default;
}

.option-label {
  font-weight: 600;
  color: #e8a75c;
}

.verdict {
  margin: 8px 0 0;
  font-size: 13px;
  color: #e8907a;
}

.verdict.ok {
  color: #7fd8a4;
}

.submit-button {
  margin-top: 24px;
  width: 100%;
  border: none;
  border-radius: 12px;
  padding: 14px;
  background: #e8a75c;
  color: #17120c;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
}

.submit-button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.transcript-block {
  margin-top: 8px;
}

.transcript {
  background: rgba(255, 255, 255, 0.04);
  border-radius: 12px;
  padding: 16px;
  font-size: 14px;
  line-height: 1.9;
  color: rgba(242, 239, 233, 0.85);
}

.transcript :deep(mark) {
  background: rgba(232, 167, 92, 0.35);
  color: #ffd9a8;
  border-radius: 4px;
  padding: 0 3px;
}

.target-note {
  margin: 12px 0 0;
  font-size: 14px;
}

.target-note strong {
  color: #e8a75c;
}

.related {
  margin: 6px 0 0;
  font-size: 13px;
  color: rgba(242, 239, 233, 0.55);
}

.result-summary {
  margin-top: 16px;
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 14px;
  background: rgba(232, 144, 122, 0.12);
  color: #e8907a;
}

.result-summary.ok {
  background: rgba(127, 216, 164, 0.12);
  color: #7fd8a4;
}

.evidence-line {
  margin-top: 10px;
  font-size: 12px;
  color: rgba(242, 239, 233, 0.45);
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
</style>
