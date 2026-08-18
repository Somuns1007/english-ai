<template>
  <div class="trainer">
    <div v-if="!content" class="empty">加载中……</div>
    <template v-else>
      <p class="instruction">{{ content.instruction }}</p>

      <div
        v-for="d in content.distractors"
        :key="d.option"
        class="distractor-block"
      >
        <p class="d-head">
          干扰项 {{ d.option }}
          <span v-if="d.source_hook" class="hook">干扰源：{{ d.source_hook }}</span>
        </p>
        <p class="d-ask">它为什么错？选择错误机制（可多选，须精确）：</p>
        <div class="mech-list">
          <label
            v-for="code in content.mechanism_pool"
            :key="code"
            class="mech"
            :class="{ checked: (selections[d.option] || []).includes(code) }"
          >
            <input
              type="checkbox"
              :checked="(selections[d.option] || []).includes(code)"
              @change="toggle(d.option, code)"
            />
            {{ tagZh(code) }}
          </label>
        </div>
      </div>

      <button class="check-btn" :disabled="checking || !allAnswered" @click="submit">
        检查辨析
      </button>

      <div v-if="feedback" class="feedback" :class="{ ok: feedback.result }">
        <p>
          得分 {{ Math.round(feedback.score * 100) }}%
          {{ feedback.result ? '· 达标' : '· 未达标' }}
        </p>
        <ul v-if="feedback.error_details.length" class="err-list">
          <li v-for="(e, i) in feedback.error_details" :key="i">
            选项 {{ e.option }}：应为
            {{ e.expected.map(tagZh).join('、') }}；
            {{ e.note }}
          </li>
        </ul>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  checkTraining,
  fetchTagDictionary,
  fetchTrainingContent
} from '../../services/listeningApi'

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
const tagDict = ref<Record<string, { zh: string }>>({})
const selections = ref<Record<string, string[]>>({})
const checking = ref(false)
const feedback = ref<any>(null)
let startedAt = Date.now()

const allAnswered = computed(
  () =>
    content.value?.distractors?.every(
      (d: any) => (selections.value[d.option] || []).length > 0
    ) ?? false
)

function tagZh(code: string): string {
  return tagDict.value[code]?.zh || code
}

function toggle(option: string, code: string) {
  const list = (selections.value[option] ||= [])
  const i = list.indexOf(code)
  if (i >= 0) list.splice(i, 1)
  else list.push(code)
}

async function submit() {
  checking.value = true
  try {
    const result = await checkTraining(
      props.attemptId, props.questionId, 'distractor',
      { selections: JSON.parse(JSON.stringify(selections.value)) }
    )
    feedback.value = result
    emit('checked', {
      input: { selections: JSON.parse(JSON.stringify(selections.value)) },
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
  const [c, tags] = await Promise.all([
    fetchTrainingContent(props.attemptId, props.questionId, 'distractor'),
    fetchTagDictionary()
  ])
  content.value = c
  tagDict.value = tags
  startedAt = Date.now()
})
</script>

<style scoped>
.trainer { margin-top: 10px; }
.instruction { font-size: 13px; color: rgba(242,239,233,.6); margin: 12px 0; line-height: 1.7; }
.distractor-block {
  border: 1px solid rgba(255,255,255,.08); border-radius: 12px;
  padding: 12px 14px; margin-bottom: 12px;
}
.d-head { margin: 0; font-size: 14px; font-weight: 600; }
.hook { font-size: 12px; color: rgba(242,239,233,.45); font-weight: 400; margin-left: 10px; }
.d-ask { font-size: 12.5px; color: rgba(242,239,233,.5); margin: 8px 0; }
.mech-list { display: flex; flex-wrap: wrap; gap: 8px; }
.mech {
  border: 1px solid rgba(255,255,255,.12); border-radius: 999px;
  padding: 5px 12px; font-size: 12.5px; cursor: pointer;
  color: rgba(242,239,233,.65); display: inline-flex; align-items: center; gap: 6px;
}
.mech.checked { border-color: #e8a75c; background: rgba(232,167,92,.1); color: #e8a75c; }
.mech input { accent-color: #e8a75c; }
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
