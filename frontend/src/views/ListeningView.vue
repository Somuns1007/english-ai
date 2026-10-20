<template>
  <div class="listening-page">
    <PlanetCanvas planet="jupiter" />
    <div class="listening-container">
      <div class="topbar">
        <button class="back-button" @click="router.push('/')">← 返回首页</button>
      </div>

      <section class="hero">
        <p class="eyebrow">CET Listening</p>
        <h1>四六级听力训练</h1>
        <p class="description">先做一套真题，再把没听懂的地方一句一句弄懂。</p>
      </section>

      <!-- 新手三步：只告诉学生现在该点哪里 -->
      <section class="guide" aria-labelledby="guide-title">
        <h2 id="guide-title">第一次来？按下面三步走</h2>

        <ol class="guide-steps">
          <li class="guide-step" :class="{ done: currentUser }">
            <span class="num">{{ currentUser ? '✓' : '1' }}</span>
            <div class="body">
              <h3>登录</h3>
              <template v-if="currentUser">
                <p>已登录：{{ currentUser.email }}</p>
              </template>
              <template v-else>
                <p>没有账号的话先注册，只需要邮箱和密码。</p>
                <p class="note">不登录也能做题，但记录保存不了，第三步也就用不了。</p>
                <div class="btn-row">
                  <RouterLink class="btn primary" :to="{ path: '/login', query: { next: '/listening/' } }">登录</RouterLink>
                  <RouterLink class="btn" to="/register">注册</RouterLink>
                </div>
              </template>
            </div>
          </li>

          <li class="guide-step">
            <span class="num">2</span>
            <div class="body">
              <h3>做一套听力真题</h3>
              <p v-if="loading">正在加载……</p>
              <p v-else-if="errorMessage" class="warn">
                {{ errorMessage }} <button class="link-btn" @click="loadExams">重试</button>
              </p>
              <template v-else-if="learnableExams.length">
                <p>
                  选择四级或六级第 2 套，每套 25 题，约 30 分钟。<br />
                  和真实考试一样：题目只在录音里播放，屏幕上只显示 A、B、C、D 四个选项。交卷后马上出分。
                </p>
                <div class="btn-row">
                  <button v-for="exam in learnableExams" :key="exam.id" class="btn primary big" @click="openExam(exam)">
                    做{{ exam.exam_type === 'cet4' ? '四级' : '六级' }}真题（第 2 套）→
                  </button>
                </div>
              </template>
            </div>
          </li>

          <li class="guide-step">
            <span class="num">3</span>
            <div class="body">
              <h3>逐句弄懂没听懂的地方</h3>
              <p>交卷后，成绩页上有一个<strong>「逐句精听」</strong>按钮。点进去，挑一段没听懂的：</p>
              <p class="flow">先自己听写 → 再对照原文，看看哪些词没听出来 → 把生词存进生词本</p>
              <p class="note">不必一次练完整套，弄懂一段也行。</p>
            </div>
          </li>
        </ol>
      </section>

      <!-- 以后再来 -->
      <section class="block">
        <h2>下次来，从这里接着练</h2>
        <div class="card-grid">
          <RouterLink class="link-card" to="/listening/learning">
            <b>继续精听 / 复习生词本 →</b>
            <span>接着练上次没练完的段落，也可以复习生词本里今天该复习的单词。</span>
          </RouterLink>
          <RouterLink class="link-card" to="/listening/mistakes">
            <b>我的错题 →</b>
            <span>做错的题都收在这里，方便回头再看。</span>
          </RouterLink>
        </div>
      </section>

      <!-- 其他练习 -->
      <section class="block">
        <h2>其他练习 <span class="sub">选做，有空再练</span></h2>

        <div class="card-grid">
          <article v-for="exam in otherExams" :key="exam.id" class="link-card clickable" @click="openExam(exam)">
            <b>{{ shortTitle(exam) }} →</b>
            <span>
              这套用来测水平，做完只出分数，不能逐句精听。建议练完第 2 套再做，看看自己有没有进步。
            </span>
          </article>

          <article v-if="practiceMaterials.length" class="link-card clickable" @click="scrollTo('single')">
            <b>单段练习 →</b>
            <span>只听一段对话、答 3 道题，几分钟就能做完。</span>
          </article>

          <RouterLink v-for="l in toolLinks" :key="l.to" :to="l.to" class="link-card" :class="{ muted: l.soon }">
            <b>{{ l.title }} →<span v-if="l.soon" class="tag">即将上线</span></b>
            <span>{{ l.desc }}</span>
          </RouterLink>
        </div>
      </section>

      <!-- 单段练习列表 -->
      <section v-if="practiceMaterials.length" id="single" class="block">
        <h2>单段练习</h2>
        <p class="desc">
          先看一眼选项 → 把这段对话一口气听完（中途不能暂停）→ 答题 → 再完整听一遍，重做刚才做错的题。
        </p>
        <p class="caution">
          注意：这两段就是上面两套真题里的第一段对话。打算做整套的话，先做整套再来练，否则整套的分数会不准。
        </p>
        <div class="card-grid">
          <article v-for="m in practiceMaterials" :key="m.material_id" class="link-card clickable" @click="openPractice(m)">
            <b>{{ m.title }} →</b>
            <span>
              {{ m.check_count }} 道题 ·
              {{ m.material_id.includes('set1') ? '做完只出分数' : '做完可以逐句精听' }}
            </span>
          </article>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchV2Exams, fetchV2PracticeMaterials } from '../services/listeningApi'
