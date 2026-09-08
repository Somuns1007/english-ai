<template>
  <div class="cp-page">
    <div class="cp-container">
      <div class="topbar">
        <button class="back-button" @click="$router.push('/listening')">
          ← 返回听力首页
        </button>
        <span v-if="bundle" class="material-tag">Continuous Practice · Pilot</span>
      </div>

      <div v-if="loading" class="state-card"><p>正在加载……</p></div>
      <div v-else-if="errorMessage" class="state-card error">
        <p>{{ errorMessage }}</p>
      </div>

      <template v-else-if="bundle && sessionId">
        <header class="head">
          <h1>{{ bundle.title }}</h1>
          <p class="sub">连续理解训练:先完整听,再回答,不重听单句。</p>
          <p v-if="state?.content_drifted" class="drift-note">
            提示:本材料内容在你开始后有更新,本次练习仍按你开始时的版本记录。
          </p>
        </header>

        <!-- 1. intro -->
        <section v-if="stage === 'intro'" class="card">
          <h2>开始之前</h2>
          <ul class="rules">
            <li>这段材料会<strong>完整连续播放</strong>,第一遍不能暂停、不能拖动。</li>
            <li>听完后回答 {{ bundle.checks.length }} 道整体理解题。</li>
            <li>答完后会有一次<strong>完整盲重播</strong>(不看文本、不看答案),再答一次首次答错的题。</li>
            <li>本练习只记录"首次抓住 / 重听后恢复"的数量观察,不评分、不进画像。</li>
          </ul>
          <div class="btn-row">
            <button class="primary" @click="enterPreview">先预览选项再听</button>
            <button class="ghost" @click="skipPreview">跳过预读,直接听</button>
          </div>
        </section>

        <!-- 2. option preview(只记行为, 无对错) -->
        <section v-else-if="stage === 'option_preview'" class="card">
          <h2>选项预读 <span class="hint-tag">不产生评分</span></h2>
          <p class="tip">听之前快速扫一遍每组选项,想一想:这组选项之间的区别主要是什么?</p>
          <div v-for="c in bundle.checks" :key="c.check_id" class="preview-block">
            <ul class="opt-list">
              <li v-for="o in c.options" :key="o.label">
                <b>{{ o.label }}.</b> {{ o.text }}
              </li>
            </ul>
            <div class="chips">
              <span class="chips-label">区别主要在:</span>
              <button
                v-for="f in FOCUS_TYPES" :key="f"
                class="chip"
                :class="{ on: focusMarks[c.check_id] === f }"
                @click="focusMarks[c.check_id] = f"
              >{{ f }}</button>
            </div>
          </div>
          <div class="btn-row">
            <button class="primary" @click="finishPreview">开始第一遍连续播放</button>
          </div>
        </section>

        <!-- 3. first pass -->
        <section v-else-if="stage === 'first_pass'" class="card">
          <h2>第一遍 · 连续播放</h2>
          <p v-if="interruptedOnce" class="warn-note">
            上一次播放被中断,中断的播放不计入记录;请重新完整播放一遍。
          </p>
          <p class="tip">播放中不能暂停或拖动。请一次性听完整段对话。</p>
          <RangePlayer
            :key="'pass-' + state?.pass_attempt_count"
            :src="audioSrc"
            :start-ms="bundle.audio.start_ms"
            :end-ms="bundle.audio.end_ms"
            play-label="开始播放"
            note="第一遍:不可暂停 / 不可拖动 / 不可重播"
            @pass-event="onPassEvent"
          />
        </section>

        <!-- 4. check round 1 -->
        <section v-else-if="stage === 'check_round_1'" class="card">
          <h2>整体理解检测</h2>
          <p class="tip">根据刚才完整听到的内容作答。提交前不能重听。</p>
          <div v-for="c in bundle.checks" :key="c.check_id" class="q-block">
            <p class="q-text">{{ c.question }}</p>
            <label
              v-for="o in c.options" :key="o.label"
              class="opt"
              :class="{ on: round1Answers[c.check_id] === o.label }"
            >
              <input
                type="radio"
                :name="c.check_id"
                :value="o.label"
                v-model="round1Answers[c.check_id]"
              />
              <b>{{ o.label }}.</b> {{ o.text }}
            </label>
          </div>
          <div class="btn-row">
            <button
              class="primary"
              :disabled="!round1Complete || submitting"
              @click="submitRound1"
            >提交</button>
          </div>
        </section>

        <!-- 5. blind full replay -->
        <section v-else-if="stage === 'blind_full_replay'" class="card">
          <h2>完整盲重播</h2>
          <p class="score-line">
            首次抓住:{{ state?.first_pass_score?.correct }}/{{ state?.first_pass_score?.total }}
          </p>
          <p class="tip">
            现在完整重听一遍这段材料。仍然不显示文本和答案;听完后会请你再答一次首次没抓住的题。
          </p>
          <RangePlayer
            :key="'replay-' + state?.replay_count"
            :src="audioSrc"
            :start-ms="bundle.audio.start_ms"
            :end-ms="bundle.audio.end_ms"
            play-label="开始完整重播"
            note="盲重播:不可暂停 / 不可拖动"
            @pass-event="onReplayEvent"
          />
        </section>

        <!-- 6. check round 2(recovery) -->
        <section v-else-if="stage === 'check_round_2'" class="card">
          <h2>再答一次</h2>
          <p class="tip">
            首次抓住:{{ state?.first_pass_score?.correct }}/{{ state?.first_pass_score?.total }}。
            以下是首次没抓住的题,根据刚才的完整重听再答一次。
          </p>
          <div v-for="c in state?.round2_checks || []" :key="c.check_id" class="q-block">
            <p class="q-text">{{ c.question }}</p>
            <label
              v-for="o in c.options" :key="o.label"
              class="opt"
              :class="{ on: round2Answers[c.check_id] === o.label }"
            >
              <input
                type="radio"
                :name="'r2-' + c.check_id"
                :value="o.label"
                v-model="round2Answers[c.check_id]"
              />
              <b>{{ o.label }}.</b> {{ o.text }}
            </label>
          </div>
          <div class="btn-row">
            <button
              class="primary"
              :disabled="!round2Complete || submitting"
              @click="submitRound2"
            >提交</button>
          </div>
        </section>

        <!-- 7. result final -->
        <section v-else-if="stage === 'result_final'" class="card">
          <h2>本次结果</h2>
          <p class="score-line big">{{ state?.result?.display }}</p>
          <p class="tip">
            这是一次观察性记录(首次抓住 / 完整重听后恢复),不构成能力评定,也不会进入能力画像。
          </p>
          <p class="tip dim">
            需要逐句定位、听写、错因分析和词汇采集的内容,将在后续的独立学习入口
            (Sentence Lab)开放。届时会基于原文单独提供,不在盲听 bundle 中携带
            transcript,以保证首听独立性。
          </p>

          <div class="btn-row">
            <button class="ghost" @click="$router.push('/listening')">返回听力首页</button>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import RangePlayer from '../../components/listening/RangePlayer.vue'
