<template>
  <div class="mistakes-page">
    <div class="mistakes-container">
      <div class="topbar">
        <button class="back-button" @click="$router.push('/listening')">
          ← 返回听力首页
        </button>
      </div>

      <section class="hero">
        <p class="eyebrow">Mistakes</p>
        <h1>错题本</h1>
        <p class="description">
          聚合历次作答中的错题，按掌握度与证据链状态给出下一步建议。
        </p>
      </section>

      <!-- 筛选栏 -->
      <div class="filters">
        <label class="filter">
          <span>掌握度</span>
          <select v-model="filters.mastery">
            <option value="">全部</option>
            <option value="unreviewed">未复盘</option>
            <option value="reviewing">复盘中</option>
            <option value="improved">已改进</option>
            <option value="mastered">已掌握</option>
          </select>
        </label>
        <label class="filter">
          <span>Section</span>
          <select v-model="filters.section">
            <option value="">全部</option>
            <option value="A">A</option>
            <option value="B">B</option>
            <option value="C">C</option>
          </select>
        </label>
        <label class="filter">
          <span>错因</span>
          <select v-model="filters.tag">
            <option value="">全部</option>
            <option
              v-for="(meta, code) in studentLayerTags"
              :key="code"
              :value="code"
            >
              {{ meta.zh }}
            </option>
          </select>
        </label>
        <label class="filter check">
          <input v-model="filters.trained" type="checkbox" />
          <span>已完成训练</span>
        </label>
        <label class="filter check">
          <input v-model="filters.retested" type="checkbox" />
          <span>已裸听复测</span>
        </label>
      </div>

      <div v-if="loading" class="state-card"><p>加载中……</p></div>
      <div v-else-if="errorMessage" class="state-card error">
        <p>{{ errorMessage }}</p>
      </div>
      <div v-else-if="!mistakes.length" class="state-card">
        <p>当前筛选条件下没有错题。</p>
      </div>

      <div v-else class="mistake-list">
        <div v-for="m in mistakes" :key="m.exam_id + m.question_id" class="m-card">
          <div class="m-head">
            <span class="m-no">Q{{ m.question_number }}</span>
            <span class="m-section">Section {{ m.section }}</span>
            <span class="mastery" :class="m.mastery">
              {{ masteryLabel(m.mastery) }}
            </span>
          </div>
          <p class="m-title">{{ m.exam_title }}</p>
          <p v-if="m.question_text" class="m-qtext">{{ m.question_text }}</p>
          <p class="m-answers">
            你的答案 {{ m.final_answer || '—' }} · 正确答案
            {{ m.correct_answer }}
            <template v-if="m.max_hint_level">
              · 提示开到 L{{ m.max_hint_level }}
            </template>
            <template v-if="m.relisten_count">
              · 整段重播 {{ m.relisten_count }} 次
            </template>
          </p>
          <div v-if="m.final_tags.length" class="m-tags">
            <span class="tag-label">最终确认错因：</span>
            <span v-for="t in m.final_tags" :key="t" class="tag">
              {{ tagZh(t) }}
            </span>
          </div>
          <div v-else-if="m.student_tags.length" class="m-tags">
            <span class="tag-label">学生自判（未确认）：</span>
            <span v-for="t in m.student_tags" :key="t" class="tag student">
              {{ tagZh(t) }}
            </span>
          </div>
          <div class="m-footer">
            <p class="next-step">{{ m.next_step }}</p>
            <button
              class="review-link"
              @click="$router.push(`/listening/review/${m.attempt_id}`)"
            >
              回到复盘 →
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { fetchMistakes, fetchTagDictionary } from '../../services/listeningApi'
import { getStudentId } from '../../services/listeningEvents'

const studentId = getStudentId()

const loading = ref(true)
const errorMessage = ref('')
const mistakes = ref<any[]>([])
const tagDict = ref<Record<string, { zh: string; layer: string }>>({})

const filters = reactive({
  mastery: '',
  section: '',
  tag: '',
  trained: false,
  retested: false
})

