<template>
  <!--
    Work Order H — 学生仪表盘

    Copy 规范：所有文案只呈现事实数字与状态，禁止 ability 结论：
      ❌ "你已掌握"、"能力提升"、"尚未达标"
      ✅ "已练习 N 次"、"覆盖率 X%（阈值 70%）"、"近 5 次正确率 Y%"
  -->
  <div class="db-page">
    <div class="db-container">

      <div class="topbar">
        <button class="back-btn" @click="$router.push('/listening')">← 返回听力首页</button>
        <span class="page-tag">My Dashboard</span>
        <button class="refresh-btn" :disabled="loading" @click="load">
          {{ loading ? '…' : '↻ 刷新' }}
        </button>
      </div>

      <div v-if="loading && !data" class="state-card">正在加载……</div>
      <div v-else-if="err" class="state-card error">{{ err }}</div>

      <template v-else-if="data">

        <!-- ① Phase 0 状态卡 -->
        <section class="db-card phase0-card" v-if="data.phase0.status !== 'not_started'">
          <div class="card-header">
            <span class="card-title">词汇覆盖率 Phase</span>
            <span class="status-chip" :class="phase0ChipClass">{{ phase0Label }}</span>
          </div>

          <!-- Coverage bar -->
          <div v-if="data.phase0.entry_score !== null" class="cov-wrap">
            <div class="cov-bar-track">
              <div class="cov-bar-fill" :style="{ width: covPct + '%' }"></div>
              <div class="cov-threshold" :style="{ left: thresholdPct + '%' }"></div>
            </div>
            <div class="cov-labels">
              <span class="cov-num">覆盖率 {{ covPct }}%</span>
              <span class="cov-thresh">阈值 {{ thresholdPct }}%</span>
            </div>
          </div>

          <!-- Days remaining (only if active) -->
          <div v-if="data.phase0.phase0_active && data.phase0.started_at" class="days-row">
            <span class="days-label">已进行</span>
            <strong>{{ daysActive }} 天</strong>
            <span class="days-label">· 上限</span>
            <strong>{{ data.phase0.cap_days }} 天</strong>
            <div class="days-bar-track">
              <div class="days-bar-fill" :style="{ width: daysPct + '%' }"></div>
            </div>
          </div>

          <!-- Gate status -->
          <div class="gate-row">
            <span class="gate-icon" :class="data.phase0.exam_practice_allowed ? 'open' : 'closed'">
              {{ data.phase0.exam_practice_allowed ? '✓' : '✕' }}
            </span>
            <span class="gate-text">
              {{ data.phase0.exam_practice_allowed
                ? '题目练习已开放（单元练习 / 全真 / 节奏模拟）'
                : '题目练习待开放（词汇 Phase 进行中）' }}
            </span>
          </div>
        </section>

        <!-- ② 今日词汇卡 -->
        <section class="db-card vocab-card">
          <div class="card-header">
            <span class="card-title">今日词汇</span>
            <router-link to="/listening/lexicon" class="card-action">进入训练 →</router-link>
          </div>
          <div class="vocab-stats">
            <div class="vocab-stat">
              <span class="vs-num">{{ data.vocab.due_count }}</span>
              <span class="vs-label">待复习</span>
            </div>
            <div class="vocab-stat">
              <span class="vs-num">{{ data.vocab.total_in_srs }}</span>
              <span class="vs-label">SRS 队列</span>
            </div>
            <div class="vocab-stat">
              <span class="vs-num">{{ data.vocab.total_lex_items }}</span>
              <span class="vs-label">词库总量</span>
            </div>
            <div class="vocab-stat">
              <span class="vs-num">{{ data.vocab.daily_minutes_cap }}</span>
              <span class="vs-label">分钟/日</span>
            </div>
          </div>
          <!-- SRS progress bar -->
          <div class="srs-bar-wrap">
            <div class="srs-bar-track">
              <div
                class="srs-bar-fill"
                :style="{ width: srsProgressPct + '%' }"
              ></div>
            </div>
            <span class="srs-bar-label">
              已进入 SRS {{ data.vocab.total_in_srs }} / {{ data.vocab.total_lex_items }} 词
            </span>
          </div>
        </section>

        <!-- ③ 快捷入口 -->
        <section class="shortcuts">
          <router-link
            v-for="s in shortcuts"
            :key="s.to"
            :to="s.to"
            class="shortcut-btn"
            :class="{ disabled: s.requiresExam && !data.phase0.exam_practice_allowed }"
          >
            <span class="sc-icon">{{ s.icon }}</span>
            <span class="sc-label">{{ s.label }}</span>
            <span v-if="s.requiresExam && !data.phase0.exam_practice_allowed" class="sc-lock">🔒</span>
          </router-link>
        </section>

        <!-- ④ 题型预测统计 -->
        <section class="db-card stem-card">
          <div class="card-header">
            <span class="card-title">题型预测准确率</span>
            <router-link to="/listening/stem-bank" class="card-action">去练习 →</router-link>
          </div>
          <p v-if="data.stem_bank.total_predictions === 0" class="no-data-msg">
            暂无记录。前往题干银行开始练习后显示。
          </p>
          <template v-else>
            <p class="stem-summary">
              共预测 {{ data.stem_bank.total_predictions }} 次 ·
              答题准确率
              <strong>{{ data.stem_bank.answer_accuracy !== null ? pct(data.stem_bank.answer_accuracy) : '—' }}</strong>
            </p>
            <div class="type-bars">
              <div
                v-for="(s, qt) in data.stem_bank.type_accuracy_by_type"
                :key="qt"
                class="type-bar-row"
                v-show="s.total > 0"
              >
                <span class="tb-label">{{ typeLabel(qt) }}</span>
                <div class="tb-track">
                  <div
                    class="tb-fill"
                    :class="accClass(s.accuracy)"
                    :style="{ width: s.accuracy !== null ? pct(s.accuracy) : '0%' }"
                  ></div>
                </div>
                <span class="tb-pct">{{ s.accuracy !== null ? pct(s.accuracy) : '—' }}</span>
                <span class="tb-count">n={{ s.total }}</span>
              </div>
            </div>
          </template>
        </section>

        <!-- ⑤ 近期答题 -->
        <section class="db-card attempts-card">
          <div class="card-header">
            <span class="card-title">近期答题</span>
          </div>
          <p v-if="!data.recent_attempts.length" class="no-data-msg">
            暂无已提交的答题记录。
          </p>
          <div v-else class="attempt-list">
            <div
              v-for="a in data.recent_attempts"
              :key="a.attempt_id"
              class="attempt-row"
            >
              <span class="att-exam">{{ fmtExamId(a.exam_id) }}</span>
              <span class="att-score">
                {{ a.score !== null ? `${a.score} / 25` : '—' }}
              </span>
              <span class="att-date">{{ fmtDate(a.submitted_at) }}</span>
              <router-link
                :to="`/listening/review/${a.attempt_id}`"
                class="att-link"
              >复盘 →</router-link>
            </div>
          </div>
        </section>

      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getStudentId } from '../../services/listeningEvents'

