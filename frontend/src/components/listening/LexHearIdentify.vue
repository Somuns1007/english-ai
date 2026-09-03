<template>
  <!-- hear_identify: 播放单词音频，从4个选项中选出听到的单词 -->
  <div class="lex-card">
    <div class="task-label">🎧 听音识词</div>

    <button class="play-btn" :disabled="played && answered" @click="speak">
      <span class="play-icon">{{ speaking ? '🔊' : '▶' }}</span>
      <span>{{ playCount === 0 ? '播放' : `再播（${playCount}）` }}</span>
    </button>
    <div v-if="!played" class="hint-txt">点击播放后作答</div>

    <div v-if="played" class="options">
      <button
        v-for="opt in options"
        :key="opt.surface"
        class="opt-btn"
        :class="optClass(opt)"
        :disabled="answered"
        @click="select(opt)"
      >
        {{ opt.surface }}
      </button>
    </div>

    <div v-if="answered" class="feedback" :class="correct ? 'ok' : 'fail'">
      <span>{{ correct ? '已识别 ✓' : '未识别 ✗' }}</span>
      <span class="correct-word">正确：{{ item.surface }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { LexItem } from '../../types/listening'

interface Opt { surface: string; isTarget: boolean }

const props = defineProps<{
  item: LexItem
  distractors: LexItem[]   // 3 个干扰项
  autoPlay?: boolean
}>()

const emit = defineEmits<{
  (e: 'done', payload: { is_correct: boolean }): void
}>()

const played   = ref(false)
const speaking = ref(false)
const answered = ref(false)
const selected = ref<string | null>(null)
const playCount = ref(0)

// 构建4个选项（1正确 + 3干扰），随机打乱
const options = computed<Opt[]>(() => {
  const all: Opt[] = [
    { surface: props.item.surface, isTarget: true },
    ...props.distractors.slice(0, 3).map(d => ({ surface: d.surface, isTarget: false }))
  ]
  return all.sort(() => Math.random() - 0.5)
})

const correct = computed(() => selected.value === props.item.surface)

function speak() {
  if (typeof window === 'undefined' || !window.speechSynthesis) return
  window.speechSynthesis.cancel()
  const utt = new SpeechSynthesisUtterance(props.item.surface)
  utt.lang = 'en-US'
  utt.rate = 0.85
  utt.onstart = () => { speaking.value = true }
  utt.onend   = () => { speaking.value = false; played.value = true }
  window.speechSynthesis.speak(utt)
  playCount.value++
}

function select(opt: Opt) {
  if (answered.value) return
  selected.value = opt.surface
  answered.value = true
  setTimeout(() => emit('done', { is_correct: opt.isTarget }), 900)
}

function optClass(opt: Opt) {
  if (!answered.value) return {}
  if (opt.isTarget)                           return { correct: true }
  if (opt.surface === selected.value)         return { wrong: true }
  return {}
}

onMounted(() => { if (props.autoPlay !== false) setTimeout(speak, 300) })
onUnmounted(() => window.speechSynthesis?.cancel())
</script>

<style scoped>
.lex-card {
  background: rgba(255,255,255,0.045);
  border: 1px solid rgba(255,255,255,0.09);
  border-radius: 18px;
  padding: 28px 26px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18px;
}
.task-label {
  font-size: 13px;
  color: rgba(255,255,255,0.45);
  letter-spacing: 0.05em;
}
.play-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(99,179,237,0.15);
  border: 1px solid rgba(99,179,237,0.35);
  color: #90cdf4;
  border-radius: 12px;
  padding: 14px 28px;
  font-size: 17px;
  cursor: pointer;
  transition: background 0.2s;
}
.play-btn:hover:not(:disabled) { background: rgba(99,179,237,0.25); }
.play-btn:disabled { opacity: 0.4; cursor: default; }
.play-icon { font-size: 22px; }
.hint-txt  { font-size: 13px; color: rgba(255,255,255,0.3); }
.options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  width: 100%;
  max-width: 380px;
}
.opt-btn {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.12);
  color: rgba(255,255,255,0.88);
  border-radius: 10px;
  padding: 12px 8px;
  font-size: 15px;
  cursor: pointer;
  transition: background 0.15s;
}
.opt-btn:hover:not(:disabled) { background: rgba(255,255,255,0.12); }
.opt-btn.correct { border-color: #68d391; background: rgba(104,211,145,0.15); color: #68d391; }
.opt-btn.wrong   { border-color: #fc8181; background: rgba(252,129,129,0.12); color: #fc8181; }
.opt-btn:disabled { cursor: default; }
.feedback {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  font-size: 15px;
  font-weight: 600;
}
.feedback.ok   { color: #68d391; }
.feedback.fail { color: #fc8181; }
.correct-word { font-size: 13px; font-weight: 400; opacity: 0.7; }
</style>