// NOTE: 采词面板(TranscriptHarvestPanel)已从盲听练习页移除。
// 盲听 bundle 不携带 transcript(首听独立性),采词将在后置的独立学习入口重新接线。
import {
  createV2PracticeSession,
  fetchV2PracticeBundle,
  fetchV2PracticeState,
  findV2PracticeSession,
  postV2PracticeEvents,
  submitV2PracticeRound1,
  submitV2PracticeRound2,
  type CpEvent,
  type V2PracticeBundle,
  type V2PracticeState
} from '../../services/listeningApi'
// 统一学生身份：使用 listeningEvents 的 getStudentId()（key: aq_listening_student_id）
// 旧版硬写 'anonymous'，多用户服务器下所有学生共用同一 student_id，已修正。
import { getStudentId } from '../../services/listeningEvents'

const route = useRoute()
const materialId = route.params.materialId as string
const studentId = computed(() => getStudentId())

const FOCUS_TYPES = ['人物', '动作行为', '原因', '态度', '时间地点']

const loading = ref(true)
const errorMessage = ref('')
const bundle = ref<V2PracticeBundle | null>(null)
const sessionId = ref('')
const state = ref<V2PracticeState | null>(null)
const stage = ref<V2PracticeState['stage']>('intro')

const focusMarks = ref<Record<string, string>>({})
const round1Answers = ref<Record<string, string>>({})
const round2Answers = ref<Record<string, string>>({})
const submitting = ref(false)
const interruptedOnce = ref(false)
let previewOpenedAt = 0