import { currentUser, getMe } from '../services/authApi'
import PlanetCanvas from '../components/PlanetCanvas.vue'
import type { V2ExamSummary } from '../types/listening'
import type { V2PracticeMaterialSummary } from '../services/listeningApi'

const router = useRouter()

const exams = ref<V2ExamSummary[]>([])
const practiceMaterials = ref<V2PracticeMaterialSummary[]>([])
const loading = ref(true)
const errorMessage = ref('')

// 新手主线推荐第 2 套：只有它交卷后能进入逐句精听（与 ListeningExamV2View 结果页按钮条件一致）。
// 第 1 套保留为测评卷，放在「其他练习」里，供学完后测进步。
const LEARNABLE_EXAMS = ['cet6_202606_set2_v2', 'cet4_202606_set2_v2']
const learnableExams = computed(() => LEARNABLE_EXAMS.flatMap(id => exams.value.filter(e => e.id === id)))
const otherExams = computed(() => exams.value.filter(e => !LEARNABLE_EXAMS.includes(e.id)))

const toolLinks = [
  { to: '/listening/profile', title: '我的弱项', desc: '看看你在哪类题上丢分最多，主要错在哪里。', soon: false },
  { to: '/listening/dashboard', title: '学习记录', desc: '做过的练习、学过的单词，在一页里都能看到。', soon: false },
  { to: '/listening/expressions', title: '换场景练短语', desc: '把真题里的常用短语放进酒店、医院、公司等新的对话里，看看换个场景你还能不能听出来。', soon: false },
  { to: '/listening/lexicon', title: '听单词', desc: '先做一个小测试，再专门练习把单词听准。', soon: false },
  { to: '/listening/stem-bank', title: '按题型刷题', desc: '把四级或六级第 2 套的题按题型分开练。里面能看到原题，建议先做完对应整套再来。', soon: false },
  { to: '/listening/corpus', title: '真实录音', desc: '用真实的英语录音练听力。', soon: true },
]

function shortTitle(exam: V2ExamSummary) {
  const m = exam.title.match(/第\s*(\d+)\s*套/)
  return m ? `第 ${m[1]} 套${exam.exam_type === 'cet4' ? '四级' : '六级'}听力` : exam.title
}