const studentId = getStudentId()

// ── Types ─────────────────────────────────────────────────────────────

interface DashboardData {
  student_id: string
  phase0: {
    status: string
    phase0_active: boolean
    exam_practice_allowed: boolean
    entry_score: number | null
    entry_threshold: number
    cap_days: number
    started_at: string | null
    completed_at: string | null
    forced_exit_at: string | null
  }
  vocab: {
    due_count: number
    total_in_srs: number
    total_lex_items: number
    daily_minutes_cap: number
    session_item_cap: number
  }
  stem_bank: {
    total_predictions: number
    answer_accuracy: number | null
    type_accuracy_by_type: Record<string, { total: number; accuracy: number | null }>
  }
  recent_attempts: {
    attempt_id: string
    exam_id: string
    score: number | null
    submitted_at: string | null
  }[]
}

// ── State ─────────────────────────────────────────────────────────────

const loading = ref(true)
const err = ref('')
const data = ref<DashboardData | null>(null)

// ── Load ──────────────────────────────────────────────────────────────

onMounted(load)

async function load() {
  loading.value = true
  err.value = ''
  try {
    const res = await fetch(`/api/listening/dashboard?student_id=${studentId}`)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    data.value = (await res.json()).data
  } catch (e: unknown) {
    err.value = e instanceof Error ? e.message : String(e)
  } finally {
    loading.value = false
  }
}

// ── Computed ──────────────────────────────────────────────────────────

const covPct = computed(() =>
  data.value?.phase0.entry_score !== null
    ? Math.round((data.value!.phase0.entry_score ?? 0) * 100)
    : 0
)

const thresholdPct = computed(() =>
  Math.round((data.value?.phase0.entry_threshold ?? 0.7) * 100)
)

const daysActive = computed(() => {
  const s = data.value?.phase0.started_at
  if (!s) return 0
  const diff = Date.now() - new Date(s).getTime()
  return Math.floor(diff / 86_400_000)
})

const daysPct = computed(() => {
  const cap = data.value?.phase0.cap_days ?? 21
  return Math.min(100, Math.round((daysActive.value / cap) * 100))
})

const srsProgressPct = computed(() => {
  const total = data.value?.vocab.total_lex_items ?? 1
  const inSrs = data.value?.vocab.total_in_srs ?? 0
  return Math.round((inSrs / total) * 100)
})

const phase0Label = computed(() => {
  const s = data.value?.phase0.status
  return { active: '进行中', completed: '已完成', forced_exit: '已到期结束', not_started: '未开始' }[s ?? ''] ?? s
})