const audioSrc = computed(() => bundle.value?.audio.url || '')
const round1Complete = computed(
  () => Object.keys(round1Answers.value).length === (bundle.value?.checks.length || 0)
)
const round2Complete = computed(
  () =>
    (state.value?.round2_checks || []).length > 0 &&
    Object.keys(round2Answers.value).length === (state.value?.round2_checks || []).length
)

async function refreshState() {
  if (!sessionId.value) return
  state.value = await fetchV2PracticeState(sessionId.value)
  stage.value = state.value.stage
}

async function sendEvents(events: CpEvent[], keepalive = false) {
  if (!sessionId.value || !events.length) return
  const stamped = events.map(e => ({
    ...e,
    client_at: new Date().toISOString()
  }))
  await postV2PracticeEvents(sessionId.value, stamped, studentId.value, keepalive)
}

async function enterPreview() {
  await sendEvents([{ event_type: 'cp_preview_open', payload: {} }])
  previewOpenedAt = Date.now()
  stage.value = 'option_preview'
}

async function skipPreview() {
  await sendEvents([{ event_type: 'cp_preview_skip', payload: {} }])
  stage.value = 'first_pass'
}

async function finishPreview() {
  const events: CpEvent[] = Object.entries(focusMarks.value).map(([cid, f]) => ({
    event_type: 'cp_preview_mark',
    payload: { check_id: cid, focus_type: f }
  }))
  events.push({
    event_type: 'cp_preview_open',
    payload: { preview_duration_ms: Date.now() - previewOpenedAt }
  })
  // preview_open 重复上报只会保持 preview_used; duration 由 payload 记录
  await sendEvents(events)
  stage.value = 'first_pass'
}

async function onPassEvent(type: 'start' | 'progress' | 'end' | 'interrupted', payload: { position_ms: number }) {
  const keepalive = type === 'interrupted'
  await sendEvents([{ event_type: `cp_pass_${type}`, payload }], keepalive)
  if (type === 'end') {
    await refreshState()
  } else if (type === 'interrupted') {
    interruptedOnce.value = true
    await refreshState()
    stage.value = 'first_pass'
  }
}

async function onReplayEvent(type: 'start' | 'progress' | 'end' | 'interrupted', payload: { position_ms: number }) {
  const keepalive = type === 'interrupted'
  await sendEvents([{ event_type: `cp_replay_${type}`, payload }], keepalive)
  if (type === 'end') {
    await refreshState()
  }
}

async function submitRound1() {
  submitting.value = true
  try {
    await submitV2PracticeRound1(sessionId.value, round1Answers.value)
    await refreshState()
  } catch (e) {
    errorMessage.value = e instanceof Error ? e.message : '提交失败'
  } finally {
    submitting.value = false
  }
}