function scrollTo(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function loadExams() {
  loading.value = true
  errorMessage.value = ''
  try {
    // V2.1: 首页只列 V2 套题(audio_only 新数据); legacy 套题入口暂时隐藏,旧数据与旧路由保留未删。
    exams.value = await fetchV2Exams()
    // V2.2: Continuous Practice Pilot 材料(gate 关闭时为空列表)
    practiceMaterials.value = await fetchV2PracticeMaterials()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '题目加载失败，请稍后重试。'
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

onMounted(() => {
  loadExams()
  getMe().catch(() => null)
})
</script>

<style scoped>
/* 木星 · 六级听力训练主页。背景由 <PlanetCanvas planet="jupiter"> 绘制，本页透明。
   结构：新手 3 步（登录 → 做第 2 套 → 逐句精听）+ 以后再来 + 其他练习。 */
.listening-page {
  position: relative;
  z-index: 0;
  min-height: 100vh;
  background: transparent;
  color: #f2efe9;
  color-scheme: dark;
  padding: 32px 24px 90px;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}
.listening-container { width: 100%; max-width: 860px; margin: 0 auto; }

.topbar { margin-bottom: 40px; }
.back-button {
  border: none; background: transparent; color: rgba(242, 239, 233, 0.55);
  font-size: 14px; cursor: pointer; padding: 0; transition: color 0.25s ease;
}
.back-button:hover { color: #e8a75c; }

.eyebrow { margin: 0 0 12px; color: #e8a75c; font-size: 12px; letter-spacing: 4px; text-transform: uppercase; }
.hero h1 {
  margin: 0; font-size: clamp(32px, 5vw, 46px); font-weight: 700; letter-spacing: 2px;
  text-shadow: 0 0 44px rgba(232, 167, 92, 0.3);
}
.description { margin: 16px 0 0; color: rgba(242, 239, 233, 0.8); line-height: 1.8; font-size: 17px; }

/* 新手三步 */
.guide {
  margin-top: 36px;
  padding: 28px 30px 10px;
  border-radius: 22px;
  background: rgba(30, 20, 14, 0.6);
  border: 1px solid rgba(232, 167, 92, 0.35);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
}
.guide h2 { margin: 0 0 8px; font-size: 22px; letter-spacing: 1px; color: #f3c48a; }
.guide-steps { list-style: none; margin: 0; padding: 0; }
.guide-step { display: flex; gap: 18px; padding: 20px 0; border-top: 1px solid rgba(226, 172, 110, 0.14); }
.guide-step:first-child { border-top: none; }
.num {
  flex: none; width: 38px; height: 38px; border-radius: 50%;
  display: grid; place-items: center; font-weight: 700; font-size: 17px;
  background: rgba(232, 167, 92, 0.16); border: 1px solid rgba(232, 167, 92, 0.5); color: #e8a75c;
}
.guide-step.done .num { background: rgba(127, 216, 164, 0.16); border-color: rgba(127, 216, 164, 0.55); color: #7fd8a4; }
.body { flex: 1; min-width: 0; }
.body h3 { margin: 6px 0 8px; font-size: 18px; letter-spacing: 1px; }
.body p { margin: 0 0 6px; line-height: 1.8; font-size: 15px; color: rgba(242, 239, 233, 0.82); }
.body strong { color: #f3c48a; }
.body .note { font-size: 13.5px; color: rgba(242, 239, 233, 0.55); }
.body .warn { color: #e8907a; }
.flow {
  display: inline-block; margin: 4px 0 8px !important; padding: 8px 14px; border-radius: 10px;
  background: rgba(232, 167, 92, 0.1); color: #f2dcc0 !important;
}

.btn-row { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 12px; }
.btn {
  display: inline-block; padding: 8px 20px; border-radius: 999px;
  border: 1px solid rgba(232, 167, 92, 0.45); background: transparent; color: #e8a75c;
  font-size: 14px; text-decoration: none; cursor: pointer; font-family: inherit;
  transition: background 0.25s, color 0.25s;
}
.btn:hover { background: rgba(232, 167, 92, 0.14); }
.btn.primary { background: #e8a75c; color: #17120c; border-color: #e8a75c; font-weight: 700; }
.btn.primary:hover { background: #f0b874; }
.btn.big { padding: 12px 30px; font-size: 16px; letter-spacing: 1px; }
.link-btn { border: none; background: none; color: #e8a75c; cursor: pointer; text-decoration: underline; font: inherit; }

/* 其他区块 */
.block { margin-top: 52px; scroll-margin-top: 24px; }
.block h2 { margin: 0; font-size: 20px; letter-spacing: 1px; }
.block h2 .sub { font-size: 13px; font-weight: 400; color: rgba(242, 239, 233, 0.45); margin-left: 8px; letter-spacing: 0; }
.desc { margin: 10px 0 0; color: rgba(242, 239, 233, 0.7); line-height: 1.8; font-size: 14.5px; }
.caution {
  margin: 10px 0 0; padding: 10px 14px; border-left: 3px solid rgba(232, 144, 122, 0.7);
  background: rgba(232, 144, 122, 0.08); border-radius: 0 10px 10px 0;
  color: rgba(242, 222, 214, 0.85); font-size: 13.5px; line-height: 1.7;
}

.card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; margin-top: 16px; }
.link-card {
  display: flex; flex-direction: column; gap: 8px; padding: 18px 20px; border-radius: 16px;
  background: rgba(30, 20, 14, 0.45); border: 1px solid rgba(226, 172, 110, 0.14);
  color: inherit; text-decoration: none;
  backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
  transition: border-color 0.25s, transform 0.25s;
}
.link-card.clickable { cursor: pointer; }
.link-card:hover { border-color: rgba(232, 167, 92, 0.45); transform: translateY(-2px); }
.link-card b { color: #e8a75c; font-size: 15.5px; letter-spacing: 0.5px; }
.link-card span { font-size: 13.5px; line-height: 1.7; color: rgba(242, 239, 233, 0.65); }
.link-card.muted { opacity: 0.55; }
.tag {
  margin-left: 8px; font-size: 11px; font-weight: 400; color: #e8a75c;
  border: 1px solid rgba(232, 167, 92, 0.35); border-radius: 999px; padding: 1px 8px;
}

@media (max-width: 640px) {
  .listening-page { padding: 24px 16px 70px; }
  .guide { padding: 22px 18px 6px; }
  .guide-step { gap: 12px; }
}

@media (prefers-reduced-motion: reduce) {
  .listening-page *, .listening-page *::before, .listening-page *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
  .link-card:hover { transform: none; }
}
</style>
