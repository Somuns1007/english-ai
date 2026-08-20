<template>
  <TeacherGate>
  <div class="teacher-page">
    <div class="teacher-container">
      <div class="topbar">
        <button class="back-button" @click="$router.push('/listening/teacher/corpus')">
          ← 返回语料列表
        </button>
      </div>

      <div v-if="loading" class="state-card"><p>正在加载……</p></div>
      <div v-else-if="errorMessage" class="state-card error"><p>{{ errorMessage }}</p></div>

      <template v-else-if="asset">
        <section class="hero">
          <p class="eyebrow">Corpus Asset</p>
          <h1>{{ asset.title }}</h1>
          <p class="meta-line">
            {{ asset.source_name }} · {{ asset.license }}
            <span class="badge" :class="`rs-${asset.review_status}`">{{ statusLabel(asset.review_status) }}</span>
            <span class="badge" :class="asset.permission_status === 'unverified' ? 'rs-rejected' : 'rs-approved'">
              {{ permissionLabel(asset.permission_status) }}
            </span>
            <span class="rev">rev {{ asset.revision }}</span>
          </p>
          <p v-if="asset.source_url" class="meta-line dim">{{ asset.source_url }}</p>
        </section>

        <!-- 许可与审核 -->
        <section class="card">
          <h2 class="card-title">来源与许可</h2>
          <div class="field-grid">
            <label class="field">
              <span>许可状态</span>
              <select v-model="permEdit">
                <option value="unverified">unverified(未核实)</option>
                <option value="verified_open_license">verified_open_license</option>
                <option value="owned">owned</option>
              </select>
            </label>
            <label class="field">
              <span>许可证</span>
              <input v-model="licenseEdit" />
            </label>
          </div>
          <!-- Phase 7.7: 自建录音授权链(owned 必填 consent_id 才能批准/进学生端) -->
          <template v-if="permEdit === 'owned'">
            <p v-if="!consentEdit.consent_id" class="consent-warning">
              ⚠ 自有录音缺少 consent_id —— 无法批准, 也不会进入学生端。请先完成授权登记(docs/recording_kit/04_consent_log.md)。
            </p>
            <div class="field-grid">
              <label class="field">
                <span>授权编号 consent_id</span>
                <input v-model="consentEdit.consent_id" placeholder="CONSENT-2026-0001" />
              </label>
              <label class="field">
                <span>录音者(匿名ID, 逗号分隔)</span>
                <input v-model="consentEdit.speakerIdsText" placeholder="SPK_A, SPK_B" />
              </label>
              <label class="field">
                <span>录音日期</span>
                <input v-model="consentEdit.recorded_at" placeholder="2026-08-21" />
              </label>
            </div>
            <div class="consent-checks">
              <label><input type="checkbox" v-model="consentEdit.commercial_permission" /> 商用授权</label>
              <label><input type="checkbox" v-model="consentEdit.editing_permission" /> 剪辑/加工授权</label>
              <label><input type="checkbox" v-model="consentEdit.ai_processing_permission" /> AI 处理授权(不含声音克隆)</label>
            </div>
          </template>
          <div class="actions">
            <button class="btn" :disabled="busy" @click="saveMeta">保存元数据</button>
            <button class="btn approve" :disabled="busy" @click="reviewAsset('approve')">批准素材</button>
            <button class="btn reject" :disabled="busy" @click="reviewAsset('reject')">拒绝</button>
          </div>
        </section>

        <!-- 流水线 -->
        <section class="card">
          <h2 class="card-title">
            处理流水线
            <span class="pipeline-state">{{ pipelineLabel(asset.pipeline_status) }}</span>
          </h2>
          <div class="actions">
            <button class="btn" :disabled="busy" @click="runStep('run-asr')">
              ① 运行 ASR{{ asset.pipeline_status !== 'uploaded' ? '(重跑)' : '' }}
            </button>
            <button class="btn" :disabled="busy || !asrDone" @click="runStep('run-segmentation')">
              ② 语义切分{{ segmented ? '(重跑, 清除未审核 clip)' : '' }}
            </button>
            <button class="btn" :disabled="busy || !segmented" @click="runStep('run-matching')">
              ③ Expression 匹配{{ asset.pipeline_status === 'matched' ? '(重跑)' : '' }}
            </button>
          </div>
          <p v-if="asset.pipeline_error" class="error-line">{{ asset.pipeline_error }}</p>
          <details v-if="asset.raw_asr_text" class="raw-asr">
            <summary>
              原始 ASR 文本(置信度 {{ asset.asr_confidence ?? '—' }}, 状态 {{ asset.transcript_status }})
            </summary>
            <p>{{ asset.raw_asr_text }}</p>
          </details>
        </section>

        <!-- 教师手工创建 clip(用官方注释/参考文本定位教学目标段) -->
        <section class="card">
          <h2 class="card-title">手工创建 clip(参考注释定位)</h2>
          <div class="field-grid">
            <label class="field">
              <span>start_ms</span>
              <input type="number" v-model.number="newClip.start_ms" />
            </label>
            <label class="field">
              <span>end_ms</span>
              <input type="number" v-model.number="newClip.end_ms" />
            </label>
            <label class="field">
              <span>说话人(可选)</span>
              <input v-model="newClip.speaker_info" placeholder="A,B" />
            </label>
          </div>
          <label class="field">
            <span>参考 transcript(可选, 可先用官方注释文本, 审核时再校)</span>
            <textarea v-model="newClip.transcript" rows="3"></textarea>
          </label>
          <div class="actions">
            <button class="btn" :disabled="busy" @click="createClip">创建手工 clip</button>
          </div>
        </section>

        <!-- Clip 审核 -->
        <section v-for="c in asset.clips" :key="c.clip_id" class="card">
          <div class="card-head">
            <h2 class="card-title">
              Clip {{ fmtMs(c.start_ms) }} – {{ fmtMs(c.end_ms) }}
              <span class="rev">内容 v{{ c.content_revision ?? c.revision }}</span>
              <span class="rev rev-meta">元数据 v{{ c.metadata_revision ?? 1 }}</span>
            </h2>
            <span class="badge" :class="`rs-${c.review_status}`">{{ statusLabel(c.review_status) }}</span>
          </div>

          <!-- 区间播放 -->
          <div class="audio-row">
            <audio
              :ref="(el) => setAudioRef(c.clip_id, el)"
              :src="audioUrl"
              preload="auto"
              controls
              @timeupdate="(e) => onTimeUpdate(c, e)"
            ></audio>
            <button class="btn small" @click="playSegment(c)">▶ 播放区间</button>
          </div>
          <div class="field-grid">
            <label class="field">
              <span>start_ms</span>
              <input type="number" v-model.number="clipEdits[c.clip_id].start_ms" />
            </label>
            <label class="field">
              <span>end_ms</span>
              <input type="number" v-model.number="clipEdits[c.clip_id].end_ms" />
            </label>
            <label class="field">
              <span>难度</span>
              <select v-model="clipEdits[c.clip_id].difficulty">
                <option :value="null">未标</option>
                <option value="easy">easy</option>
                <option value="medium">medium</option>
                <option value="hard">hard</option>
              </select>
            </label>
          </div>
          <label class="field">
            <span>transcript(修改产生新 revision, 原始 ASR 保留在素材层)</span>
            <textarea v-model="clipEdits[c.clip_id].transcript" rows="3"></textarea>
          </label>
          <div class="field-grid">
            <label class="field">
              <span>场景标签(逗号分隔)</span>
              <input v-model="clipEdits[c.clip_id].tagsText" placeholder="travel, phone" />
            </label>
            <label class="field">
              <span>交际功能</span>
              <input v-model="clipEdits[c.clip_id].communicative_function" />
            </label>
            <label class="field">
              <span>口音</span>
              <select v-model="clipEdits[c.clip_id].accent">
                <option :value="null">未标</option>
                <option value="american">american</option>
                <option value="british">british</option>
                <option value="mixed_native">mixed_native</option>
                <option value="non_native">non_native</option>
                <option value="mixed_non_native">mixed_non_native</option>
              </select>
            </label>
            <label class="field">
              <span>说话人数</span>
              <input type="number" min="1" v-model.number="clipEdits[c.clip_id].speaker_count" />
            </label>
            <label class="field">
              <span>语速</span>
              <select v-model="clipEdits[c.clip_id].speech_rate">
                <option :value="null">未标</option>
                <option value="slow">slow</option>
                <option value="normal">normal</option>
                <option value="fast">fast</option>
              </select>
            </label>
          </div>
          <div class="field">
            <span>听力现象(listening_features)</span>
            <div class="feature-checks">
              <label v-for="f in LISTENING_FEATURES" :key="f" class="feature-check">
                <input
                  type="checkbox"
                  :checked="clipEdits[c.clip_id].featuresSet.has(f)"
                  @change="toggleFeature(c.clip_id, f)"
                />
                {{ f }}
              </label>
            </div>
          </div>

          <div v-if="c.expression_matches.length" class="matches">
            <span class="matches-title">匹配到的表达(教师确认后才算正式关联):</span>
            <span
              v-for="m in c.expression_matches"
              :key="m.expression_id + m.status"
              class="match-tag"
              :class="{ 'match-approved': m.status === 'approved', 'match-rejected': m.status === 'rejected' }"
            >
              {{ m.expression_id }}({{ m.match_type }}/{{ m.match_method || '?' }}, conf={{ m.confidence ?? '?' }}: "{{ m.matched_text }}")
              <em v-if="m.note" class="match-note">{{ m.note }}</em>
              <template v-if="m.status === 'candidate'">
                [候选
                <button class="match-btn" :disabled="busy" @click="reviewMatch(c.clip_id, m.expression_id, 'approve')">确认</button>
                <button class="match-btn reject" :disabled="busy" @click="reviewMatch(c.clip_id, m.expression_id, 'reject')">否决</button>]
              </template>
              <template v-else>[{{ m.status === 'approved' ? '已确认' : '已否决' }}]</template>
            </span>
          </div>

          <!-- Phase 7.7: 教师手动建立匹配(真人功能等价表达 → communicative_equivalent) -->
          <details class="add-match">
            <summary>＋ 手动添加匹配(规则没抓到的真实说法 / 功能等价)</summary>
            <div class="field-grid">
              <label class="field">
                <span>目标表达</span>
                <select v-model="addMatch[c.clip_id].expression_id">
                  <option value="">选择表达…</option>
                  <option v-for="e in expressions" :key="e.expression_id" :value="e.expression_id">
                    {{ e.expression }}
                  </option>
                </select>
              </label>
              <label class="field">
                <span>匹配类型</span>
                <select v-model="addMatch[c.clip_id].match_type">
                  <option value="communicative_equivalent">communicative_equivalent(功能等价)</option>
                  <option value="related_expression">related_expression</option>
                  <option value="exact_expression">exact_expression</option>
                  <option value="target_surface">target_surface</option>
                </select>
              </label>
            </div>
            <label class="field">
              <span>录音中的原话(matched_text)</span>
              <input v-model="addMatch[c.clip_id].matched_text" placeholder="we don't have any rooms available" />
            </label>
            <label class="field">
              <span>教师判断依据 note</span>
              <input v-model="addMatch[c.clip_id].note" placeholder="真人口语等价说法, 未使用目标词" />
            </label>
            <div class="actions">
              <button class="btn" :disabled="busy" @click="submitAddMatch(c.clip_id)">建立关联(直接生效)</button>
            </div>
          </details>

          <div class="review-checklist">
            <span class="matches-title">批准前自查:</span>
            <span>□ 音质可教学 □ 上下文完整 □ 表达自然 □ 难度合适 □ 有迁移训练价值(仅含某表达不足以批准)</span>
          </div>

          <details v-if="c.context_before || c.context_after" class="context">
            <summary>上下文</summary>
            <p v-if="c.context_before"><em>前:</em> {{ c.context_before }}</p>
            <p v-if="c.context_after"><em>后:</em> {{ c.context_after }}</p>
          </details>

          <details v-if="c.revisions_log.length" class="context">
            <summary>revision 历史({{ c.revisions_log.length }})</summary>
            <p v-for="(r, i) in c.revisions_log" :key="i" class="rev-line">
              <template v-if="r.bump">
                内容 v{{ r.content_revision }} · 元数据 v{{ r.metadata_revision }} ·
                {{ r.edited_at.slice(0, 19) }} · 修改: {{ r.changed_fields.join(', ') }}
                {{ r.bump === 'content' ? '(实质修改, 已回落待审核)' : '(仅元数据)' }}
              </template>
              <template v-else>
                rev {{ r.revision }} · {{ r.edited_at.slice(0, 19) }} ·
                修改: {{ r.changed_fields.join(', ') }}
                {{ r.substantive ? '(实质修改, 已回落待审核)' : '' }}
              </template>
            </p>
          </details>

          <div class="actions">
            <button class="btn" :disabled="busy" @click="saveClip(c.clip_id)">保存修改</button>
            <button class="btn approve" :disabled="busy" @click="reviewClip(c.clip_id, 'approve')">批准 clip</button>
            <button class="btn reject" :disabled="busy" @click="reviewClip(c.clip_id, 'reject')">拒绝</button>
          </div>
        </section>

        <p v-if="toast" class="toast">{{ toast }}</p>
      </template>
    </div>
  </div>
  </TeacherGate>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import TeacherGate from './TeacherGate.vue'
