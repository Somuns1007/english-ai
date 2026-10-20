<!-- Optional post-listening study: owned sessions, progressive reveal and contextual review. -->
<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import { currentUser, getMe } from '../../services/authApi'
import { learningRequest, type LearningState, type LearningMaterial, type LearningRecent, type LearningCard, type LearningWord } from '../../services/learningApi'
import PlanetCanvas from '../../components/PlanetCanvas.vue'

const route = useRoute()
const router = useRouter()
const state = ref<LearningState | null>(null)
const materials = ref<LearningMaterial[]>([])
const recent = ref<LearningRecent[]>([])
const cards = ref<LearningCard[]>([])
const cardDetails = ref<Record<string, { vocabulary: LearningWord; review_id: string }>>({})
const selected = ref(0)
const text = ref('')
const difficulty = ref('unsure')
const error = ref('')
const notice = ref('')
const busy = ref(false)
const loading = ref(false)
const folded = ref(false)
const savedDraft = ref(false)
const audio = ref<HTMLAudioElement | null>(null)
const clipStartMs = ref<number | null>(null)
const clipEndMs = ref<number | null>(null)
const recording = ref(false)
const recordingUrl = ref('')
const recordedAudio = ref<HTMLAudioElement | null>(null)
let recordingGeneration = 0
const recorderSupported = typeof MediaRecorder !== 'undefined' && !!navigator.mediaDevices?.getUserMedia
const differences = ref<{ type: string; expected: string[]; written: string[] }[] | null>(null)
let controller = new AbortController()
let recorder: MediaRecorder | null = null
let stream: MediaStream | null = null
let recordingTimer: number | undefined
let active = true
let identity: string | null = null
const segment = computed(() => state.value?.segments[selected.value])
const sourceKind = computed(() => typeof route.query.gate_type === 'string' ? route.query.gate_type : '')
const sourceId = computed(() => typeof route.query.gate_id === 'string' ? route.query.gate_id : '')
const draftKey = () => `learning-draft:${identity}:${state.value?.session_id}:${segment.value?.id}`