const phase0ChipClass = computed(() => {
  const s = data.value?.phase0.status
  if (s === 'active') return 'chip-active'
  if (s === 'completed') return 'chip-done'
  if (s === 'forced_exit') return 'chip-exit'
  return 'chip-na'
})

// ── Shortcuts ─────────────────────────────────────────────────────────

const shortcuts = [
  { icon: '🎧', label: '词汇训练', to: '/listening/lexicon', requiresExam: false },
  { icon: '📝', label: '题干银行', to: '/listening/stem-bank', requiresExam: false },
  { icon: '⏱', label: '仿真节奏', to: '/listening/pacing/cet6_202606_set2', requiresExam: true },
  { icon: '📋', label: '全真题', to: '/listening/v2/exams/cet6_202606_set2', requiresExam: true },
  { icon: '❌', label: '错题本', to: '/listening/mistakes', requiresExam: false },
]

// ── Helpers ───────────────────────────────────────────────────────────

const TYPE_LABELS: Record<string, string> = {
  main_idea: '主旨题', detail: '细节题', suggestion: '建议题',
  cause_effect: '因果题', inference: '推断题', attitude: '态度题',
}

function typeLabel(qt: string) { return TYPE_LABELS[qt] ?? qt }
function pct(n: number) { return `${Math.round(n * 100)}%` }

function accClass(acc: number | null) {
  if (acc === null) return 'acc-na'
  if (acc >= 0.8) return 'acc-good'
  if (acc >= 0.5) return 'acc-mid'
  return 'acc-bad'
}

function fmtExamId(id: string) {
  return id.replace(/_/g, ' ').replace('cet6', 'CET-6').replace('cet4', 'CET-4')
}

function fmtDate(iso: string | null) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.db-page { min-height: 100vh; padding: 0 16px 60px; }
.db-container { max-width: 760px; margin: 0 auto; padding: 24px 0; }

/* topbar */
.topbar {
  display: flex; align-items: center; gap: 12px; margin-bottom: 28px;
}
.back-btn {
  background: none; border: none; color: rgba(242,239,233,0.5);
  font-size: 14px; cursor: pointer; padding: 0;
}
.back-btn:hover { color: rgba(242,239,233,0.85); }
.page-tag {
  font-size: 11px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase;
  color: rgba(232,167,92,0.7); border: 1px solid rgba(232,167,92,0.2);
  border-radius: 20px; padding: 3px 10px;
}
.refresh-btn {
  margin-left: auto; background: none; border: none;
  color: rgba(242,239,233,0.4); cursor: pointer; font-size: 13px;
}
.refresh-btn:hover { color: rgba(242,239,233,0.75); }
.refresh-btn:disabled { opacity: 0.3; }

