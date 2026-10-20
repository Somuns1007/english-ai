<template>
  <div class="writing-page">
    <PlanetCanvas planet="neptune" />
    <div class="writing-container">
      <div class="topbar">
        <button
          class="back-button"
          @click="$router.push('/')"
        >
          ← 返回首页
        </button>
      </div>

      <section class="hero">
        <p class="eyebrow">
          AI Writing Coach
        </p>

        <h1>作文批改</h1>

        <p class="description">
          选择考试类型并提交作文，系统将从语法、词汇、句式、逻辑、内容和整体表达等方面进行分析。
        </p>
      </section>

      <section class="editor-card">
        <div class="form-row">
          <div class="form-group">
            <label>考试类型</label>

            <select v-model="examType">
              <option value="cet4">
                大学英语四级
              </option>

              <option value="cet6">
                大学英语六级
              </option>

              <option value="postgraduate">
                考研英语
              </option>

              <option value="ielts">
                雅思写作
              </option>

              <option value="gaokao">
                高考英语
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>作文类型</label>

            <select v-model="writingType">
              <option value="essay">
                议论文
              </option>

              <option value="application">
                应用文
              </option>

              <option value="continuation">
                读后续写
              </option>

              <option value="translation">
                翻译写作
              </option>
            </select>
          </div>
        </div>

        <div class="form-group">
          <label>作文题目</label>

          <textarea
            v-model="prompt"
            class="prompt-input"
            placeholder="请输入作文题目或写作要求"
          ></textarea>
        </div>

        <div class="form-group">
          <div class="label-row">
            <label>学生作文</label>

            <span>
              {{ wordCount }} words
            </span>
          </div>

          <textarea
            v-model="essay"
            class="essay-input"
            placeholder="Paste or type the student's essay here..."
          ></textarea>
        </div>

        <div class="actions">
          <button
            class="clear-button"
            :disabled="loading"
            @click="clearEssay"
          >
            清空
          </button>

          <button
            class="submit-button"
            :disabled="!essay.trim() || loading"
            @click="submitEssay"
          >
            {{
              loading
                ? 'AI 正在批改...'
                : '开始批改'
            }}
          </button>
        </div>

        <div
          v-if="loading"
          class="loading-area"
        >
          <div class="loading-line"></div>

          <p>
            正在分析作文，请稍候……
          </p>
        </div>
      </section>

      <section
        v-if="submitted && grading"
        class="result-card main-result"
      >
        <div class="result-header">
          <div>
            <p class="result-label">
              AI GRADING REPORT
            </p>

            <h2>
              作文批改完成
            </h2>
          </div>

          <div class="overall-score">
            <span class="score-number">
              {{ grading.score.overall }}
            </span>

            <span class="score-text">
              综合评分
            </span>
          </div>
        </div>

        <div class="meta-grid">
          <div class="meta-item">
            <span>考试类型</span>

            <strong>
              {{ examTypeLabel }}
            </strong>
          </div>

          <div class="meta-item">
            <span>作文类型</span>

            <strong>
              {{ writingTypeLabel }}
            </strong>
          </div>

          <div class="meta-item">
            <span>字数</span>

            <strong>
              {{ responseData.data.wordCount }}
            </strong>
          </div>
        </div>

        <div class="score-grid">
          <div class="score-card">
            <span class="score-name">
              语言
            </span>

            <strong>
              {{ grading.score.language }}
            </strong>
          </div>

          <div class="score-card">
            <span class="score-name">
              内容
            </span>

            <strong>
              {{ grading.score.content }}
            </strong>
          </div>

          <div class="score-card">
            <span class="score-name">
              结构
            </span>

            <strong>
              {{ grading.score.organization }}
            </strong>
          </div>
        </div>
      </section>

      <section
        v-if="submitted && grading"
        class="result-card"
      >
        <p class="section-kicker">
          OVERALL FEEDBACK
        </p>

        <h3>
          整体评价
        </h3>

        <p class="feedback-text">
          {{ grading.summary }}
        </p>
      </section>

      <section
        v-if="
          submitted &&
          grading &&
          grading.sentenceFeedback &&
          grading.sentenceFeedback.length
        "
        class="result-card"
      >
        <div class="section-heading">
          <div>
            <p class="section-kicker">
              SENTENCE FEEDBACK
            </p>

            <h3>
              逐句批改
            </h3>
          </div>

          <span class="feedback-count">
            {{ grading.sentenceFeedback.length }}
            处
          </span>
        </div>

        <div
          v-for="(item, index) in grading.sentenceFeedback"
          :key="index"
          class="sentence-card"
        >
          <div class="sentence-index">
            {{ String(index + 1).padStart(2, '0') }}
          </div>

          <div class="sentence-content">
            <div class="feedback-block original-block">
              <p class="feedback-label">
                原句
              </p>

              <p class="english-text">
                {{ item.original }}
              </p>
            </div>

            <div class="feedback-block">
              <p class="feedback-label">
                问题
              </p>

              <p>
                {{ item.problem }}
              </p>
            </div>

            <div class="feedback-block">
              <p class="feedback-label">
                为什么
              </p>

              <p>
                {{ item.reason }}
              </p>
            </div>

            <div class="feedback-block revision-block">
              <p class="feedback-label">
                修改后
              </p>

              <p class="english-text revision-text">
                {{ item.revision }}
              </p>
            </div>
          </div>
        </div>
      </section>

      <section
        v-if="submitted && grading"
        class="result-card"
      >
        <p class="section-kicker">
          LOGIC & ORGANIZATION
        </p>

        <h3>
          逻辑与结构分析
        </h3>

        <p class="feedback-text">
          {{ grading.logicFeedback }}
        </p>
      </section>

      <section
        v-if="submitted && grading"
        class="result-card rewrite-card"
      >
        <div class="section-heading">
          <div>
            <p class="section-kicker">
              REWRITTEN VERSION
            </p>

            <h3>
              全文升级版
            </h3>
          </div>

          <button
            class="copy-button"
            @click="copyRewrite"
          >
            {{
              copied
                ? '已复制'
                : '复制全文'
            }}
          </button>
        </div>

        <div class="rewrite-content">
          {{ grading.rewrite }}
        </div>
      </section>

      <section
        v-if="
          submitted &&
          responseData &&
          responseData.data &&
          responseData.data.prompt
        "
        class="result-card original-info"
      >
        <p class="section-kicker">
          ORIGINAL SUBMISSION
        </p>

        <h3>
          原始提交内容
        </h3>

        <div class="original-section">
          <span>作文题目</span>

          <p>
            {{ responseData.data.prompt }}
          </p>
        </div>

        <div class="original-section">
          <span>学生原文</span>

          <p class="original-essay">
            {{ responseData.data.essay }}
          </p>
        </div>
      </section>

      <section
        v-if="errorMessage"
        class="result-card error-card"
      >
        <p class="section-kicker error-kicker">
          REQUEST FAILED
        </p>

        <h3>
          批改失败
        </h3>

        <p class="feedback-text">
          {{ errorMessage }}
        </p>
      </section>
    </div>
  </div>
