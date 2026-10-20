<template>
  <div class="lex-view">
    <PlanetCanvas planet="jupiter" />
    <p><RouterLink to="/listening/learning">我的生词本和逐句精听 →</RouterLink></p>
    <!-- ── 加载中 ── -->
    <div v-if="stage === 'loading'" class="center-msg">加载中…</div>

    <!-- ── 错误 ── -->
    <div v-else-if="stage === 'error'" class="center-msg err">
      {{ errorMsg }}
      <button class="retry-btn" @click="init">重试</button>
    </div>

    <!-- ── 入口测试（Phase 0 尚未开始）── -->
    <template v-else-if="stage === 'entry_test'">
      <div class="section-head">
        <h2>词汇小测试</h2>
        <p class="sub">共 {{ entryItems.length }} 题 · 还剩 {{ entryTimeLeft }} 秒</p>
      </div>
      <div class="progress-bar-wrap">
        <div class="progress-bar" :style="{ width: entryProgressPct + '%' }" />
      </div>
      <LexHearIdentify
        v-if="entryItems.length && entryIdx < entryItems.length"
        :item="entryItems[entryIdx]"
        :distractors="entryDistractors"
        :auto-play="true"
        @done="onEntryItemDone"
      />
      <div v-if="entryIdx >= entryItems.length" class="center-msg">提交中…</div>
    </template>

    <!-- ── 入口测试结果 ── -->
    <template v-else-if="stage === 'entry_result'">
      <div class="result-card">
        <div class="result-icon">{{ phase0Status?.phase0_active ? '📖' : '✅' }}</div>
        <div class="result-score">认识的词 {{ Math.round((entryScore ?? 0) * 100) }}%</div>
        <p class="result-note">
          {{ phase0Status?.phase0_active
            ? '建议先每天花 15 分钟练基础词汇'
            : '基础词汇没问题，可以开始做四六级听力题' }}
        </p>
        <button class="next-btn" @click="startSession">开始今日词汇</button>
      </div>
    </template>

    <!-- ── 词汇每日会话 ── -->
    <template v-else-if="stage === 'session'">
      <div class="section-head">
        <div class="head-row">
          <h2>听单词</h2>
          <span v-if="phase0Status?.phase0_active" class="phase0-badge">基础词汇阶段</span>
        </div>
        <div class="stats-row">
          <span>今日进度：{{ sessionDone }}/{{ sessionItems.length }} 词</span>
          <span class="time-stat">已用时 {{ elapsedMin }} 分钟 / {{ dailyCap }} 分钟上限</span>
        </div>
      </div>

      <!-- 进度条 -->
      <div class="progress-bar-wrap">
        <div class="progress-bar" :style="{ width: sessionProgressPct + '%' }" />
      </div>

      <!-- 时间封顶警告 -->
      <div v-if="timeCapped" class="cap-warn">
        今日词汇时间（{{ dailyCap }} 分钟）已到，明天继续 📅
      </div>

      <!-- 任务组件（三选一） -->
      <template v-else-if="currentItem">
        <LexHearIdentify
          v-if="currentTaskType === 'hear_identify'"
          :item="currentItem"
          :distractors="currentDistractors"
          :auto-play="true"
          @done="onSessionItemDone"
        />
        <LexMicroDictation
          v-else-if="currentTaskType === 'micro_dictation'"
          :item="currentItem"
          :auto-play="true"
          @done="onSessionItemDone"
        />
        <LexSpeedLadder
          v-else-if="currentTaskType === 'speed_ladder'"
          :item="currentItem"
          :distractors="currentDistractors.slice(0, 2)"
          @done="onSessionItemDone"
        />
      </template>

      <!-- 本轮完成 -->
      <div v-else-if="sessionDone >= sessionItems.length" class="result-card">
        <div class="result-icon">🎉</div>
        <div class="result-score">本轮完成</div>
        <p class="result-note">
          已处理 {{ sessionItems.length }} 个词条 ·
          听出 {{ sessionCorrect }} 个
        </p>
        <!-- 不展示能力结论文案 -->
        <button class="next-btn" @click="init">刷新下一轮</button>
      </div>
    </template>

    <!-- ── Phase 0 强制退出提示 ── -->
    <template v-else-if="stage === 'forced_exit'">
      <div class="result-card">
        <div class="result-icon">⏰</div>
        <p class="result-note">基础词汇阶段（{{ phase0Status?.cap_days }} 天）已结束，接下来正常练习就行。</p>
        <button class="next-btn" @click="startSession">今日词汇</button>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { LexItem, Phase0Status, LexTaskType } from '../../types/listening'