async function request<T>(path: string, body?: object) {
  const owner = currentUser.value?.id
  const result = await learningRequest<T>(path, body, controller.signal)
  if (!active || owner !== currentUser.value?.id) throw new Error('账号已变化，请重新打开学习记录')
  return result
}
function stopRecording() {
  if (recorder?.state === 'recording') recorder.stop()
  stream?.getTracks().forEach(track => track.stop())
  stream = null
  clearTimeout(recordingTimer)
  recording.value = false
}
function stopMedia() {
  recordingGeneration += 1
  audio.value?.pause()
  if (audio.value) audio.value.playbackRate = 1
  clipStartMs.value = null
  clipEndMs.value = null
  recordedAudio.value?.pause()
  stopRecording()
  if (recordingUrl.value) URL.revokeObjectURL(recordingUrl.value)
  recordingUrl.value = ''
}
function readDraft() {
  text.value = segment.value?.last_attempt?.text ?? ''
  difficulty.value = segment.value?.last_attempt?.difficulty ?? 'unsure'
  savedDraft.value = false
  try {
    const value = sessionStorage.getItem(draftKey())
    if (value) { const draft = JSON.parse(value); text.value = draft.text; difficulty.value = draft.difficulty; savedDraft.value = true }
  } catch { /* Browser storage can be disabled; server-saved attempts remain available. */ }
  differences.value = null
  folded.value = false
}
function persistDraft() {
  if (!state.value || !identity) return
  try { sessionStorage.setItem(draftKey(), JSON.stringify({ text: text.value, difficulty: difficulty.value })); savedDraft.value = true }
  catch { notice.value = '浏览器无法暂存，请点击保存尝试；离开前留意未同步内容。' }
}
async function load() {
  controller.abort(); controller = new AbortController()
  stopMedia()
  state.value = null; materials.value = []; recent.value = []; cards.value = []; cardDetails.value = {}
  text.value = ''; error.value = ''; notice.value = ''; busy.value = false; loading.value = true
  const signal = controller.signal
  try {
    const user = await getMe()
    if (signal.aborted) return
    identity = user?.id ?? null
    if (!user) return
    if (route.params.sessionId) {
      state.value = await request<LearningState>(`/sessions/${encodeURIComponent(String(route.params.sessionId))}`)
      selected.value = Math.max(0, state.value.segments.findIndex(s => s.id === state.value?.last_segment_id))
      readDraft()
    } else if (sourceKind.value && sourceId.value) {
      materials.value = await request<LearningMaterial[]>(`/materials?gate_type=${encodeURIComponent(sourceKind.value)}&gate_id=${encodeURIComponent(sourceId.value)}`)
    } else {
      const result = await Promise.all([request<LearningRecent[]>('/sessions'), request<LearningCard[]>('/cards')])
      recent.value = result[0]; cards.value = result[1]
    }
  } catch (e) { if (!signal.aborted) error.value = e instanceof Error ? e.message : '加载失败' }
  finally { if (!signal.aborted) loading.value = false }
}
async function act(action: () => Promise<void>) {
  if (busy.value) return
  busy.value = true; error.value = ''; notice.value = ''
  try { await action() }
  catch (e) { if (!controller.signal.aborted) error.value = e instanceof Error ? e.message : '操作失败，输入已保留，请重试' }
  finally { busy.value = false }
}
async function start(materialId: string) {
  await act(async () => {
    const result = await request<LearningState>('/sessions', { gate_type: sourceKind.value, gate_id: sourceId.value, material_id: materialId })
    await router.push(`/listening/learning/${result.session_id}`)
  })
}
async function saveAttempt(skip = false) {
  if (!state.value || !segment.value) return
  const key = draftKey()
  const result = await request<LearningState>(`/sessions/${state.value.session_id}/attempts`, {
    request_id: crypto.randomUUID(), segment_id: segment.value.id,
    text: skip ? '' : text.value, difficulty: skip ? 'skip' : difficulty.value,
  })
  state.value = result
  try { sessionStorage.removeItem(key) } catch { /* optional browser storage */ }
  savedDraft.value = false
  notice.value = skip ? '已记录暂时没听出，可以揭示文字。' : '尝试已保存，可以按需揭示文字。'
}
async function reveal() {
  if (!state.value || !segment.value) return
  state.value = await request<LearningState>(`/sessions/${state.value.session_id}/reveal`, {
    request_id: crypto.randomUUID(), segment_id: segment.value.id,
  })
  folded.value = false
}
async function compare() {
  if (!state.value || !segment.value) return
  const result = await request<{ differences: typeof differences.value; note: string }>(
    `/sessions/${state.value.session_id}/compare?segment_id=${encodeURIComponent(segment.value.id)}`)
  differences.value = result.differences; notice.value = result.note
}
function choose(index: number) {
  if (savedDraft.value) persistDraft()
  stopMedia(); selected.value = index; readDraft(); error.value = ''; notice.value = ''
}
function boundAudio(initial = false) {
  const player = audio.value; const bounds = state.value?.audio
  if (!player || !bounds || bounds.start_ms === null || bounds.end_ms === null) return
  if (clipStartMs.value !== null && clipEndMs.value !== null) {
    if (initial || player.currentTime < clipStartMs.value / 1000) player.currentTime = clipStartMs.value / 1000
    if (player.currentTime >= clipEndMs.value / 1000) {
      player.pause()
      player.currentTime = clipStartMs.value / 1000
      player.playbackRate = 1
      clipStartMs.value = null
      clipEndMs.value = null
    }
    return
  }
  if (initial || player.currentTime < bounds.start_ms / 1000) player.currentTime = bounds.start_ms / 1000
  if (player.currentTime >= bounds.end_ms / 1000) { player.pause(); player.currentTime = bounds.start_ms / 1000 }
}
async function playSentence(rate: number) {
  const player = audio.value
  const start = segment.value?.start_ms
  const end = segment.value?.end_ms
  if (!player || start == null || end == null) return
  stopRecording()
  recordedAudio.value?.pause()
  player.pause()
  clipStartMs.value = start
  clipEndMs.value = end
  player.playbackRate = rate
  player.currentTime = start / 1000
  try { await player.play() }
  catch { error.value = '这一句暂时播放不了，请刷新页面重试。' }
}
async function record() {
  if (recording.value) { stopRecording(); return }
  stopMedia()
  const generation = recordingGeneration
  const owner = currentUser.value?.id
  try {
    const input = await navigator.mediaDevices.getUserMedia({ audio: true })
    if (!active || generation !== recordingGeneration || owner !== currentUser.value?.id) { input.getTracks().forEach(t => t.stop()); return }
    stream = input
    const parts: BlobPart[] = []
    recorder = new MediaRecorder(input)
    const mimeType = recorder.mimeType
    recorder.ondataavailable = event => { if (event.data.size) parts.push(event.data) }
    recorder.onstop = () => {
      if (active && generation === recordingGeneration && owner === currentUser.value?.id && parts.length) recordingUrl.value = URL.createObjectURL(new Blob(parts, { type: mimeType || 'audio/webm' }))
    }
    recorder.start(); recording.value = true
    recordingTimer = window.setTimeout(stopRecording, 60000)
  } catch { stopRecording(); error.value = '未获得录音权限或当前浏览器不支持。可以跳过，不影响学习。' }
}
async function finish() {
  if (!state.value) return
  if (savedDraft.value) await saveAttempt()
  state.value = await request<LearningState>(`/sessions/${state.value.session_id}/finish`, { request_id: crypto.randomUUID() })
  stopMedia(); notice.value = '本次学习已保存。无需完成所有句段；之后可以复习已收藏的表达。'
}
async function collect(word: LearningWord) {
  if (!state.value || !segment.value) return
  const result = await request<{ note: string }>(`/sessions/${state.value.session_id}/cards`, { segment_id: segment.value.id, vocabulary_id: word.id })
  notice.value = result.note
}
async function revealCard(card: LearningCard) {
  cardDetails.value[card.card_id] = await request(`/cards/${card.card_id}/reveal`, { request_id: crypto.randomUUID() })
}
async function gradeCard(card: LearningCard, grade: number) {
  const detail = cardDetails.value[card.card_id]
  if (!detail) return
  await request(`/cards/${card.card_id}/grade`, { review_id: detail.review_id, grade, request_id: crypto.randomUUID() })
  cards.value = cards.value.filter(c => c.card_id !== card.card_id)
  delete cardDetails.value[card.card_id]
  notice.value = '已安排下次复习；这是自评记录，不进入能力画像。'
}
watch(() => route.fullPath, load, { immediate: true })
watch(() => currentUser.value?.id, (next, previous) => {
  if (previous && next !== previous) {
    controller.abort(); stopMedia(); state.value = null; materials.value = []; recent.value = []; cards.value = []; cardDetails.value = {}
    text.value = ''; notice.value = ''; differences.value = null; savedDraft.value = false
    identity = next ?? null; error.value = '账号已变化，请重新加载。旧账号内容已清除。'
  }
})
onBeforeRouteLeave(() => {
  if (savedDraft.value && !window.confirm('还有未同步的输入，已尽量暂存在当前浏览器。确定离开？')) return false
  stopMedia()
})
onBeforeUnmount(() => { active = false; controller.abort(); stopMedia() })
</script>

