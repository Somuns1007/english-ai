<template>
  <div class="sb-page">
    <div class="sb-container">
      <div class="topbar">
        <button class="back-btn" @click="$router.push('/listening')">← 返回</button>
        <span class="page-tag">Stem Bank · Option Prediction</span>
      </div>

      <!-- Stats bar (after at least one prediction) -->
      <div v-if="stats && stats.total_predictions > 0" class="stats-bar">
        <span class="stat-item">共练习 {{ stats.total_predictions }} 次</span>
        <span class="stat-item">
          答题准确率
          <strong>{{ stats.answer_accuracy !== null ? pct(stats.answer_accuracy) : '—' }}</strong>
        </span>
        <div class="type-chips">
          <span
            v-for="(s, qt) in stats.type_accuracy_by_type"
            :key="qt"
            class="type-chip"
            :class="chipClass(s.accuracy)"
          >
            {{ typeLabel(qt) }}
            {{ s.accuracy !== null ? pct(s.accuracy) : '—' }}
          </span>
        </div>
      </div>

      <!-- Mode selector -->
      <div v-if="mode === 'menu'" class="menu-section">
        <h1 class="page-title">题干银行</h1>
        <p class="page-desc">
          Set 2 共 25 道题，分 6 种题型。练习流程：先判断题型 → 再选答案 → 查看结果。
        </p>

        <div class="filter-row">
          <span class="filter-label">题型筛选</span>
          <button
            v-for="qt in ['all', ...QUESTION_TYPES]"
            :key="qt"
            class="filter-btn"
            :class="{ on: filterType === qt }"
            @click="filterType = qt"
          >
            {{ qt === 'all' ? '全部' : typeLabel(qt) }}
          </button>
        </div>

        <div class="filter-row">
          <span class="filter-label">材料类型</span>
          <button
            v-for="ut in ['all', 'conversation', 'passage', 'lecture']"
            :key="ut"
            class="filter-btn"
            :class="{ on: filterUnit === ut }"
            @click="filterUnit = ut"
          >
            {{ ut === 'all' ? '全部' : unitLabel(ut) }}
          </button>
        </div>

        <div class="count-row">
          <span class="filter-label">每次练习题数</span>
          <button
            v-for="n in [3, 5, 10, 25]"
            :key="n"
            class="filter-btn"
            :class="{ on: sessionCount === n }"
            @click="sessionCount = n"
          >
            {{ n }}
          </button>
        </div>

        <div class="menu-actions">
          <button class="start-btn" :disabled="loading" @click="startSession">
            {{ loading ? '加载中……' : '开始练习' }}
          </button>
          <button class="browse-btn" @click="mode = 'browse'">浏览题干列表</button>
        </div>
        <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>
      </div>

      <!-- Browse mode: list all stems without correct answers -->
      <div v-else-if="mode === 'browse'" class="browse-section">
        <div class="browse-topbar">
          <button class="back-link" @click="mode = 'menu'">← 返回</button>
          <span>题干列表（{{ browseItems.length }} 题）</span>
        </div>
        <div v-if="loadingBrowse" class="loading-msg">加载中……</div>
        <div v-else class="browse-list">
          <div
            v-for="it in browseItems"
            :key="it.question_no"
            class="browse-row"
          >
            <span class="q-no">Q{{ it.question_no }}</span>
            <span class="q-type">{{ typeLabel(it.question_type) }}</span>
            <span class="q-unit">{{ unitLabel(it.unit_type) }}</span>
            <span class="q-stem">{{ it.stem_en }}</span>
          </div>
        </div>
      </div>

      <!-- Training mode -->
      <div v-else-if="mode === 'training'" class="training-section">
        <div class="training-topbar">
          <button class="back-link" @click="endSession">✕ 结束练习</button>
          <span>{{ currentIndex + 1 }} / {{ sessionItems.length }}</span>
        </div>

        <OptionPredictionTrainer
          v-if="currentIndex < sessionItems.length"
          :key="sessionItems[currentIndex].question_no"
          :item="sessionItems[currentIndex]"
          :student-id="studentId"
          @next="nextItem"
        />

        <!-- All done -->
        <div v-if="currentIndex >= sessionItems.length" class="done-card">
          <p class="done-title">本轮练习完成</p>
          <div class="done-actions">
            <button class="start-btn" @click="startSession">再来一轮</button>
            <button class="browse-btn" @click="mode = 'menu'">返回菜单</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import OptionPredictionTrainer, { type StemItem } from '../../components/listening/OptionPredictionTrainer.vue'
