<template>
  <div class="corpus-page">
    <div class="corpus-container">
      <div class="topbar">
        <button class="back-button" @click="$router.push('/listening')">← 返回听力首页</button>
        <button class="back-button" @click="$router.push('/listening/expressions')">表达迁移训练 →</button>
      </div>

      <section class="hero">
        <p class="eyebrow">Authentic Corpus</p>
        <h1>真实语料库</h1>
        <p class="description">
          这些片段来自许可明确的真实录音, 经过教师审核。先听不看文本, 自己判断场景、
          说话人和关键信息, 再点开文本核对。
        </p>
        <p class="honesty-note">
          每条片段都标注真实来源与许可(attribution), 与 AI 生成内容严格区分。
        </p>
      </section>

      <div v-if="loading" class="state-card"><p>正在加载语料……</p></div>
      <div v-else-if="errorMessage" class="state-card error">
        <p>{{ errorMessage }}</p>
        <button class="retry-button" @click="load">重试</button>
      </div>
      <div v-else-if="clips.length === 0" class="state-card">
        <p>暂无可用的真实语料片段, 教师审核后会出现在这里。</p>
      </div>

      <template v-else>
        <section v-for="group in groupedClips" :key="group.attribution.asset_id" class="asset-group">
          <header class="attribution">
            <h2>{{ group.attribution.title }}</h2>
            <p class="attr-line">
              来源: {{ group.attribution.source_name }}
              <template v-if="group.attribution.source_url">
                · <a :href="group.attribution.source_url" target="_blank" rel="noopener noreferrer">原始出处 ↗</a>
              </template>
            </p>
            <p class="attr-line">
              许可: {{ group.attribution.license }} · 类型: {{ group.attribution.source_type }}
            </p>
          </header>

          <article v-for="clip in group.clips" :key="clip.clip_id" class="clip-card">
            <div class="clip-head">
              <span v-if="clip.communicative_function" class="tag func">{{ clip.communicative_function }}</span>
              <span v-for="t in clip.scenario_tags" :key="t" class="tag">{{ t }}</span>
              <span v-if="clip.difficulty" class="tag diff">{{ clip.difficulty }}</span>
              <span class="duration">{{ formatDuration(clip) }}</span>
            </div>

            <div class="clip-meta">
              <span v-if="clip.speaker_count">{{ clip.speaker_count }} 人对话</span>
              <span v-if="clip.accent">口音: {{ clip.accent }}</span>
              <span v-if="clip.speech_rate">语速: {{ clip.speech_rate }}</span>
            </div>

            <div class="player-row">
              <audio :src="corpusStudentClipAudioUrl(clip.clip_id)" controls preload="none"></audio>
              <button class="reveal-button" @click="toggleTranscript(clip.clip_id)">
                {{ revealed.has(clip.clip_id) ? '隐藏文本' : '显示文本' }}
              </button>
            </div>

            <p v-if="revealed.has(clip.clip_id)" class="transcript">{{ clip.transcript }}</p>

            <div v-if="revealed.has(clip.clip_id) && clip.listening_features.length" class="features">
              <span class="features-label">听力现象:</span>
              <span v-for="f in clip.listening_features" :key="f" class="tag feature">{{ f }}</span>
            </div>

            <div v-if="clip.expression_matches.length" class="matches">
              <span class="features-label">迁移表达:</span>
              <span v-for="m in clip.expression_matches" :key="m.expression_id" class="tag expr">
                {{ m.matched_text }}
              </span>
            </div>
          </article>
        </section>
      </template>

      <p class="footnote">共 {{ clips.length }} 条已审核真实片段 · 教师审核通过后才出现在这里</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  corpusStudentClipAudioUrl,
  corpusStudentClips,
  type StudentCorpusClip
} from '../../services/listeningApi'

const clips = ref<StudentCorpusClip[]>([])
const loading = ref(true)
const errorMessage = ref('')
const revealed = ref(new Set<string>())

