<!-- Four gallery routes share layout, pagination and accessible moderation controls. -->
<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { currentUser, getMe } from '../../services/authApi'
import { getTeacherToken, setTeacherToken, clearTeacherToken } from '../../services/listeningApi'
import { galleryRequest, toggleLike, type GalleryImage, type GalleryPage, type GalleryStatus, type GallerySort } from '../../services/galleryApi'
import GalleryPhoto from '../../components/gallery/GalleryPhoto.vue'

const route = useRoute()
const mode = computed(() => route.path === '/admin/gallery' ? 'admin' : route.path.split('/')[2] || 'public')
const titles: Record<string, string> = { public: '学习间隙，看点可爱的', upload: '分享一张小美好', mine: '我的图片', admin: '图片审核' }
const labels: Record<GalleryStatus, string> = { pending: '审核中', approved: '已通过', rejected: '未通过' }
const items = ref<GalleryImage[]>([])
const page = ref(1), total = ref(0)
const filter = ref('pending')
const sort = ref<GallerySort>('latest')
const loading = ref(false), busy = ref(false), ready = ref(false), isAdmin = ref(false)
const error = ref(''), notice = ref(''), teacherToken = ref('')
const selected = ref<File | null>(null), preview = ref(''), caption = ref('')
const fileInput = ref<HTMLInputElement | null>(null)
const dragOver = ref(false)
const modal = ref<HTMLDialogElement | null>(null)
const enlarged = ref<GalleryImage | null>(null)
let requestId = 0

async function verifyAdmin() {
  isAdmin.value = false
  if (!currentUser.value) return
  if (currentUser.value.role !== 'admin' && !getTeacherToken()) return
  try { await galleryRequest<GalleryPage>('admin/gallery?page_size=1', {}, true); isAdmin.value = true }
  catch { /* Ordinary accounts must never get an administrative navigation entry. */ }
}
async function unlock() {
  error.value = ''; busy.value = true
  setTeacherToken(teacherToken.value)
  await verifyAdmin()
  teacherToken.value = ''
  if (!isAdmin.value) { clearTeacherToken(); error.value = '无法进入审核区，请确认已登录且教师口令正确。' }
  else await load()
  busy.value = false
}
async function load() {
  const ticket = ++requestId
  items.value = []; total.value = 0; error.value = ''; loading.value = false
  if (mode.value === 'upload' || (mode.value !== 'public' && !currentUser.value)
      || (mode.value === 'admin' && !isAdmin.value)) return
  loading.value = true
  try {
    const sortParam = mode.value === 'public' ? `&sort=${sort.value}` : ''
    const endpoint = mode.value === 'admin' ? `admin/gallery?status=${filter.value}`
      : `gallery/${mode.value === 'mine' ? 'mine' : 'public'}?`
    const result = await galleryRequest<GalleryPage>(`${endpoint}&page=${page.value}&page_size=30${sortParam}`, {}, mode.value === 'admin')
    if (ticket === requestId) { items.value = result.data; total.value = result.total }
  } catch (e) { if (ticket === requestId) error.value = e instanceof Error ? e.message : '加载失败' }
  finally { if (ticket === requestId) loading.value = false }
}
function clearSelection() {
  if (preview.value) URL.revokeObjectURL(preview.value)
  preview.value = ''; selected.value = null
  if (fileInput.value) fileInput.value.value = ''
}
function choose(files: FileList | null) {
  if (busy.value || !files?.length) return
  const selection = Array.from(files)
  error.value = ''; notice.value = ''; clearSelection()
  if (selection.length !== 1) { error.value = '一次请选择一张图片。'; return }
  const file = selection[0]!
  const extension = file.name.split('.').pop()?.toLowerCase() || ''
  const types: Record<string, string> = { jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png', webp: 'image/webp' }
  if (!types[extension] || types[extension] !== file.type) { error.value = '仅支持 JPG、PNG 和 WebP 图片。'; return }
  if (file.size > 10 * 1024 * 1024) { error.value = '图片不能超过 10MB。'; return }
  selected.value = file; preview.value = URL.createObjectURL(file)
}
function changed(event: Event) {
  const input = event.target as HTMLInputElement
  choose(input.files)
}
function dropped(event: DragEvent) { dragOver.value = false; choose(event.dataTransfer?.files || null) }
async function submit() {
  if (!selected.value || busy.value) return
  busy.value = true; error.value = ''; notice.value = ''
  const data = new FormData(); data.append('file', selected.value); data.append('caption', caption.value)
  try {
    await galleryRequest('gallery/upload', { method: 'POST', body: data })
    clearSelection(); caption.value = ''; notice.value = '上传成功，图片将在审核通过后展示。'
  } catch (e) { error.value = e instanceof Error ? e.message : '上传失败，请稍后重试。' }
  finally { busy.value = false }
}
async function review(item: GalleryImage, action: 'approve' | 'reject' | 'delete') {
  if (busy.value) return
  let reason = ''
  if (action === 'reject') {
    const answer = window.prompt('拒绝原因（可不填，最多 300 字）', '')
    if (answer === null) return
    reason = answer.trim()
    if (reason.length > 300) { error.value = '拒绝原因不能超过 300 字。'; return }
  }
  if (action === 'delete' && !window.confirm('确定删除图片和缩略图？此操作无法撤销。')) return
  busy.value = true; error.value = ''; notice.value = ''
  try {
    await galleryRequest(`admin/gallery/${item.id}${action === 'delete' ? '' : `/${action}`}`, {
      method: action === 'delete' ? 'DELETE' : 'POST',
      ...(action === 'reject' ? { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ reject_reason: reason }) } : {}),
    }, true)
    notice.value = action === 'approve' ? '已通过，图片已进入公开图片墙。' : action === 'reject' ? '已拒绝，图片不会公开展示。' : '图片已删除。'
    if (items.value.length === 1 && page.value > 1) page.value--
    await load()
  } catch (e) { error.value = e instanceof Error ? e.message : '操作失败' }
  finally { busy.value = false }
}
async function like(item: GalleryImage) {
  if (busy.value || !currentUser.value) return
  try {
    const result = await toggleLike(item.id)
    item.liked = result.liked
    item.like_count = result.like_count
    if (enlarged.value?.id === item.id) { enlarged.value.liked = result.liked; enlarged.value.like_count = result.like_count }
  } catch { /* silent — like is non-critical */ }
}
function openImage(item: GalleryImage) { enlarged.value = item; modal.value?.showModal() }
function date(value: string | null) { return value ? new Date(value).toLocaleString('zh-CN') : '' }
watch(() => route.path, () => { page.value = 1; notice.value = ''; clearSelection(); modal.value?.close(); void load() })
watch(filter, () => { page.value = 1; void load() })
watch(sort, () => { page.value = 1; void load() })
watch(() => currentUser.value?.id, async () => {
  if (!ready.value) return
  clearTeacherToken()
  ++requestId; items.value = []; isAdmin.value = false; modal.value?.close(); enlarged.value = null
  clearSelection(); await verifyAdmin(); await load()
})
onMounted(async () => {
  try { await getMe(); await verifyAdmin(); ready.value = true; await load() }
  catch { error.value = '无法获取登录状态，请刷新重试。'; ready.value = true }
})
onBeforeUnmount(() => { ++requestId; clearSelection() })