import {
  fetchPhase0Status,
  fetchEntryTestItems,
  submitEntryTestResults,
  fetchLexSession,
  recordLexAttempt
} from '../../services/listeningApi'
import LexHearIdentify   from '../../components/listening/LexHearIdentify.vue'
import LexMicroDictation from '../../components/listening/LexMicroDictation.vue'
import LexSpeedLadder    from '../../components/listening/LexSpeedLadder.vue'
import PlanetCanvas from '../../components/PlanetCanvas.vue'
// 统一学生身份：使用 listeningEvents 的 getStudentId()（key: aq_listening_student_id）
// 旧版用 'aq_student_id'，与事件采集/V2.2/StemBank 的 student_id 不一致，已修正。
import { getStudentId } from '../../services/listeningEvents'

const studentId = computed(() => getStudentId())

// ── Stage 状态机 ──────────────────────────────────────────────────────
type Stage = 'loading' | 'error' | 'entry_test' | 'entry_result' | 'session' | 'forced_exit'
const stage    = ref<Stage>('loading')
const errorMsg = ref('')

// ── Phase 0 ──────────────────────────────────────────────────────────
const phase0Status = ref<Phase0Status | null>(null)

// ── 入口测试 ──────────────────────────────────────────────────────────
const entryItems         = ref<LexItem[]>([])
const entryIdx           = ref(0)
const entryResults       = ref<{ item_id: string; is_correct: boolean }[]>([])
const entryScore         = ref<number | null>(null)
const entryTimerInterval = ref<ReturnType<typeof setInterval> | null>(null)
const entryTimeLeft      = ref(300)   // 5 分钟

const entryProgressPct = computed(() =>
  entryItems.value.length ? (entryIdx.value / entryItems.value.length) * 100 : 0
)
const entryDistractors = computed<LexItem[]>(() => {
  const others = entryItems.value.filter((_, i) => i !== entryIdx.value)
  return shuffle(others).slice(0, 3)
})

// ── 每日会话 ──────────────────────────────────────────────────────────
const sessionItems   = ref<LexItem[]>([])
const sessionIdx     = ref(0)
const sessionDone    = ref(0)
const sessionCorrect = ref(0)
const dailyCap       = ref(10)

// 每日时间计时
const sessionStartMs = ref(0)
const elapsedMin     = ref(0)
let   elapsedTimer: ReturnType<typeof setInterval> | null = null
const timeCapped = computed(() =>
  elapsedMin.value >= dailyCap.value && dailyCap.value > 0
)

const sessionProgressPct = computed(() =>
  sessionItems.value.length ? (sessionDone.value / sessionItems.value.length) * 100 : 0
)

const currentItem = computed<LexItem | null>(() =>
  sessionIdx.value < sessionItems.value.length ? sessionItems.value[sessionIdx.value] : null
)
const currentDistractors = computed<LexItem[]>(() => {
  if (!currentItem.value) return []
  const others = sessionItems.value.filter((_, i) => i !== sessionIdx.value)
  return shuffle(others).slice(0, 3)
})
const currentTaskType = computed<LexTaskType>(() =>
  pickTaskType(currentItem.value)
)

// ── 工具函数 ──────────────────────────────────────────────────────────
function shuffle<T>(arr: T[]): T[] {
  const a = [...arr]
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]]
  }
  return a
}

