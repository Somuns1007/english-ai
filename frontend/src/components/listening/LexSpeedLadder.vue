<template>
  <!-- speed_ladder: 显示词义/释义，从3个词中快速选出正确单词（8秒限时） -->
  <div class="lex-card">
    <div class="task-label">⚡ 快速识词</div>

    <!-- 倒计时条 -->
    <div class="timer-bar-wrap">
      <div class="timer-bar" :style="{ width: timerPct + '%' }" :class="{ danger: timerPct < 30 }" />
    </div>
    <div class="timer-txt">{{ timeLeft.toFixed(1) }}s</div>

    <!-- 提示：显示词义（L2/L3）或 "听到的词是？"（L1 无 gloss） -->
    <div class="prompt">
      <span v-if="item.gloss" class="gloss-txt">{{ item.gloss }}</span>
      <span v-else class="gloss-txt muted">请选出你听到的词</span>
    </div>

    <!-- 如果 L1 无 gloss，提供一次语音提示 -->
    <button
      v-if="!item.gloss && !played"
      class="play-hint-btn"
      @click="speakHint"
    >🔊 播放提示</button>

    <!-- 3 个选项 -->
    <div class="options">
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
      {{ correct ? '已识别 ✓' : (timedOut ? '超时 ✗' : '未识别 ✗') }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { LexItem } from '../../types/listening'

const TIME_LIMIT = 8   // seconds

interface Opt { surface: string; isTarget: boolean }

const props = defineProps<{
  item: LexItem
  distractors: LexItem[]   // 2 个干扰项（speed_ladder 共3个选项）
}>()

const emit = defineEmits<{
  (e: 'done', payload: { is_correct: boolean }): void
}>()

const answered  = ref(false)
const correct   = ref(false)
const timedOut  = ref(false)
const selected  = ref<string | null>(null)
const timeLeft  = ref(TIME_LIMIT)
const played    = ref(false)
let   interval: ReturnType<typeof setInterval> | null = null

const timerPct = computed(() => (timeLeft.value / TIME_LIMIT) * 100)

const options = computed<Opt[]>(() => {
  const all: Opt[] = [
    { surface: props.item.surface, isTarget: true },
    ...props.distractors.slice(0, 2).map(d => ({ surface: d.surface, isTarget: false }))
  ]
  return all.sort(() => Math.random() - 0.5)
})

function startTimer() {
  interval = setInterval(() => {
    timeLeft.value = Math.max(0, timeLeft.value - 0.1)
    if (timeLeft.value <= 0) {
      clearInterval(interval!)
      if (!answered.value) {
        timedOut.value = true
        answered.value = true
        setTimeout(() => emit('done', { is_correct: false }), 800)
      }
    }
  }, 100)
}

function select(opt: Opt) {
  if (answered.value) return
  clearInterval(interval!)
  selected.value  = opt.surface
  correct.value   = opt.isTarget
  answered.value  = true
  setTimeout(() => emit('done', { is_correct: opt.isTarget }), 700)
}

function optClass(opt: Opt) {
  if (!answered.value) return {}
  if (opt.isTarget)                    return { correct: true }
  if (opt.surface === selected.value)  return { wrong: true }
  return {}
}

function speakHint() {
  if (typeof window === 'undefined' || !window.speechSynthesis) return
  played.value = true
  const utt = new SpeechSynthesisUtterance(props.item.surface)
  utt.lang = 'en-US'; utt.rate = 0.85
  window.speechSynthesis.speak(utt)
}

onMounted(() => { startTimer() })
onUnmounted(() => {
  clearInterval(interval!)
  window.speechSynthesis?.cancel()
})
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
  gap: 14px;
}
.task-label { font-size: 13px; color: rgba(255,255,255,0.45); letter-spacing: 0.05em; }
.timer-bar-wrap {
  width: 100%; max-width: 340px;
  height: 6px;
  background: rgba(255,255,255,0.1);
  border-radius: 3px;
  overflow: hidden;
}
.timer-bar {
  height: 100%;
  background: #63b3ed;
  border-radius: 3px;
  transition: width 0.1s linear, background 0.3s;
}
.timer-bar.danger { background: #fc8181; }
.timer-txt { font-size: 12px; color: rgba(255,255,255,0.4); }
.prompt {
  min-height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}
.gloss-txt {
  font-size: 18px;
  color: rgba(255,255,255,0.9);
  font-style: italic;
}
.gloss-txt.muted { color: rgba(255,255,255,0.4); font-style: normal; font-size: 14px; }
.play-hint-btn {
  background: rgba(99,179,237,0.12);
  border: 1px solid rgba(99,179,237,0.3);
  color: #90cdf4;
  border-radius: 10px;
  padding: 8px 18px;
  font-size: 13px;
  cursor: pointer;
}
.options {
  display: flex;
  gap: 10px;
  width: 100%;
  max-width: 380px;
}
.opt-btn {
  flex: 1;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.12);
  color: rgba(255,255,255,0.88);
  border-radius: 10px;
  padding: 14px 8px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s;
}
.opt-btn:hover:not(:disabled) { background: rgba(255,255,255,0.12); }
.opt-btn.correct { border-color: #68d391; background: rgba(104,211,145,0.15); color: #68d391; }
.opt-btn.wrong   { border-color: #fc8181; background: rgba(252,129,129,0.12); color: #fc8181; }
.opt-btn:disabled { cursor: default; }
.feedback { font-size: 15px; font-weight: 600; }
.feedback.ok   { color: #68d391; }
.feedback.fail { color: #fc8181; }
</style>
