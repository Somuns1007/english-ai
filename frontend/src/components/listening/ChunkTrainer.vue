<template>
  <div class="trainer">
    <div v-if="!content" class="empty">加载中……</div>
    <template v-else>
      <p class="instruction">{{ content.instruction }}</p>
      <p v-if="content.text_quality === 'needs_review'" class="quality-note">
        语块来自原始 transcript（待教师校对）
      </p>

      <div class="pool">
        <button
          v-for="(chunk, idx) in content.chunks"
          :key="idx"
          class="chunk"
          :disabled="placed.includes(Number(idx))"
          @click="placed.push(Number(idx))"
        >
          {{ chunk }}
        </button>
      </div>

      <div class="placed-box">
        <p class="placed-label">你的顺序（点击移除）：</p>
        <div class="placed-list">
          <button
            v-for="(idx, pos) in placed"
            :key="pos"
            class="chunk placed"
            @click="placed.splice(pos, 1)"
          >
            {{ pos + 1 }}. {{ content.chunks[idx] }}
          </button>
          <span v-if="!placed.length" class="empty">尚未选择</span>
        </div>
      </div>

      <button
        class="check-btn"
        :disabled="checking || placed.length !== content.chunks.length"
        @click="submit"
      >
        检查顺序
      </button>

      <div v-if="feedback" class="feedback" :class="{ ok: feedback.result }">
        <p>
          得分 {{ Math.round(feedback.score * 100) }}%
          {{ feedback.result ? '· 达标' : '· 未达标' }}
        </p>
        <ul v-if="feedback.error_details.length" class="err-list">
          <li v-for="(e, i) in feedback.error_details" :key="i">
            第 {{ e.position + 1 }} 块放错了：「{{ e.placed_chunk }}」
            应在第 {{ e.expected_position + 1 }} 位
          </li>
        </ul>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
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
const placed = ref<number[]>([])
const checking = ref(false)
const feedback = ref<any>(null)
let startedAt = Date.now()

async function submit() {
  checking.value = true
  try {
    const result = await checkTraining(
      props.attemptId, props.questionId, 'chunk',
      { order: [...placed.value] }
    )
    feedback.value = result
    emit('checked', {
      input: { order: [...placed.value] },
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
    props.attemptId, props.questionId, 'chunk'
  )
  startedAt = Date.now()
})
</script>

<style scoped>
.trainer { margin-top: 10px; }
.instruction { font-size: 13px; color: rgba(242,239,233,.6); margin: 12px 0; }
.quality-note { font-size: 12px; color: #e8907a; margin: 0 0 8px; }
.pool { display: flex; flex-wrap: wrap; gap: 8px; }
.chunk {
  border: 1px solid rgba(126,184,232,.3); border-radius: 10px;
  background: rgba(126,184,232,.06); color: #f2efe9;
  font-size: 13px; padding: 8px 12px; cursor: pointer; line-height: 1.5;
}
.chunk:disabled { opacity: .3; cursor: default; }
.chunk.placed { border-color: rgba(232,167,92,.4); background: rgba(232,167,92,.08); }
.placed-box { margin-top: 14px; }
.placed-label { font-size: 12px; color: rgba(242,239,233,.45); margin: 0 0 8px; }
.placed-list { display: grid; gap: 6px; }
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