<template>
  <main class="learning-page">
    <PlanetCanvas planet="jupiter" />
    <nav class="learning-nav"><RouterLink to="/listening">← 听力首页</RouterLink><RouterLink to="/listening/learning">我的精听记录和生词本</RouterLink></nav>
    <header><p class="eyebrow">逐句精听</p><h1>{{ state?.title || '逐句精听' }}</h1>
      <p>挑一段没听懂的：先自己听写，再对照原文。弄懂一段就可以结束，不必整篇听写。</p></header>
    <p v-if="loading" role="status">正在读取学习记录…</p>
    <section v-else-if="!currentUser" class="panel"><h2>请先登录</h2><p>逐句精听需要登录后才能使用。未登录时做的题无法补存，请登录后重新做一次第 2 套（整套或单段练习均可），交卷后点「逐句精听」。</p>
      <RouterLink :to="{ path: '/login', query: { next: route.fullPath } }">去登录</RouterLink></section>
    <p v-if="error" class="error" role="alert">{{ error }} <button :disabled="busy" @click="load">重新加载</button></p>
    <p v-if="notice" class="notice" role="status">{{ notice }}</p>
    <template v-if="currentUser && !loading">
      <section v-if="materials.length" class="panel"><h2>选一段来练</h2><p>不用全部练，从最没听懂的一段开始就行。</p>
        <button v-for="material in materials" :key="material.material_id" class="material-button" :disabled="busy" @click="start(material.material_id)">{{ material.title }} · 共 {{ material.segment_count }} 小段 →</button></section>
      <template v-if="state">
        <section class="panel"><p class="muted">提示：原文和讲解已经过机器核对，但尚未经老师逐句审核。</p>
          <p v-if="state.audio.sentence_timing === 'machine_aligned'" class="muted">句子起止是机器对齐的，可能差半秒左右。也可以播放整段录音。</p>
          <p v-else class="muted">这条旧学习记录还没有逐句时间轴，可以播放整段录音。</p>
          <audio ref="audio" :src="state.audio.url" controls preload="none" @loadedmetadata="boundAudio(true)" @timeupdate="boundAudio()" @seeking="boundAudio()" @play="stopRecording(); recordedAudio?.pause()" @error="error = '录音放不出来，可能是登录过期了，请刷新页面重试。'" />
          <p class="muted">看过原文后再听，就属于复习，不再算第一次听。</p>
        </section>
        <div class="study-layout"><aside class="panel"><h2>这一段分成几小段</h2><p class="muted">每一小段可能有好几句话。</p>
          <div class="segment-list"><button v-for="(item, index) in state.segments" :key="item.id" :aria-current="selected === index ? 'step' : undefined" :class="{ selected: selected === index }" :disabled="busy" @click="choose(index)">第 {{ item.number }} 段 {{ item.speaker }}<small>{{ item.revealed ? '已看原文' : item.attempted ? '已听写' : '还没练' }}</small></button></div>
        </aside>
        <section v-if="segment" class="panel study"><h2>第 {{ segment.number }} 小段</h2>
          <p>先听这一小段，把听到的英文写下来（写中文意思也行）。实在听不出，点「没听出来」。</p>
          <div class="actions"><button :disabled="segment.start_ms === null || segment.end_ms === null" @click="playSentence(1)">▶ 听这一句</button><button :disabled="segment.start_ms === null || segment.end_ms === null" @click="playSentence(0.75)">🐢 慢速听</button><span v-if="segment.timing_status === 'needs_check'" class="muted">这句边界待听核</span></div>
          <label for="learning-answer">我听到的<textarea id="learning-answer" v-model="text" maxlength="4000" rows="4" :disabled="busy || state.finished" @input="persistDraft" /></label>
          <label for="learning-difficulty">难在哪里<select id="learning-difficulty" v-model="difficulty" :disabled="busy || state.finished" @change="persistDraft"><option value="unsure">说不清</option><option value="meaning">看了文字也不懂意思</option><option value="sound">单词认识，但没听出来</option><option value="relation">单词都听到了，但句子意思没连起来</option><option value="spelling">听出来了，只是不会拼</option></select></label>
          <p v-if="savedDraft" class="muted">内容还没保存，请点「保存」。</p>
          <div class="actions" v-if="!state.finished"><button :disabled="busy" @click="act(() => saveAttempt())">保存</button><button :disabled="busy" @click="act(() => saveAttempt(true))">没听出来</button><button :disabled="busy || !segment.attempted" @click="act(reveal)">看原文和讲解</button></div>
          <template v-if="segment.revealed"><button class="fold" :disabled="busy" @click="folded = !folded">{{ folded ? '重新显示文字' : '收起文字，再听一次' }}</button>
            <div v-if="!folded" class="revealed"><p class="transcript">{{ segment.text }}</p><button :disabled="busy" @click="act(compare)">对比我的听写</button>
              <div v-if="differences !== null" class="diff"><p>下面列出原文和你写的不一样的地方。如果你写的是中文，可以忽略这个对比。</p><p v-if="!differences.length">完全正确，和原文一致！</p><p v-for="(difference, index) in differences" :key="index">原文：{{ difference.expected.join(' ') || '—' }} ｜ 你写的：{{ difference.written.join(' ') || '—' }}</p></div>
              <div v-if="segment.sound_notes?.length" class="sound-notes"><h3>🎧 发音提示</h3><p class="muted">按发音规则给出的提示，未逐条人工听核。</p>
                <p v-for="note in segment.sound_notes" :key="note.id"><span class="sound-type">{{ note.type }}</span> <strong>{{ note.anchor }}</strong>：{{ note.note }} <button @click="playSentence(1)">▶ 听这一句</button></p>
              </div>
              <details v-for="note in segment.guidance" :key="note.id" class="word"><summary>难句讲解：{{ note.anchor }}</summary><p>意思：{{ note.gloss }}</p><p>结构：{{ note.structure }}</p><p v-if="note.pattern">句型模板：{{ note.pattern }}</p><div v-if="note.examples?.length">套用例句：<p v-for="example in note.examples" :key="example">{{ example }}</p></div><div v-if="note.pitfalls?.length">易错提醒：<p v-for="pitfall in note.pitfalls" :key="pitfall">{{ pitfall }}</p></div><p>再听时注意：{{ note.listening }}</p><p>换个情境说：{{ note.transfer }}</p></details>
              <article v-for="word in segment.vocabulary" :key="word.id" class="word"><h3>{{ word.surface }}</h3><p>释义：{{ word.gloss }}</p><details><summary>搭配和例句</summary><p>原例句：{{ word.example }}</p><div v-if="word.collocations?.length">常用搭配：<p v-for="item in word.collocations" :key="item">{{ item }}</p></div><div v-if="word.more_examples?.length">更多例句：<p v-for="item in word.more_examples" :key="item">{{ item }}</p></div><div v-if="word.pitfalls?.length">易错提醒：<p v-for="item in word.pitfalls" :key="item">{{ item }}</p></div><p v-if="word.listening_trap">听力陷阱：{{ word.listening_trap }}</p><p class="muted">拓展例句没有单独录音。</p></details><button :disabled="busy" @click="act(() => collect(word))">存进生词本</button></article>
              <p v-if="!segment.vocabulary?.length" class="muted">这一小段没有标出生词，能说出大意就行。</p>
            </div>
            <details><summary>可选：跟着读一遍</summary><p>听懂后跟读一遍，再仿照这句话说说自己的情况。录下来自己对比着听，网站不打分。</p><p>录音最长 60 秒，只保存在当前页面，不会上传，离开页面后自动删除。</p>
              <button :disabled="!recorderSupported || busy" @click="record">{{ recording ? '停止录音' : '开始录音' }}</button><p v-if="!recorderSupported">当前浏览器不支持录音，可以跳过。</p><audio v-if="recordingUrl" ref="recordedAudio" :src="recordingUrl" controls @play="audio?.pause()" />
            </details>
          </template>
          <div class="actions"><button :disabled="busy || selected === 0" @click="choose(selected - 1)">上一段</button><button :disabled="busy || selected === state.segments.length - 1" @click="choose(selected + 1)">下一段</button></div>
        </section></div>
        <section class="panel finish"><p>{{ state.finished ? '这次精听已结束。可以回看原文，或去生词本复习。' : '今天练到这里也可以，没练的小段以后再练。' }}</p><button v-if="!state.finished" :disabled="busy" @click="act(finish)">保存并结束</button><RouterLink to="/listening/learning">去生词本复习 →</RouterLink></section>
      </template>
      <template v-else-if="!sourceId">
        <section class="panel"><h2>今天该复习的生词 · {{ cards.length }} 个</h2><p class="muted">先看英文，自己想想是什么意思，再点开对答案。</p><p v-if="!cards.length">今天没有要复习的词。精听时点「存进生词本」，过几天它会出现在这里提醒你复习。</p>
          <article v-for="card in cards" :key="card.card_id" class="word"><h3>{{ card.surface }}</h3><RouterLink :to="`/listening/learning/${card.session_id}`">回到原来那段</RouterLink><button :disabled="busy" @click="act(() => revealCard(card))">想好了，看答案</button>
            <div v-if="cardDetails[card.card_id]"><p>{{ cardDetails[card.card_id]?.vocabulary.gloss }}</p><p>{{ cardDetails[card.card_id]?.vocabulary.example }}</p><div class="actions"><button :disabled="busy" @click="act(() => gradeCard(card, 1))">还需复习</button><button :disabled="busy" @click="act(() => gradeCard(card, 3))">有些犹豫</button><button :disabled="busy" @click="act(() => gradeCard(card, 5))">这次记得</button></div></div></article>
        </section>
        <section class="panel"><h2>我的精听记录</h2><p v-if="!recent.length">还没有记录。做完第 2 套（整套或单段练习），在成绩页点「逐句精听」，就会出现在这里。</p><RouterLink v-for="item in recent" :key="item.session_id" class="material-button" :to="`/listening/learning/${item.session_id}`">{{ item.title }} · {{ item.finished ? '回看' : '继续练' }} →</RouterLink></section>
      </template>
    </template>
  </main>