</template>

<script>
import PlanetCanvas from '../components/PlanetCanvas.vue'

export default {
  name: 'WritingView',
  components: { PlanetCanvas },

  data() {
    return {
      examType: 'cet6',
      writingType: 'essay',
      prompt: '',
      essay: '',
      submitted: false,
      loading: false,
      errorMessage: '',
      responseData: null,
      copied: false
    }
  },

  computed: {
    wordCount() {
      const text = this.essay.trim()

      if (!text) {
        return 0
      }

      return text
        .split(/\s+/)
        .filter(Boolean)
        .length
    },

    examTypeLabel() {
      const labels = {
        cet4: '大学英语四级',
        cet6: '大学英语六级',
        postgraduate: '考研英语',
        ielts: '雅思写作',
        gaokao: '高考英语'
      }

      return (
        labels[this.examType] ||
        this.examType
      )
    },

    writingTypeLabel() {
      const labels = {
        essay: '议论文',
        application: '应用文',
        continuation: '读后续写',
        translation: '翻译写作'
      }

      return (
        labels[this.writingType] ||
        this.writingType
      )
    },

    grading() {
      if (
        !this.responseData ||
        !this.responseData.data
      ) {
        return null
      }

      return (
        this.responseData.data.grading ||
        null
      )
    }
  },

  methods: {
    clearEssay() {
      this.prompt = ''
      this.essay = ''
      this.submitted = false
      this.loading = false
      this.errorMessage = ''
      this.responseData = null
      this.copied = false
    },

    async submitEssay() {
      if (!this.essay.trim()) {
        return
      }

      this.loading = true
      this.submitted = false
      this.errorMessage = ''
      this.responseData = null
      this.copied = false

      try {
        const response = await fetch(
          '/api/essay',
          {
            method: 'POST',

            headers: {
              'Content-Type':
                'application/json'
            },

            body: JSON.stringify({
              examType: this.examType,
              writingType: this.writingType,
              prompt: this.prompt,
              essay: this.essay
            })
          }
        )

        let result = null

        try {
          result =
            await response.json()
        } catch {
          result = null
        }

        if (!response.ok) {
          const backendMessage =
            result &&
            result.detail
              ? result.detail
              : `请求失败，状态码：${response.status}`

          throw new Error(
            backendMessage
          )
        }

        if (
          !result ||
          !result.success
        ) {
          throw new Error(
            '后端没有返回有效的批改结果'
          )
        }

        if (
          !result.data ||
          !result.data.grading
        ) {
          throw new Error(
            'AI 批改结果结构不完整'
          )
        }

        this.responseData =
          result

        this.submitted =
          true
      } catch (error) {
        console.error(
          '提交作文时发生错误：',
          error
        )

        this.errorMessage =
          error instanceof Error
            ? error.message
            : '作文批改失败，请稍后重试。'
      } finally {
        this.loading = false
      }
    },

    async copyRewrite() {
      if (
        !this.grading ||
        !this.grading.rewrite
      ) {
        return
      }

      try {
        await navigator.clipboard.writeText(
          this.grading.rewrite
        )

        this.copied = true

        setTimeout(() => {
          this.copied = false
        }, 1800)
      } catch (error) {
        console.error(
          '复制失败：',
          error
        )
      }
    }
  }
}
</script>

