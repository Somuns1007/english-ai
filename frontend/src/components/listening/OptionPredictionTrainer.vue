<template>
  <!--
    Option Prediction Trainer (Work Order G)
    三阶段：① 判断题型 → ② 作答选项 → ③ 查看反馈
    所有题目都来自 Set 2（已在后端封装）。
    正确答案只有提交后才从服务端返回（DTO 白名单）。
  -->
  <div class="trainer-card">
    <!-- 题目头部 -->
    <div class="q-header">
      <span class="q-badge">Q{{ item.question_no }}</span>
      <span class="unit-tag">{{ unitLabel(item.unit_type) }}</span>
      <span class="phase-tag">{{ phaseLabel }}</span>
    </div>

    <!-- 题干（始终可见） -->
    <p class="stem-text">{{ item.stem_en }}</p>

    <!-- 阶段 1：判断题目类型 -->
    <div v-if="phase === 'type_id'" class="phase-block">
      <p class="phase-hint">这道题考查的是哪种题型？</p>
      <div class="type-grid">
        <button
          v-for="qt in QUESTION_TYPES"
          :key="qt"
          class="type-btn"
          :class="{ picked: pickedType === qt }"
          @click="pickedType = qt"
        >
          {{ typeLabel(qt) }}
        </button>
      </div>
      <button
        class="confirm-btn"
        :disabled="!pickedType || submitting"
        @click="submitPhase1"
      >
        确认题型，查看选项
      </button>
    </div>

    <!-- 阶段 2：选择答案（看到选项后） -->
    <div v-else-if="phase === 'answer'" class="phase-block">
      <!-- Type feedback -->
      <div
        class="type-result"
        :class="feedback?.is_type_correct ? 'correct' : 'wrong'"
      >
        题型：你选「{{ typeLabel(pickedType || '') }}」——
        {{ feedback?.is_type_correct ? '✓ 判断正确' : `✗ 实际是「${typeLabel(feedback?.correct_type || '')}」` }}
      </div>

      <p class="phase-hint">现在看选项，选出你认为正确的答案：</p>
      <div class="options-list">
        <button
          v-for="opt in item.options"
          :key="opt.label"
          class="opt-btn"
          :class="{ picked: pickedAnswer === opt.label }"
          @click="pickedAnswer = opt.label"
        >
          <span class="opt-label">{{ opt.label }}</span>
          <span class="opt-text">{{ opt.text_zh }}</span>
        </button>
      </div>
      <button
        class="confirm-btn"
        :disabled="!pickedAnswer || submitting"
        @click="submitPhase2"
      >
        提交答案
      </button>
    </div>

    <!-- 阶段 3：结果反馈 -->
    <div v-else-if="phase === 'result'" class="phase-block">
      <div class="result-grid">
        <!-- 题型判断 -->
        <div class="result-row">
          <span class="result-label">题型判断</span>
          <span class="result-val" :class="feedback?.is_type_correct ? 'ok' : 'fail'">
            {{ feedback?.is_type_correct ? '✓ 正确' : '✗ 错误' }}
          </span>
          <span class="result-detail">正确：{{ typeLabel(feedback?.correct_type || '') }}</span>
        </div>
        <!-- 答案 -->
        <div class="result-row">
          <span class="result-label">答案选择</span>
          <span class="result-val" :class="feedback?.is_answer_correct ? 'ok' : 'fail'">
            {{ feedback?.is_answer_correct ? '✓ 正确' : '✗ 错误' }}
          </span>
          <span class="result-detail">
            你选 {{ pickedAnswer }} → 正确 {{ feedback?.correct_answer }}
          </span>
        </div>
      </div>

      <!-- Options with correct highlighted -->
      <div class="options-list review">
        <div
          v-for="opt in item.options"
          :key="opt.label"
          class="opt-btn"
          :class="{
            correct: opt.label === feedback?.correct_answer,
            wrong: opt.label === pickedAnswer && !feedback?.is_answer_correct,
          }"
        >
          <span class="opt-label">{{ opt.label }}</span>
          <span class="opt-text">{{ opt.text_zh }}</span>
          <span v-if="opt.label === feedback?.correct_answer" class="marker">✓</span>
          <span v-if="opt.label === pickedAnswer && !feedback?.is_answer_correct" class="marker">✗</span>
        </div>
      </div>

      <button class="next-btn" @click="emit('next')">
        下一题 →
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

// ── Types ─────────────────────────────────────────────────────────────

export interface StemItem {
  question_no: number
  unit_id: string
  unit_type: string
  stem_en: string
  question_type: string
  template_family: string
  options: { label: string; text_zh: string }[]
}

// 两阶段协议：
//   阶段1 (selected_answer=null) → {correct_type, is_type_correct}，无 correct_answer
//   阶段2 (selected_answer 已知) → 完整响应含 correct_answer, is_answer_correct
interface PredictFeedback {
  correct_type: string
  is_type_correct: number | null
  correct_answer?: string         // 仅阶段2响应中存在
  is_answer_correct?: number | null  // 仅阶段2响应中存在
}

const props = defineProps<{
  item: StemItem
  studentId: string
}>()

const emit = defineEmits<{
  (e: 'next'): void
}>()

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
  lecture:      'Lecture / Recording',
}

function typeLabel(qt: string) { return TYPE_LABELS[qt] ?? qt }
function unitLabel(ut: string) { return UNIT_LABELS[ut] ?? ut }