import {
  corpusAssetAudioUrl,
  corpusAssetDetail,
  corpusAddClipMatch,
  corpusCreateClip,
  corpusReviewAsset,
  corpusReviewClip,
  corpusReviewClipMatch,
  corpusRunStep,
  corpusUpdateAsset,
  corpusUpdateClip,
  teacherFetchExpressions,
  type CorpusAsset,
  type CorpusClip
} from '../../services/listeningApi'

const LISTENING_FEATURES = [
  'weak_form', 'linking', 'reduction', 'hesitation', 'self_correction',
  'interruption', 'discourse_marker', 'implicit_meaning', 'paraphrase'
]

const route = useRoute()
const assetId = String(route.params.assetId)

const asset = ref<(CorpusAsset & { clips: CorpusClip[] }) | null>(null)
const loading = ref(true)
const errorMessage = ref('')
const busy = ref(false)
const toast = ref('')

const permEdit = ref('unverified')
const licenseEdit = ref('')
const consentEdit = ref({
  consent_id: '',
  speakerIdsText: '',
  recorded_at: '',
  commercial_permission: false,
  editing_permission: false,
  ai_processing_permission: false
})
const clipEdits = ref<Record<string, any>>({})
const addMatch = ref<Record<string, any>>({})
const expressions = ref<{ expression_id: string; expression: string }[]>([])
const newClip = ref({ start_ms: 0, end_ms: 0, transcript: '', speaker_info: '' })
const audioRefs = new Map<string, HTMLAudioElement>()

