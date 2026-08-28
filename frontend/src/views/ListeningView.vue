<template>
  <div class="listening-page">
    <div class="listening-container">
      <div class="topbar">
        <button class="back-button" @click="$router.push('/')">
          ← 返回首页
        </button>
        <div class="topbar-right">
          <button
            class="back-button"
            @click="$router.push('/listening/corpus')"
          >
            真实语料 →
          </button>
          <button
            class="back-button"
            @click="$router.push('/listening/expressions')"
          >
            表达迁移 →
          </button>
          <button
            class="back-button"
            @click="$router.push('/listening/profile')"
          >
            能力画像 →
          </button>
          <button
            class="back-button"
            @click="$router.push('/listening/mistakes')"
          >
            错题本 →
          </button>
        </div>
      </div>

      <section class="hero">
        <p class="eyebrow">Listening Diagnosis</p>
        <h1>听力诊断与训练</h1>
        <p class="description">
          真实考试 → 错因诊断 → 定位复听 → 对症训练 → 复测追踪。
          选择一套真题开始。
        </p>
      </section>

      <div v-if="loading" class="state-card">
        <p>正在加载套题……</p>
      </div>

      <div v-else-if="errorMessage" class="state-card error">
        <p>{{ errorMessage }}</p>
        <button class="retry-button" @click="loadExams">重试</button>
      </div>

      <section v-else class="exam-grid">
        <article
          v-for="exam in exams"
          :key="exam.id"
          class="exam-card"
          @click="openExam(exam)"
        >
          <div class="exam-head">
            <span class="exam-type">CET-6</span>
            <span class="exam-status">V2 · audio_only</span>
          </div>

          <h2>{{ exam.title }}</h2>

          <div class="exam-meta">
            <span>{{ exam.unit_count }} 个听力材料</span>
            <span>{{ exam.question_count }} 题</span>
            <span v-if="!exam.has_audio" class="warn">音频缺失</span>
          </div>

          <div class="exam-foot">
            <span class="score empty">题干由音频朗读 · 卷面仅选项</span>
            <span class="go">
              进入套题
              <svg
                width="15"
                height="15"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <path d="M5 12h14M13 6l6 6-6 6" />
              </svg>
            </span>
          </div>
        </article>
      </section>

      <p class="footnote">
        共 {{ exams.length }} 套正式材料 · 新套题上线无需更新本页
      </p>

      <section v-if="practiceMaterials.length" class="practice-section">
        <h2 class="practice-title">连续理解训练 <span class="pilot-tag">Pilot</span></h2>
        <div class="exam-grid">
          <article
            v-for="m in practiceMaterials"
            :key="m.material_id"
            class="exam-card"
            @click="openPractice(m)"
          >
            <div class="exam-head">
              <span class="exam-type">CET-6</span>
              <span class="exam-status">V2.2 · continuous</span>
            </div>
            <h2>{{ m.title }}</h2>
            <div class="exam-meta">
              <span>{{ m.check_count }} 道整体理解检测</span>
              <span v-if="!m.has_audio" class="warn">音频缺失</span>
            </div>
            <div class="exam-foot">
              <span class="score empty">先完整听 · 再作答 · 盲重播恢复</span>
              <span class="go">进入训练 →</span>
            </div>
          </article>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchV2Exams, fetchV2PracticeMaterials } from '../services/listeningApi'
import type { V2ExamSummary } from '../types/listening'
import type { V2PracticeMaterialSummary } from '../services/listeningApi'

const router = useRouter()

const exams = ref<V2ExamSummary[]>([])
const practiceMaterials = ref<V2PracticeMaterialSummary[]>([])
const loading = ref(true)
const errorMessage = ref('')

