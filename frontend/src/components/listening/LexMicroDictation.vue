<template>
  <!-- micro_dictation: 听音频，在输入框中打出听到的单词/短语 -->
  <div class="lex-card">
    <div class="task-label">✍️ 拼写听写</div>

    <button class="play-btn" :disabled="playCount >= MAX_PLAYS && answered" @click="speak">
      <span>{{ speaking ? '🔊 播放中' : `▶ 播放（已播 ${playCount} 次）` }}</span>
    </button>
    <div class="hint-txt">听到单词后在下方输入</div>

    <form class="input-row" @submit.prevent="submit">
      <input
        ref="inputEl"
        v-model="typed"
        class="dictation-input"
        :disabled="answered"
        placeholder="输入你听到的词"
        autocomplete="off"
        spellcheck="false"
      />
      <button type="submit" class="submit-btn" :disabled="!typed.trim() || answered">
        提交
      </button>
    </form>

    <div v-if="answered" class="feedback" :class="correct ? 'ok' : 'fail'">
      <span>{{ correct ? '已识别 ✓' : '未识别 ✗' }}</span>
      <span class="reveal">正确：<b>{{ item.surface }}</b>
        <span v-if="item.gloss" class="gloss">— {{ item.gloss }}</span>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, onUnmounted } from 'vue'
import type { LexItem } from '../../types/listening'

const MAX_PLAYS = 3

const props = defineProps<{
  item: LexItem
  autoPlay?: boolean
}>()

const emit = defineEmits<{
  (e: 'done', payload: { is_correct: boolean }): void
}>()

const typed    = ref('')
const answered = ref(false)
const correct  = ref(false)
const speaking = ref(false)
const playCount = ref(0)
const inputEl  = ref<HTMLInputElement | null>(null)

function speak() {
  if (playCount.value >= MAX_PLAYS) return
  if (typeof window === 'undefined' || !window.speechSynthesis) return
  window.speechSynthesis.cancel()
  const utt = new SpeechSynthesisUtterance(props.item.surface)
  utt.lang = 'en-US'
  utt.rate = 0.80
  utt.onstart = () => { speaking.value = true }
  utt.onend   = () => {
    speaking.value = false
    playCount.value++
    nextTick(() => inputEl.value?.focus())
  }
  window.speechSynthesis.speak(utt)
}

function submit() {
  if (answered.value || !typed.value.trim()) return
  const isCorrect = typed.value.trim().toLowerCase() === props.item.surface.toLowerCase()
  correct.value  = isCorrect
  answered.value = true
  setTimeout(() => emit('done', { is_correct: isCorrect }), 1200)
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
.task-label { font-size: 13px; color: rgba(255,255,255,0.45); letter-spacing: 0.05em; }
.play-btn {
  background: rgba(99,179,237,0.15);
  border: 1px solid rgba(99,179,237,0.35);
  color: #90cdf4;
  border-radius: 12px;
  padding: 12px 28px;
  font-size: 15px;
  cursor: pointer;
}
.play-btn:hover:not(:disabled) { background: rgba(99,179,237,0.25); }
.play-btn:disabled { opacity: 0.4; cursor: default; }
.hint-txt { font-size: 13px; color: rgba(255,255,255,0.3); }
.input-row {
  display: flex;
  gap: 10px;
  width: 100%;
  max-width: 360px;
}
.dictation-input {
  flex: 1;
  background: rgba(255,255,255,0.07);
  border: 1px solid rgba(255,255,255,0.18);
  border-radius: 10px;
  color: #fff;
  padding: 10px 14px;
  font-size: 16px;
  outline: none;
}
.dictation-input:focus { border-color: rgba(99,179,237,0.6); }
.dictation-input:disabled { opacity: 0.5; }
.submit-btn {
  background: rgba(99,179,237,0.2);
  border: 1px solid rgba(99,179,237,0.4);
  color: #90cdf4;
  border-radius: 10px;
  padding: 10px 18px;
  font-size: 14px;
  cursor: pointer;
}
.submit-btn:hover:not(:disabled) { background: rgba(99,179,237,0.3); }
.submit-btn:disabled { opacity: 0.35; cursor: default; }
.feedback {
  display: flex; flex-direction: column; align-items: center;
  gap: 6px; font-size: 15px; font-weight: 600; text-align: center;
}
.feedback.ok   { color: #68d391; }
.feedback.fail { color: #fc8181; }
.reveal { font-size: 14px; font-weight: 400; color: rgba(255,255,255,0.75); }
.reveal b { color: #fff; }
.gloss { opacity: 0.55; }
</style>