// 根据词条选择任务类型：L1无gloss只做hear_identify，其余轮转
const taskRotation: LexTaskType[] = ['hear_identify', 'micro_dictation', 'speed_ladder']
function pickTaskType(item: LexItem | null): LexTaskType {
  if (!item) return 'hear_identify'
  if (!item.gloss) return 'hear_identify'   // L1 无释义 → 只能听辨
  const idx = Math.floor(Math.random() * taskRotation.length)
  return taskRotation[idx]
}

// ── 初始化 ────────────────────────────────────────────────────────────
async function init() {
  stage.value = 'loading'
  try {
    const status = await fetchPhase0Status(studentId.value)
    phase0Status.value = status

    if (status.status === 'not_started') {
      await loadEntryTest()
    } else if (status.status === 'forced_exit') {
      stage.value = 'forced_exit'
    } else {
      // active / completed — 直接进今日会话
      await loadSession()
    }
  } catch (e: any) {
    errorMsg.value = e?.message || '加载失败'
    stage.value = 'error'
  }
}

// ── 入口测试 ──────────────────────────────────────────────────────────
async function loadEntryTest() {
  const data = await fetchEntryTestItems(studentId.value)
  entryItems.value   = data.items
  entryIdx.value     = 0
  entryResults.value = []
  entryTimeLeft.value = data.time_limit_minutes * 60

  // 倒计时
  entryTimerInterval.value = setInterval(() => {
    entryTimeLeft.value = Math.max(0, entryTimeLeft.value - 1)
    if (entryTimeLeft.value <= 0) finishEntryTest()
  }, 1000)

  stage.value = 'entry_test'
}

function onEntryItemDone(payload: { is_correct: boolean }) {
  if (!entryItems.value[entryIdx.value]) return
  entryResults.value.push({
    item_id: entryItems.value[entryIdx.value].item_id,
    is_correct: payload.is_correct
  })
  entryIdx.value++
  if (entryIdx.value >= entryItems.value.length) finishEntryTest()
}

async function finishEntryTest() {
  clearInterval(entryTimerInterval.value!)
  if (entryResults.value.length === 0) { await loadSession(); return }
  try {
    const res = await submitEntryTestResults(studentId.value, entryResults.value)
    entryScore.value  = res.entry_score
    phase0Status.value = await fetchPhase0Status(studentId.value)
    stage.value = 'entry_result'
  } catch {
    await loadSession()   // 提交失败降级直接进词汇
  }
}

// ── 每日会话 ──────────────────────────────────────────────────────────
async function loadSession() {
  const data = await fetchLexSession(studentId.value)
  const all  = [...data.due_review, ...data.new_items]
  sessionItems.value   = shuffle(all)
  sessionIdx.value     = 0
  sessionDone.value    = 0
  sessionCorrect.value = 0
  dailyCap.value       = data.daily_minutes_cap

  // 启动计时
  sessionStartMs.value = Date.now()
  elapsedTimer = setInterval(() => {
    elapsedMin.value = Math.round((Date.now() - sessionStartMs.value) / 60000 * 10) / 10
  }, 5000)

  stage.value = 'session'
}

async function startSession() {
  stage.value = 'loading'
  try { await loadSession() }
  catch (e: any) { errorMsg.value = e?.message || '加载失败'; stage.value = 'error' }
}

async function onSessionItemDone(payload: { is_correct: boolean }) {
  const item = currentItem.value
  if (!item) return
  sessionDone.value++
  if (payload.is_correct) sessionCorrect.value++

  // 上报（fire-and-forget，不阻塞 UI）
  recordLexAttempt(studentId.value, item.item_id, currentTaskType.value, payload.is_correct)
    .catch(() => {/* 静默失败 */})

  sessionIdx.value++
}

// ── 生命周期 ──────────────────────────────────────────────────────────
onMounted(init)
onUnmounted(() => {
  clearInterval(entryTimerInterval.value!)
  clearInterval(elapsedTimer!)
})
</script>

<style scoped>
/* ============================================================
   木星 · 聆听巨行星 —— 听后词汇
   与 ListeningLearningView 同一颗行星：横向云带 + 大红斑余晖。
   语义色保留（警告=锈琥珀，错误=红），只重写基础视觉层。
   ============================================================ */
