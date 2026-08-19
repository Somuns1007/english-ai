<template>
  <TeacherGate>
  <div class="teacher-page">
    <div class="teacher-container">
      <div class="topbar">
        <button class="back-button" @click="$router.push('/listening/expressions')">
          ← 学生端表达页
        </button>
        <button class="back-button" @click="$router.push('/listening/teacher/corpus')">
          语料库 →
        </button>
      </div>

      <section class="hero">
        <p class="eyebrow">Teacher Review</p>
        <h1>表达内容审核</h1>
        <p class="description">
          AI 生成的场景与 TTS 在审核通过(approved)前, 最多只能作为 provisional
          证据, 不能支撑 demonstrated 结论。请逐条听音频、对原文、改文本后再批准。
        </p>
      </section>

      <div v-if="loading" class="state-card"><p>正在加载……</p></div>
      <div v-else-if="errorMessage" class="state-card error">
        <p>{{ errorMessage }}</p>
        <button class="retry-button" @click="load">重试</button>
      </div>

      <section v-else class="expr-list">
        <article
          v-for="e in expressions"
          :key="e.expression_id"
          class="expr-row"
          @click="$router.push(`/listening/teacher/expressions/${e.expression_id}`)"
        >
          <div class="expr-main">
            <span class="expr-name">{{ e.expression }}</span>
            <span class="expr-meaning">{{ e.meaning }}</span>
            <span class="expr-source">
              {{ e.source_exam_id }} · {{ e.source_question_id?.split('_').pop() }} · rev {{ e.revision }}
            </span>
          </div>
          <div class="expr-status">
            <span class="badge" :class="`rs-${e.review_status}`">
              表达: {{ statusLabel(e.review_status) }}
            </span>
            <span
              v-for="s in e.scenarios"
              :key="s.scenario_id"
              class="badge small"
              :class="`rs-${s.review_status}`"
            >
              {{ s.scenario }} {{ statusLabel(s.review_status) }}{{ s.has_audio ? '' : ' · 无音频' }}
            </span>
          </div>
        </article>
      </section>
    </div>
  </div>
  </TeacherGate>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { teacherFetchExpressions } from '../../services/listeningApi'
import TeacherGate from './TeacherGate.vue'

const expressions = ref<any[]>([])
const loading = ref(true)
const errorMessage = ref('')

function statusLabel(s: string): string {
  return { pending_teacher: '待审核', approved: '已批准', rejected: '已拒绝' }[s] || s
}

async function load() {
  loading.value = true
  errorMessage.value = ''
  try {
    expressions.value = await teacherFetchExpressions()
  } catch (e) {
    errorMessage.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
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

.teacher-container {
  max-width: 900px;
  margin: 0 auto;
}

.topbar { margin-bottom: 40px; }

.back-button {
  border: none;
  background: transparent;
  color: rgba(242, 239, 233, 0.55);
  font-size: 14px;
  cursor: pointer;
}

.back-button:hover { color: #e8a75c; }

.eyebrow {
  margin: 0 0 12px;
  color: #e8a75c;
  font-size: 12px;
  letter-spacing: 4px;
  text-transform: uppercase;
}

.hero h1 { margin: 0; font-size: 34px; }

.description {
  margin-top: 14px;
  max-width: 720px;
  color: rgba(242, 239, 233, 0.55);
  line-height: 1.8;
  font-size: 14px;
}

.expr-list { margin-top: 30px; }

.expr-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 16px;
  padding: 18px 20px;
  margin-bottom: 12px;
  cursor: pointer;
}

.expr-row:hover { border-color: rgba(232, 167, 92, 0.35); }

.expr-main { display: flex; flex-direction: column; gap: 4px; }

.expr-name { font-size: 16px; font-weight: 600; }

.expr-meaning { font-size: 13px; color: rgba(242, 239, 233, 0.6); }

.expr-source { font-size: 11.5px; color: rgba(242, 239, 233, 0.35); }

.expr-status { display: flex; flex-wrap: wrap; gap: 6px; justify-content: flex-end; }

.badge {
  font-size: 11.5px;
  border: 1px solid;
  border-radius: 999px;
  padding: 3px 10px;
}

.badge.rs-pending_teacher { color: #e8a75c; border-color: rgba(232, 167, 92, 0.4); }
.badge.rs-approved { color: #7fd8a4; border-color: rgba(127, 216, 164, 0.4); }
.badge.rs-rejected { color: #e8907a; border-color: rgba(232, 144, 122, 0.4); }

.state-card {
  margin-top: 36px;
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 20px;
  padding: 40px;
  text-align: center;
  color: rgba(242, 239, 233, 0.6);
}

.state-card.error { border-color: rgba(232, 144, 122, 0.4); }

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
</style>