const audioUrl = computed(() => corpusAssetAudioUrl(assetId))
const asrDone = computed(() =>
  ['asr_done', 'segmented', 'matched'].includes(asset.value?.pipeline_status || '')
)
const segmented = computed(() =>
  ['segmented', 'matched'].includes(asset.value?.pipeline_status || '')
)

function setAudioRef(clipId: string, el: any) {
  if (el) audioRefs.set(clipId, el as HTMLAudioElement)
}

function playSegment(c: CorpusClip) {
  const el = audioRefs.get(c.clip_id)
  if (!el) return
  el.currentTime = c.start_ms / 1000
  el.play()
}

function onTimeUpdate(c: CorpusClip, e: Event) {
  const el = e.target as HTMLAudioElement
  if (el.currentTime * 1000 >= c.end_ms) el.pause()
}

function fmtMs(ms: number): string {
  return `${(ms / 1000).toFixed(1)}s`
}

function statusLabel(s: string): string {
  return { pending_teacher: '待审核', approved: '已批准', rejected: '已拒绝' }[s] || s
}

function permissionLabel(s: string): string {
  return { unverified: '许可未核实', verified_open_license: '开放许可', owned: '自有版权' }[s] || s
}

function pipelineLabel(s: string): string {
  return {
    uploaded: '已上传(待 ASR)',
    asr_done: 'ASR 完成(待切分)',
    segmented: '切分完成(待匹配)',
    matched: '匹配完成(待审核)'
  }[s] || s
}