<style scoped>
/* ============================================================
   海王星 · 冰巨星 v2 —— 作文批改
   背景由 <PlanetCanvas planet="neptune"> 实时绘制：
   三层视差超音速风纹 + 鼠标气流吹偏的钻石雨 + 大暗斑涡旋。
   本样式只负责冰晶玻璃组件层。
   ============================================================ */
.writing-page {
  --nep-ink: #e9f2fb;
  --nep-muted: rgba(214, 230, 246, .60);
  --nep-faint: rgba(206, 224, 246, .40);
  --nep-accent: #79c5ec;
  --nep-deep: #3d7fc4;
  --nep-ice: #7de0d0;
  --nep-border: rgba(140, 200, 240, .15);
  --nep-glass: rgba(14, 26, 48, .48);

  position: relative;
  z-index: 0;
  min-height: 100vh;
  padding: 48px 24px 96px;
  color: var(--nep-muted);
  color-scheme: dark;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.writing-container { width: 100%; max-width: 980px; margin: 0 auto; }

.topbar { margin-bottom: 56px; }
.back-button {
  border: none;
  background: transparent;
  color: var(--nep-faint);
  font-size: 14px;
  cursor: pointer;
  padding: 0;
  transition: color .25s ease-out, text-shadow .25s ease-out;
}
.back-button:hover {
  color: var(--nep-accent);
  text-shadow: 0 0 14px rgba(121, 197, 236, .4);
}

.hero { margin-bottom: 34px; }
.eyebrow {
  margin: 0 0 12px;
  color: var(--nep-accent);
  font-size: 12px;
  letter-spacing: 4px;
  text-transform: uppercase;
}
.hero h1 {
  margin: 0;
  font-size: clamp(36px, 6vw, 58px);
  font-weight: 700;
  letter-spacing: 2px;
  color: var(--nep-ink);
  text-shadow: 0 0 44px rgba(121, 197, 236, .28);
}
.description {
  max-width: 720px;
  margin-top: 18px;
  color: var(--nep-muted);
  line-height: 1.8;
  font-size: 15px;
}

/* 冰晶玻璃卡片 */
.editor-card,
.result-card {
  background: var(--nep-glass);
  border: 1px solid var(--nep-border);
  border-radius: 22px;
  padding: 30px;
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  box-shadow:
    0 22px 70px rgba(0, 0, 0, .35),
    inset 0 1px 0 rgba(190, 225, 255, .07);
}
.result-card { margin-top: 24px; }
.main-result {
  border-color: rgba(140, 200, 240, .24);
  box-shadow:
    0 22px 70px rgba(0, 0, 0, .35),
    0 0 54px -14px rgba(90, 150, 220, .30),
    inset 0 1px 0 rgba(190, 225, 255, .08);
}

.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
.form-group { margin-bottom: 24px; }
.form-group label {
  display: block;
  margin-bottom: 10px;
  font-size: 14px;
  color: var(--nep-muted);
}
.label-row { display: flex; justify-content: space-between; align-items: center; }
.label-row span { font-size: 12px; color: var(--nep-faint); }

/* 表单控件：极夜深海 + 冰蓝聚焦 */
select,
textarea {
  width: 100%;
  box-sizing: border-box;
  border: 1px solid rgba(140, 200, 240, .18);
  background: rgba(8, 18, 36, .55);
  color: var(--nep-ink);
  border-radius: 14px;
  outline: none;
  font: inherit;
  transition: border-color .25s ease-out, box-shadow .25s ease-out, background .25s ease-out;
}
select { height: 48px; padding: 0 14px; }
textarea { resize: vertical; padding: 16px; line-height: 1.8; }
textarea::placeholder { color: var(--nep-faint); }
select:focus,
textarea:focus {
  border-color: rgba(121, 197, 236, .6);
  background: rgba(10, 22, 42, .65);
  box-shadow: 0 0 0 3px rgba(121, 197, 236, .12), 0 0 22px -6px rgba(121, 197, 236, .3);
}
.prompt-input { min-height: 110px; }
.essay-input { min-height: 320px; }

.actions { display: flex; justify-content: flex-end; gap: 12px; margin-top: 8px; }
.clear-button,
.submit-button,
.copy-button {
  border: none;
  border-radius: 12px;
  font-size: 14px;
  cursor: pointer;
  transition: opacity .2s ease-out, transform .2s ease-out, box-shadow .2s ease-out, filter .2s ease-out;
}
.clear-button,
.submit-button { padding: 12px 22px; }
.clear-button {
  background: rgba(140, 190, 240, .08);
  color: var(--nep-muted);
  border: 1px solid rgba(140, 200, 240, .16);
}

/* 主按钮：一片冰川光 */
.submit-button {
  background: linear-gradient(135deg, #8fd2f2, #3f86c8);
  color: #061423;
  font-weight: 600;
}
.clear-button:hover:not(:disabled),
.submit-button:hover:not(:disabled),
.copy-button:hover { transform: translateY(-1px); }
.submit-button:hover:not(:disabled) {
  box-shadow: 0 0 26px -6px rgba(121, 197, 236, .55);
  filter: brightness(1.05);
}
.clear-button:hover:not(:disabled) {
  box-shadow: 0 0 16px -6px rgba(121, 197, 236, .3);
}
.clear-button:disabled,
.submit-button:disabled { opacity: .35; cursor: not-allowed; transform: none; }

/* 加载：一道扫过的冰晶光 */
.loading-area { margin-top: 24px; }
.loading-area p { margin: 12px 0 0; color: var(--nep-faint); font-size: 13px; }
.loading-line {
  height: 2px;
  border-radius: 999px;
  background: linear-gradient(90deg, transparent, rgba(121, 197, 236, .85), transparent);
  background-size: 200% 100%;
  animation: loadingMove 1.4s linear infinite;
}
@keyframes loadingMove {
  from { background-position: 200% 0; }
  to   { background-position: -200% 0; }
}

.result-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 24px; }
.result-header h2,
.result-card h3 { margin: 0; font-weight: 650; letter-spacing: 1px; color: var(--nep-ink); }
.result-header h2 { font-size: 28px; }
.result-card h3 { font-size: 22px; }
.result-label,
.section-kicker {
  margin: 0 0 10px;
  color: var(--nep-accent);
  font-size: 11px;
  letter-spacing: 3px;
  text-transform: uppercase;
}

/* 综合评分：冰蓝光环 */
.overall-score {
  min-width: 110px;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 18px 20px;
  border: 1px solid rgba(121, 197, 236, .24);
  border-radius: 18px;
  background: rgba(121, 197, 236, .07);
  box-shadow: inset 0 0 24px rgba(121, 197, 236, .06);
}
.score-number {
  color: var(--nep-accent);
  font-size: 40px;
  line-height: 1;
  font-weight: 700;
  text-shadow: 0 0 24px rgba(121, 197, 236, .45);
}
.score-text { margin-top: 8px; color: var(--nep-faint); font-size: 11px; letter-spacing: 1.5px; }

.meta-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 28px; }
.meta-item {
  display: flex;
  flex-direction: column;
  gap: 7px;
  padding: 16px;
  border-radius: 14px;
  background: rgba(5, 12, 26, .5);
}
.meta-item span { color: var(--nep-faint); font-size: 11px; }
.meta-item strong { color: var(--nep-ink); font-size: 14px; }

