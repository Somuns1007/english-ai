<template>
  <div class="training-panel">
    <div v-if="loading" class="state">加载训练计划……</div>
    <div v-else-if="errorMessage" class="state error">{{ errorMessage }}</div>

    <template v-else-if="plan">
      <!-- 错因驱动: 证据不足时不推荐训练 -->
      <div v-if="!plan.available" class="state blocked">
        <p class="blocked-title">暂未生成训练</p>
        <p class="blocked-reason">{{ plan.reason }}</p>
      </div>

      <template v-else>
        <div class="trigger-note">
          <p
            v-for="(t, i) in plan.triggers"
            :key="i"
            class="trigger-line"
          >
            触发依据：{{ tagZh(t.tag) }}（{{ t.trigger_source
            }}<template v-if="t.confidence != null">
              ，置信度 {{ Math.round(t.confidence * 100) }}%</template
            >）
          </p>
        </div>

        <div
          v-for="t in plan.trainings"
          :key="t.type"
          class="training-item"
        >
          <button class="training-head" @click="toggleTraining(t.type)">
            <span class="t-title">{{ t.title }}</span>
            <span class="t-reason">{{ t.reason }}</span>
            <span class="t-status" :class="{ done: savedTypes.has(t.type) }">
              {{ savedTypes.has(t.type) ? '已完成本次' : '点击开始' }}
            </span>
          </button>
          <div v-if="activeType === t.type" class="training-body">
            <component
              :is="trainerComponent(t.type)"
              :attempt-id="attemptId"
              :question-id="questionId"
              @checked="onChecked(t.type, $event)"
            />
          </div>
        </div>

        <!-- 裸听复测 -->
        <div class="retest-block">
          <p class="retest-title">裸听复测（mastered 判定条件之一）</p>
          <p class="retest-note">
            不使用任何提示、不查看解析，重新听一遍本题所在 Unit
            的音频后直接作答。复测期间如打开提示将计入记录。
          </p>
          <div class="retest-options">
            <button
              v-for="label in ['A', 'B', 'C', 'D']"
              :key="label"
              class="retest-option"
              :disabled="retesting"
              @click="doRetest(label)"
            >
              {{ label }}
            </button>
          </div>
          <p v-if="retestFeedback" class="retest-feedback" :class="{ ok: retestFeedback.is_correct }">
            {{ retestFeedback.is_correct ? '复测答对。' : '复测仍错。' }}
            复测期间打开提示 {{ retestFeedback.hints_during_retest }} 次。
            {{ retestFeedback.note }}
          </p>
        </div>
      </template>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import DictationTrainer from './DictationTrainer.vue'
import ChunkTrainer from './ChunkTrainer.vue'
import ParaphraseTrainer from './ParaphraseTrainer.vue'
import DistractorTrainer from './DistractorTrainer.vue'
import {
  blindRetest,
  fetchTagDictionary,
  fetchTrainingPlan,
  saveTrainingResult
} from '../../services/listeningApi'

const props = defineProps<{
  attemptId: string
  questionId: string
  studentId: string
  diagnosisId?: string | null
}>()

const emit = defineEmits<{ (e: 'progress'): void }>()

const loading = ref(true)
const errorMessage = ref('')
const plan = ref<any>(null)
const activeType = ref<string | null>(null)
const savedTypes = ref(new Set<string>())
const retesting = ref(false)
const retestFeedback = ref<{
  is_correct: boolean
  hints_during_retest: number
  note: string
} | null>(null)
const tagDict = ref<Record<string, { zh: string; layer: string }>>({})

function tagZh(code: string): string {
  return tagDict.value[code]?.zh || code
}

function trainerComponent(type: string) {
  switch (type) {
    case 'dictation':
      return DictationTrainer
    case 'chunk':
      return ChunkTrainer
    case 'paraphrase':
      return ParaphraseTrainer
    case 'distractor':
      return DistractorTrainer
    default:
      return DictationTrainer
  }
}

function toggleTraining(type: string) {
  activeType.value = activeType.value === type ? null : type
}

