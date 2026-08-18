<template>
  <div class="diagnosis-panel">
    <h4 class="panel-title">错因诊断</h4>

    <!-- 第 1 层: 题目存在的典型陷阱(题目层, 与学生无关) -->
    <section class="layer">
      <p class="layer-title">
        <span class="layer-tag">题目层</span>该题存在的典型陷阱
      </p>
      <ul v-if="traps.length" class="trap-list">
        <li v-for="(t, i) in traps" :key="i">
          选项 {{ t.option }}
          <template v-if="t.source_hook">（干扰源：{{ t.source_hook }}）</template>
          →
          <span v-for="(code, j) in t.logic" :key="j" class="tag">
            {{ tagZh(code) }}
          </span>
        </li>
      </ul>
      <p v-else class="empty">该题暂无教师登记的陷阱标注</p>
    </section>

    <!-- 第 2 层: 系统基于行为证据的候选错因 -->
    <section class="layer">
      <p class="layer-title">
        <span class="layer-tag system">系统推测</span>候选错因（基于你的行为证据）
      </p>
      <div v-if="loadingCandidates" class="empty">分析中……</div>
      <template v-else-if="candidates">
        <div
          v-for="(c, i) in candidates.candidates"
          :key="i"
          class="candidate"
        >
          <div class="candidate-head">
            <span class="tag system">{{ tagZh(c.candidate_tag) }}</span>
            <span class="confidence">
              置信度 {{ Math.round(c.confidence * 100) }}%
            </span>
          </div>
          <div class="confidence-bar">
            <div
              class="confidence-fill"
              :style="{ width: `${c.confidence * 100}%` }"
            ></div>
          </div>
          <ul class="evidence-list">
            <li v-for="(ev, j) in c.evidence" :key="j">{{ ev }}</li>
          </ul>
        </div>
        <p v-if="candidates.note" class="empty">{{ candidates.note }}</p>
        <p class="disclaimer">{{ candidates.disclaimer }}</p>
      </template>
    </section>

    <!-- 第 3 层: 学生自判 -->
    <section class="layer">
      <p class="layer-title">
        <span class="layer-tag self">学生自判</span>你觉得错在哪里？（可多选）
      </p>
      <div class="self-options">
        <label
          v-for="opt in selfOptions"
          :key="opt.code"
          class="self-option"
          :class="{ checked: selfSelected.includes(opt.code) }"
        >
          <input
            type="checkbox"
            :value="opt.code"
            :checked="selfSelected.includes(opt.code)"
            @change="toggleSelf(opt.code)"
          />
          <span class="self-label">{{ opt.label }}</span>
          <span class="self-hint">{{ opt.hint }}</span>
        </label>
        <label
          class="self-option unsure"
          :class="{ checked: selfSelected.includes('unsure') }"
        >
          <input
            type="checkbox"
            :checked="selfSelected.includes('unsure')"
            @change="toggleSelf('unsure')"
          />
          <span class="self-label">我不确定</span>
        </label>
      </div>
      <button
        class="save-btn"
        :disabled="saving || !selfDirty"
        @click="saveSelf"
      >
        {{ saving ? '保存中…' : '保存我的自判' }}
      </button>
    </section>

    <!-- 第 4 层: 最终确认 -->
    <section class="layer">
      <p class="layer-title">
        <span class="layer-tag final">最终确认</span>确认的错因（将进入能力画像）
      </p>
      <p class="layer-desc">
        从“我的自判”和“系统候选”中勾选你认可的错因，确认后写入最终诊断。
      </p>
      <div class="self-options">
        <label
          v-for="code in confirmPool"
          :key="code"
          class="self-option"
          :class="{ checked: finalSelected.includes(code) }"
        >
          <input
            type="checkbox"
            :checked="finalSelected.includes(code)"
            @change="toggleFinal(code)"
          />
          <span class="self-label">{{ tagZh(code) }}</span>
          <span class="self-hint">{{ sourceOf(code) }}</span>
        </label>
      </div>
      <p v-if="!confirmPool.length" class="empty">
        请先完成“学生自判”或等待系统候选
      </p>
      <button
        class="save-btn final"
        :disabled="saving || !finalSelected.length"
        @click="saveFinal"
      >
        确认最终错因
      </button>
      <p v-if="savedFinal.length" class="confirmed">
        已确认：{{ savedFinal.map(tagZh).join('、') }}
      </p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  fetchCandidates,
  fetchSelfDiagnosisOptions,
  fetchTagDictionary,
  saveDiagnosis
} from '../../services/listeningApi'
import type {
  CandidatesResult,
  SelfDiagnosisOption
} from '../../types/listening'

const props = defineProps<{
  attemptId: string
  questionId: string
  studentId: string
  initialStudentTags: string[]
  initialFinalTags: string[]
}>()

const emit = defineEmits<{
  (e: 'saved', diagnosis: { id: string; revision: number }): void
}>()

const tagDict = ref<Record<string, { zh: string; layer: string }>>({})
const selfOptions = ref<SelfDiagnosisOption[]>([])
const candidates = ref<CandidatesResult | null>(null)
const loadingCandidates = ref(true)

const selfSelected = ref<string[]>([...props.initialStudentTags])
const finalSelected = ref<string[]>([...props.initialFinalTags])
const savedFinal = ref<string[]>([...props.initialFinalTags])
const selfDirty = ref(false)
const saving = ref(false)

const traps = computed(() => candidates.value?.question_level_traps || [])