async function submitRound2() {
  submitting.value = true
  try {
    await submitV2PracticeRound2(sessionId.value, round2Answers.value)
    await refreshState()
  } catch (e) {
    errorMessage.value = e instanceof Error ? e.message : '提交失败'
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  try {
    bundle.value = await fetchV2PracticeBundle(materialId)
    const found = await findV2PracticeSession(materialId, studentId.value)
    if (found) {
      sessionId.value = found.session_id
    } else {
      const created = await createV2PracticeSession(materialId, studentId.value)
      sessionId.value = created.session_id
    }
    await refreshState()
    // 恢复到 first_pass 且上次未 valid: 提示中断重开
    if (stage.value === 'first_pass' && (state.value?.pass_attempt_count || 0) > 0) {
      interruptedOnce.value = true
    }
    if (stage.value === 'option_preview') {
      previewOpenedAt = Date.now()
    }
  } catch (e) {
    errorMessage.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.cp-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at 50% -10%, rgba(232, 167, 92, 0.12), transparent 34%),
    radial-gradient(circle at 90% 30%, rgba(94, 84, 140, 0.08), transparent 28%),
    #06070c;
  color: #f2efe9;
  padding: 32px 24px 90px;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.cp-container {
  width: 100%;
  max-width: 860px;
  margin: 0 auto;
}

.topbar {
  margin-bottom: 32px;
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

.material-tag {
  font-size: 12px;
  letter-spacing: 2px;
  color: rgba(242, 239, 233, 0.4);
}

.head h1 {
  margin: 0;
  font-size: 26px;
  letter-spacing: 1px;
}

.sub {
  color: rgba(242, 239, 233, 0.5);
  font-size: 13px;
  margin-top: 8px;
}

.drift-note {
  margin-top: 10px;
  font-size: 12px;
  color: #e8a75c;
}

.card {
  margin-top: 24px;
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 20px;
  padding: 28px;
}

.card h2 {
  margin: 0 0 14px;
  font-size: 19px;
}

.hint-tag {
  font-size: 11px;
  color: rgba(242, 239, 233, 0.45);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 999px;
  padding: 2px 10px;
  margin-left: 8px;
  vertical-align: middle;
}

.rules {
  margin: 0 0 8px;
  padding-left: 20px;
  color: rgba(242, 239, 233, 0.7);
  line-height: 2;
  font-size: 14px;
}

.tip {
  color: rgba(242, 239, 233, 0.55);
  font-size: 13px;
  line-height: 1.8;
  margin: 0 0 16px;
}

.tip.dim {
  color: rgba(242, 239, 233, 0.35);
}

.warn-note {
  color: #e8907a;
  font-size: 13px;
  margin: 0 0 12px;
}

.btn-row {
  margin-top: 20px;
  display: flex;
  gap: 14px;
}

.primary {
  border: none;
  border-radius: 12px;
  padding: 12px 26px;
  background: #e8a75c;
  color: #17120c;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
}

.primary:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.ghost {
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  padding: 12px 26px;
  background: transparent;
  color: rgba(242, 239, 233, 0.7);
  font-size: 14px;
  cursor: pointer;
}

.preview-block {
  border-top: 1px solid rgba(255, 255, 255, 0.07);
  padding: 16px 0;
}

.opt-list {
  margin: 0 0 10px;
  padding-left: 4px;
  list-style: none;
  color: rgba(242, 239, 233, 0.75);
  font-size: 14px;
  line-height: 1.9;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.chips-label {
  font-size: 12px;
  color: rgba(242, 239, 233, 0.45);
  margin-right: 4px;
}

.chip {
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 999px;
  background: transparent;
  color: rgba(242, 239, 233, 0.6);
  font-size: 12px;
  padding: 5px 14px;
  cursor: pointer;
}

.chip.on {
  border-color: #e8a75c;
  color: #e8a75c;
}

.q-block {
  border-top: 1px solid rgba(255, 255, 255, 0.07);
  padding: 18px 0;
}

.q-text {
  font-size: 15px;
  margin: 0 0 12px;
  line-height: 1.7;
}

.opt {
  display: block;
  padding: 10px 14px;
  margin: 6px 0;
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 12px;
  cursor: pointer;
  font-size: 14px;
  color: rgba(242, 239, 233, 0.75);
  line-height: 1.6;
}

.opt.on {
  border-color: #e8a75c;
  background: rgba(232, 167, 92, 0.08);
}

.opt input {
  margin-right: 8px;
  accent-color: #e8a75c;
}

.score-line {
  font-size: 18px;
  color: #e8a75c;
  font-weight: 600;
  margin: 0 0 14px;
}

.score-line.big {
  font-size: 24px;
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
