<template>
  <div class="hint-stepper">
    <div class="steps">
      <button
        v-for="level in 5"
        :key="level"
        class="step"
        :class="{
          unlocked: level <= unlockedLevel,
          active: level === activeLevel,
          locked: level > unlockedLevel + 1
        }"
        :disabled="level > unlockedLevel + 1 || opening"
        @click="open(level)"
      >
        <span class="step-no">{{ level }}</span>
        <span class="step-name">{{ stepNames[level - 1] }}</span>
        <span v-if="level > unlockedLevel + 1" class="lock">🔒</span>
      </button>
    </div>

    <div v-if="errorMessage" class="hint-error">{{ errorMessage }}</div>

    <div v-if="current" class="hint-content">
      <p class="hint-title">Level {{ current.level }} · {{ current.title }}</p>

      <!-- L1: 重新听 -->
      <template v-if="current.level === 1">
        <p class="hint-line">{{ content.instruction }}</p>
        <p class="hint-note">{{ content.note }}</p>
      </template>

      <!-- L2: 定位方向 -->
      <template v-else-if="current.level === 2">
        <p v-if="content.question_focus" class="hint-line">
          题干在问：{{ content.question_focus }}
        </p>
        <ul class="hint-list">
          <li v-for="(d, i) in content.directions || []" :key="i">{{ d }}</li>
        </ul>
        <p
          v-if="(content.key_locators || []).length"
          class="hint-note"
        >
          教师定位标记：{{ (content.key_locators || []).join(' · ') }}
        </p>
      </template>

      <!-- L3: 关键词 -->
      <template v-else-if="current.level === 3">
        <div v-if="(content.key_phrases || []).length" class="chips">
          <span v-for="(p, i) in content.key_phrases" :key="i" class="chip">
            {{ p }}
          </span>
        </div>
        <p v-if="content.note" class="hint-note">{{ content.note }}</p>
      </template>

      <!-- L4: 定位原文 -->
      <template v-else-if="current.level === 4">
        <p v-if="content.evidence_text" class="evidence">
          <template v-for="(seg, i) in evidenceSegments" :key="i">
            <mark v-if="seg.hit" class="hl">{{ seg.text }}</mark>
            <span v-else>{{ seg.text }}</span>
          </template>
        </p>
        <p class="hint-note">
          {{ content.note || '定位句按原文标记显示；音频时间戳待校准，暂不支持片段跳转。' }}
        </p>
      </template>

      <!-- L5: 完整解析 -->
      <template v-else>
        <p class="hint-line answer-line">
          正确答案：<strong>{{ content.correct_answer }}</strong>
        </p>
        <p v-if="content.source_explanation" class="hint-line">
          {{ content.source_explanation }}
        </p>
        <p v-if="content.distractor_analysis" class="hint-line dim">
          {{ content.distractor_analysis }}
        </p>
        <div
          v-if="(content.teacher_distractors || []).length"
          class="teacher-box"
        >
          <p class="hint-note">教师标注 · 干扰项逻辑：</p>
          <ul class="hint-list">
            <li v-for="(d, i) in content.teacher_distractors" :key="i">
              选项 {{ d.option }}：{{ d.note }}
              <span v-if="d.source_hook" class="dim">
                （干扰源：{{ d.source_hook }}）
              </span>
            </li>
          </ul>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { openHint } from '../../services/listeningApi'
import type { HintContent } from '../../types/listening'

const props = defineProps<{
  attemptId: string
  questionId: string
  unlockedLevel: number
}>()

const emit = defineEmits<{
  (e: 'unlocked', level: number): void
}>()

const stepNames = ['重新听', '定位方向', '关键词', '定位原文', '完整解析']

const unlockedLevel = ref(props.unlockedLevel)
watch(
  () => props.unlockedLevel,
  (v) => {
    unlockedLevel.value = Math.max(unlockedLevel.value, v)
  }
)

const activeLevel = ref(0)
const cache = ref<Record<number, HintContent>>({})
const opening = ref(false)
const errorMessage = ref('')

const current = computed(() => cache.value[activeLevel.value] || null)
const content = computed<Record<string, any>>(
  () => (current.value?.content as Record<string, any>) || {}
)

/** L4 定位句高亮切分 */
const evidenceSegments = computed(() => {
  const text = (content.value.evidence_text as string) || ''
  const marks = (content.value.highlight as string[]) || []
  if (!text || !marks.length) return [{ text, hit: false }]
  const pattern = marks
    .map((m) => m.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
    .join('|')
  const re = new RegExp(`(${pattern})`, 'gi')
  return text
    .split(re)
    .filter((s) => s.length)
    .map((s) => ({
      text: s,
      hit: marks.some((m) => m.toLowerCase() === s.toLowerCase())
    }))
})

async function open(level: number) {
  activeLevel.value = level
  errorMessage.value = ''
  if (cache.value[level]) return
  opening.value = true
  try {
    const result = await openHint(props.attemptId, props.questionId, level)
    cache.value[level] = result
    if (level > unlockedLevel.value) {
      unlockedLevel.value = level
      emit('unlocked', level)
    }
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : '提示打开失败'
  } finally {
    opening.value = false
  }
}
</script>

<style scoped>
.hint-stepper {
  margin-top: 16px;
}

.steps {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.step {
  display: flex;
  align-items: center;
  gap: 6px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.04);
  color: rgba(242, 239, 233, 0.6);
  font-size: 12px;
  padding: 7px 12px;
  cursor: pointer;
}

.step .step-no {
  font-weight: 700;
  color: #e8a75c;
}

.step.unlocked {
  border-color: rgba(232, 167, 92, 0.4);
}

.step.active {
  background: rgba(232, 167, 92, 0.15);
  border-color: #e8a75c;
}

.step.locked {
  opacity: 0.45;
  cursor: not-allowed;
}

.hint-error {
  margin-top: 10px;
  font-size: 13px;
  color: #e8907a;
}

.hint-content {
  margin-top: 14px;
  border: 1px solid rgba(232, 167, 92, 0.2);
  border-radius: 14px;
  padding: 16px 18px;
  background: rgba(232, 167, 92, 0.05);
}

.hint-title {
  margin: 0 0 10px;
  font-size: 12px;
  letter-spacing: 2px;
  color: #e8a75c;
}

.hint-line {
  margin: 6px 0;
  font-size: 14px;
  line-height: 1.8;
}

.hint-list {
  margin: 6px 0;
  padding-left: 18px;
  font-size: 14px;
  line-height: 1.9;
}

.hint-note {
  margin: 10px 0 0;
  font-size: 12px;
  color: rgba(242, 239, 233, 0.45);
  line-height: 1.7;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  border: 1px solid rgba(232, 167, 92, 0.35);
  border-radius: 999px;
  padding: 4px 12px;
  font-size: 13px;
  color: #e8a75c;
}

.evidence {
  margin: 4px 0;
  font-size: 14px;
  line-height: 1.9;
}

.hl {
  background: rgba(232, 167, 92, 0.35);
  color: #f2efe9;
  border-radius: 4px;
  padding: 0 3px;
}

.answer-line strong {
  color: #e8a75c;
  font-size: 16px;
}

.dim {
  color: rgba(242, 239, 233, 0.55);
}

.teacher-box {
  margin-top: 12px;
  border-top: 1px dashed rgba(255, 255, 255, 0.12);
  padding-top: 10px;
}
</style>