const groupedClips = computed(() => {
  const groups = new Map<string, { attribution: StudentCorpusClip['attribution']; clips: StudentCorpusClip[] }>()
  for (const clip of clips.value) {
    const key = clip.attribution.asset_id
    if (!groups.has(key)) groups.set(key, { attribution: clip.attribution, clips: [] })
    groups.get(key)!.clips.push(clip)
  }
  return [...groups.values()]
})

function formatDuration(clip: StudentCorpusClip): string {
  return `${((clip.end_ms - clip.start_ms) / 1000).toFixed(1)}s`
}

function toggleTranscript(clipId: string) {
  const next = new Set(revealed.value)
  if (next.has(clipId)) next.delete(clipId)
  else next.add(clipId)
  revealed.value = next
}

async function load() {
  loading.value = true
  errorMessage.value = ''
  try {
    clips.value = await corpusStudentClips()
  } catch (e) {
    errorMessage.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.corpus-page { min-height: 100vh; background: #f8fafc; padding: 24px 16px 64px; }
.corpus-container { max-width: 860px; margin: 0 auto; }
.topbar { display: flex; justify-content: space-between; margin-bottom: 20px; }
.back-button { background: none; border: 1px solid #cbd5e1; border-radius: 8px; padding: 6px 14px; cursor: pointer; color: #475569; font-size: 14px; }
.back-button:hover { background: #f1f5f9; }
.hero { margin-bottom: 24px; }
.eyebrow { color: #6366f1; font-size: 13px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; margin: 0 0 4px; }
.hero h1 { margin: 0 0 8px; font-size: 26px; color: #0f172a; }
.description { color: #475569; margin: 0 0 8px; line-height: 1.6; }
.honesty-note { color: #92400e; background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 8px 12px; font-size: 13px; margin: 0; }
.state-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 32px; text-align: center; color: #64748b; }
.state-card.error { color: #b91c1c; }
.retry-button { margin-top: 12px; background: #4f46e5; color: #fff; border: none; border-radius: 8px; padding: 8px 20px; cursor: pointer; }
.asset-group { margin-bottom: 28px; }
.attribution { background: #eef2ff; border: 1px solid #c7d2fe; border-radius: 12px; padding: 12px 16px; margin-bottom: 12px; }
.attribution h2 { margin: 0 0 6px; font-size: 17px; color: #312e81; }
.attr-line { margin: 2px 0; font-size: 13px; color: #4338ca; }
.attr-line a { color: #4f46e5; }
.clip-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; margin-bottom: 10px; }
.clip-head { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-bottom: 8px; }
.tag { background: #f1f5f9; color: #475569; border-radius: 6px; padding: 2px 8px; font-size: 12px; }
.tag.func { background: #ecfdf5; color: #047857; }
.tag.diff { background: #fef3c7; color: #b45309; }
.tag.feature { background: #eff6ff; color: #1d4ed8; }
.tag.expr { background: #fdf4ff; color: #a21caf; }
.duration { margin-left: auto; color: #94a3b8; font-size: 12px; }
.clip-meta { display: flex; gap: 14px; color: #64748b; font-size: 13px; margin-bottom: 10px; }
.player-row { display: flex; align-items: center; gap: 12px; }
.player-row audio { flex: 1; height: 36px; }
.reveal-button { background: none; border: 1px solid #c7d2fe; color: #4f46e5; border-radius: 8px; padding: 6px 12px; cursor: pointer; font-size: 13px; white-space: nowrap; }
.transcript { background: #f8fafc; border-left: 3px solid #6366f1; padding: 10px 14px; border-radius: 0 8px 8px 0; color: #334155; line-height: 1.7; margin: 12px 0 0; }
.features, .matches { margin-top: 10px; display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
.features-label { font-size: 12px; color: #94a3b8; }
.footnote { text-align: center; color: #94a3b8; font-size: 13px; margin-top: 24px; }
</style>
