<template>
  <div class="profile-page">
    <div class="profile-container">
      <div class="topbar">
        <button class="back-button" @click="$router.push('/listening')">
          ← 返回听力首页
        </button>
        <button
          class="back-button"
          @click="$router.push('/listening/mistakes')"
        >
          错题本 →
        </button>
      </div>

      <div v-if="loading" class="state-card"><p>正在聚合证据……</p></div>
      <div v-else-if="errorMessage" class="state-card error">
        <p>{{ errorMessage }}</p>
      </div>

      <template v-else-if="profile">
        <section class="hero">
          <p class="eyebrow">Evidence Profile</p>
          <h1>能力画像</h1>
          <p class="description">{{ profile.evidence_note }}</p>
        </section>

        <!-- 推荐卡片(最多 3 个; 证据不足时如实显示继续观察) -->
        <section class="block">
          <h2 class="block-title">推荐</h2>
          <div
            v-if="!profile.recommendations.length"
            class="state-card small"
          >
            <p>暂无任何证据, 先去完成一套题。</p>
          </div>
          <div
            v-for="(r, i) in topRecommendations"
            :key="i"
            class="rec-card"
            :class="`p-${r.priority}`"
          >
            <div class="rec-head">
              <span class="rec-priority">{{ priorityLabel(r.priority) }}</span>
              <span class="rec-cause">{{ r.target_cause_zh }}</span>
              <span
                v-for="s in r.target_skill"
                :key="s.skill"
                class="skill-chip"
              >
                {{ s.zh }}
              </span>
            </div>
            <p class="rec-text">{{ r.recommendation }}</p>
            <button class="why-toggle" @click="toggleWhy(Number(i))">
              {{ whyOpen.has(Number(i)) ? '收起证据 ▲' : '为什么推荐我练这个？ ▼' }}
            </button>
            <div v-if="whyOpen.has(Number(i))" class="why-box">
              <ul class="why-list">
                <li v-for="(w, j) in r.why" :key="j">{{ w }}</li>
              </ul>
              <div class="ref-list">
                <template v-for="(ref, j) in r.evidence_refs" :key="j">
                  <button
                    v-if="ref.type === 'question' && ref.attempt_id"
                    class="ref-link"
                    @click="goReview(ref.attempt_id)"
                  >
                    Q{{ ref.question_number }} 题目证据 →
                  </button>
                  <span v-else class="ref-plain">
                    <template v-if="ref.type === 'training'">
                      训练记录 {{ ref.id }}
                    </template>
                    <template v-else>Q{{ ref.question_number }}</template>
                  </span>
                </template>
              </div>
            </div>
          </div>
        </section>

        <!-- 错因画像: 弱项排序, 历史置信度与当前风险分开 -->
        <section class="block">
          <h2 class="block-title">错因画像</h2>
          <div v-if="!profile.causes.length" class="state-card small">
            <p>暂无错因证据。</p>
          </div>
          <div
            v-for="c in profile.causes"
            :key="c.cause_tag"
            class="cause-card"
          >
            <button class="cause-head" @click="toggleCause(c.cause_tag)">
              <span class="cause-name">{{ c.zh }}</span>
              <span class="cause-conf">
                <template v-if="c.evidence_questions > 0">
                  历史置信度
                  <b>{{ Math.round(c.evidence_confidence * 100) }}%</b>
                  ({{ confLabel(c.confidence_level) }})
                </template>
                <template v-else>仅有反证</template>
              </span>
              <span class="badge" :class="`risk-${c.current_risk}`">
                当前风险 {{ riskLabel(c.current_risk) }}
              </span>
              <span class="badge mastery-badge" :class="c.cause_mastery">
                {{ causeMasteryLabel(c.cause_mastery) }}
              </span>
            </button>

            <p
              v-if="showRiskDropNote(c)"
              class="risk-drop"
            >
              历史弱项存在，近期风险下降（新题反证正在修正判断）。
            </p>

            <div class="cause-stats">
              <span>证据题数 {{ c.evidence_questions }}</span>
              <span>确认 {{ c.confirmed_questions }}</span>
              <span>候选 {{ c.candidate_only_questions }}</span>
              <span>
                训练 {{ c.trainings.passed }}/{{ c.trainings.total }} 达标
              </span>
              <span>
                同题恢复 {{ c.trend.within_question_recovery.recovered }}/{{
                  c.trend.within_question_recovery.total
                }}
              </span>
              <span>
                新题迁移 {{ c.trend.cross_question_transfer.transferred }}
              </span>
            </div>

            <div v-if="causeOpen.has(c.cause_tag)" class="cause-detail">
              <div class="reason-box">
                <p class="detail-label">置信度构成</p>
                <ul class="why-list">
                  <li v-for="(r, j) in c.reason" :key="j">{{ r.text }}</li>
                </ul>
                <p v-if="c.only_unverified_evidence" class="warn-note">
                  现有证据全部来自未经教师校验的内容，不单独形成结论。
                </p>
              </div>

              <div v-if="c.supporting_evidence.length" class="ev-box">
                <p class="detail-label">支持证据</p>
                <div
                  v-for="(e, j) in c.supporting_evidence"
                  :key="j"
                  class="ev-item"
                >
                  <span class="ev-type">{{ evidenceTypeLabel(e.type) }}</span>
                  <span v-if="e.question_number" class="ev-q">
                    Q{{ e.question_number }}
                  </span>
                  <span v-if="e.first_answer" class="ev-ans">
                    首答 {{ e.first_answer }} → 终答 {{ e.final_answer || '—' }}
                  </span>
                  <span v-if="e.confidence" class="ev-conf">
                    候选置信度 {{ Math.round(e.confidence * 100) }}%
                  </span>
                  <span v-if="e.provenance" class="ev-prov">
                    {{ provenanceLabel(e.provenance) }}
                  </span>
                  <button
                    v-if="e.attempt_id"
                    class="ref-link"
                    @click="goReview(e.attempt_id)"
                  >
                    复盘页 →
                  </button>
                  <ul v-if="e.evidence" class="ev-lines">
                    <li v-for="(line, k) in e.evidence" :key="k">
                      {{ line }}
                    </li>
                  </ul>
                </div>
              </div>

              <div v-if="c.counter_evidence.length" class="ev-box">
                <p class="detail-label">反证(含该陷阱但首答即对)</p>
                <div
                  v-for="(e, j) in c.counter_evidence"
                  :key="j"
                  class="ev-item counter"
                >
                  <span class="ev-type">反证</span>
                  <span class="ev-q">Q{{ e.question_number }}</span>
                  <span class="ev-ans">首答即对, 未被该陷阱带跑</span>
                  <button
                    v-if="e.attempt_id"
                    class="ref-link"
                    @click="goReview(e.attempt_id)"
                  >
                    复盘页 →
                  </button>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- 能力维度: 列表展示(不用雷达图), null 显示证据不足 -->
        <section class="block">
          <h2 class="block-title">能力维度</h2>
          <div class="skill-list">
            <div v-for="s in profile.skills" :key="s.skill" class="skill-row">
              <span class="skill-name">{{ s.zh }}</span>
              <template v-if="s.score === null">
                <span class="skill-insufficient">证据不足</span>
              </template>
              <template v-else>
                <span class="skill-bar">
                  <span
                    class="skill-fill"
                    :style="{ width: `${Math.round(s.score * 100)}%` }"
                  ></span>
                </span>
                <span class="skill-score">
                  {{ Math.round(s.score * 100) }}%
                </span>
                <span class="badge" :class="`risk-${s.level}`">
                  {{ skillLevelLabel(s.level) }}
                </span>
              </template>
              <span
                v-if="s.from_causes.length"
                class="skill-from"
              >
                来源: {{ s.from_causes.map((x: any) => x.cause_zh).join('、') }}
              </span>
            </div>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchProfile } from '../../services/listeningApi'