/* cards */
.db-card {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 18px;
  padding: 22px 24px;
  margin-bottom: 16px;
}
.card-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 16px;
}
.card-title { font-size: 13px; font-weight: 700; color: rgba(242,239,233,0.7); letter-spacing: 0.04em; text-transform: uppercase; }
.card-action { font-size: 13px; color: rgba(232,167,92,0.75); text-decoration: none; }
.card-action:hover { color: #e8a75c; }
.no-data-msg { font-size: 13px; color: rgba(242,239,233,0.35); margin: 0; }

/* phase0 */
.status-chip {
  font-size: 11px; font-weight: 700; letter-spacing: 0.04em;
  padding: 3px 10px; border-radius: 20px;
}
.chip-active { background: rgba(232,167,92,0.12); color: #e8a75c; }
.chip-done   { background: rgba(100,200,140,0.12); color: #64c88c; }
.chip-exit   { background: rgba(255,255,255,0.06); color: rgba(242,239,233,0.45); }
.chip-na     { background: rgba(255,255,255,0.05); color: rgba(242,239,233,0.3); }

.cov-wrap { margin-bottom: 14px; }
.cov-bar-track {
  position: relative; height: 8px; background: rgba(255,255,255,0.07);
  border-radius: 4px; margin-bottom: 6px;
}
.cov-bar-fill {
  height: 100%; background: #e8a75c; border-radius: 4px;
  transition: width 0.4s;
}
.cov-threshold {
  position: absolute; top: -3px; bottom: -3px; width: 2px;
  background: rgba(242,239,233,0.3); border-radius: 1px;
}
.cov-labels { display: flex; justify-content: space-between; font-size: 12px; }
.cov-num { color: #e8a75c; font-weight: 600; }
.cov-thresh { color: rgba(242,239,233,0.35); }

.days-row {
  display: flex; align-items: center; gap: 6px;
  font-size: 13px; color: rgba(242,239,233,0.7); margin-bottom: 12px;
}
.days-row strong { color: rgba(242,239,233,0.9); }
.days-label { color: rgba(242,239,233,0.4); }
.days-bar-track {
  flex: 1; height: 5px; background: rgba(255,255,255,0.07);
  border-radius: 3px; margin-left: 4px;
}
.days-bar-fill {
  height: 100%; background: rgba(232,167,92,0.5); border-radius: 3px;
  transition: width 0.4s;
}

.gate-row { display: flex; align-items: center; gap: 8px; font-size: 13px; }
.gate-icon { font-weight: 700; font-size: 15px; }
.gate-icon.open { color: #64c88c; }
.gate-icon.closed { color: rgba(232,167,92,0.8); }
.gate-text { color: rgba(242,239,233,0.6); }

/* vocab */
.vocab-stats { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; margin-bottom: 14px; }
.vocab-stat { text-align: center; }
.vs-num { display: block; font-size: 24px; font-weight: 700; color: #e8a75c; line-height: 1.1; }
.vs-label { font-size: 11px; color: rgba(242,239,233,0.4); }
.srs-bar-wrap { }
.srs-bar-track { height: 5px; background: rgba(255,255,255,0.07); border-radius: 3px; margin-bottom: 5px; }
.srs-bar-fill { height: 100%; background: rgba(100,200,140,0.5); border-radius: 3px; transition: width 0.4s; }
.srs-bar-label { font-size: 11px; color: rgba(242,239,233,0.35); }

/* shortcuts */
.shortcuts {
  display: grid; grid-template-columns: repeat(5,1fr);
  gap: 10px; margin-bottom: 16px;
}
.shortcut-btn {
  display: flex; flex-direction: column; align-items: center; gap: 5px;
  padding: 14px 8px; border-radius: 14px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(255,255,255,0.03);
  text-decoration: none; cursor: pointer; position: relative;
  transition: border-color 0.15s, background 0.15s;
}
.shortcut-btn:hover:not(.disabled) {
  border-color: rgba(232,167,92,0.25);
  background: rgba(232,167,92,0.05);
}
.shortcut-btn.disabled { opacity: 0.4; pointer-events: none; }
.sc-icon { font-size: 20px; }
.sc-label { font-size: 11px; color: rgba(242,239,233,0.55); text-align: center; line-height: 1.3; }
.sc-lock { position: absolute; top: 6px; right: 8px; font-size: 10px; }

/* stem stats */
.stem-summary { font-size: 13px; color: rgba(242,239,233,0.55); margin: 0 0 12px; }
.stem-summary strong { color: #e8a75c; }
.type-bars { display: flex; flex-direction: column; gap: 8px; }
.type-bar-row { display: grid; grid-template-columns: 56px 1fr 36px 32px; gap: 8px; align-items: center; }
.tb-label { font-size: 11px; color: rgba(242,239,233,0.45); }
.tb-track { height: 6px; background: rgba(255,255,255,0.07); border-radius: 3px; }
.tb-fill { height: 100%; border-radius: 3px; transition: width 0.4s; }
.acc-good { background: #64c88c; }
.acc-mid  { background: #e8a75c; }
.acc-bad  { background: rgba(232,100,90,0.7); }
.acc-na   { background: rgba(255,255,255,0.15); }
.tb-pct { font-size: 11px; font-weight: 600; color: rgba(242,239,233,0.7); text-align: right; }
.tb-count { font-size: 10px; color: rgba(242,239,233,0.3); }

/* attempts */
.attempt-list { display: flex; flex-direction: column; gap: 8px; }
.attempt-row {
  display: grid; grid-template-columns: 1fr 80px 120px 60px;
  gap: 10px; align-items: center;
  padding: 8px 10px; border-radius: 8px;
  background: rgba(255,255,255,0.03); font-size: 13px;
}
.att-exam { color: rgba(242,239,233,0.75); }
.att-score { font-weight: 700; color: #e8a75c; text-align: right; }
.att-date { color: rgba(242,239,233,0.35); font-size: 12px; }
.att-link { color: rgba(232,167,92,0.7); text-decoration: none; font-size: 12px; text-align: right; }
.att-link:hover { color: #e8a75c; }

/* state cards */
.state-card {
  margin-top: 60px; background: rgba(255,255,255,0.045);
  border: 1px solid rgba(255,255,255,0.09); border-radius: 20px;
  padding: 40px; text-align: center; color: rgba(242,239,233,0.6);
}
.state-card.error { border-color: rgba(232,100,90,0.4); color: rgba(232,100,90,0.8); }

/* Responsive: collapse shortcuts to 3 cols on narrow */
@media (max-width: 560px) {
  .shortcuts { grid-template-columns: repeat(3,1fr); }
  .vocab-stats { grid-template-columns: repeat(2,1fr); }
  .attempt-row { grid-template-columns: 1fr 70px; }
  .att-date, .att-link { display: none; }
}
</style>
