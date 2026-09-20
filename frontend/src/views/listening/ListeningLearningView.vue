<!-- Optional post-listening study: owned sessions, progressive reveal and contextual review. -->
<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import { currentUser, getMe } from '../../services/authApi'
import { learningRequest, type LearningState, type LearningMaterial, type LearningRecent, type LearningCard, type LearningWord } from '../../services/learningApi'

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
  if (initial || player.currentTime < bounds.start_ms / 1000) player.currentTime = bounds.start_ms / 1000
  if (player.currentTime >= bounds.end_ms / 1000) { player.pause(); player.currentTime = bounds.start_ms / 1000 }
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
    <nav class="learning-nav"><RouterLink to="/listening">← 听力首页</RouterLink><RouterLink to="/listening/learning">我的句段学习与复习</RouterLink></nav>
    <header><p class="eyebrow">POST-LISTENING · PILOT</p><h1>{{ state?.title || '听后句段学习' }}</h1>
      <p>先尝试，再对照。每次解决一个困难就可以结束，不必全文听写。</p></header>
    <p v-if="loading" role="status">正在读取学习记录…</p>
    <section v-else-if="!currentUser" class="panel"><h2>登录后保存学习记录</h2><p>匿名和历史未绑定记录不能自动认领。请先登录，再创建一次新的 Set2 作答或连续练习。</p>
      <RouterLink :to="{ path: '/login', query: { next: route.fullPath } }">去登录</RouterLink></section>
    <p v-if="error" class="error" role="alert">{{ error }} <button :disabled="busy" @click="load">重新加载</button></p>
    <p v-if="notice" class="notice" role="status">{{ notice }}</p>
    <template v-if="currentUser && !loading">
      <section v-if="materials.length" class="panel"><h2>选择本次想学的材料</h2><p>完成作答不代表必须全部复习。可从一个单元开始。</p>
        <button v-for="material in materials" :key="material.material_id" class="material-button" :disabled="busy" @click="start(material.material_id)">{{ material.title }} · {{ material.segment_count }} 个原文句段 →</button></section>
      <template v-if="state">
        <section class="panel"><p class="muted">内部 Pilot · 机器核对内容，未标为教师审核 · 不进入正式能力画像</p>
          <p>{{ state.audio.scope === 'whole_unit' ? '整段回听：没有逐句精确切片，请自行留意困难位置。' : '本单元边界尚未核验，暂提供整套回听；不会自动跳到答案位置。' }}</p>
          <audio ref="audio" :src="state.audio.url" controls preload="none" @loadedmetadata="boundAudio(true)" @timeupdate="boundAudio()" @seeking="boundAudio()" @play="stopRecording(); recordedAudio?.pause()" @error="error = '音频不可用或登录已失效，请重新加载；不会替换为其他版本音频。'" />
          <p class="muted">原文目录保持顺序；文字一旦揭示，之后撤字重听仍属于熟悉材料练习。</p>
        </section>
        <div class="study-layout"><aside class="panel"><h2>原文句段</h2><p class="muted">源句段可能包含多句话。没有答案位置提示。</p>
          <div class="segment-list"><button v-for="(item, index) in state.segments" :key="item.id" :aria-current="selected === index ? 'step' : undefined" :class="{ selected: selected === index }" :disabled="busy" @click="choose(index)">第 {{ item.number }} 段 {{ item.speaker }}<small>{{ item.revealed ? '已对照' : item.attempted ? '已尝试' : '待选择' }}</small></button></div>
        </aside>
        <section v-if="segment" class="panel study"><h2>第 {{ segment.number }} 个句段</h2>
          <p>回听后，写下听到的部分或用中文说说意思；也可以选择“暂时没听出”。</p>
          <label for="learning-answer">我的尝试<textarea id="learning-answer" v-model="text" maxlength="4000" rows="4" :disabled="busy || state.finished" @input="persistDraft" /></label>
          <label for="learning-difficulty">这次哪里不确定<select id="learning-difficulty" v-model="difficulty" :disabled="busy || state.finished" @change="persistDraft"><option value="unsure">还不确定</option><option value="meaning">文字含义也不熟</option><option value="sound">看着认识，声音没认出</option><option value="relation">句子关系没连起来</option><option value="spelling">主要是拼写</option></select></label>
          <p v-if="savedDraft" class="muted">输入尚未同步到账号；点击保存尝试。</p>
          <div class="actions" v-if="!state.finished"><button :disabled="busy" @click="act(() => saveAttempt())">保存尝试</button><button :disabled="busy" @click="act(() => saveAttempt(true))">暂时没听出</button><button :disabled="busy || !segment.attempted" @click="act(reveal)">揭示原文与表达</button></div>
          <template v-if="segment.revealed"><button class="fold" :disabled="busy" @click="folded = !folded">{{ folded ? '重新显示文字' : '收起文字，再听一次' }}</button>
            <div v-if="!folded" class="revealed"><p class="transcript">{{ segment.text }}</p><button :disabled="busy" @click="act(compare)">对照已保存的英文听写</button>
              <div v-if="differences !== null" class="diff"><p>这是文字差异，不是错因诊断；中文复述不适用此对照。</p><p v-if="!differences.length">规范化后的英文文字一致。</p><p v-for="(difference, index) in differences" :key="index">原文：{{ difference.expected.join(' ') || '—' }} ｜ 输入：{{ difference.written.join(' ') || '—' }}</p></div>
              <details v-for="note in segment.guidance" :key="note.id" class="word"><summary>难句研读：{{ note.anchor }}</summary><p>{{ note.gloss }}</p><p>结构：{{ note.structure }}</p><p>再听任务：{{ note.listening }}</p><p>换个情境说：{{ note.transfer }}</p></details>
              <article v-for="word in segment.vocabulary" :key="word.id" class="word"><h3>{{ word.surface }}</h3><p>{{ word.gloss }}</p><details><summary>搭配与新编例句</summary><p>{{ word.example }}</p><p class="muted">教学新编，不是试卷原句；尚无核验的词句音频。</p></details><button :disabled="busy" @click="act(() => collect(word))">加入语境复习</button></article>
              <p v-if="!segment.vocabulary?.length" class="muted">本句没有预设重点词条，不代表没有学习价值。可以只复述意思。</p>
            </div>
            <details><summary>可选：跟读与表达迁移</summary><p>理解后跟读一句，再换成自己的情境说一句。先自我比较，不给发音分数。</p><p>录音仅保存在此页内存，最长60秒，不上传，离开页面即清除。</p>
              <button :disabled="!recorderSupported || busy" @click="record">{{ recording ? '停止录音' : '开始录音' }}</button><p v-if="!recorderSupported">当前浏览器不支持录音，可以跳过。</p><audio v-if="recordingUrl" ref="recordedAudio" :src="recordingUrl" controls @play="audio?.pause()" />
            </details>
          </template>
          <div class="actions"><button :disabled="busy || selected === 0" @click="choose(selected - 1)">上一段</button><button :disabled="busy || selected === state.segments.length - 1" @click="choose(selected + 1)">下一段</button></div>
        </section></div>
        <section class="panel finish"><p>{{ state.finished ? '本次学习已结束。可以回看已揭示内容、收藏和复习词卡。' : '今天学到这里也可以。未完成的句段不算失败。' }}</p><button v-if="!state.finished" :disabled="busy" @click="act(finish)">保存并结束本次学习</button><RouterLink to="/listening/learning">查看我的复习任务 →</RouterLink></section>
      </template>
      <template v-else-if="!sourceId">
        <section class="panel"><h2>到期的语境词卡 · {{ cards.length }}</h2><p class="muted">先看表达回想含义，再展开核对。尚无逐词核验音频，因此只记录语境／文字复习，不记声音识别成绩。</p><p v-if="!cards.length">暂无到期卡片。学完原句后可自选收藏，不必先背词才能听材料。</p>
          <article v-for="card in cards" :key="card.card_id" class="word"><h3>{{ card.surface }}</h3><RouterLink :to="`/listening/learning/${card.session_id}`">回到原材料</RouterLink><button :disabled="busy" @click="act(() => revealCard(card))">回想后展开</button>
            <div v-if="cardDetails[card.card_id]"><p>{{ cardDetails[card.card_id]?.vocabulary.gloss }}</p><p>{{ cardDetails[card.card_id]?.vocabulary.example }}</p><div class="actions"><button :disabled="busy" @click="act(() => gradeCard(card, 1))">还需复习</button><button :disabled="busy" @click="act(() => gradeCard(card, 3))">有些犹豫</button><button :disabled="busy" @click="act(() => gradeCard(card, 5))">这次记得</button></div></div></article>
        </section>
        <section class="panel"><h2>我的学习记录</h2><p v-if="!recent.length">登录后完成一次新的 Set2 连续练习或整套作答，即可从结果页进入。</p><RouterLink v-for="item in recent" :key="item.session_id" class="material-button" :to="`/listening/learning/${item.session_id}`">{{ item.title }} · {{ item.finished ? '回看' : '继续学习' }} →</RouterLink></section>
      </template>
    </template>
  </main>
