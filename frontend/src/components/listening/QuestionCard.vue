<template>
  <div class="question-card">
    <div class="q-head">
      <span class="q-number">Q{{ question.number }}</span>
      <span v-if="question.review_status === 'needs_review'" class="q-flag">
        题干待校对
      </span>
    </div>

    <p v-if="question.question_text" class="q-text-en">
      {{ question.question_text }}
    </p>
    <p v-if="question.question_text_zh" class="q-text-zh">
      {{ question.question_text_zh }}
    </p>

    <div class="options">
      <button
        v-for="opt in question.options"
        :key="opt.label"
        class="option"
        :class="{ selected: modelValue === opt.label }"
        :disabled="disabled"
        @click="$emit('update:modelValue', opt.label)"
      >
        <span class="opt-label">{{ opt.label }}</span>
        <span class="opt-text">{{ opt.text_en || opt.text }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { PublicQuestion } from '../../types/listening'

defineProps<{
  question: PublicQuestion
  modelValue: string | null
  disabled?: boolean
}>()

defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()
</script>

<style scoped>
.question-card {
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 18px;
  padding: 24px 26px;
}

.q-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.q-number {
  font-size: 13px;
  letter-spacing: 2px;
  color: #e8a75c;
  font-weight: 600;
}

.q-flag {
  font-size: 11px;
  color: rgba(242, 239, 233, 0.35);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 999px;
  padding: 2px 8px;
}

.q-text-en {
  margin: 0;
  font-size: 16px;
  line-height: 1.7;
}

.q-text-zh {
  margin: 8px 0 0;
  font-size: 13px;
  color: rgba(242, 239, 233, 0.5);
  line-height: 1.7;
}

.options {
  margin-top: 18px;
  display: grid;
  gap: 10px;
}

.option {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  text-align: left;
  background: rgba(255, 255, 255, 0.035);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 14px;
  padding: 12px 16px;
  color: #f2efe9;
  font-size: 14px;
  line-height: 1.6;
  cursor: pointer;
  transition:
    border-color 0.2s,
    background 0.2s;
}

.option:hover:not(:disabled) {
  border-color: rgba(232, 167, 92, 0.4);
}

.option.selected {
  border-color: #e8a75c;
  background: rgba(232, 167, 92, 0.12);
}

.option:disabled {
  cursor: default;
  opacity: 0.85;
}

.opt-label {
  flex-shrink: 0;
  font-weight: 700;
  color: #e8a75c;
}

.opt-text {
  flex: 1;
}
</style>