import { getStudentId } from '../../services/listeningEvents'

const studentId = getStudentId()

// ── Constants ─────────────────────────────────────────────────────────

const QUESTION_TYPES = [
  'main_idea', 'detail', 'suggestion',
  'cause_effect', 'inference', 'attitude',
] as const

const TYPE_LABELS: Record<string, string> = {
  main_idea:    '主旨题',
  detail:       '细节题',
  suggestion:   '建议题',
  cause_effect: '因果题',
  inference:    '推断题',
  attitude:     '态度题',
}

const UNIT_LABELS: Record<string, string> = {
  conversation: 'Conversation',
  passage:      'Passage',
  lecture:      'Lecture',
}

function typeLabel(qt: string) { return TYPE_LABELS[qt] ?? qt }
function unitLabel(ut: string) { return UNIT_LABELS[ut] ?? ut }
function pct(n: number) { return `${Math.round(n * 100)}%` }

function chipClass(acc: number | null) {
  if (acc === null) return 'chip-na'
  if (acc >= 0.8) return 'chip-good'
  if (acc >= 0.5) return 'chip-mid'
  return 'chip-bad'
}

// ── State ─────────────────────────────────────────────────────────────

type Mode = 'menu' | 'browse' | 'training'
const mode = ref<Mode>('menu')

const filterType = ref('all')
const filterUnit = ref('all')
const sessionCount = ref(5)
const loading = ref(false)
const loadingBrowse = ref(false)
const errorMsg = ref('')

const sessionItems = ref<StemItem[]>([])
const currentIndex = ref(0)
const browseItems = ref<StemItem[]>([])

interface Stats {
  total_predictions: number
  answer_accuracy: number | null
  type_accuracy_by_type: Record<string, { total: number; accuracy: number | null }>
}
const stats = ref<Stats | null>(null)

// ── Load stats on mount ────────────────────────────────────────────────

onMounted(async () => {
  await loadStats()
})

async function loadStats() {
  try {
    const res = await fetch(`/api/listening/stem-bank/stats?student_id=${studentId}`)
    if (res.ok) stats.value = (await res.json()).data
  } catch { /* non-critical */ }
}

// ── Browse ─────────────────────────────────────────────────────────────

watch(mode, async (m) => {
  if (m === 'browse' && !browseItems.value.length) {
    loadingBrowse.value = true
    try {
      const params = new URLSearchParams()
      if (filterType.value !== 'all') params.set('question_type', filterType.value)
      if (filterUnit.value !== 'all') params.set('unit_type', filterUnit.value)
      const res = await fetch(`/api/listening/stem-bank/stems?${params}`)
      if (res.ok) browseItems.value = (await res.json()).data
    } finally {
      loadingBrowse.value = false
    }
  }
})

// ── Training session ───────────────────────────────────────────────────

