<template>
  <div class="trainer">
    <div v-if="!content" class="empty">加载中……</div>
    <template v-else>
      <div class="level-tabs">
        <button
          v-for="lv in content.levels"
          :key="lv.level"
          class="tab"
          :class="{ active: level === lv.level }"
          @click="level = lv.level; reset()"
        >
          {{ lv.name }}
        </button>
      </div>
      <p v-if="content.text_quality === 'needs_review'" class="quality-note">
        目标文本来自原始 transcript（待教师校对，可能含识别噪声）
      </p>
      <p class="instruction">{{ currentLevel?.instruction }}</p>

      <div v-if="level === 1" class="inputs">
        <input
          v-for="i in currentLevel?.target_count || 0"
          :key="i"
          v-model="inputs[i - 1]"
          class="text-input"
          :placeholder="`关键词 ${i}`"
        />
      </div>
      <div v-else-if="level === 2" class="inputs">
        <input
          v-for="i in currentLevel?.blank_count || 0"
          :key="i"
          v-model="inputs[i - 1]"
          class="text-input"
          :placeholder="`空 ${i}`"
        />
      </div>
      <textarea
        v-else
        v-model="inputs[0]"
        class="text-area"
        placeholder="重听音频后，在此完整写出定位句……"
      ></textarea>

      <button class="check-btn" :disabled="checking" @click="submit">
        {{ checking ? '判分中…' : '检查' }}
      </button>

      <div v-if="feedback" class="feedback" :class="{ ok: feedback.result }">
        <p>
          得分 {{ Math.round(feedback.score * 100) }}%
          {{ feedback.result ? '· 达标' : '· 未达标' }}
        </p>
        <ul v-if="feedback.error_details.length" class="err-list">
          <li v-for="(e, i) in feedback.error_details.slice(0, 8)" :key="i">
            <template v-if="e.expected !== undefined">
              位置 {{ (e.index ?? 0) + 1 }}：应为 "{{ e.expected }}"，
              你写了 "{{ e.got ?? '（空）' }}"
            </template>
            <template v-else>未写出：{{ e.phrase }}</template>
          </li>
        </ul>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { checkTraining, fetchTrainingContent } from '../../services/listeningApi'

const props = defineProps<{ attemptId: string; questionId: string }>()
const emit = defineEmits<{
  (e: 'checked', payload: {
    input: Record<string, unknown>
    score: number
    result: boolean
    error_details: any[]
    duration_ms: number
  }): void
}>()

const content = ref<any>(null)
const level = ref(1)
const inputs = ref<string[]>([])
const checking = ref(false)
const feedback = ref<any>(null)
let startedAt = Date.now()

const currentLevel = computed(
  () => content.value?.levels?.find((l: any) => l.level === level.value)
)

function reset() {
  inputs.value = []
  feedback.value = null
  startedAt = Date.now()
}

async function submit() {
  checking.value = true
  try {
    const filled = inputs.value.filter((s) => s && s.trim())
    const result = await checkTraining(
      props.attemptId, props.questionId, 'dictation',
      { level: level.value, inputs: filled }
    )
    feedback.value = result
    emit('checked', {
      input: { level: level.value, inputs: filled },
      score: result.score,
      result: result.result,
      error_details: result.error_details,
      duration_ms: Date.now() - startedAt
    })
  } finally {
    checking.value = false
  }
}

onMounted(async () => {
  content.value = await fetchTrainingContent(
    props.attemptId, props.questionId, 'dictation'
  )
  if (content.value?.levels?.length) {
    level.value = content.value.levels[0].level
  }
  startedAt = Date.now()
})
</script>

<style scoped>
.trainer { margin-top: 10px; }
.level-tabs { display: flex; gap: 8px; flex-wrap: wrap; }
.tab {
  border: 1px solid rgba(255,255,255,.12); border-radius: 10px;
  background: rgba(255,255,255,.04); color: rgba(242,239,233,.6);
  font-size: 12.5px; padding: 7px 14px; cursor: pointer;
}
.tab.active { border-color: #e8a75c; color: #e8a75c; }
.quality-note { font-size: 12px; color: #e8907a; margin: 10px 0 0; }
.instruction { font-size: 13px; color: rgba(242,239,233,.6); margin: 12px 0; }
.inputs { display: grid; gap: 8px; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); }
.text-input, .text-area {
  border: 1px solid rgba(255,255,255,.1); border-radius: 10px;
  background: rgba(255,255,255,.035); color: #f2efe9;
  padding: 10px 14px; font: inherit; font-size: 14px; outline: none;
}
.text-area { width: 100%; min-height: 110px; resize: vertical; box-sizing: border-box; }
.text-input:focus, .text-area:focus { border-color: rgba(232,167,92,.6); }
.check-btn {
  margin-top: 12px; border: none; border-radius: 10px;
  padding: 9px 22px; background: #e8a75c; color: #17120c;
  font-weight: 600; font-size: 13px; cursor: pointer;
}
.check-btn:disabled { opacity: .4; }
.feedback { margin-top: 12px; font-size: 13px; color: #e8907a; }
.feedback.ok { color: #7fd8a4; }
.err-list { margin: 8px 0 0; padding-left: 18px; line-height: 1.9; color: rgba(242,239,233,.65); }
.empty { font-size: 13px; color: rgba(242,239,233,.4); }
</style>