/** 最终确认的可选池 = 学生自判 ∪ 系统候选 */
const confirmPool = computed(() => {
  const pool = new Set<string>()
  selfSelected.value
    .filter((c) => c !== 'unsure')
    .forEach((c) => pool.add(c))
  candidates.value?.candidates.forEach((c) => pool.add(c.candidate_tag))
  return [...pool]
})

function tagZh(code: string): string {
  return tagDict.value[code]?.zh || code
}

function sourceOf(code: string): string {
  const fromSelf = selfSelected.value.includes(code)
  const fromSystem = candidates.value?.candidates.some(
    (c) => c.candidate_tag === code
  )
  if (fromSelf && fromSystem) return '自判 + 系统候选一致'
  if (fromSelf) return '来自我的自判'
  return '来自系统候选'
}

function toggleSelf(code: string) {
  selfDirty.value = true
  if (code === 'unsure') {
    // “我不确定”与其他互斥
    selfSelected.value = selfSelected.value.includes('unsure') ? [] : ['unsure']
    return
  }
  selfSelected.value = selfSelected.value.filter((c) => c !== 'unsure')
  const i = selfSelected.value.indexOf(code)
  if (i >= 0) selfSelected.value.splice(i, 1)
  else selfSelected.value.push(code)
}

function toggleFinal(code: string) {
  const i = finalSelected.value.indexOf(code)
  if (i >= 0) finalSelected.value.splice(i, 1)
  else finalSelected.value.push(code)
}

async function saveSelf() {
  saving.value = true
  try {
    const diag = await saveDiagnosis(
      props.attemptId,
      props.questionId,
      selfSelected.value,
      savedFinal.value,
      props.studentId
    )
    selfDirty.value = false
    emit('saved', diag)
  } finally {
    saving.value = false
  }
}

async function saveFinal() {
  saving.value = true
  try {
    const diag = await saveDiagnosis(
      props.attemptId,
      props.questionId,
      selfSelected.value,
      finalSelected.value,
      props.studentId
    )
    savedFinal.value = [...finalSelected.value]
    emit('saved', diag)
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  const [tags, options, cand] = await Promise.all([
    fetchTagDictionary(),
    fetchSelfDiagnosisOptions(),
    fetchCandidates(props.attemptId, props.questionId)
  ])
  tagDict.value = tags
  selfOptions.value = options
  candidates.value = cand
  loadingCandidates.value = false
})
</script>

<style scoped>
.diagnosis-panel {
  margin-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding-top: 16px;
}

.panel-title {
  margin: 0 0 14px;
  font-size: 15px;
  letter-spacing: 2px;
}

.layer {
  margin-bottom: 20px;
}

.layer-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13.5px;
  margin: 0 0 10px;
}

.layer-tag {
  font-size: 11px;
  border-radius: 999px;
  padding: 2px 10px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: rgba(242, 239, 233, 0.6);
  letter-spacing: 1px;
}

.layer-tag.system {
  border-color: rgba(126, 184, 232, 0.5);
  color: #7eb8e8;
}

.layer-tag.self {
  border-color: rgba(232, 167, 92, 0.5);
  color: #e8a75c;
}

.layer-tag.final {
  border-color: rgba(127, 216, 164, 0.5);
  color: #7fd8a4;
}

.layer-desc {
  margin: 0 0 10px;
  font-size: 12px;
  color: rgba(242, 239, 233, 0.45);
}

.trap-list {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  line-height: 2;
}

.tag {
  display: inline-block;
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 999px;
  padding: 1px 9px;
  font-size: 12px;
  margin-right: 6px;
  color: rgba(242, 239, 233, 0.75);
}

.tag.system {
  border-color: rgba(126, 184, 232, 0.5);
  color: #7eb8e8;
}

.candidate {
  border: 1px solid rgba(126, 184, 232, 0.2);
  border-radius: 12px;
  padding: 12px 14px;
  margin-bottom: 10px;
  background: rgba(126, 184, 232, 0.04);
}

.candidate-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.confidence {
  font-size: 12px;
  color: #7eb8e8;
}

.confidence-bar {
  height: 4px;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.08);
  margin: 8px 0;
}

.confidence-fill {
  height: 100%;
  border-radius: 2px;
  background: #7eb8e8;
}

.evidence-list {
  margin: 6px 0 0;
  padding-left: 18px;
  font-size: 12.5px;
  line-height: 1.9;
  color: rgba(242, 239, 233, 0.65);
}

.disclaimer {
  font-size: 11.5px;
  color: rgba(242, 239, 233, 0.35);
  margin: 8px 0 0;
}

.self-options {
  display: grid;
  gap: 8px;
}

.self-option {
  display: flex;
  align-items: baseline;
  gap: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  padding: 9px 14px;
  cursor: pointer;
  font-size: 13.5px;
  transition: border-color 0.2s;
}

.self-option.checked {
  border-color: #e8a75c;
  background: rgba(232, 167, 92, 0.1);
}

.self-option input {
  accent-color: #e8a75c;
}

.self-label {
  font-weight: 600;
}

.self-hint {
  font-size: 12px;
  color: rgba(242, 239, 233, 0.4);
}

.save-btn {
  margin-top: 12px;
  border: none;
  border-radius: 10px;
  padding: 9px 20px;
  background: #e8a75c;
  color: #17120c;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
}

.save-btn.final {
  background: #7fd8a4;
}

.save-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.empty {
  font-size: 13px;
  color: rgba(242, 239, 233, 0.4);
}

.confirmed {
  margin-top: 10px;
  font-size: 13px;
  color: #7fd8a4;
}
</style>
