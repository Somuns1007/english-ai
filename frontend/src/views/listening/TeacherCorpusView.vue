<template>
  <TeacherGate>
  <div class="teacher-page">
    <div class="teacher-container">
      <div class="topbar">
        <button class="back-button" @click="$router.push('/listening/teacher/expressions')">
          ← 表达审核
        </button>
      </div>

      <section class="hero">
        <p class="eyebrow">Corpus Ingestion</p>
        <h1>真实语料库</h1>
        <p class="description">
          只接收拥有合法使用权或明确开放许可的音频。许可状态不明确(unverified)的素材
          可以上传试跑流水线, 但不能被批准进入正式语料。
        </p>
      </section>

      <!-- 上传表单 -->
      <section class="card">
        <h2 class="card-title">上传新素材</h2>
        <div class="field-grid">
          <label class="field">
            <span>音频文件(wav/mp3/m4a)</span>
            <input type="file" accept="audio/*" @change="onFile" />
          </label>
          <label class="field">
            <span>标题 *</span>
            <input v-model="form.title" placeholder="例如: LibriSpeech 1272 章节朗读" />
          </label>
          <label class="field">
            <span>来源名称 *</span>
            <input v-model="form.source_name" placeholder="例如: LibriSpeech dev-clean" />
          </label>
          <label class="field">
            <span>来源链接</span>
            <input v-model="form.source_url" placeholder="https://…" />
          </label>
          <label class="field">
            <span>许可证 *</span>
            <input v-model="form.license" placeholder="例如: CC BY 4.0 / Public Domain" />
          </label>
          <label class="field">
            <span>许可状态 *</span>
            <select v-model="form.permission_status">
              <option value="unverified">unverified(未核实)</option>
              <option value="verified_open_license">verified_open_license(已核实开放许可)</option>
              <option value="owned">owned(自有版权)</option>
            </select>
          </label>
        </div>
        <button class="btn primary" :disabled="!canUpload || uploading" @click="upload">
          {{ uploading ? '上传中……' : '上传' }}
        </button>
        <p v-if="uploadError" class="error-line">{{ uploadError }}</p>
      </section>

      <!-- 素材列表 -->
      <div v-if="loading" class="state-card"><p>正在加载……</p></div>
      <section v-else class="asset-list">
        <article
          v-for="a in assets"
          :key="a.asset_id"
          class="asset-row"
          @click="$router.push(`/listening/teacher/corpus/${a.asset_id}`)"
        >
          <div class="asset-main">
            <span class="asset-title">{{ a.title }}</span>
            <span class="asset-meta">
              {{ a.source_name }} · {{ a.license }} ·
              {{ a.duration_ms ? Math.round(a.duration_ms / 1000) + 's' : '时长未知' }}
            </span>
            <span class="asset-pipeline">
              流水线: {{ pipelineLabel(a.pipeline_status) }}
              <template v-if="a.pipeline_error"> · <span class="error-line">{{ a.pipeline_error }}</span></template>
            </span>
          </div>
          <div class="asset-badges">
            <span class="badge" :class="`rs-${a.review_status}`">{{ statusLabel(a.review_status) }}</span>
            <span class="badge" :class="a.permission_status === 'unverified' ? 'rs-rejected' : 'rs-approved'">
              {{ permissionLabel(a.permission_status) }}
            </span>
          </div>
        </article>
        <p v-if="!assets.length" class="empty">还没有素材, 先上传一个。</p>
      </section>
    </div>
  </div>
  </TeacherGate>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import TeacherGate from './TeacherGate.vue'
import {
  corpusListAssets,
  corpusUploadAsset,
  type CorpusAsset
} from '../../services/listeningApi'

const assets = ref<CorpusAsset[]>([])
const loading = ref(true)
const uploading = ref(false)
const uploadError = ref('')
const file = ref<File | null>(null)

const form = ref({
  title: '',
  source_name: '',
  source_url: '',
  license: '',
  permission_status: 'unverified'
})

const canUpload = computed(
  () => file.value && form.value.title && form.value.source_name && form.value.license
)

