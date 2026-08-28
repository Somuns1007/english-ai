<template>
  <div class="unit-group">
    <div class="unit-head">
      <span class="unit-title">{{ unit.display_title }}</span>
      <span v-if="unit.question_range" class="unit-range">
        Questions {{ unit.question_range[0] }}–{{ unit.question_range[1] }}
      </span>
    </div>

    <div
      v-for="q in unit.questions"
      :key="q.question_id"
      class="question-block"
    >
      <div class="q-number">{{ q.number }}.</div>
      <div class="options">
        <button
          v-for="opt in q.options"
          :key="opt.label"
          class="option"
          :class="{ selected: answers[q.question_id] === opt.label }"
          :disabled="disabled"
          @click="$emit('select', q.question_id, q.number, opt.label)"
        >
          <span class="opt-label">{{ opt.label }}</span>
          <span class="opt-text">{{ opt.text_en }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { V2PaperUnit } from '../../types/listening'

/**
 * V2.1 Exam 题组组件。
 * 只渲染: 题号 + A/B/C/D 英文选项。
 * 不渲染: 题干 / 中文 / 解析 / 题型提示 / 考点 / 关键词 / 与音频进度相关的任何高亮。
 */
defineProps<{
  unit: V2PaperUnit
  answers: Record<string, string | null>
  disabled?: boolean
}>()

defineEmits<{
  (e: 'select', questionId: string, number: number, label: string): void
}>()
</script>

<style scoped>
.unit-group {
  display: grid;
  gap: 26px;
}

.unit-head {
  display: flex;
  align-items: baseline;
  gap: 14px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.09);
}

.unit-title {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 1px;
}

.unit-range {
  font-size: 12px;
  color: rgba(242, 239, 233, 0.45);
  letter-spacing: 1px;
}

.question-block {
  display: grid;
  gap: 10px;
}

.q-number {
  font-size: 13px;
  font-weight: 600;
  color: rgba(242, 239, 233, 0.65);
}

.options {
  display: grid;
  gap: 8px;
}

.option {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  text-align: left;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 11px 16px;
  color: #f2efe9;
  font-size: 14px;
  line-height: 1.6;
  cursor: pointer;
  transition:
    border-color 0.15s,
    background 0.15s;
}

.option:hover:not(:disabled) {
  border-color: rgba(232, 167, 92, 0.4);
}

/* selected 只表示"已选择", 不表达对错 */
.option.selected {
  border-color: #e8a75c;
  background: rgba(232, 167, 92, 0.12);
}

.option:disabled {
  cursor: default;
}

.opt-label {
  flex-shrink: 0;
  font-weight: 700;
  color: #e8a75c;
}

.opt-text {
  flex: 1;
  min-width: 0;
  word-break: break-word;
}
</style>
