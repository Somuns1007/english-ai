<template>
  <TeacherGate>
  <div class="teacher-page">
    <div class="teacher-container">
      <div class="topbar">
        <button class="back-button" @click="$router.push('/listening/teacher/expressions')">
          ← 返回审核列表
        </button>
      </div>

      <div v-if="loading" class="state-card"><p>正在加载……</p></div>
      <div v-else-if="errorMessage" class="state-card error">
        <p>{{ errorMessage }}</p>
        <button class="retry-button" @click="load">重试</button>
      </div>

      <template v-else-if="detail">
        <section class="hero">
          <p class="eyebrow">Teacher Review</p>
          <h1>{{ detail.expression }}</h1>
          <p class="source-line">
            出处: {{ detail.source_exam_id }} · {{ detail.source_question_id?.split('_').pop() }}
            <span class="badge" :class="`rs-${detail.review_status}`">
              {{ statusLabel(detail.review_status) }}
            </span>
            <span class="rev">rev {{ detail.revision || 1 }}</span>
          </p>
          <p class="source-sentence">
            真题原句({{ detail.source_sentence_status }}):
            "{{ detail.source_sentence }}"
          </p>
        </section>

        <!-- 表达层编辑 -->
        <section class="card">
          <h2 class="card-title">表达信息</h2>
          <label class="field">
            <span>中文释义</span>
            <input v-model="editMeaning" />
          </label>
          <label class="field">
            <span>交际功能</span>
            <input v-model="editFunc" />
          </label>
          <label class="field">
            <span>同义表达(用 / 分隔)</span>
            <input v-model="editRelated" />
          </label>
          <div class="actions">
            <button class="btn" :disabled="saving" @click="saveExpression">保存修改</button>
            <button class="btn approve" :disabled="saving" @click="reviewExpression('approve')">批准表达</button>
            <button class="btn reject" :disabled="saving" @click="reviewExpression('reject')">拒绝</button>
          </div>
          <p class="hint">任何修改都会使该表达回到「待审核」并需要重新批准。</p>
        </section>

        <!-- 场景层审核 -->
        <section v-for="s in detail.scenarios" :key="s.scenario_id" class="card">
          <div class="card-head">
            <h2 class="card-title">
              {{ s.scenario }} · {{ s.communicative_function }}
            </h2>
            <div>
              <span class="badge" :class="`rs-${s.review_status}`">
                {{ statusLabel(s.review_status) }}
              </span>
              <span class="rev">rev {{ s.revision || 1 }}</span>
            </div>
          </div>

          <div class="audio-row">
            <template v-if="s.audio_meta">
              <audio
                :src="`${scenarioAudioUrl(s.scenario_id, s.revision || 1)}&v=${encodeURIComponent(s.audio_meta.generated_at)}`"
                controls
              ></audio>
              <span class="audio-meta">
                {{ s.audio_meta.voice_id }} · {{ s.audio_meta.provider }} ·
                {{ s.audio_meta.source_type }}
              </span>
            </template>
            <span v-else class="audio-meta warn">音频缺失(文本已变更, 需重新生成)</span>
            <button class="btn small" :disabled="saving" @click="regenerate(s.scenario_id)">
              重新生成 TTS
            </button>
          </div>

          <label class="field">
            <span>场景文本(A:/B: 对白)</span>
            <textarea v-model="scenarioEdits[s.scenario_id].text" rows="5"></textarea>
          </label>
          <div class="field-grid">
            <label class="field">
              <span>语境标签</span>
              <input v-model="scenarioEdits[s.scenario_id].scenario" />
            </label>
            <label class="field">
              <span>交际功能</span>
              <input v-model="scenarioEdits[s.scenario_id].communicative_function" />
            </label>
            <label class="field">
              <span>难度</span>
              <select v-model="scenarioEdits[s.scenario_id].difficulty">
                <option value="easy">easy</option>
                <option value="medium">medium</option>
                <option value="hard">hard</option>
              </select>
            </label>
          </div>

          <details class="answers">
            <summary>查看三题与答案</summary>
            <div v-for="key in ['scene', 'meaning', 'key_info']" :key="key" class="qa">
              <p class="qa-q">{{ s.questions[key].question }}</p>
              <p
                v-for="(opt, label) in s.questions[key].options"
                :key="label"
                class="qa-o"
                :class="{ correct: s.questions[key].answer === label }"
              >
                {{ label }}. {{ opt }}
              </p>
            </div>
          </details>

          <div class="actions">
            <button class="btn" :disabled="saving" @click="saveScenario(s.scenario_id)">保存修改</button>
            <button class="btn approve" :disabled="saving" @click="reviewScenario(s.scenario_id, 'approve')">批准场景</button>
            <button class="btn reject" :disabled="saving" @click="reviewScenario(s.scenario_id, 'reject')">拒绝</button>
          </div>
          <p class="hint">
            修改文本会使现有 TTS 音频作废并需重新生成; 修改后场景回到「待审核」。
            目标表达必须仍出现在文本中, 否则保存会被拒绝。
          </p>
        </section>

        <p v-if="toast" class="toast">{{ toast }}</p>
      </template>
    </div>
  </div>
  </TeacherGate>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import TeacherGate from './TeacherGate.vue'