.score-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-top: 12px; }
.score-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px;
  border-radius: 14px;
  background: rgba(140, 190, 240, .04);
  border: 1px solid rgba(140, 200, 240, .10);
}
.score-name { color: var(--nep-muted); font-size: 13px; }
.score-card strong { color: var(--nep-accent); font-size: 23px; }

.feedback-text { color: var(--nep-muted); line-height: 1.9; }
.section-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; }
.feedback-count {
  padding: 7px 10px;
  border-radius: 999px;
  background: rgba(121, 197, 236, .10);
  color: var(--nep-accent);
  font-size: 12px;
}

.sentence-card {
  display: grid;
  grid-template-columns: 44px 1fr;
  gap: 18px;
  margin-top: 22px;
  padding-top: 22px;
  border-top: 1px solid rgba(140, 200, 240, .10);
}
.sentence-index { color: rgba(121, 197, 236, .55); font-size: 13px; letter-spacing: 1px; }
.sentence-content { min-width: 0; }
.feedback-block { margin-bottom: 18px; }
.feedback-block:last-child { margin-bottom: 0; }
.feedback-label {
  margin: 0 0 8px;
  color: var(--nep-faint);
  font-size: 11px;
  letter-spacing: 1.5px;
}
.feedback-block p:not(.feedback-label) { margin: 0; color: rgba(233, 242, 251, .74); line-height: 1.9; }
.english-text { font-family: Georgia, 'Times New Roman', serif; font-size: 16px; }