.lex-view {
  --jup-ink: #f2ede3;
  --jup-muted: rgba(242, 237, 227, .62);
  --jup-faint: rgba(242, 237, 227, .42);
  --jup-accent: #e2ac6e;
  --jup-rust: #d4673a;
  --jup-border: rgba(226, 172, 110, .16);

  position: relative;
  z-index: 0;
  max-width: 560px;
  margin: 0 auto;
  padding: 32px 16px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-height: 100vh;
  color: var(--jup-ink);
  color-scheme: dark;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}
.lex-view, .lex-view * { box-sizing: border-box; }

/* 木星夜空由 <PlanetCanvas planet="jupiter"> 实时绘制：
   交替喷流云带 + 大红斑涡旋 + 极光影帘 */

a {
  color: var(--jup-accent);
  text-decoration: none;
  transition: text-shadow .25s ease-out;
}
a:hover { text-shadow: 0 0 14px rgba(226, 172, 110, .4); }

.center-msg {
  text-align: center;
  color: var(--jup-faint);
  padding: 60px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}
.center-msg.err { color: #e0705f; }

.retry-btn, .next-btn {
  background: rgba(226, 172, 110, .10);
  border: 1px solid rgba(226, 172, 110, .35);
  color: var(--jup-accent);
  border-radius: 10px;
  padding: 10px 24px;
  font-size: 14px;
  font: inherit;
  cursor: pointer;
  transition: border-color .25s ease-out, box-shadow .25s ease-out, background .25s ease-out;
}
.retry-btn:hover, .next-btn:hover {
  background: rgba(226, 172, 110, .18);
  border-color: rgba(226, 172, 110, .55);
  box-shadow: 0 0 20px -6px rgba(226, 172, 110, .4);
}
button:focus-visible, a:focus-visible {
  outline: 2px solid var(--jup-accent);
  outline-offset: 3px;
}

/* 区块标题 */
.section-head { display: flex; flex-direction: column; gap: 6px; }
.head-row { display: flex; align-items: center; gap: 10px; }
.section-head h2 { margin: 0; font-size: 20px; font-weight: 600; color: var(--jup-ink); }
.sub { margin: 0; font-size: 13px; color: var(--jup-faint); }
.stats-row {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: var(--jup-muted);
}
.time-stat { color: var(--jup-faint); }

/* Phase 0 徽章：语义=进行中，用锈琥珀 */
.phase0-badge {
  background: rgba(212, 103, 58, .14);
  border: 1px solid rgba(212, 103, 58, .4);
  color: #eda06c;
  border-radius: 6px;
  font-size: 11px;
  padding: 2px 8px;
}

/* 进度条：云带渐层 */
.progress-bar-wrap {
  width: 100%;
  height: 4px;
  background: rgba(255, 235, 205, .08);
  border-radius: 2px;
  overflow: hidden;
}
.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, var(--jup-accent), var(--jup-rust));
  border-radius: 2px;
  transition: width .4s ease;
}

/* 时间封顶警告：保留琥珀语义 */
.cap-warn {
  background: rgba(212, 103, 58, .10);
  border: 1px solid rgba(212, 103, 58, .3);
  color: #eda06c;
  border-radius: 12px;
  padding: 16px 20px;
  font-size: 14px;
  text-align: center;
}

/* 结果卡片：暖棕玻璃 */
.result-card {
  background: rgba(30, 20, 14, .5);
  border: 1px solid var(--jup-border);
  border-radius: 18px;
  padding: 36px 26px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  text-align: center;
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  box-shadow: inset 0 1px 0 rgba(255, 226, 190, .06);
}
.result-icon  { font-size: 42px; }
.result-score { font-size: 22px; font-weight: 700; color: var(--jup-ink); }
.result-note  { margin: 0; font-size: 14px; color: var(--jup-muted); max-width: 300px; }

@media (prefers-reduced-motion: reduce) {
  .lex-view *, .lex-view *::before, .lex-view *::after {
    animation-duration: .01ms !important;
    transition-duration: .01ms !important;
  }
}
</style>