</template>

<style scoped>
/* ============================================================
   木星 · 聆听巨行星 —— 听后句段学习
   木星是太阳系最强的射电源：在这里听到的每一段音频，
   都是云带之上掠过的电波。横向云带 + 大红斑余晖 + 焦糖金强调色。
   语义色（错误红等）保留，只重写基础视觉层。
   ============================================================ */
.learning-page{
  --jup-ink:#f2ede3;
  --jup-muted:rgba(242,237,227,.62);
  --jup-faint:rgba(242,237,227,.42);
  --jup-accent:#e2ac6e;
  --jup-rust:#d4673a;
  --jup-border:rgba(226,172,110,.16);
  --jup-glass:rgba(30,20,14,.5);

  position:relative;z-index:0;width:100%;min-width:0;box-sizing:border-box;text-align:left;
  max-width:1100px;margin:auto;padding:28px 20px 80px;
  color:var(--jup-muted);line-height:1.75;color-scheme:dark;
  font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;
}
.learning-page *{box-sizing:border-box}
.study-layout>.panel{min-width:0}
summary{overflow-wrap:anywhere}

/* 木星夜空由 <PlanetCanvas planet="jupiter"> 实时绘制：
   交替喷流云带 + 大红斑涡旋 + 极光影帘 */

.learning-nav,.actions{display:flex;gap:12px;flex-wrap:wrap;align-items:center}
.learning-nav{justify-content:space-between;margin-bottom:28px;font-size:14px}
.eyebrow{font-size:.75rem;letter-spacing:.13em;color:var(--jup-accent)}
h1,h2,h3{color:var(--jup-ink);line-height:1.4}
h1{font-size:clamp(1.6rem,4vw,2.3rem);letter-spacing:1px}
h2{font-size:1.15rem}
h3{font-size:1.05rem}