/** 错因筛选只列学生层标签(题目层陷阱不参与学生错因筛选) */
const studentLayerTags = computed(() => {
  const out: Record<string, { zh: string; layer: string }> = {}
  for (const [code, meta] of Object.entries(tagDict.value)) {
    if (meta.layer !== 'question') out[code] = meta
  }
  return out
})

function tagZh(code: string): string {
  return tagDict.value[code]?.zh || code
}

function masteryLabel(m: string): string {
  const labels: Record<string, string> = {
    unreviewed: '未复盘',
    reviewing: '复盘中',
    improved: '已改进',
    mastered: '已掌握'
  }
  return labels[m] || m
}

async function load() {
  loading.value = true
  errorMessage.value = ''
  try {
    mistakes.value = await fetchMistakes(studentId, {
      mastery: filters.mastery || undefined,
      section: filters.section || undefined,
      tag: filters.tag || undefined,
      trained: filters.trained || undefined,
      retested: filters.retested || undefined
    })
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : '错题本加载失败'
  } finally {
    loading.value = false
  }
}

watch(filters, () => load())

onMounted(async () => {
  try {
    tagDict.value = await fetchTagDictionary()
  } catch {
    // 标签字典失败不阻塞列表
  }
  await load()
})
</script>

<style scoped>
.mistakes-page {
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

.mistakes-container {
  max-width: 980px;
  margin: 0 auto;
}

.topbar {
  margin-bottom: 32px;
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
  font-size: clamp(26px, 4vw, 36px);
  letter-spacing: 2px;
}

.description {
  margin-top: 12px;
  color: rgba(242, 239, 233, 0.55);
  font-size: 14px;
}

.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 24px;
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 14px;
}

.filter {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: rgba(242, 239, 233, 0.65);
}

.filter select {
  background: #12141d;
  color: #f2efe9;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 13px;
}

.filter.check input {
  accent-color: #e8a75c;
}

.state-card {
  margin-top: 24px;
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

.mistake-list {
  margin-top: 20px;
}

.m-card {
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 16px;
  padding: 16px 20px;
  margin-bottom: 12px;
}

.m-head {
  display: flex;
  align-items: center;
  gap: 12px;
}

.m-no {
  font-weight: 700;
  color: #e8a75c;
}

.m-section {
  font-size: 12px;
  color: rgba(242, 239, 233, 0.5);
}

.mastery {
  font-size: 11.5px;
  border-radius: 999px;
  padding: 2px 10px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: rgba(242, 239, 233, 0.5);
}

.mastery.improved {
  border-color: rgba(126, 184, 232, 0.5);
  color: #7eb8e8;
}

.mastery.mastered {
  border-color: rgba(127, 216, 164, 0.5);
  color: #7fd8a4;
}

.mastery.reviewing {
  border-color: rgba(232, 167, 92, 0.5);
  color: #e8a75c;
}

.m-title {
  margin: 8px 0 0;
  font-size: 12px;
  color: rgba(242, 239, 233, 0.45);
}

.m-qtext {
  margin: 8px 0 0;
  font-size: 14px;
  line-height: 1.7;
}

.m-answers {
  margin: 8px 0 0;
  font-size: 12.5px;
  color: rgba(242, 239, 233, 0.55);
}

.m-tags {
  margin-top: 10px;
  font-size: 12.5px;
}

.tag-label {
  color: rgba(242, 239, 233, 0.5);
  margin-right: 6px;
}

.tag {
  display: inline-block;
  border: 1px solid rgba(232, 167, 92, 0.4);
  color: #e8a75c;
  border-radius: 999px;
  padding: 1px 10px;
  margin: 2px 4px 2px 0;
  font-size: 12px;
}

.tag.student {
  border-style: dashed;
  color: rgba(232, 167, 92, 0.7);
}

.m-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.07);
  padding-top: 12px;
}

.next-step {
  margin: 0;
  font-size: 13px;
  color: #7eb8e8;
  line-height: 1.6;
}

.review-link {
  border: 1px solid rgba(232, 167, 92, 0.4);
  background: transparent;
  color: #e8a75c;
  border-radius: 10px;
  padding: 6px 14px;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
}

.review-link:hover {
  background: rgba(232, 167, 92, 0.1);
}
</style>