function onFile(e: Event) {
  file.value = (e.target as HTMLInputElement).files?.[0] || null
}

function statusLabel(s: string): string {
  return { pending_teacher: '待审核', approved: '已批准', rejected: '已拒绝' }[s] || s
}

function permissionLabel(s: string): string {
  return {
    unverified: '许可未核实',
    verified_open_license: '开放许可',
    owned: '自有版权'
  }[s] || s
}

function pipelineLabel(s: string): string {
  return {
    uploaded: '已上传(待 ASR)',
    asr_done: 'ASR 完成(待切分)',
    segmented: '切分完成(待匹配)',
    matched: '匹配完成(待审核)'
  }[s] || s
}

async function load() {
  loading.value = true
  try {
    assets.value = await corpusListAssets()
  } finally {
    loading.value = false
  }
}

async function upload() {
  if (!file.value) return
  uploading.value = true
  uploadError.value = ''
  try {
    await corpusUploadAsset(file.value, form.value)
    form.value = { title: '', source_name: '', source_url: '', license: '', permission_status: 'unverified' }
    file.value = null
    await load()
  } catch (e) {
    uploadError.value = e instanceof Error ? e.message : '上传失败'
  } finally {
    uploading.value = false
  }
}

onMounted(load)
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
.topbar { margin-bottom: 32px; }
.back-button {
  border: none; background: transparent;
  color: rgba(242, 239, 233, 0.55); font-size: 14px; cursor: pointer;
}
.back-button:hover { color: #e8a75c; }
.eyebrow {
  margin: 0 0 12px; color: #e8a75c; font-size: 12px;
  letter-spacing: 4px; text-transform: uppercase;
}
.hero h1 { margin: 0; font-size: 32px; }
.description {
  margin-top: 12px; max-width: 720px;
  color: rgba(242, 239, 233, 0.55); line-height: 1.8; font-size: 14px;
}
.card {
  margin-top: 24px;
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 18px; padding: 22px;
}
.card-title { margin: 0 0 14px; font-size: 17px; }
.field-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
}
.field { display: flex; flex-direction: column; gap: 6px; }
.field span { font-size: 12px; color: rgba(242, 239, 233, 0.5); }
.field input, .field select {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px; color: #f2efe9;
  padding: 10px 12px; font-size: 14px; font-family: inherit;
}
.btn {
  margin-top: 14px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: transparent; color: #f2efe9;
  border-radius: 10px; padding: 10px 20px;
  font-size: 14px; cursor: pointer;
}
.btn.primary { background: #e8a75c; color: #17120c; border: none; font-weight: 600; }
.btn:disabled { opacity: 0.4; cursor: not-allowed; }
.error-line { color: #e8907a; font-size: 12.5px; }
.asset-list { margin-top: 24px; }
.asset-row {
  display: flex; justify-content: space-between; align-items: center; gap: 16px;
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 16px; padding: 18px 20px; margin-bottom: 12px; cursor: pointer;
}
.asset-row:hover { border-color: rgba(232, 167, 92, 0.35); }
.asset-main { display: flex; flex-direction: column; gap: 4px; }
.asset-title { font-size: 15px; font-weight: 600; }
.asset-meta, .asset-pipeline { font-size: 12px; color: rgba(242, 239, 233, 0.45); }
.asset-badges { display: flex; gap: 6px; flex-wrap: wrap; justify-content: flex-end; }
.badge {
  font-size: 11.5px; border: 1px solid; border-radius: 999px; padding: 3px 10px;
}
.badge.rs-pending_teacher { color: #e8a75c; border-color: rgba(232, 167, 92, 0.4); }
.badge.rs-approved { color: #7fd8a4; border-color: rgba(127, 216, 164, 0.4); }
.badge.rs-rejected { color: #e8907a; border-color: rgba(232, 144, 122, 0.4); }
.empty { text-align: center; color: rgba(242, 239, 233, 0.35); margin-top: 30px; }
.state-card {
  margin-top: 36px; background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 20px; padding: 40px; text-align: center;
  color: rgba(242, 239, 233, 0.6);
}
</style>
