<template>
  <div class="audio-player">
    <audio
      ref="audioEl"
      :src="src"
      preload="auto"
      @play="handlePlay"
      @pause="handlePause"
      @ended="handleEnded"
      @seeking="handleSeeking"
      @timeupdate="handleTimeUpdate"
    ></audio>

    <div class="controls">
      <button class="ctrl-btn" @click="togglePlay">
        {{ playing ? '暂停' : '播放' }}
      </button>

      <div class="progress-wrap">
        <input
          type="range"
          class="progress"
          :max="durationSec || 0"
          :value="currentSec"
          :disabled="controlsLocked"
          @input="onSliderInput"
        />
        <div class="time-row">
          <span>{{ formatTime(currentSec) }}</span>
          <span>{{ durationSec ? formatTime(durationSec) : '--:--' }}</span>
        </div>
      </div>

      <button
        v-if="!controlsLocked"
        class="ctrl-btn secondary"
        @click="replay"
      >
        重播
      </button>
    </div>

    <p v-if="controlsLocked" class="mode-note">
      考试模式：音频不可拖动、不可重播
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import type { ExamMode } from '../../types/listening'

const props = defineProps<{
  src: string
  mode: ExamMode
  /**
   * V2.1: 显式控制播放器交互权限。
   * 'full'   — play/pause/seek/replay 全部允许(新 Exam 规则, 现实容错)
   * 'locked' — 禁止拖动与重播
   * 不传时保持 legacy 行为: exam_mode 锁定, practice_mode 开放。
   */
  controls?: 'locked' | 'full'
}>()

const controlsLocked = computed(() =>
  props.controls ? props.controls === 'locked' : props.mode === 'exam_mode'
)

const emit = defineEmits<{
  (
    e: 'audio-event',
    eventType: 'audio_play' | 'audio_pause' | 'audio_seek' | 'audio_replay' | 'audio_ended',
    payload: Record<string, unknown>
  ): void
}>()

const audioEl = ref<HTMLAudioElement | null>(null)
const playing = ref(false)
const currentSec = ref(0)
const durationSec = ref(0)
/** exam_mode 下阻止拖动: 记住上一个合法位置 */
let lastValidSec = 0
let replaying = false

function positionMs(): number {
  return Math.round((audioEl.value?.currentTime || 0) * 1000)
}

function togglePlay() {
  const el = audioEl.value
  if (!el) return
  if (el.paused) {
    el.play().catch(() => {})
  } else {
    el.pause()
  }
}

function replay() {
  const el = audioEl.value
  if (!el || controlsLocked.value) return
  replaying = true
  lastValidSec = 0
  el.currentTime = 0
  el.play().catch(() => {})
  emit('audio-event', 'audio_replay', { position_ms: 0 })
  replaying = false
}

function onSliderInput(e: Event) {
  const el = audioEl.value
  if (!el || controlsLocked.value) return
  el.currentTime = Number((e.target as HTMLInputElement).value)
}

function handlePlay() {
  playing.value = true
  emit('audio-event', 'audio_play', { position_ms: positionMs() })
}

function handlePause() {
  playing.value = false
  if (audioEl.value && !audioEl.value.ended) {
    emit('audio-event', 'audio_pause', { position_ms: positionMs() })
  }
}

function handleEnded() {
  playing.value = false
  emit('audio-event', 'audio_ended', { position_ms: positionMs() })
}

function handleSeeking() {
  const el = audioEl.value
  if (!el) return
  if (controlsLocked.value && !replaying) {
    // 考试模式: 撤销拖动
    const target = el.currentTime
    if (Math.abs(target - lastValidSec) > 1.5) {
      el.currentTime = lastValidSec
      return
    }
  }
  if (!replaying) {
    emit('audio-event', 'audio_seek', {
      from_ms: Math.round(lastValidSec * 1000),
      to_ms: positionMs()
    })
  }
}

function handleTimeUpdate() {
  const el = audioEl.value
  if (!el) return
  currentSec.value = el.currentTime
  lastValidSec = el.currentTime
  if (el.duration && Number.isFinite(el.duration)) {
    durationSec.value = el.duration
  }
}

function formatTime(sec: number): string {
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

onBeforeUnmount(() => {
  audioEl.value?.pause()
})
</script>

<style scoped>
.audio-player {
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

.ctrl-btn.secondary {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(242, 239, 233, 0.75);
}

.progress-wrap {
  flex: 1;
}

.progress {
  width: 100%;
  accent-color: #e8a75c;
}

.progress:disabled {
  opacity: 0.45;
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