function showToast(msg: string) {
  toast.value = msg
  setTimeout(() => (toast.value = ''), 3000)
}

async function load() {
  loading.value = true
  errorMessage.value = ''
  try {
    asset.value = await corpusAssetDetail(assetId)
    permEdit.value = asset.value.permission_status
    licenseEdit.value = asset.value.license
    consentEdit.value = {
      consent_id: asset.value.consent_id || '',
      speakerIdsText: (asset.value.speaker_ids || []).join(', '),
      recorded_at: asset.value.recorded_at || '',
      commercial_permission: !!asset.value.commercial_permission,
      editing_permission: !!asset.value.editing_permission,
      ai_processing_permission: !!asset.value.ai_processing_permission
    }
    const edits: Record<string, any> = {}
    const adds: Record<string, any> = {}
    for (const c of asset.value.clips) {
      edits[c.clip_id] = {
        start_ms: c.start_ms,
        end_ms: c.end_ms,
        transcript: c.transcript,
        tagsText: (c.scenario_tags || []).join(', '),
        communicative_function: c.communicative_function || '',
        difficulty: c.difficulty,
        accent: c.accent,
        speaker_count: c.speaker_count,
        speech_rate: c.speech_rate,
        featuresSet: new Set(c.listening_features || [])
      }
      if (!addMatch.value[c.clip_id]) {
        adds[c.clip_id] = {
          expression_id: '',
          match_type: 'communicative_equivalent',
          matched_text: '',
          note: ''
        }
      }
    }
    clipEdits.value = edits
    addMatch.value = { ...adds, ...addMatch.value }
  } catch (e) {
    errorMessage.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function saveMeta() {
  busy.value = true
  try {
    await corpusUpdateAsset(assetId, {
      permission_status: permEdit.value,
      license: licenseEdit.value,
      consent_id: consentEdit.value.consent_id || undefined,
      speaker_ids: consentEdit.value.speakerIdsText
        .split(',').map((x: string) => x.trim()).filter(Boolean),
      recorded_at: consentEdit.value.recorded_at || undefined,
      commercial_permission: consentEdit.value.commercial_permission,
      editing_permission: consentEdit.value.editing_permission,
      ai_processing_permission: consentEdit.value.ai_processing_permission
    })
    showToast('元数据已保存')
    await load()
  } catch (e) {
    showToast(e instanceof Error ? e.message : '保存失败')
  } finally {
    busy.value = false
  }
}

async function submitAddMatch(clipId: string) {
  const a = addMatch.value[clipId]
  if (!a || !a.expression_id || !a.matched_text.trim()) {
    showToast('请先选择目标表达并填写录音中的原话')
    return
  }
  busy.value = true
  try {
    await corpusAddClipMatch(clipId, {
      expression_id: a.expression_id,
      matched_text: a.matched_text.trim(),
      match_type: a.match_type,
      note: a.note.trim() || undefined
    })
    addMatch.value[clipId] = {
      expression_id: '', match_type: 'communicative_equivalent',
      matched_text: '', note: ''
    }
    showToast('已建立匹配(teacher_judgement, 直接生效)')
    await load()
  } catch (err) {
    showToast(err instanceof Error ? err.message : '建立失败')
  } finally {
    busy.value = false
  }
}

async function reviewAsset(action: 'approve' | 'reject') {
  busy.value = true
  try {
    await corpusReviewAsset(assetId, action)
    showToast(action === 'approve' ? '素材已批准' : '素材已拒绝')
    await load()
  } catch (e) {
    showToast(e instanceof Error ? e.message : '操作失败')
  } finally {
    busy.value = false
  }
}

async function runStep(step: 'run-asr' | 'run-segmentation' | 'run-matching') {
  busy.value = true
  try {
    const r = await corpusRunStep(assetId, step)
    showToast(`${step} 完成: ${JSON.stringify(r)}`)
    await load()
  } catch (e) {
    showToast(e instanceof Error ? e.message : '执行失败')
  } finally {
    busy.value = false
  }
}

async function saveClip(clipId: string) {
  busy.value = true
  try {
    const e = clipEdits.value[clipId]
    await corpusUpdateClip(clipId, {
      start_ms: e.start_ms,
      end_ms: e.end_ms,
      transcript: e.transcript,
      scenario_tags: e.tagsText.split(',').map((x: string) => x.trim()).filter(Boolean),
      communicative_function: e.communicative_function || undefined,
      difficulty: e.difficulty || undefined,
      accent: e.accent || undefined,
      speaker_count: e.speaker_count || undefined,
      speech_rate: e.speech_rate || undefined,
      listening_features: [...e.featuresSet]
    })
    showToast('clip 已保存, 新 revision 已记录')
    await load()
  } catch (err) {
    showToast(err instanceof Error ? err.message : '保存失败')
  } finally {
    busy.value = false
  }
}

function toggleFeature(clipId: string, f: string) {
  const s: Set<string> = clipEdits.value[clipId].featuresSet
  if (s.has(f)) s.delete(f)
  else s.add(f)
}

async function createClip() {
  busy.value = true
  try {
    await corpusCreateClip(assetId, {
      start_ms: newClip.value.start_ms,
      end_ms: newClip.value.end_ms,
      transcript: newClip.value.transcript || undefined,
      speaker_info: newClip.value.speaker_info || undefined
    })
    newClip.value = { start_ms: 0, end_ms: 0, transcript: '', speaker_info: '' }
    showToast('手工 clip 已创建')
    await load()
  } catch (err) {
    showToast(err instanceof Error ? err.message : '创建失败')
  } finally {
    busy.value = false
  }
}

async function reviewMatch(clipId: string, expressionId: string, action: 'approve' | 'reject') {
  busy.value = true
  try {
    await corpusReviewClipMatch(clipId, expressionId, action)
    showToast(action === 'approve' ? '匹配已确认(正式关联)' : '匹配已否决')
    await load()
  } catch (err) {
    showToast(err instanceof Error ? err.message : '操作失败')
  } finally {
    busy.value = false
  }
}

async function reviewClip(clipId: string, action: 'approve' | 'reject') {
  busy.value = true
  try {
    await corpusReviewClip(clipId, action)
    showToast(action === 'approve' ? 'clip 已批准' : 'clip 已拒绝')
    await load()
  } catch (e) {
    showToast(e instanceof Error ? e.message : '操作失败')
  } finally {
    busy.value = false
  }
}

onMounted(async () => {
  await load()
  try {
    expressions.value = await teacherFetchExpressions()
  } catch {
    expressions.value = []
  }
})
</script>

<style scoped>
.teacher-page {
  min-height: 100vh;
  background: #06070c;
  color: #f2efe9;
  padding: 32px 24px 90px;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}
.teacher-container { max-width: 900px; margin: 0 auto; }
.topbar { margin-bottom: 28px; }
.back-button {
  border: none; background: transparent;
  color: rgba(242, 239, 233, 0.55); font-size: 14px; cursor: pointer;
}
.back-button:hover { color: #e8a75c; }
.eyebrow {
  margin: 0 0 12px; color: #e8a75c; font-size: 12px;
  letter-spacing: 4px; text-transform: uppercase;
}
.hero h1 { margin: 0; font-size: 28px; }
.meta-line {
  margin-top: 10px; font-size: 13px; color: rgba(242, 239, 233, 0.55);
  display: flex; gap: 10px; align-items: center; flex-wrap: wrap;
}
.meta-line.dim { color: rgba(242, 239, 233, 0.35); font-size: 12px; }
.rev { font-size: 11px; color: rgba(242, 239, 233, 0.35); }
.rev-meta { color: rgba(242, 239, 233, 0.22); }
.consent-warning {
  font-size: 13px;
  color: #e8b45a;
  background: rgba(232, 180, 90, 0.08);
  border: 1px solid rgba(232, 180, 90, 0.3);
  border-radius: 8px;
  padding: 8px 12px;
}
.consent-checks { display: flex; gap: 18px; flex-wrap: wrap; font-size: 13px; margin-top: 4px; }
.consent-checks label { display: flex; gap: 6px; align-items: center; }
.add-match { margin-top: 10px; }
.add-match summary { cursor: pointer; font-size: 13px; color: rgba(242, 239, 233, 0.6); }
.match-note { display: block; font-size: 11px; color: rgba(242, 239, 233, 0.45); }
.card {
  margin-top: 20px;
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 18px; padding: 22px;
}
.card-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
.card-title { margin: 0 0 14px; font-size: 16px; }
.pipeline-state {
  margin-left: 10px; font-size: 12px; color: #e8a75c; font-weight: 400;
}
.field-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
}
.field { display: flex; flex-direction: column; gap: 6px; margin-bottom: 10px; }
.field span { font-size: 12px; color: rgba(242, 239, 233, 0.5); }
.field input, .field select, .field textarea {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px; color: #f2efe9;
  padding: 10px 12px; font-size: 14px; font-family: inherit;
}
.field textarea { resize: vertical; line-height: 1.7; }
.audio-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 14px; }
.audio-row audio { max-width: 340px; }
.actions { display: flex; gap: 10px; margin-top: 8px; flex-wrap: wrap; }
.btn {
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: transparent; color: #f2efe9;
  border-radius: 10px; padding: 9px 16px; font-size: 13px; cursor: pointer;
}
.btn:hover:not(:disabled) { border-color: #e8a75c; color: #e8a75c; }
.btn.approve { border-color: rgba(127, 216, 164, 0.5); color: #7fd8a4; }
.btn.reject { border-color: rgba(232, 144, 122, 0.5); color: #e8907a; }
.btn.small { padding: 6px 12px; font-size: 12px; }
.btn:disabled { opacity: 0.4; cursor: not-allowed; }
.error-line { color: #e8907a; font-size: 12.5px; }
.badge {
  font-size: 11.5px; border: 1px solid; border-radius: 999px; padding: 3px 10px;
}
.badge.rs-pending_teacher { color: #e8a75c; border-color: rgba(232, 167, 92, 0.4); }
.badge.rs-approved { color: #7fd8a4; border-color: rgba(127, 216, 164, 0.4); }
.badge.rs-rejected { color: #e8907a; border-color: rgba(232, 144, 122, 0.4); }
.raw-asr, .context { margin-top: 14px; font-size: 13px; }
.raw-asr summary, .context summary { cursor: pointer; color: rgba(242, 239, 233, 0.55); }
.raw-asr p, .context p {
  color: rgba(242, 239, 233, 0.6); line-height: 1.8; font-size: 12.5px;
}
.rev-line { font-size: 12px; }
.matches { margin-top: 10px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.matches-title { font-size: 12px; color: rgba(242, 239, 233, 0.5); }
.match-tag {
  font-size: 11.5px; color: #e8a75c;
  border: 1px dashed rgba(232, 167, 92, 0.4);
  border-radius: 999px; padding: 3px 10px;
}
.match-tag.match-approved { color: #7fd8a4; border-style: solid; border-color: rgba(127, 216, 164, 0.5); }
.match-tag.match-rejected { color: rgba(242, 239, 233, 0.35); text-decoration: line-through; }
.match-btn {
  background: none; border: none; color: #7fd8a4; cursor: pointer;
  font-size: 11.5px; padding: 0 3px; text-decoration: underline;
}
.match-btn.reject { color: #e88a8a; }
.feature-checks { display: flex; flex-wrap: wrap; gap: 6px 14px; margin-top: 6px; }
.feature-check { font-size: 12px; color: rgba(242, 239, 233, 0.75); display: flex; align-items: center; gap: 4px; }
.review-checklist {
  margin-top: 12px; padding: 8px 12px; border-radius: 8px;
  border: 1px dashed rgba(232, 167, 92, 0.35);
  font-size: 12px; color: rgba(242, 239, 233, 0.6);
  display: flex; gap: 10px; flex-wrap: wrap; align-items: center;
}
.toast {
  position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%);
  background: rgba(232, 167, 92, 0.95); color: #17120c;
  border-radius: 12px; padding: 10px 22px; font-size: 14px; font-weight: 600;
}
.state-card {
  margin-top: 36px; background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 20px; padding: 40px; text-align: center;
  color: rgba(242, 239, 233, 0.6);
}
.state-card.error { border-color: rgba(232, 144, 122, 0.4); }
</style>