import { getStudentId } from '../../services/listeningEvents'

const router = useRouter()
const studentId = getStudentId()

const loading = ref(true)
const errorMessage = ref('')
const profile = ref<any>(null)
const whyOpen = ref(new Set<number>())
const causeOpen = ref(new Set<string>())

/** 推荐默认最多 3 个 */
const topRecommendations = computed(() =>
  (profile.value?.recommendations || []).slice(0, 3)
)

function toggleWhy(i: number) {
  const s = new Set(whyOpen.value)
  s.has(i) ? s.delete(i) : s.add(i)
  whyOpen.value = s
}

function toggleCause(tag: string) {
  const s = new Set(causeOpen.value)
  s.has(tag) ? s.delete(tag) : s.add(tag)
  causeOpen.value = s
}

function goReview(attemptId: string) {
  router.push(`/listening/review/${attemptId}`)
}

function priorityLabel(p: string): string {
  return (
    {
      high: '高优先级',
      medium: '巩固迁移',
      low: '间隔巩固',
      observe: '继续观察'
    }[p] || p
  )
}

function confLabel(level: string): string {
  return (
    { high: '高', medium: '中', low: '低', insufficient: '证据不足' }[level] ||
    level
  )
}

function riskLabel(r: string): string {
  return (
    { high: '高', medium: '中', low: '低', insufficient: '证据不足' }[r] || r
  )
}

