<template>
  <div class="trainer">
    <div v-if="!content" class="empty">加载中……</div>
    <template v-else>
      <p class="instruction">{{ content.instruction }}</p>

      <div
        v-for="pair in content.pairs"
        :key="pair.source"
        class="pair-row"
      >
        <div class="pair-source">
          <p class="en">"{{ pair.source }}"</p>
          <p class="origin">
            来源：{{ pair.origin === 'teacher_annotation' ? '教师标注' : '解析机械提取(待校对)' }}
          </p>
        </div>
        <select v-model="selections[pair.source]" class="pair-select">
          <option value="" disabled>选择对应选项</option>
          <option
            v-for="opt in content.options"
            :key="opt.label"
            :value="opt.label"
          >
            {{ opt.label }}. {{ opt.text }}
          </option>
        </select>
      </div>

      <button class="check-btn" :disabled="checking || !allSelected" @click="submit">
        检查配对
      </button>

      <div v-if="feedback" class="feedback" :class="{ ok: feedback.result }">
        <p>
          得分 {{ Math.round(feedback.score * 100) }}%
          {{ feedback.result ? '· 达标' : '· 未达标' }}
        </p>
        <ul v-if="feedback.error_details.length" class="err-list">
          <li v-for="(e, i) in feedback.error_details" :key="i">
            「{{ e.source }}」应对应 {{ e.expected_option }}，你选了
            {{ e.got || '（空）' }}
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
const selections = ref<Record<string, string>>({})
const checking = ref(false)
const feedback = ref<any>(null)
let startedAt = Date.now()

const allSelected = computed(
  () =>
    content.value?.pairs?.every(
      (p: any) => selections.value[p.source]
    ) ?? false
)

async function submit() {
  checking.value = true
  try {
    const result = await checkTraining(
      props.attemptId, props.questionId, 'paraphrase',
      { answers_map: { ...selections.value } }
    )
    feedback.value = result
    emit('checked', {
      input: { answers_map: { ...selections.value } },
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
    props.attemptId, props.questionId, 'paraphrase'
  )
  startedAt = Date.now()
})
</script>

<style scoped>
.trainer { margin-top: 10px; }
.instruction { font-size: 13px; color: rgba(242,239,233,.6); margin: 12px 0; }
.pair-row {
  display: grid; grid-template-columns: 1fr 1fr; gap: 14px;
  align-items: center; margin-bottom: 12px;
  border: 1px solid rgba(255,255,255,.08); border-radius: 12px; padding: 12px 14px;
}
.pair-source .en { margin: 0; font-size: 14px; line-height: 1.6; }
.pair-source .origin { margin: 6px 0 0; font-size: 11.5px; color: rgba(242,239,233,.35); }
.pair-select {
  border: 1px solid rgba(255,255,255,.1); border-radius: 10px;
  background: rgba(255,255,255,.035); color: #f2efe9;
  padding: 10px 12px; font: inherit; font-size: 13px; outline: none;
}
.check-btn {
  margin-top: 12px; border: none; border-radius: 10px;
  padding: 9px 22px; background: #e8a75c; color: #17120c;
  font-weight: 600; font-size: 13px; cursor: pointer;
}
.check-btn:disabled { opacity: .4; cursor: not-allowed; }
.feedback { margin-top: 12px; font-size: 13px; color: #e8907a; }
.feedback.ok { color: #7fd8a4; }
.err-list { margin: 8px 0 0; padding-left: 18px; line-height: 1.9; color: rgba(242,239,233,.65); }
.empty { font-size: 13px; color: rgba(242,239,233,.4); }
</style>