import {
  scenarioAudioUrl,
  teacherFetchExpressionDetail,
  teacherRegenerateAudio,
  teacherReviewExpression,
  teacherReviewScenario,
  teacherUpdateExpression,
  teacherUpdateScenario
} from '../../services/listeningApi'

const route = useRoute()
const expressionId = String(route.params.expressionId)

const detail = ref<any>(null)
const loading = ref(true)
const errorMessage = ref('')
const saving = ref(false)
const toast = ref('')

const editMeaning = ref('')
const editFunc = ref('')
const editRelated = ref('')
const scenarioEdits = ref<Record<string, any>>({})

function statusLabel(s: string): string {
  return { pending_teacher: '待审核', approved: '已批准', rejected: '已拒绝' }[s] || s
}

function showToast(msg: string) {
  toast.value = msg
  setTimeout(() => (toast.value = ''), 3000)
}

async function load() {
  loading.value = true
  errorMessage.value = ''
  try {
    detail.value = await teacherFetchExpressionDetail(expressionId)
    editMeaning.value = detail.value.meaning
    editFunc.value = detail.value.communicative_function
    editRelated.value = (detail.value.related_expressions || []).join(' / ')
    const edits: Record<string, any> = {}
    for (const s of detail.value.scenarios) {
      edits[s.scenario_id] = {
        text: s.text,
        scenario: s.scenario,
        communicative_function: s.communicative_function,
        difficulty: s.difficulty
      }
    }
    scenarioEdits.value = edits
  } catch (e) {
    errorMessage.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    loading.value = false
  }
}

async function saveExpression() {
  saving.value = true
  try {
    await teacherUpdateExpression(expressionId, {
      meaning: editMeaning.value,
      communicative_function: editFunc.value,
      related_expressions: editRelated.value.split('/').map((x) => x.trim()).filter(Boolean)
    })
    showToast('表达已保存, 状态回到待审核')
    await load()
  } catch (e) {
    showToast(e instanceof Error ? e.message : '保存失败')
  } finally {
    saving.value = false
  }
}

async function saveScenario(scenarioId: string) {
  saving.value = true
  try {
    await teacherUpdateScenario(scenarioId, scenarioEdits.value[scenarioId])
    showToast('场景已保存; 若文本变更, 音频已作废, 请重新生成')
    await load()
  } catch (e) {
    showToast(e instanceof Error ? e.message : '保存失败')
  } finally {
    saving.value = false
  }
}

async function reviewExpression(action: 'approve' | 'reject') {
  saving.value = true
  try {
    await teacherReviewExpression(expressionId, action)
    showToast(action === 'approve' ? '表达已批准' : '表达已拒绝')
    await load()
  } finally {
    saving.value = false
  }
}

