<template>
  <div class="exam-page">
    <div class="exam-container">
      <div class="topbar">
        <button class="back-button" @click="$router.push('/listening')">
          ← 返回听力首页
        </button>
      </div>

      <div v-if="loading" class="state-card">
        <p>正在加载套题……</p>
      </div>

      <div v-else-if="errorMessage" class="state-card error">
        <p>{{ errorMessage }}</p>
      </div>

      <template v-else-if="exam">
        <section class="hero">
          <p class="eyebrow">{{ exam.exam_type.toUpperCase() }} Listening</p>
          <h1>{{ exam.title }}</h1>
          <p class="description">
            共 {{ exam.question_count }} 题 · {{ exam.units.length }} 个听力单元
          </p>
        </section>

        <section class="unit-list">
          <div
            v-for="unit in exam.units"
            :key="unit.id"
            class="unit-card"
          >
            <div class="unit-head">
              <span class="unit-section">Section {{ unit.section }}</span>
              <span class="unit-title">{{ unit.title }}</span>
            </div>
            <p class="unit-meta">
              {{ unit.question_count }} 题 ·
              {{ unitTypeLabel(unit.type) }}
            </p>
          </div>
        </section>

        <p class="notice">
          考试 / 练习模式将在下一阶段（Phase 2）开放。
        </p>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

interface UnitBrief {
  id: string
  section: string
  type: string
  title: string
  question_count: number
}

interface ExamDetail {
  id: string
  exam_type: string
  title: string
  question_count: number
  units: UnitBrief[]
}

const route = useRoute()
const exam = ref<ExamDetail | null>(null)
const loading = ref(true)
const errorMessage = ref('')

function unitTypeLabel(t: string): string {
  const labels: Record<string, string> = {
    conversation: '长对话',
    passage: '短文',
    recording: '讲座/讲话'
  }
  return labels[t] || t
}

onMounted(async () => {
  try {
    const response = await fetch(
      `/api/listening/exams/${encodeURIComponent(route.params.examId as string)}`
    )
    const result = await response.json()
    if (!response.ok) {
      throw new Error(result?.detail || `请求失败，状态码：${response.status}`)
    }
    exam.value = result.data
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : '套题加载失败，请稍后重试。'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.exam-page {
  min-height: 100vh;
  background:
    radial-gradient(
      circle at 50% -10%,
      rgba(232, 167, 92, 0.12),
      transparent 34%
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

.exam-container {
  max-width: 980px;
  margin: 0 auto;
}

.topbar {
  margin-bottom: 48px;
}

.back-button {
  border: none;
  background: transparent;
  color: rgba(242, 239, 233, 0.55);
  font-size: 14px;
  cursor: pointer;
  padding: 0;
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
  font-size: clamp(28px, 4vw, 40px);
  letter-spacing: 2px;
}

.description {
  margin-top: 14px;
  color: rgba(242, 239, 233, 0.55);
  font-size: 15px;
}

.unit-list {
  margin-top: 32px;
  display: grid;
  gap: 14px;
}

.unit-card {
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 16px;
  padding: 18px 22px;
}

.unit-head {
  display: flex;
  gap: 12px;
  align-items: baseline;
}

.unit-section {
  font-size: 12px;
  color: #e8a75c;
  letter-spacing: 1.5px;
}

.unit-title {
  font-size: 15px;
  font-weight: 600;
}

.unit-meta {
  margin: 8px 0 0;
  font-size: 13px;
  color: rgba(242, 239, 233, 0.5);
}

.notice {
  margin-top: 36px;
  text-align: center;
  font-size: 13px;
  letter-spacing: 1px;
  color: rgba(242, 239, 233, 0.35);
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
</style>