function causeMasteryLabel(m: string): string {
  return (
    {
      unknown: '无证据',
      evidence_accumulating: '证据累积中',
      improving: '改善中',
      stable: '跨题稳定'
    }[m] || m
  )
}

function skillLevelLabel(level: string): string {
  return (
    {
      high_risk: '高风险',
      medium_risk: '中风险',
      low_risk: '低风险',
      insufficient: '证据不足'
    }[level] || level
  )
}

function evidenceTypeLabel(t: string): string {
  return (
    {
      confirmed_diagnosis: '已确认诊断',
      high_confidence_candidate: '系统候选',
      training_failed: '训练未达标'
    }[t] || t
  )
}

function provenanceLabel(p: string): string {
  return (
    {
      teacher_calibrated: '教师校准内容',
      generated_unverified: '未校验内容(弱证据)'
    }[p] || p
  )
}

/** 历史弱项存在(confidence 中/高)但当前风险被压低或已改善 → 明确区分表达 */
function showRiskDropNote(c: any): boolean {
  const historical = ['high', 'medium'].includes(c.confidence_level)
  const riskDropped = ['low', 'insufficient'].includes(c.current_risk)
  const improving = ['improving', 'stable'].includes(c.cause_mastery)
  return historical && (riskDropped || improving)
}