// ── State ─────────────────────────────────────────────────────────────

type Phase = 'type_id' | 'answer' | 'result'
const phase = ref<Phase>('type_id')
const pickedType = ref<string>('')
const pickedAnswer = ref<string>('')
const feedback = ref<PredictFeedback | null>(null)
const submitting = ref(false)

const phaseLabel = computed(() => ({
  type_id: '① 判断题型',
  answer:  '② 选择答案',
  result:  '③ 查看结果',
}[phase.value]))

// ── API calls ─────────────────────────────────────────────────────────

async function callPredict(selectedAnswer?: string) {
  submitting.value = true
  try {
    const res = await fetch('/api/listening/stem-bank/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_id: props.studentId,
        question_no: props.item.question_no,
        predicted_type: pickedType.value || null,
        selected_answer: selectedAnswer ?? null,
      }),
    })
    if (!res.ok) throw new Error(`predict failed: ${res.status}`)
    const json = await res.json()
    return json.data as PredictFeedback
  } finally {
    submitting.value = false
  }
}

// ── Phase transitions ─────────────────────────────────────────────────

async function submitPhase1() {
  // Submit type prediction only (no answer yet)
  // We still call the API so type accuracy is recorded
  const fb = await callPredict()
  feedback.value = fb
  phase.value = 'answer'
}

async function submitPhase2() {
  // Submit final answer (overwrites previous record)
  const fb = await callPredict(pickedAnswer.value)
  feedback.value = fb
  phase.value = 'result'
}
</script>

<style scoped>
.trainer-card {
  padding: 24px 26px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 18px;
  margin-bottom: 16px;
}

/* header */
.q-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}
.q-badge {
  font-size: 12px;
  font-weight: 700;
  color: #e8a75c;
  background: rgba(232,167,92,0.1);
  border-radius: 8px;
  padding: 2px 8px;
}
.unit-tag, .phase-tag {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: rgba(242,239,233,0.35);
}
.phase-tag {
  margin-left: auto;
  color: rgba(232,167,92,0.65);
}

/* stem */
.stem-text {
  font-size: 16px;
  font-weight: 500;
  color: rgba(242,239,233,0.9);
  line-height: 1.55;
  margin: 0 0 18px;
}

/* phase block */
.phase-block { }

.phase-hint {
  font-size: 13px;
  color: rgba(242,239,233,0.45);
  margin: 0 0 12px;
}

/* type grid */
.type-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-bottom: 14px;
}
.type-btn {
  padding: 8px 6px;
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.09);
  background: transparent;
  color: rgba(242,239,233,0.65);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}
.type-btn.picked {
  border-color: #e8a75c;
  background: rgba(232,167,92,0.12);
  color: #e8a75c;
}

/* type result banner */
.type-result {
  font-size: 13px;
  padding: 8px 12px;
  border-radius: 8px;
  margin-bottom: 14px;
}
.type-result.correct {
  background: rgba(100,200,140,0.1);
  color: #64c88c;
  border: 1px solid rgba(100,200,140,0.2);
}
.type-result.wrong {
  background: rgba(232,100,90,0.1);
  color: rgba(232,130,120,0.9);
  border: 1px solid rgba(232,100,90,0.2);
}

/* options */
.options-list { display: flex; flex-direction: column; gap: 7px; margin-bottom: 14px; }
.opt-btn {
  display: flex;
  gap: 10px;
  align-items: baseline;
  padding: 10px 14px;
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.09);
  background: transparent;
  color: rgba(242,239,233,0.72);
  font-size: 14px;
  text-align: left;
  cursor: pointer;
  line-height: 1.5;
  transition: border-color 0.15s, background 0.15s;
  width: 100%;
}
.options-list.review .opt-btn { cursor: default; }
.opt-btn:hover:not(:disabled) {
  border-color: rgba(232,167,92,0.3);
  background: rgba(232,167,92,0.06);
}
.opt-btn.picked {
  border-color: #e8a75c;
  background: rgba(232,167,92,0.1);
  color: #e8a75c;
}
.opt-btn.correct { border-color: #64c88c; background: rgba(100,200,140,0.1); color: #64c88c; }
.opt-btn.wrong   { border-color: rgba(232,100,90,0.5); background: rgba(232,100,90,0.08); color: rgba(232,130,120,0.9); }
.opt-label { font-weight: 700; flex-shrink: 0; }
.marker { margin-left: auto; flex-shrink: 0; }

/* result grid */
.result-grid { display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; }
.result-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}
.result-label { color: rgba(242,239,233,0.4); width: 72px; flex-shrink: 0; }
.result-val { font-weight: 700; flex-shrink: 0; }
.result-val.ok   { color: #64c88c; }
.result-val.fail { color: rgba(232,130,120,0.9); }
.result-detail { color: rgba(242,239,233,0.5); font-size: 12px; }

/* buttons */
.confirm-btn, .next-btn {
  padding: 9px 22px;
  border-radius: 10px;
  border: 1px solid rgba(232,167,92,0.3);
  background: rgba(232,167,92,0.09);
  color: #e8a75c;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}
.confirm-btn:hover:not(:disabled), .next-btn:hover { background: rgba(232,167,92,0.18); }
.confirm-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.next-btn { margin-top: 4px; float: right; }
</style>