/* ================================================================
 * 【新增】太阳 Canvas —— 呼吸的恒星 + 日冕 + 太阳风粒子
 *  - 与现有钩子并存（Vue 3 <script setup> 允许多个 onMounted）
 *  - 不触碰任何现有 ref / 函数 / watch
 * ================================================================ */
const sunCanvas = ref<HTMLCanvasElement | null>(null)
let sunRaf: number | null = null
let sunResize: (() => void) | null = null

function initSun() {
  const canvas = sunCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches

  let W = 0, H = 0, DPR = 1

  const resize = () => {
    DPR = Math.min(window.devicePixelRatio || 1, 1.5)
    W = canvas.width = innerWidth * DPR
    H = canvas.height = innerHeight * DPR
    canvas.style.width = innerWidth + 'px'
    canvas.style.height = innerHeight + 'px'
  }
  resize()
  sunResize = resize
  addEventListener('resize', resize)

  const sun = () => {
    const s = Math.min(Math.max(Math.min(innerWidth, innerHeight) / 900, .6), 1.3)
    const R = 130 * s * DPR
    return { x: W * .5, y: -R * .42, R }
  }

  const DUST_COLORS = ['255,240,220', '255,214,150', '210,180,255']
  const dust = Array.from({ length: 110 }, () => ({
    x: Math.random(),
    y: Math.random(),
    r: Math.random() * 1.1 + .3,
    p: Math.random() * Math.PI * 2,
    s: .3 + Math.random() * .7,
    c: DUST_COLORS[Math.floor(Math.random() * DUST_COLORS.length)]
  }))

  const wind = Array.from({ length: 130 }, () => ({
    a: Math.random() * Math.PI * 2,
    d: Math.random(),
    v: .0006 + Math.random() * .0016,
    len: 6 + Math.random() * 18,
    w: .5 + Math.random() * 1.2,
    tw: Math.random() * Math.PI * 2,
    c: Math.random() < .72 ? '240,170,70' : (Math.random() < .6 ? '232,85,42' : '192,132,252')
  }))

  const proms = Array.from({ length: 4 }, (_, i) => ({
    ph: i * Math.PI * .5 + Math.random(),
    sp: .05 + Math.random() * .05,
    lift: 1.06 + Math.random() * .14,
    arc: .5 + Math.random() * .6
  }))

  const frame = (now: number) => {
    const t = now / 1000
    const { x: sx, y: sy, R } = sun()
    const breath = 1 + Math.sin(t * .55) * .035

    ctx.clearRect(0, 0, W, H)

    const bg = ctx.createLinearGradient(0, 0, 0, H)
    bg.addColorStop(0, '#161008')
    bg.addColorStop(.5, '#130f08')
    bg.addColorStop(1, '#0a0704')
    ctx.fillStyle = bg
    ctx.fillRect(0, 0, W, H)

    const corona = ctx.createRadialGradient(sx, sy, R * .6, sx, sy, R * 7.5 * breath)
    corona.addColorStop(0, 'rgba(255,190,90,.20)')
    corona.addColorStop(.35, 'rgba(240,150,50,.09)')
    corona.addColorStop(.7, 'rgba(210,90,40,.035)')
    corona.addColorStop(1, 'rgba(210,90,40,0)')
    ctx.fillStyle = corona
    ctx.fillRect(0, 0, W, H)

    const chromo = ctx.createRadialGradient(sx, sy, R * 1.05, sx, sy, R * 2.1 * breath)
    chromo.addColorStop(0, 'rgba(192,132,252,.10)')
    chromo.addColorStop(1, 'rgba(192,132,252,0)')
    ctx.fillStyle = chromo
    ctx.beginPath()
    ctx.arc(sx, sy, R * 2.1 * breath, 0, Math.PI * 2)
    ctx.fill()

    for (const d of dust) {
      const tw = .3 + .7 * Math.abs(Math.sin(t * d.s + d.p))
      ctx.beginPath()
      ctx.arc(d.x * W, d.y * H, d.r * DPR, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(${d.c},${tw * .55})`
      ctx.fill()
    }

    ctx.save()
    ctx.globalCompositeOperation = 'lighter'
    ctx.lineCap = 'round'
    for (const p of wind) {
      p.d += p.v
      if (p.d > 1) { p.d = 0; p.a = Math.random() * Math.PI * 2 }
      const dist = R * (1.1 + p.d * 4.2)
      const px = sx + Math.cos(p.a) * dist
      const py = sy + Math.sin(p.a) * dist
      const alpha = Math.sin(p.d * Math.PI) * (.5 + .5 * Math.sin(t * 1.8 + p.tw)) * .5
      if (alpha <= .01) continue
      ctx.beginPath()
      ctx.moveTo(px, py)
      ctx.lineTo(px + Math.cos(p.a) * p.len * DPR, py + Math.sin(p.a) * p.len * DPR)
      ctx.strokeStyle = `rgba(${p.c},${alpha})`
      ctx.lineWidth = p.w * DPR
      ctx.stroke()
    }
    ctx.restore()

    ctx.save()
    ctx.globalCompositeOperation = 'lighter'
    for (const pr of proms) {
      const a = pr.ph + t * pr.sp
      ctx.beginPath()
      ctx.ellipse(sx, sy, R * pr.lift * breath, R * (pr.lift - .04) * breath, 0, a, a + pr.arc)
      ctx.strokeStyle = 'rgba(255,170,80,.34)'
      ctx.lineWidth = 2.2 * DPR
      ctx.shadowColor = 'rgba(255,140,60,.8)'
      ctx.shadowBlur = 16 * DPR
      ctx.stroke()
      ctx.shadowBlur = 0
    }
    ctx.restore()

    const disc = ctx.createRadialGradient(sx - R * .25, sy - R * .25, R * .1, sx, sy, R)
    disc.addColorStop(0, '#fff6dd')
    disc.addColorStop(.35, '#ffd98a')
    disc.addColorStop(.7, '#f59a3c')
    disc.addColorStop(1, '#e8552a')
    ctx.beginPath()
    ctx.arc(sx, sy, R * breath, 0, Math.PI * 2)
    ctx.fillStyle = disc
    ctx.shadowColor = 'rgba(255,180,80,.9)'
    ctx.shadowBlur = 60 * DPR
    ctx.fill()
    ctx.shadowBlur = 0

    ctx.beginPath()
    ctx.arc(sx, sy, R * breath * 1.01, 0, Math.PI * 2)
    ctx.strokeStyle = 'rgba(255,220,150,.5)'
    ctx.lineWidth = 1.4 * DPR
    ctx.stroke()
  }

  if (reduced) {
    frame(0)
  } else {
    const loop = (now: number) => { frame(now); sunRaf = requestAnimationFrame(loop) }
    sunRaf = requestAnimationFrame(loop)
  }
}

onMounted(initSun)
onBeforeUnmount(() => {
  if (sunRaf !== null) cancelAnimationFrame(sunRaf)
  if (sunResize) removeEventListener('resize', sunResize)
})
</script>

<template>
  <main class="gallery-page">
    <!-- 太阳画布：呼吸的恒星 + 日冕 + 太阳风粒子，铺满整个视口 -->
    <canvas ref="sunCanvas" class="sun-canvas" aria-hidden="true"></canvas>
    <!-- 舷窗暗角：飞船窗口边缘的收光 -->
    <div class="sun-vignette" aria-hidden="true"></div>

    <!-- 内容层，z-index 抬升到画布之上 -->
    <div class="gallery-content">
      <nav class="gallery-nav" aria-label="图片分享导航">
        <RouterLink to="/">← 返回自习室</RouterLink>
        <div><RouterLink to="/gallery">图片墙</RouterLink><RouterLink to="/gallery/upload">分享图片</RouterLink>
          <RouterLink to="/gallery/mine">我的图片</RouterLink><RouterLink v-if="isAdmin" to="/admin/gallery">审核后台</RouterLink></div>
      </nav>
      <header><p class="eyebrow">自习室 · 休息一下</p><h1>{{ titles[mode] }}</h1>
        <p>猫猫狗狗、校园风景，或是今天的小小惊喜。每一张公开图片，都经过人工审核。</p></header>
      <p v-if="error" class="message error" role="alert">{{ error }} <button v-if="!busy" @click="load">刷新列表</button></p>
      <p v-if="notice" class="message success" role="status">{{ notice }} <RouterLink to="/gallery/mine">查看我的图片 →</RouterLink></p>
      <section v-if="!ready" class="empty" role="status">正在检查登录状态…</section>
      <section v-else-if="mode !== 'public' && !currentUser" class="empty"><h2>先登录，再分享</h2>
        <p>登录后可以提交图片、查看自己的审核结果。</p><RouterLink class="primary" :to="{ path: '/login', query: { next: route.path } }">去登录</RouterLink></section>
      <section v-else-if="mode === 'admin' && !isAdmin" class="upload-card">
        <h2>管理员验证</h2><p>使用现有教师口令验证权限，审核操作会记录到当前登录账号。</p>
        <form @submit.prevent="unlock"><label>教师口令<input v-model="teacherToken" type="password" autocomplete="off" required /></label>
          <button class="primary" :disabled="busy">验证并进入</button></form>
      </section>
      <form v-else-if="mode === 'upload'" class="upload-card" @submit.prevent="submit">
        <div class="drop-zone" :class="{ dragging: dragOver }" @dragover.prevent="dragOver = true" @dragleave.prevent="dragOver = false" @drop.prevent="dropped">
          <img v-if="preview" class="upload-preview" :src="preview" alt="待提交图片预览" />
          <template v-else><span class="upload-symbol" aria-hidden="true">＋</span><h2>把今天的小美好放在这里</h2><p>拖入一张图片，或从手机相册选择</p></template>
          <input ref="fileInput" class="file-input" type="file" accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp" :disabled="busy" aria-label="选择图片" @change="changed" />
          <button type="button" :disabled="busy" @click="fileInput?.click()">{{ preview ? '重新选择' : '选择图片' }}</button>
          <button v-if="preview" type="button" :disabled="busy" @click="clearSelection">移除</button>
          <small>JPG / PNG / WebP · 每张不超过 10MB</small>
        </div>
        <label>一句图片说明 <span>（选填）</span><textarea v-model="caption" maxlength="200" rows="3" placeholder="比如：自习结束，遇见一只晒太阳的猫。" :disabled="busy" /></label>
        <small>{{ caption.length }}/200</small>
        <p class="privacy-note">请分享你有权发布的图片，避免包含人脸隐私、证件、联系方式等信息。图片和说明通过人工审核后才会公开。</p>
        <button class="primary" :disabled="!selected || busy">{{ busy ? '正在提交…' : '提交审核' }}</button>
      </form>
      <section v-else>
        <div class="list-heading"><h2>{{ mode === 'admin' ? '审核队列' : mode === 'mine' ? '每一份分享都有记录' : '今日随手拍' }}</h2>
          <div v-if="mode === 'public'" class="sort-tabs">
            <button :class="{ active: sort === 'latest' }" @click="sort = 'latest'">最新</button>
            <button :class="{ active: sort === 'popular' }" @click="sort = 'popular'">最热</button>
          </div>
          <label v-if="mode === 'admin'">筛选 <select v-model="filter" :disabled="busy"><option value="pending">待审核</option><option value="approved">已通过</option><option value="rejected">已拒绝</option><option value="all">全部</option></select></label>
          <span>{{ total }} 张图片</span></div>
        <p v-if="loading" class="empty" role="status">正在加载图片…</p>
        <div v-else-if="!items.length" class="empty"><h2>{{ mode === 'admin' ? '这里暂时没有图片' : '这里还很安静' }}</h2><p>{{ mode === 'public' ? '分享一张生活照片，审核通过后就会出现在这里。' : '新的上传和审核结果会显示在这里。' }}</p></div>
        <div v-else class="gallery-grid">
          <article v-for="item in items" :key="`${currentUser?.id || 'guest'}-${item.id}`" class="photo-card">
            <button class="photo-button" :aria-label="`查看大图：${item.caption || '分享图片'}`" @click="openImage(item)">
              <GalleryPhoto :url="item.thumbnail_url" :admin="mode === 'admin'" :alt="item.caption || '自习室生活分享'" />
            </button>
            <div class="photo-info"><span v-if="mode !== 'public'" class="status" :class="item.status">{{ labels[item.status] }}</span>
              <p class="caption">{{ item.caption || '一张生活里的小美好' }}</p>
              <div class="photo-meta">
                <button v-if="mode === 'public' || mode === 'mine'" class="like-btn" :class="{ liked: item.liked }" :disabled="!currentUser" :title="currentUser ? (item.liked ? '取消喜欢' : '喜欢') : '登录后可点赞'" @click.stop="like(item)">{{ item.liked ? '❤️' : '🤍' }} {{ item.like_count || '' }}</button>
                <small>{{ date(mode === 'public' ? item.reviewed_at : item.created_at) }}</small>
              </div>
              <p v-if="item.status === 'rejected' && item.reject_reason" class="reason">未通过原因：{{ item.reject_reason }}</p>
              <template v-if="mode === 'admin'"><p class="user-info">{{ item.user_email || '账号已不可用' }} · {{ ((item.file_size || 0) / 1024).toFixed(0) }} KB</p>
                <div class="actions"><button :disabled="busy || item.status === 'approved'" @click="review(item, 'approve')">通过</button>
                  <button :disabled="busy || item.status === 'rejected'" @click="review(item, 'reject')">拒绝</button><button :disabled="busy" @click="review(item, 'delete')">删除</button></div></template>
            </div>
          </article>
        </div>
        <nav v-if="total > 30 || page > 1" class="pagination" aria-label="图片分页"><button :disabled="page <= 1 || loading || busy" @click="page--; load()">上一页</button><span>第 {{ page }} 页</span><button :disabled="page * 30 >= total || loading || busy" @click="page++; load()">下一页</button></nav>
      </section>
      <dialog ref="modal" class="image-dialog" @close="enlarged = null" @click="($event.target === modal) && modal?.close()">
        <button class="close-preview" autofocus @click="modal?.close()">关闭大图 ×</button>
        <GalleryPhoto v-if="enlarged" :url="enlarged.image_url" :admin="mode === 'admin'" :alt="enlarged.caption || '分享图片大图'" />
        <div v-if="enlarged" class="dialog-footer">
          <p>{{ enlarged.caption }}</p>
          <button v-if="mode !== 'admin'" class="like-btn" :class="{ liked: enlarged.liked }" :disabled="!currentUser" @click="like(enlarged!)">{{ enlarged.liked ? '❤️' : '🤍' }} {{ enlarged.like_count || '' }}</button>
        </div>
      </dialog>
    </div>
  </main>
</template>

<style scoped>
/* ============================================================
   图片墙 · 太阳 —— 「舷窗」版
   深空暖黑强制深色；太阳在视口上方之外，光辉泼进页面。
   ============================================================ */

@keyframes heartbeat {
  0%   { transform: scale(1); }
  25%  { transform: scale(1.28); }
  45%  { transform: scale(.92); }
  65%  { transform: scale(1.12); }
  100% { transform: scale(1); }
}
@keyframes cardIn {
  from { opacity: 0; transform: translateY(18px); }
}
@keyframes headIn {
  from { opacity: 0; transform: translateY(14px); }
}

.gallery-page {
  /* —— 太阳色板（页面级，强制深色）—— */
  --sun-ink: #f4e9d6;
  --sun-muted: rgba(244, 233, 214, .72);
  --sun-faint: rgba(244, 233, 214, .55);
  --sun-gold: #f0a030;
  --sun-gold-soft: #f2b45c;
  --sun-corona: #e8552a;
  --sun-violet: #c084fc;
  --sun-border: rgba(240, 170, 70, .22);
  --sun-border-soft: rgba(240, 170, 70, .12);
  --sun-glass: rgba(26, 17, 9, .55);
  --sun-tint: rgba(240, 160, 48, .09);

  position: relative;
  max-width: 1160px;
  min-height: 75vh;
  margin: auto;
  padding: 24px 24px 64px;
  color: var(--sun-muted);
}
.gallery-page, .gallery-page * { box-sizing: border-box; }

/* —— 画布与舷窗 —— */
.sun-canvas { position: fixed; inset: 0; z-index: 0; display: block; }
.sun-vignette {
  position: fixed; inset: 0; z-index: 2;
  pointer-events: none;
  background: radial-gradient(ellipse 130% 100% at 50% 32%, transparent 52%, rgba(8, 5, 2, .55) 100%);
}
.gallery-content { position: relative; z-index: 1; }

/* —— 可访问性 —— */
.gallery-page :is(a, button, input, textarea, select):focus-visible {
  outline: 2px solid var(--sun-gold);
  outline-offset: 2px;
}
@media (prefers-reduced-motion: reduce) {
  .gallery-page *, .gallery-page *::before, .gallery-page *::after {
    animation-duration: .01ms !important;
    transition-duration: .01ms !important;
  }
}

/* ---------- 导航（座舱控制台条） ---------- */
.gallery-nav, .gallery-nav div, .list-heading, .pagination, .actions {
  display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
}
.gallery-nav {
  justify-content: space-between;
  padding: 12px 18px;
  border: 1px solid var(--sun-border-soft);
  border-radius: 14px;
  background: rgba(19, 13, 7, .5);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  font-size: 14px;
}
a {
  color: var(--sun-gold-soft);
  text-decoration: none;
  transition: color .25s ease-out, text-shadow .25s ease-out;
}
a:hover { text-decoration: underline; text-shadow: 0 0 14px rgba(240, 160, 48, .4); }
.router-link-exact-active {
  font-weight: 700;
  color: #ffd98a;
  text-shadow: 0 0 14px rgba(240, 160, 48, .45);
}

/* ---------- 页头（逆光标题，太阳在文字之上） ---------- */
header {
  padding: 64px 0 40px;
  text-align: center;
  animation: headIn .8s cubic-bezier(.2, .7, .3, 1) both;
}
.eyebrow {
  font-size: 12px;
  letter-spacing: 3px;
  color: var(--sun-violet);
}
h1 {
  font-size: clamp(30px, 5.4vw, 46px);
  line-height: 1.3;
  margin: 16px 0;
  background: linear-gradient(120deg, #fff3dc 20%, #ffd98a 52%, var(--sun-gold) 82%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  -webkit-text-fill-color: transparent;
  text-shadow: none;
  filter: drop-shadow(0 0 26px rgba(240, 160, 48, .28));
}
header > p:last-child, .privacy-note { line-height: 1.9; font-size: 14px; }
header > p:last-child { max-width: 520px; margin: 0 auto; }

/* ---------- 按钮基座 ---------- */
button, .primary, select {
  font: inherit; font-size: 14px;
  border: 1px solid var(--sun-border);
  border-radius: 10px;
  padding: 10px 16px;
  color: var(--sun-ink);
  background: rgba(24, 16, 8, .6);
  cursor: pointer;
  transition: border-color .25s ease-out, box-shadow .25s ease-out,
              background .25s ease-out, color .25s ease-out, transform .25s ease-out;
}
button:hover:not(:disabled) {
  border-color: rgba(240, 170, 70, .45);
  box-shadow: 0 0 18px -6px rgba(240, 160, 48, .45);
}
button:disabled { opacity: .5; cursor: not-allowed; }

/* 主按钮：一小片日光 */
.primary {
  display: inline-block;
  background: linear-gradient(135deg, #f5b045, var(--sun-corona));
  border-color: rgba(255, 200, 120, .5);
  color: #241203;
  font-weight: 700;
  margin-top: 16px;
  text-decoration: none;
}
.primary:hover {
  text-decoration: none;
  box-shadow: 0 0 28px -6px rgba(240, 160, 48, .6);
}

/* ---------- 卡片（暖玻璃） ---------- */
.upload-card, .empty {
  border: 1px solid var(--sun-border-soft);
  border-radius: 20px;
  padding: 28px;
  background: var(--sun-glass);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: inset 0 1px 0 rgba(255, 220, 160, .08);
}
.upload-card { max-width: 740px; margin: 0 auto; }
.upload-card label { display: block; margin-top: 22px; color: var(--sun-ink); font-size: 14px; }
.upload-card h2, .empty h2 { color: var(--sun-ink); }
label span, small { color: var(--sun-faint); font-size: 12px; }
input, textarea {
  width: 100%;
  border: 1px solid var(--sun-border-soft);
  background: rgba(14, 9, 5, .7);
  color: var(--sun-ink);
  border-radius: 10px;
  padding: 12px;
  font: inherit;
  margin-top: 8px;
  transition: border-color .25s ease-out, box-shadow .25s ease-out;
}
input:focus, textarea:focus {
  border-color: var(--sun-border);
  box-shadow: 0 0 0 3px rgba(240, 160, 48, .14);
  outline: none;
}
.gallery-page input:focus-visible, .gallery-page textarea:focus-visible { outline: none; }
textarea { resize: vertical; }

/* ---------- 上传区 ---------- */
.drop-zone {
  border: 1.5px dashed rgba(240, 170, 70, .4);
  border-radius: 16px;
  text-align: center;
  padding: 28px 16px;
  background: linear-gradient(160deg, var(--sun-tint), rgba(232, 85, 42, .04));
  transition: border-color .3s ease-out, box-shadow .3s ease-out, background .3s ease-out;
}
.drop-zone.dragging {
  outline: none;
  border-color: var(--sun-gold);
  background: linear-gradient(160deg, rgba(240, 160, 48, .14), rgba(232, 85, 42, .07));
  box-shadow:
    0 0 0 4px rgba(240, 160, 48, .14),
    0 0 48px -8px rgba(240, 160, 48, .4),
    inset 0 0 32px rgba(240, 160, 48, .08);
}
.drop-zone h2 { color: var(--sun-ink); }
.drop-zone p { font-size: 14px; margin: 10px 0 20px; }
.drop-zone small { display: block; margin-top: 16px; }
.drop-zone button { margin: 4px; }
.upload-symbol {
  display: block;
  color: var(--sun-gold);
  font-size: 48px;
  line-height: 1;
  margin: 8px 0 20px;
  text-shadow: 0 0 24px rgba(240, 160, 48, .55), 0 0 60px rgba(232, 85, 42, .3);
}
.file-input { position: absolute; width: 1px; height: 1px; opacity: 0; padding: 0; }
.upload-preview {
  max-width: 100%; max-height: 380px; object-fit: contain;
  border-radius: 12px; display: block; margin: 0 auto 18px;
  box-shadow: 0 12px 34px -14px rgba(0, 0, 0, .6), 0 0 30px -10px rgba(240, 160, 48, .25);
}
.privacy-note { margin-top: 20px; }

/* ---------- 排序标签（太阳黑子 pill） ---------- */
.sort-tabs {
  display: flex; gap: 2px;
  border: 1px solid var(--sun-border-soft);
  border-radius: 999px;
  overflow: hidden;
  padding: 3px;
  background: var(--sun-glass);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}
.sort-tabs button {
  border: 0; border-radius: 999px;
  padding: 7px 16px; font-size: 13px;
  background: transparent; color: var(--sun-muted);
  box-shadow: none;
}
.sort-tabs button.active {
  background: linear-gradient(135deg, rgba(240, 160, 48, .26), rgba(232, 85, 42, .16));
  color: #ffd98a;
  font-weight: 650;
  box-shadow:
    inset 0 0 12px rgba(240, 160, 48, .3),
    0 0 16px -4px rgba(240, 160, 48, .45);
}
.sort-tabs button:hover:not(.active) { background: var(--sun-tint); box-shadow: none; }

/* ---------- 点赞（心跳） ---------- */
.like-btn {
  border: 0; background: transparent;
  padding: 4px 8px; font-size: 14px;
  cursor: pointer; color: var(--sun-muted); border-radius: 8px;
  transition: background .25s ease-out, color .25s ease-out, transform .25s ease-out;
}
.like-btn:hover:not(:disabled) { background: var(--sun-tint); }
.like-btn.liked {
  color: #ff7a5c;
  animation: heartbeat .45s ease-out;
  text-shadow: 0 0 12px rgba(232, 85, 42, .5);
}
.like-btn.liked:hover:not(:disabled) { background: rgba(232, 85, 42, .1); }
.like-btn:disabled { opacity: .6; cursor: default; }

.photo-meta { display: flex; align-items: center; justify-content: space-between; gap: 8px; }

/* ---------- 图片网格（窗台上的照片，被阳光照亮） ---------- */
.gallery-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 20px; }

.photo-card {
  border: 1px solid var(--sun-border-soft);
  border-radius: 18px;
  overflow: hidden;
  background: var(--sun-glass);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow:
    0 10px 30px -18px rgba(0, 0, 0, .6),
    inset 0 1px 0 rgba(255, 220, 160, .07);
  transition: transform .35s ease-out, border-color .35s ease-out, box-shadow .35s ease-out;
  animation: cardIn .6s cubic-bezier(.2, .7, .3, 1) both;
}
.photo-card:nth-child(2) { animation-delay: .05s; }
.photo-card:nth-child(3) { animation-delay: .1s; }
.photo-card:nth-child(4) { animation-delay: .15s; }
.photo-card:nth-child(5) { animation-delay: .2s; }
.photo-card:nth-child(6) { animation-delay: .25s; }
.photo-card:nth-child(7) { animation-delay: .3s; }
.photo-card:nth-child(8) { animation-delay: .35s; }
.photo-card:nth-child(9) { animation-delay: .4s; }
.photo-card:hover {
  transform: translateY(-4px);
  border-color: rgba(240, 170, 70, .4);
  box-shadow:
    0 18px 44px -20px rgba(0, 0, 0, .65),
    0 0 42px -10px rgba(240, 160, 48, .35),
    inset 0 1px 0 rgba(255, 220, 160, .1);
}
.photo-button {
  display: block; padding: 0; border: 0; border-radius: 0;
  width: 100%; height: 230px; overflow: hidden;
  background: rgba(14, 9, 5, .8);
  box-shadow: none;
  transition: transform .4s ease-out;
}
.photo-button:hover:not(:disabled) { box-shadow: none; border-color: transparent; }
.photo-card:hover .photo-button { transform: scale(1.03); }
.photo-info { padding: 16px; }
.caption {
  color: var(--sun-ink); font-size: 15px; line-height: 1.7;
  margin-bottom: 8px; overflow-wrap: anywhere; white-space: pre-wrap;
}

/* ---------- 审核状态 ---------- */
.status {
  display: inline-block; font-size: 12px;
  padding: 3px 9px; border-radius: 20px;
  background: rgba(240, 160, 48, .14); color: var(--sun-gold-soft);
  margin-bottom: 10px;
}
.status.approved { color: #9fd6ab; background: rgba(120, 200, 140, .12); }
.status.rejected, .rejected { color: #ff8a6a; background: rgba(232, 85, 42, .12); }
.reason, .user-info { font-size: 12px; line-height: 1.7; overflow-wrap: anywhere; margin-top: 12px; }
.actions { margin-top: 14px; gap: 8px; }
.actions button { padding: 7px 12px; }

/* ---------- 空状态 / 列表头 / 分页 ---------- */
.empty { text-align: center; padding: 48px 20px; }
.empty p { margin-top: 12px; font-size: 14px; }
.list-heading { justify-content: space-between; margin-bottom: 20px; font-size: 13px; }
.list-heading h2 { font-size: 20px; margin: 0; color: var(--sun-ink); }
.pagination { justify-content: center; margin-top: 28px; font-size: 14px; }
.pagination span { color: var(--sun-faint); }

/* ---------- 消息条 ---------- */
.message {
  padding: 14px 18px; border-radius: 12px;
  border: 1px solid var(--sun-border-soft);
  background: rgba(26, 17, 9, .6);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  margin-bottom: 20px; font-size: 14px;
}
.error { color: #ff8a6a; }
.success { color: #ffd98a; }

/* ---------- 大图弹窗 ---------- */
.image-dialog {
  width: min(1000px, 94vw); max-height: 92vh;
  border: 1px solid var(--sun-border);
  border-radius: 16px;
  background: #16100a;
  color: var(--sun-ink);
  padding: 16px;
  box-shadow:
    0 0 90px -18px rgba(240, 160, 48, .3),
    0 30px 70px -30px rgba(0, 0, 0, .7);
}
.image-dialog::backdrop {
  background: rgba(8, 5, 2, .74);
  backdrop-filter: blur(4px);
}
.image-dialog :deep(img) { max-width: 100%; max-height: 72vh; object-fit: contain; }
.close-preview { display: block; margin: 0 0 12px auto; }
.image-dialog p { font-size: 14px; padding-top: 12px; overflow-wrap: anywhere; }
.dialog-footer {
  display: flex; align-items: center; justify-content: space-between;
  gap: 12px; padding-top: 12px;
  border-top: 1px solid var(--sun-border-soft);
  margin-top: 12px;
}
.dialog-footer p { font-size: 14px; overflow-wrap: anywhere; margin: 0; }

/* ---------- 响应式（断点不变，移动端不溢出） ---------- */
@media (max-width: 900px) {
  .gallery-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 540px) {
  .gallery-page { padding: 18px 16px 48px; }
  .gallery-grid { grid-template-columns: 1fr; }
  .upload-card { padding: 18px; }
  .gallery-nav { gap: 18px; }
  .gallery-nav div { gap: 16px; }
  .photo-button { height: 270px; }
  header { padding-top: 36px; }
}
</style>