</template>

<style scoped>
.learning-page{width:100%;box-sizing:border-box;min-width:0;text-align:left}.learning-page *{box-sizing:border-box}.study-layout>.panel{min-width:0}summary{overflow-wrap:anywhere}
.learning-page .actions button{flex:1 1 140px;max-width:100%}
.learning-page{max-width:1100px;margin:auto;padding:28px 20px 80px;color:var(--text);line-height:1.75}.learning-nav,.actions{display:flex;gap:12px;flex-wrap:wrap;align-items:center}.learning-nav{justify-content:space-between;margin-bottom:28px}.eyebrow{font-size:.75rem;letter-spacing:.13em;color:var(--accent)}h1,h2,h3{color:var(--text-h);line-height:1.4}h1{font-size:clamp(1.6rem,4vw,2.3rem)}h2{font-size:1.15rem}h3{font-size:1.05rem}.panel{border:1px solid var(--border);border-radius:18px;padding:24px;margin:20px 0;background:var(--bg)}button,.material-button{min-height:44px;padding:10px 16px;border:1px solid var(--border);border-radius:10px;background:var(--accent-bg);color:var(--text-h);font:inherit;cursor:pointer;text-align:left}button:disabled{opacity:.5;cursor:not-allowed}button:focus-visible,a:focus-visible,textarea:focus-visible,select:focus-visible{outline:3px solid var(--accent);outline-offset:3px}.material-button{display:block;margin:10px 0;text-decoration:none}.study-layout{display:grid;grid-template-columns:220px minmax(0,1fr);gap:20px}.segment-list{display:grid;gap:8px;max-height:65vh;overflow:auto}.segment-list button{display:flex;justify-content:space-between;gap:8px}.segment-list .selected{border-color:var(--accent);background:var(--accent-bg)}small,.muted{font-size:.85rem;color:var(--text)}label{display:block;margin:14px 0}textarea,select{display:block;box-sizing:border-box;width:100%;margin-top:6px;border:1px solid var(--border);border-radius:8px;padding:10px;background:var(--bg);color:var(--text-h);font:inherit}textarea{resize:vertical}audio{width:100%;margin:8px 0}.transcript{font-size:1.12rem;white-space:pre-wrap;overflow-wrap:anywhere}.word{border-top:1px solid var(--border);padding:16px 0}.word button{margin:8px}.fold{margin:16px 0}.error{color:#d34b53;border-left:3px solid currentColor;padding:12px}.notice{background:var(--accent-bg);padding:12px;border-radius:10px}.finish{display:flex;gap:16px;align-items:center;flex-wrap:wrap}.diff{overflow-wrap:anywhere}.diff p{margin:8px 0}summary{cursor:pointer;min-height:44px;line-height:44px}a{color:var(--accent)}@media(max-width:720px){.study-layout{grid-template-columns:1fr;gap:0}.panel{padding:16px}.segment-list{display:flex;overflow:auto;max-height:none}.segment-list button{flex:none}.learning-page{padding:20px 12px 60px}.actions button{flex:1}.study{min-width:0}}
</style>