async function reviewScenario(scenarioId: string, action: 'approve' | 'reject') {
  saving.value = true
  try {
    await teacherReviewScenario(scenarioId, action)
    showToast(action === 'approve' ? '场景已批准' : '场景已拒绝')
    await load()
  } finally {
    saving.value = false
  }
}

async function regenerate(scenarioId: string) {
  saving.value = true
  try {
    await teacherRegenerateAudio(scenarioId)
    showToast('TTS 已重新生成')
    await load()
  } catch (e) {
    showToast(e instanceof Error ? e.message : '生成失败')
  } finally {
    saving.value = false
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

.teacher-container { max-width: 860px; margin: 0 auto; }

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

.hero h1 { margin: 0; font-size: 30px; }

.source-line {
  margin-top: 10px; font-size: 13px; color: rgba(242, 239, 233, 0.5);
  display: flex; gap: 10px; align-items: center; flex-wrap: wrap;
}

.source-sentence {
  margin-top: 10px; font-size: 13px; font-style: italic;
  color: rgba(242, 239, 233, 0.55); line-height: 1.7;
}

.rev { font-size: 11px; color: rgba(242, 239, 233, 0.35); }

.card {
  margin-top: 20px;
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 18px;
  padding: 22px;
}

.card-head {
  display: flex; justify-content: space-between;
  align-items: center; gap: 10px; flex-wrap: wrap;
}

.card-title { margin: 0 0 14px; font-size: 17px; }

.field { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }

.field span { font-size: 12px; color: rgba(242, 239, 233, 0.5); }

.field input, .field textarea, .field select {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  color: #f2efe9;
  padding: 10px 12px;
  font-size: 14px;
  font-family: inherit;
}

.field textarea { resize: vertical; line-height: 1.7; }

.field-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.audio-row {
  display: flex; align-items: center; gap: 12px;
  flex-wrap: wrap; margin-bottom: 14px;
}

.audio-row audio { max-width: 320px; }

.audio-meta { font-size: 11.5px; color: rgba(242, 239, 233, 0.4); }

.audio-meta.warn { color: #e8907a; }

.actions { display: flex; gap: 10px; margin-top: 6px; flex-wrap: wrap; }

.btn {
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: transparent; color: #f2efe9;
  border-radius: 10px; padding: 9px 18px;
  font-size: 13px; cursor: pointer;
}

.btn:hover:not(:disabled) { border-color: #e8a75c; color: #e8a75c; }

.btn.approve { border-color: rgba(127, 216, 164, 0.5); color: #7fd8a4; }
.btn.reject { border-color: rgba(232, 144, 122, 0.5); color: #e8907a; }
.btn.small { padding: 6px 12px; font-size: 12px; }
.btn:disabled { opacity: 0.4; cursor: not-allowed; }

.hint { margin-top: 10px; font-size: 11.5px; color: rgba(242, 239, 233, 0.35); }

.badge {
  font-size: 11.5px; border: 1px solid;
  border-radius: 999px; padding: 3px 10px;
}
.badge.rs-pending_teacher { color: #e8a75c; border-color: rgba(232, 167, 92, 0.4); }
.badge.rs-approved { color: #7fd8a4; border-color: rgba(127, 216, 164, 0.4); }
.badge.rs-rejected { color: #e8907a; border-color: rgba(232, 144, 122, 0.4); }

.answers { margin-top: 14px; font-size: 13px; }
.answers summary { cursor: pointer; color: rgba(242, 239, 233, 0.55); }
.qa { margin-top: 10px; }
.qa-q { margin: 0 0 6px; color: rgba(242, 239, 233, 0.8); }
.qa-o { margin: 2px 0; color: rgba(242, 239, 233, 0.55); }
.qa-o.correct { color: #7fd8a4; }

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

.retry-button {
  margin-top: 16px; border: none; border-radius: 12px;
  padding: 10px 22px; background: #e8a75c;
  color: #17120c; font-weight: 600; cursor: pointer;
}
</style>