onMounted(async () => {
  try {
    profile.value = await fetchProfile(studentId)
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : '画像加载失败'
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.profile-page {
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

.profile-container {
  max-width: 980px;
  margin: 0 auto;
}

.topbar {
  margin-bottom: 32px;
  display: flex;
  justify-content: space-between;
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
  font-size: 13.5px;
  line-height: 1.8;
}

.block {
  margin-top: 36px;
}

.block-title {
  font-size: 15px;
  letter-spacing: 2px;
  color: rgba(242, 239, 233, 0.75);
  margin: 0 0 14px;
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

.state-card.small {
  margin-top: 0;
  padding: 24px;
}

.state-card.error {
  border-color: rgba(232, 144, 122, 0.4);
}

/* 推荐卡片 */
.rec-card {
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 16px;
  padding: 16px 20px;
  margin-bottom: 12px;
}

.rec-card.p-high {
  border-color: rgba(232, 144, 122, 0.45);
}

.rec-card.p-medium {
  border-color: rgba(232, 167, 92, 0.35);
}

.rec-card.p-observe {
  border-style: dashed;
  opacity: 0.85;
}

.rec-head {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.rec-priority {
  font-size: 11.5px;
  border-radius: 999px;
  padding: 2px 10px;
  border: 1px solid rgba(232, 167, 92, 0.5);
  color: #e8a75c;
}

.p-high .rec-priority {
  border-color: rgba(232, 144, 122, 0.6);
  color: #e8907a;
}

.p-observe .rec-priority {
  border-color: rgba(255, 255, 255, 0.2);
  color: rgba(242, 239, 233, 0.5);
}

.rec-cause {
  font-size: 14.5px;
  font-weight: 600;
}

.skill-chip {
  font-size: 11px;
  border-radius: 999px;
  padding: 1px 8px;
  background: rgba(126, 184, 232, 0.12);
  color: #7eb8e8;
}

.rec-text {
  margin: 10px 0 0;
  font-size: 13.5px;
  line-height: 1.7;
  color: rgba(242, 239, 233, 0.8);
}

.why-toggle {
  margin-top: 10px;
  border: none;
  background: transparent;
  color: #7eb8e8;
  font-size: 12.5px;
  cursor: pointer;
  padding: 0;
}

.why-box {
  margin-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.07);
  padding-top: 10px;
}

.why-list {
  margin: 0;
  padding-left: 18px;
  font-size: 12.5px;
  color: rgba(242, 239, 233, 0.65);
  line-height: 1.8;
}

.ref-list {
  margin-top: 8px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.ref-link {
  border: 1px solid rgba(126, 184, 232, 0.4);
  background: transparent;
  color: #7eb8e8;
  border-radius: 8px;
  padding: 3px 10px;
  font-size: 12px;
  cursor: pointer;
}

.ref-link:hover {
  background: rgba(126, 184, 232, 0.1);
}

.ref-plain {
  font-size: 12px;
  color: rgba(242, 239, 233, 0.45);
}

/* 错因卡片 */
.cause-card {
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 16px;
  padding: 14px 20px;
  margin-bottom: 10px;
}

.cause-head {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  background: transparent;
  border: none;
  color: inherit;
  cursor: pointer;
  padding: 0;
  text-align: left;
}

.cause-name {
  font-size: 14.5px;
  font-weight: 600;
}

.cause-conf {
  flex: 1;
  font-size: 12.5px;
  color: rgba(242, 239, 233, 0.55);
}

.cause-conf b {
  color: #e8a75c;
}

.badge {
  font-size: 11.5px;
  border-radius: 999px;
  padding: 2px 10px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  color: rgba(242, 239, 233, 0.5);
}

.badge.risk-high {
  border-color: rgba(232, 144, 122, 0.55);
  color: #e8907a;
}

.badge.risk-medium {
  border-color: rgba(232, 167, 92, 0.5);
  color: #e8a75c;
}

.badge.risk-low {
  border-color: rgba(127, 216, 164, 0.5);
  color: #7fd8a4;
}

.mastery-badge.improving {
  border-color: rgba(126, 184, 232, 0.5);
  color: #7eb8e8;
}

.mastery-badge.stable {
  border-color: rgba(127, 216, 164, 0.5);
  color: #7fd8a4;
}

.risk-drop {
  margin: 8px 0 0;
  font-size: 12.5px;
  color: #7fd8a4;
}

.cause-stats {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  margin-top: 10px;
  font-size: 12px;
  color: rgba(242, 239, 233, 0.5);
}

.cause-detail {
  margin-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.07);
  padding-top: 12px;
}

.detail-label {
  margin: 0 0 6px;
  font-size: 12px;
  letter-spacing: 1px;
  color: rgba(232, 167, 92, 0.85);
}

.warn-note {
  margin: 8px 0 0;
  font-size: 12px;
  color: #e8907a;
}

.ev-box {
  margin-top: 12px;
}

.ev-item {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  font-size: 12.5px;
  color: rgba(242, 239, 233, 0.65);
  padding: 6px 0;
  border-bottom: 1px dashed rgba(255, 255, 255, 0.06);
}

.ev-item.counter {
  color: rgba(127, 216, 164, 0.8);
}

.ev-type {
  font-size: 11px;
  border-radius: 6px;
  padding: 1px 8px;
  background: rgba(255, 255, 255, 0.07);
}

.ev-q {
  font-weight: 700;
  color: #e8a75c;
}

.ev-lines {
  width: 100%;
  margin: 4px 0 0;
  padding-left: 18px;
  font-size: 12px;
  color: rgba(242, 239, 233, 0.45);
  line-height: 1.7;
}

/* 能力维度 */
.skill-list {
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 16px;
  padding: 8px 20px;
}

.skill-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  flex-wrap: wrap;
}

.skill-row:last-child {
  border-bottom: none;
}

.skill-name {
  min-width: 130px;
  font-size: 13.5px;
}

.skill-insufficient {
  font-size: 12.5px;
  color: rgba(242, 239, 233, 0.35);
}

.skill-bar {
  flex: 1;
  max-width: 220px;
  height: 8px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.08);
  overflow: hidden;
}

.skill-fill {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, #e8a75c, #e8907a);
}

.skill-score {
  font-size: 12.5px;
  color: rgba(242, 239, 233, 0.65);
  min-width: 40px;
}

.skill-from {
  width: 100%;
  font-size: 11.5px;
  color: rgba(242, 239, 233, 0.4);
}
</style>