/* 面板：暖棕玻璃 */
.panel{
  border:1px solid var(--jup-border);border-radius:18px;padding:24px;margin:20px 0;
  background:var(--jup-glass);
  backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);
  box-shadow:inset 0 1px 0 rgba(255,226,190,.06);
}

button,.material-button{
  min-height:44px;padding:10px 16px;border:1px solid rgba(226,172,110,.22);border-radius:10px;
  background:rgba(226,172,110,.08);color:var(--jup-ink);
  font:inherit;cursor:pointer;text-align:left;
  transition:border-color .25s ease-out,box-shadow .25s ease-out,background .25s ease-out;
}
button:hover:not(:disabled),.material-button:hover{
  border-color:rgba(226,172,110,.45);
  box-shadow:0 0 18px -6px rgba(226,172,110,.35);
}
button:disabled{opacity:.5;cursor:not-allowed}
button:focus-visible,a:focus-visible,textarea:focus-visible,select:focus-visible{
  outline:2px solid var(--jup-accent);outline-offset:3px;
}
.material-button{display:block;margin:10px 0;text-decoration:none}
.learning-page .actions button{flex:1 1 140px;max-width:100%}

.study-layout{display:grid;grid-template-columns:220px minmax(0,1fr);gap:20px}
.segment-list{display:grid;gap:8px;max-height:65vh;overflow:auto}
.segment-list button{display:flex;justify-content:space-between;gap:8px}
.segment-list .selected{
  border-color:var(--jup-accent);
  background:rgba(226,172,110,.16);
  box-shadow:inset 0 0 12px rgba(226,172,110,.12);
}
small,.muted{font-size:.85rem;color:var(--jup-faint)}
label{display:block;margin:14px 0;color:var(--jup-muted)}