async function onChecked(
  type: string,
  payload: {
    input: Record<string, unknown>
    score: number
    result: boolean
    error_details: any[]
    duration_ms: number
  }
) {
  try {
    await saveTrainingResult({
      student_id: props.studentId,
      question_id: props.questionId,
      attempt_id: props.attemptId,
      // 诊断绑定以服务端权威为准(保存时服务端会重查当前有效诊断),
      // 这里上送仅作链路提示
      diagnosis_id: props.diagnosisId || undefined,
      training_type: type,
      input: payload.input,
      result: payload.result,
      score: payload.score,
      error_details: payload.error_details,
      hints_used: 0,
      duration_ms: payload.duration_ms
    })
    savedTypes.value = new Set([...savedTypes.value, type])
    emit('progress')
  } catch (error) {
    window.alert(error instanceof Error ? error.message : '训练结果保存失败')
  }
}

async function doRetest(label: string) {
  retesting.value = true
  try {
    retestFeedback.value = await blindRetest(props.attemptId, props.questionId, label)
    emit('progress')
  } catch (error) {
    window.alert(error instanceof Error ? error.message : '复测提交失败')
  } finally {
    retesting.value = false
  }
}

onMounted(async () => {
  try {
    const [p, dict] = await Promise.all([
      fetchTrainingPlan(props.attemptId, props.questionId),
      fetchTagDictionary()
    ])
    plan.value = p
    tagDict.value = dict
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '训练计划加载失败'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.training-panel {
  margin-top: 4px;
}

.state {
  font-size: 13px;
  color: rgba(242, 239, 233, 0.5);
  padding: 10px 0;
}

.state.error {
  color: #e8907a;
}

.state.blocked {
  background: rgba(255, 255, 255, 0.04);
  border: 1px dashed rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  padding: 14px 16px;
}

.blocked-title {
  margin: 0 0 6px;
  font-size: 13.5px;
  font-weight: 600;
  color: #e8a75c;
}

.blocked-reason {
  margin: 0;
  font-size: 12.5px;
  line-height: 1.7;
  color: rgba(242, 239, 233, 0.55);
}

.trigger-note {
  margin-bottom: 10px;
}

.trigger-line {
  margin: 2px 0;
  font-size: 12px;
  color: rgba(232, 167, 92, 0.85);
}

.training-item {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 12px;
  margin-bottom: 8px;
  overflow: hidden;
}

.training-head {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: transparent;
  border: none;
  color: inherit;
  cursor: pointer;
  text-align: left;
}

.t-title {
  font-size: 13.5px;
  font-weight: 600;
  color: #f2efe9;
  min-width: 88px;
}

.t-reason {
  flex: 1;
  font-size: 12px;
  color: rgba(242, 239, 233, 0.5);
  line-height: 1.6;
}

.t-status {
  font-size: 11.5px;
  color: rgba(242, 239, 233, 0.45);
  white-space: nowrap;
}

.t-status.done {
  color: #7fd8a4;
}

.training-body {
  border-top: 1px solid rgba(255, 255, 255, 0.07);
  padding: 14px 16px;
}

.retest-block {
  margin-top: 14px;
  background: rgba(126, 184, 232, 0.06);
  border: 1px solid rgba(126, 184, 232, 0.25);
  border-radius: 12px;
  padding: 14px 16px;
}

.retest-title {
  margin: 0 0 6px;
  font-size: 13.5px;
  font-weight: 600;
  color: #7eb8e8;
}

.retest-note {
  margin: 0 0 12px;
  font-size: 12.5px;
  line-height: 1.7;
  color: rgba(242, 239, 233, 0.55);
}

.retest-options {
  display: flex;
  gap: 10px;
}

.retest-option {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  border: 1px solid rgba(126, 184, 232, 0.4);
  background: rgba(255, 255, 255, 0.05);
  color: #f2efe9;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
}

.retest-option:hover:not(:disabled) {
  border-color: #7eb8e8;
}

.retest-option:disabled {
  opacity: 0.5;
  cursor: default;
}

.retest-feedback {
  margin: 12px 0 0;
  font-size: 13px;
  line-height: 1.7;
  color: #e8907a;
}

.retest-feedback.ok {
  color: #7fd8a4;
}
</style>
