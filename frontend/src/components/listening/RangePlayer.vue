<template>
  <div class="range-player">
    <audio
      ref="audioEl"
      :src="src"
      preload="auto"
      @timeupdate="handleTimeUpdate"
      @play="handlePlay"
      @pause="handlePause"
      @ratechange="handleRateChange"
    ></audio>

    <div class="controls">
      <button
        v-if="!finished"
        class="ctrl-btn"
        :disabled="playing"
        @click="startPlay"
      >
        {{ started ? '播放中…' : playLabel }}
      </button>
      <span v-else class="done-tag">播放完成</span>

      <div class="progress-wrap">
        <input
          type="range"
          class="progress"
          :min="startMs"
          :max="endMs"
          :value="currentMs"
          disabled
        />
        <div class="time-row">
          <span>{{ formatTime(relativeSec) }}</span>
          <span>{{ formatTime(totalSec) }}</span>
        </div>
      </div>
    </div>

    <p class="mode-note">
      {{ note }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps<{
  src: string
  startMs: number
  endMs: number
  playLabel: string
  note: string
}>()

const emit = defineEmits<{
  (
    e: 'pass-event',
    eventType: 'start' | 'progress' | 'end' | 'interrupted',
    payload: { position_ms: number }
  ): void
}>()

const audioEl = ref<HTMLAudioElement | null>(null)
const playing = ref(false)
const started = ref(false)
const finished = ref(false)
const currentMs = ref(props.startMs)

let lastProgressMs = -1
let endedEmitted = false

const totalSec = computed(() => Math.round((props.endMs - props.startMs) / 1000))
const relativeSec = computed(() =>
  Math.max(0, Math.round((currentMs.value - props.startMs) / 1000))
)

function positionMs(): number {
  return Math.round((audioEl.value?.currentTime || 0) * 1000)
}

function startPlay() {
  const el = audioEl.value
  if (!el || playing.value || finished.value) return
  // 学生端连续播放锁定原速: 不提供任何倍速控制
  el.playbackRate = 1.0
  if (!started.value) {
    started.value = true
    lastProgressMs = -1
    emit('pass-event', 'start', { position_ms: props.startMs })
  }
  el.currentTime = props.startMs / 1000
  el.play().catch(() => {})
}

function handleRateChange() {
  // 速率锁: 任何外部修改(控制台/插件)立即重置回 1.0
  const el = audioEl.value
  if (el && el.playbackRate !== 1.0) {
    el.playbackRate = 1.0
  }
}

function handlePlay() {
  playing.value = true
}

function handlePause() {
  playing.value = false
  const el = audioEl.value
  if (!el) return
  // 未到达终点的暂停 = 中断(第一遍不允许暂停; 中断不产生证据)
  if (started.value && !endedEmitted && positionMs() < props.endMs - 2000) {
    emit('pass-event', 'interrupted', { position_ms: positionMs() })
  }
}

function handleTimeUpdate() {
  const el = audioEl.value
  if (!el || !started.value) return
  const pos = positionMs()
  currentMs.value = Math.max(props.startMs, Math.min(pos, props.endMs))
  // 到达区间终点: 钳制 + 结束
  if (pos >= props.endMs - 200 && !endedEmitted) {
    endedEmitted = true
    el.pause()
    playing.value = false
    finished.value = true
    currentMs.value = props.endMs
    emit('pass-event', 'end', { position_ms: props.endMs })
    return
  }
  // 心跳: 位置每推进约 4.5s 发一次(服务端要求 <=9s 间距)
  if (lastProgressMs < 0 || pos - lastProgressMs >= 4500) {
    lastProgressMs = pos
    emit('pass-event', 'progress', { position_ms: pos })
  }
}

function handleVisibility() {
  // 切后台/关页: 播放中则记中断(不产生 evidence)
  if (playing.value && !endedEmitted) {
    emit('pass-event', 'interrupted', { position_ms: positionMs() })
    audioEl.value?.pause()
  }
}

function formatTime(sec: number): string {
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

onMounted(() => {
  if (audioEl.value) audioEl.value.playbackRate = 1.0
  document.addEventListener('visibilitychange', handleVisibility)
})

onBeforeUnmount(() => {
  document.removeEventListener('visibilitychange', handleVisibility)
  handleVisibility()
})
</script>

<style scoped>
.range-player {
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 18px;
  padding: 18px 22px;
}

.controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.ctrl-btn {
  border: none;
  border-radius: 12px;
  padding: 10px 20px;
  background: #e8a75c;
  color: #17120c;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  flex-shrink: 0;
}

.ctrl-btn:disabled {
  opacity: 0.55;
  cursor: default;
}

.done-tag {
  color: #7fd8a4;
  font-size: 14px;
  flex-shrink: 0;
}

.progress-wrap {
  flex: 1;
}

.progress {
  width: 100%;
  accent-color: #e8a75c;
}

.progress:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.time-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: rgba(242, 239, 233, 0.45);
  margin-top: 2px;
}

.mode-note {
  margin: 10px 0 0;
  font-size: 12px;
  color: rgba(242, 239, 233, 0.35);
  letter-spacing: 1px;
}
</style>