/* 原句 = 深海暗格；修改后 = 冰青正色，语义区分保留 */
.original-block {
  padding: 15px 17px;
  border-radius: 12px;
  background: rgba(8, 16, 34, .55);
  border: 1px solid rgba(140, 200, 240, .08);
}
.revision-block {
  padding: 15px 17px;
  border-radius: 12px;
  background: rgba(125, 224, 208, .06);
  border: 1px solid rgba(125, 224, 208, .14);
}
.revision-text { color: rgba(196, 236, 223, .95) !important; }

.copy-button {
  padding: 9px 14px;
  background: rgba(121, 197, 236, .10);
  color: var(--nep-accent);
  border: 1px solid rgba(121, 197, 236, .18);
}
.copy-button:hover { box-shadow: 0 0 16px -6px rgba(121, 197, 236, .35); }
.rewrite-content {
  margin-top: 22px;
  padding: 22px;
  border-radius: 16px;
  background: rgba(4, 10, 22, .55);
  color: rgba(233, 242, 251, .84);
  line-height: 2;
  white-space: pre-wrap;
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 16px;
}

.original-info { opacity: .82; }
.original-section { margin-top: 20px; }
.original-section span {
  display: block;
  margin-bottom: 8px;
  color: var(--nep-faint);
  font-size: 11px;
  letter-spacing: 1.5px;
}
.original-section p { margin: 0; color: var(--nep-muted); line-height: 1.9; }
.original-essay { white-space: pre-wrap; }

/* 错误语义色保留 */
.error-card { border-color: rgba(235, 110, 110, .3); }
.error-kicker { color: rgba(235, 130, 130, .9); }

/* 可访问性 */
.writing-page :is(a, button, select, textarea):focus-visible {
  outline: 2px solid var(--nep-accent);
  outline-offset: 3px;
}
@media (prefers-reduced-motion: reduce) {
  .writing-page *,
  .writing-page *::before,
  .writing-page *::after {
    animation-duration: .01ms !important;
    transition-duration: .01ms !important;
  }
}

@media (max-width: 720px) {
  .writing-page { padding: 24px 16px 60px; }
  .topbar { margin-bottom: 38px; }
  .form-row { grid-template-columns: 1fr; gap: 0; }
  .editor-card,
  .result-card,
  .main-result { padding: 22px; }
  .result-header { flex-direction: column; }
  .overall-score { width: 100%; box-sizing: border-box; }
  .meta-grid,
  .score-grid { grid-template-columns: 1fr; }
  .sentence-card { grid-template-columns: 1fr; gap: 8px; }
  .section-heading { flex-direction: column; }
  .essay-input { min-height: 260px; }
}
</style>