/* 表单控件：深色 + 焦糖金聚焦 */
textarea,select{
  display:block;box-sizing:border-box;width:100%;margin-top:6px;
  border:1px solid rgba(226,172,110,.2);border-radius:10px;padding:10px;
  background:rgba(20,13,9,.6);color:var(--jup-ink);font:inherit;
  transition:border-color .25s ease-out,box-shadow .25s ease-out;
}
textarea:focus,select:focus{
  outline:none;border-color:rgba(226,172,110,.55);
  box-shadow:0 0 0 3px rgba(226,172,110,.13),0 0 18px -6px rgba(226,172,110,.3);
}
textarea{resize:vertical}
audio{width:100%;margin:8px 0}
.sound-notes{border-top:1px solid var(--jup-border);padding:14px 0}
.sound-notes p{line-height:1.7}
.sound-notes button{margin-left:8px}
.sound-type{color:var(--jup-accent);font-weight:700}

.transcript{font-size:1.12rem;white-space:pre-wrap;overflow-wrap:anywhere;color:var(--jup-ink)}
.word{border-top:1px solid var(--jup-border);padding:16px 0}
.word button{margin:8px}
.fold{margin:16px 0}

/* 语义色：错误保持红，提示用焦糖金 */
.error{color:#e0705f;border-left:3px solid currentColor;padding:12px}
.notice{background:rgba(226,172,110,.12);border:1px solid var(--jup-border);padding:12px;border-radius:10px}
.finish{display:flex;gap:16px;align-items:center;flex-wrap:wrap}
.diff{overflow-wrap:anywhere}
.diff p{margin:8px 0}
summary{cursor:pointer;min-height:44px;line-height:44px}
a{color:var(--jup-accent);transition:text-shadow .25s ease-out}
a:hover{text-shadow:0 0 14px rgba(226,172,110,.4)}

@media (prefers-reduced-motion: reduce){
  .learning-page *,.learning-page *::before,.learning-page *::after{
    animation-duration:.01ms !important;transition-duration:.01ms !important;
  }
}

@media(max-width:720px){
  .study-layout{grid-template-columns:1fr;gap:0}
  .panel{padding:16px}
  .segment-list{display:flex;overflow:auto;max-height:none}
  .segment-list button{flex:none}
  .learning-page{padding:20px 12px 60px}
  .actions button{flex:1}
  .study{min-width:0}
}
</style>