async function loadExams() {
  loading.value = true
  errorMessage.value = ''
  try {
    // V2.1: 首页只列 V2 套题(audio_only 新数据); legacy 套题入口暂时隐藏,
    // 旧数据与旧路由保留未删。
    exams.value = await fetchV2Exams()
    // V2.2: Continuous Practice Pilot 材料(gate 关闭时为空列表)
    practiceMaterials.value = await fetchV2PracticeMaterials()
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : '套题加载失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

function openExam(exam: V2ExamSummary) {
  router.push(`/listening/v2/exams/${exam.id}`)
}

function openPractice(m: V2PracticeMaterialSummary) {
  router.push(`/listening/v2/practice/${m.material_id}`)
}

onMounted(loadExams)
</script>

<style scoped>
.listening-page {
  min-height: 100vh;
  background:
    radial-gradient(
      circle at 50% -10%,
      rgba(232, 167, 92, 0.12),
      transparent 34%
    ),
    radial-gradient(
      circle at 90% 30%,
      rgba(94, 84, 140, 0.08),
      transparent 28%
    ),
    #06070c;
  color: #f2efe9;
  padding: 32px 24px 90px;
  font-family:
    -apple-system,
    BlinkMacSystemFont,
    'PingFang SC',
    'Microsoft YaHei',
    sans-serif;
}

.listening-container {
  width: 100%;
  max-width: 980px;
  margin: 0 auto;
}

.topbar {
  margin-bottom: 56px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.topbar-right {
  display: flex;
  gap: 18px;
}

.back-button {
  border: none;
  background: transparent;
  color: rgba(242, 239, 233, 0.55);
  font-size: 14px;
  cursor: pointer;
  padding: 0;
  transition: color 0.25s ease;
}

.back-button:hover {
  color: #e8a75c;
}

.eyebrow {
  margin: 0 0 12px;
  color: #e8a75c;
  font-size: 12px;
  letter-spacing: 4px;
  text-transform: uppercase;
}

.hero h1 {
  margin: 0;
  font-size: clamp(32px, 5vw, 48px);
  font-weight: 700;
  letter-spacing: 2px;
}

.description {
  max-width: 720px;
  margin-top: 18px;
  color: rgba(242, 239, 233, 0.55);
  line-height: 1.8;
  font-size: 15px;
}

.exam-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 36px;
}

.exam-card {
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 20px;
  padding: 26px;
  cursor: pointer;
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  transition:
    transform 0.3s cubic-bezier(0.2, 0.7, 0.3, 1),
    border-color 0.3s,
    box-shadow 0.3s;
}

.exam-card:hover {
  transform: translateY(-4px);
  border-color: rgba(232, 167, 92, 0.35);
  box-shadow:
    0 18px 44px -18px rgba(0, 0, 0, 0.7),
    0 0 32px -10px rgba(232, 167, 92, 0.15);
}

.exam-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.exam-type {
  font-size: 12px;
  letter-spacing: 2px;
  color: #e8a75c;
  border: 1px solid rgba(232, 167, 92, 0.3);
  border-radius: 999px;
  padding: 3px 10px;
}

.exam-status {
  font-size: 12px;
  color: rgba(242, 239, 233, 0.4);
}

.exam-status.done {
  color: #7fd8a4;
}

.exam-card h2 {
  margin: 0;
  font-size: 19px;
  font-weight: 600;
  letter-spacing: 1px;
}

.exam-meta {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  font-size: 13px;
  color: rgba(242, 239, 233, 0.55);
}

.exam-meta .warn {
  color: #e8907a;
}

.exam-foot {
  margin-top: 22px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.score {
  font-size: 13px;
  color: rgba(242, 239, 233, 0.7);
}

.score.empty {
  color: rgba(242, 239, 233, 0.35);
}

.go {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  letter-spacing: 1.5px;
  color: #e8a75c;
}

.state-card {
  margin-top: 36px;
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 20px;
  padding: 40px;
  text-align: center;
  color: rgba(242, 239, 233, 0.6);
}

.state-card.error {
  border-color: rgba(232, 144, 122, 0.4);
}

.retry-button {
  margin-top: 16px;
  border: none;
  border-radius: 12px;
  padding: 10px 22px;
  background: #e8a75c;
  color: #17120c;
  font-weight: 600;
  cursor: pointer;
}

.footnote {
  margin-top: 32px;
  text-align: center;
  font-size: 12px;
  letter-spacing: 1.5px;
  color: rgba(242, 239, 233, 0.3);
}

.practice-section {
  margin-top: 56px;
}

.practice-title {
  font-size: 20px;
  letter-spacing: 2px;
  margin: 0;
}

.pilot-tag {
  font-size: 11px;
  color: #e8a75c;
  border: 1px solid rgba(232, 167, 92, 0.35);
  border-radius: 999px;
  padding: 3px 10px;
  margin-left: 10px;
  vertical-align: middle;
  letter-spacing: 1px;
}
</style>
