<template>
  <div class="expr-page">
    <div class="expr-container">
      <div class="topbar">
        <button class="back-button" @click="$router.push('/listening')">
          ← 返回听力首页
        </button>
        <div class="topbar-right">
          <button v-if="currentUser?.role === 'admin'" class="back-button dim" @click="$router.push('/listening/teacher/expressions')">
            教师审核
          </button>
          <button class="back-button" @click="$router.push('/listening/profile')">
            我的弱项 →
          </button>
        </div>
      </div>

      <section class="hero">
        <p class="eyebrow">Phrase Practice</p>
        <h1>换场景练短语</h1>
        <p class="description">
          这些短语出自四六级听力真题。我们把每个短语放进酒店、药房、公司、校园等新的对话里：
          你先听对话，再回答问题，看看换个场景还能不能听出来。
        </p>
        <p class="honesty-note">
          说明：这些对话由 AI 编写，语音由电脑合成，仅供练习，内容还在等老师审核。
        </p>
      </section>

      <div v-if="loading" class="state-card">
        <p>正在加载表达……</p>
      </div>

      <div v-else-if="errorMessage" class="state-card error">
        <p>{{ errorMessage }}</p>
        <button class="retry-button" @click="load">重试</button>
      </div>

      <section v-else class="expr-grid">
        <article
          v-for="e in expressions"
          :key="e.expression_id"
          class="expr-card"
          @click="openExpression(e)"
        >
          <div class="expr-head">
            <span class="expr-func">{{ e.communicative_function }}</span>
            <span class="expr-progress" :class="{ done: e.done_count >= e.scenario_count }">
              已练 {{ e.done_count }}/{{ e.scenario_count }} 个场景
            </span>
          </div>

          <h2>{{ e.expression }}</h2>
          <p class="meaning">{{ e.meaning }}</p>

          <p class="source">
            出自：{{ sourceLabel(e.source_exam_id, e.source_question_id) }}
          </p>
          <p class="source-sentence">"{{ e.source_sentence }}"</p>

          <div class="expr-foot">
            <span v-if="e.correct_count > 0" class="correct-count">
              {{ e.correct_count }} 个场景全部答对
            </span>
            <span v-else class="correct-count empty">还没练</span>
            <span class="go">开始练习 →</span>
          </div>
        </article>
      </section>

      <p class="footnote">
        共 {{ expressions.length }} 个短语，都是日常常用、换个场景也经常听到的说法
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchExpressions, type ExpressionCard } from '../../services/listeningApi'
import { getStudentId } from '../../services/listeningEvents'
import { currentUser, getMe } from '../../services/authApi'

const router = useRouter()

// 「cet6_202606_set2」+「cet6_202606_set2_q3」→「2026 年 6 月六级第 2 套第 3 题」
function sourceLabel(examId?: string, questionId?: string): string {
  const m = (examId || '').match(/cet(\d)_(\d{4})(\d{2})_set(\d+)/)
  const q = (questionId || '').match(/q(\d+)$/)
  if (!m) return examId || ''
  const level = m[1] === '4' ? '四级' : '六级'
  return `${m[2]} 年 ${Number(m[3])} 月${level}第 ${m[4]} 套` + (q ? `第 ${q[1]} 题` : '')
}

onMounted(() => { getMe().catch(() => null) })
const studentId = computed(() => getStudentId())

const expressions = ref<ExpressionCard[]>([])
const loading = ref(true)
const errorMessage = ref('')

async function load() {
  loading.value = true
  errorMessage.value = ''
  try {
    expressions.value = await fetchExpressions(studentId.value)
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : '表达加载失败, 请稍后重试。'
  } finally {
    loading.value = false
  }
}

function openExpression(e: ExpressionCard) {
  router.push(`/listening/expressions/${e.expression_id}`)
}

onMounted(load)
</script>

<style scoped>
.expr-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at 50% -10%, rgba(232, 167, 92, 0.12), transparent 34%),
    radial-gradient(circle at 90% 30%, rgba(94, 84, 140, 0.08), transparent 28%),
    #06070c;
  color: #f2efe9;
  padding: 32px 24px 90px;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.expr-container {
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

.back-button.dim {
  color: rgba(242, 239, 233, 0.35);
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

.honesty-note {
  max-width: 720px;
  margin-top: 10px;
  font-size: 12px;
  line-height: 1.7;
  color: rgba(242, 239, 233, 0.35);
}

.expr-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 36px;
}

.expr-card {
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 20px;
  padding: 26px;
  cursor: pointer;
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  transition: transform 0.3s cubic-bezier(0.2, 0.7, 0.3, 1), border-color 0.3s, box-shadow 0.3s;
}

.expr-card:hover {
  transform: translateY(-4px);
  border-color: rgba(232, 167, 92, 0.35);
  box-shadow: 0 18px 44px -18px rgba(0, 0, 0, 0.7), 0 0 32px -10px rgba(232, 167, 92, 0.15);
}

.expr-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.expr-func {
  font-size: 12px;
  letter-spacing: 1px;
  color: #e8a75c;
  border: 1px solid rgba(232, 167, 92, 0.3);
  border-radius: 999px;
  padding: 3px 10px;
}

.expr-progress {
  font-size: 12px;
  color: rgba(242, 239, 233, 0.4);
}

.expr-progress.done {
  color: #7fd8a4;
}

.expr-card h2 {
  margin: 0;
  font-size: 19px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.meaning {
  margin: 8px 0 0;
  font-size: 14px;
  color: rgba(242, 239, 233, 0.7);
}

.source {
  margin: 14px 0 0;
  font-size: 12px;
  color: rgba(242, 239, 233, 0.4);
  letter-spacing: 0.5px;
}

.source-sentence {
  margin: 6px 0 0;
  font-size: 12px;
  font-style: italic;
  color: rgba(242, 239, 233, 0.45);
  line-height: 1.6;
}

.expr-foot {
  margin-top: 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.correct-count {
  font-size: 13px;
  color: #7fd8a4;
}

.correct-count.empty {
  color: rgba(242, 239, 233, 0.35);
}

.go {
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
</style>