async function startSession() {
  loading.value = true
  errorMsg.value = ''
  try {
    const params = new URLSearchParams({ count: String(sessionCount.value) })
    if (filterType.value !== 'all') params.set('question_type', filterType.value)
    if (filterUnit.value !== 'all') params.set('unit_type', filterUnit.value)
    const res = await fetch(`/api/listening/stem-bank/session?${params}`)
    if (!res.ok) throw new Error(`fetch failed: ${res.status}`)
    const json = await res.json()
    sessionItems.value = json.data.items
    currentIndex.value = 0
    mode.value = 'training'
  } catch (e: unknown) {
    errorMsg.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

function nextItem() {
  currentIndex.value++
  if (currentIndex.value >= sessionItems.value.length) {
    // Session done — reload stats
    loadStats()
  }
}

function endSession() {
  mode.value = 'menu'
  loadStats()
}
</script>

<style scoped>
.sb-page { min-height: 100vh; padding: 0 16px 60px; }
.sb-container { max-width: 760px; margin: 0 auto; padding: 24px 0; }

.topbar {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 28px;
}
.back-btn {
  background: none; border: none;
  color: rgba(242,239,233,0.5); font-size: 14px; cursor: pointer; padding: 0;
}
.back-btn:hover { color: rgba(242,239,233,0.85); }
.page-tag {
  font-size: 11px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase;
  color: rgba(232,167,92,0.7); border: 1px solid rgba(232,167,92,0.2);
  border-radius: 20px; padding: 3px 10px;
}

/* stats bar */
.stats-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 12px;
  margin-bottom: 24px;
  font-size: 13px;
  color: rgba(242,239,233,0.6);
}
.stat-item strong { color: #e8a75c; }
.type-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-left: auto; }
.type-chip { font-size: 11px; padding: 2px 8px; border-radius: 12px; font-weight: 600; }
.chip-good { background: rgba(100,200,140,0.12); color: #64c88c; }
.chip-mid  { background: rgba(232,167,92,0.12); color: #e8a75c; }
.chip-bad  { background: rgba(232,100,90,0.12); color: rgba(232,130,120,0.9); }
.chip-na   { background: rgba(255,255,255,0.05); color: rgba(242,239,233,0.3); }

/* menu */
.page-title { font-size: 26px; font-weight: 700; color: rgba(242,239,233,0.92); margin: 0 0 8px; }
.page-desc { font-size: 14px; color: rgba(242,239,233,0.5); margin: 0 0 24px; line-height: 1.6; }
.filter-row, .count-row { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-bottom: 12px; }
.filter-label { font-size: 12px; color: rgba(242,239,233,0.35); width: 64px; flex-shrink: 0; }
.filter-btn {
  padding: 5px 12px; border-radius: 16px; font-size: 12px;
  border: 1px solid rgba(255,255,255,0.1); background: transparent;
  color: rgba(242,239,233,0.55); cursor: pointer; transition: all 0.15s;
}
.filter-btn.on { border-color: #e8a75c; background: rgba(232,167,92,0.1); color: #e8a75c; }
.menu-actions { display: flex; gap: 12px; margin-top: 24px; }
.start-btn {
  padding: 11px 26px; border-radius: 12px;
  border: 1px solid rgba(232,167,92,0.35); background: rgba(232,167,92,0.1);
  color: #e8a75c; font-size: 15px; font-weight: 600; cursor: pointer;
}
.start-btn:hover:not(:disabled) { background: rgba(232,167,92,0.2); }
.start-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.browse-btn {
  padding: 11px 22px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);
  background: transparent; color: rgba(242,239,233,0.55); font-size: 15px; cursor: pointer;
}
.error-msg { margin-top: 12px; font-size: 13px; color: rgba(232,100,90,0.8); }

/* browse */
.browse-section { }
.browse-topbar, .training-topbar {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 20px; font-size: 13px; color: rgba(242,239,233,0.45);
}
.back-link { background: none; border: none; color: rgba(242,239,233,0.5); cursor: pointer; font-size: 13px; }
.loading-msg { color: rgba(242,239,233,0.4); font-size: 14px; }
.browse-list { display: flex; flex-direction: column; gap: 6px; }
.browse-row {
  display: grid;
  grid-template-columns: 40px 72px 90px 1fr;
  gap: 10px;
  align-items: baseline;
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  font-size: 13px;
}
.q-no { font-weight: 700; color: rgba(232,167,92,0.8); }
.q-type { color: rgba(242,239,233,0.45); font-size: 12px; }
.q-unit { color: rgba(242,239,233,0.3); font-size: 11px; }
.q-stem { color: rgba(242,239,233,0.75); }

/* training */
.done-card { padding: 28px; text-align: center; }
.done-title { font-size: 18px; font-weight: 700; color: #64c88c; margin: 0 0 16px; }
.done-actions { display: flex; justify-content: center; gap: 12px; }
</style>
