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
  if (!currentUser.value || !getTeacherToken()) return
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
</script>

<template>
  <main class="gallery-page">
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
  </main>
</template>

<style scoped>
.gallery-page { max-width: 1160px; min-height: 75vh; margin: auto; padding: 24px 24px 64px; color: var(--text); }
.gallery-page, .gallery-page * { box-sizing: border-box; }
.gallery-nav, .gallery-nav div, .list-heading, .pagination, .actions { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.gallery-nav { justify-content: space-between; padding-bottom: 28px; border-bottom: 1px solid var(--border); font-size: 14px; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.router-link-exact-active { font-weight: 700; }
header { padding: 42px 0 32px; }
.eyebrow { font-size: 12px; letter-spacing: 2px; color: var(--accent); }
h1 { font-size: clamp(28px, 5vw, 42px); line-height: 1.3; margin: 16px 0; }
header > p:last-child, .privacy-note { line-height: 1.9; font-size: 14px; }
button, .primary, select { font: inherit; font-size: 14px; border: 1px solid var(--border); border-radius: 10px; padding: 10px 16px; color: var(--text-h); background: var(--bg); cursor: pointer; }
button:hover:not(:disabled) { border-color: var(--accent); }
button:disabled { opacity: .5; cursor: not-allowed; }
.primary { display: inline-block; background: var(--accent-bg); border-color: var(--accent-border); color: var(--accent); font-weight: 650; margin-top: 16px; }
.upload-card, .empty { border: 1px solid var(--border); border-radius: 20px; padding: 28px; background: var(--social-bg); }
.upload-card { max-width: 740px; margin: 0 auto; }
.upload-card label { display: block; margin-top: 22px; color: var(--text-h); font-size: 14px; }
label span, small { color: var(--text); font-size: 12px; }
input, textarea { width: 100%; border: 1px solid var(--border); background: var(--bg); color: var(--text-h); border-radius: 10px; padding: 12px; font: inherit; margin-top: 8px; }
textarea { resize: vertical; }
.drop-zone { border: 1px dashed var(--accent-border); border-radius: 16px; text-align: center; padding: 28px 16px; background: var(--accent-bg); }
.drop-zone.dragging { outline: 2px solid var(--accent); }
.drop-zone p { font-size: 14px; margin: 10px 0 20px; }
.drop-zone small { display: block; margin-top: 16px; }
.drop-zone button { margin: 4px; }
.upload-symbol { display: block; color: var(--accent); font-size: 48px; line-height: 1; margin: 8px 0 20px; }
.file-input { position: absolute; width: 1px; height: 1px; opacity: 0; padding: 0; }
.upload-preview { max-width: 100%; max-height: 380px; object-fit: contain; border-radius: 12px; display: block; margin: 0 auto 18px; }
.privacy-note { margin-top: 20px; }
.sort-tabs { display: flex; gap: 0; border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }
.sort-tabs button { border: 0; border-radius: 0; padding: 7px 16px; font-size: 13px; background: transparent; color: var(--text); }
.sort-tabs button.active { background: var(--accent-bg); color: var(--accent); font-weight: 650; }
.sort-tabs button:hover:not(.active) { background: var(--code-bg); }
.like-btn { border: 0; background: transparent; padding: 4px 8px; font-size: 14px; cursor: pointer; color: var(--text); border-radius: 8px; }
.like-btn:hover:not(:disabled) { background: var(--code-bg); }
.like-btn.liked { color: #e25555; }
.like-btn:disabled { opacity: .6; cursor: default; }
.photo-meta { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.dialog-footer { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding-top: 12px; }
.dialog-footer p { font-size: 14px; overflow-wrap: anywhere; margin: 0; }
.list-heading { justify-content: space-between; margin-bottom: 20px; font-size: 13px; }
.list-heading h2 { font-size: 20px; margin: 0; }
.gallery-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 20px; }
.photo-card { border: 1px solid var(--border); border-radius: 16px; overflow: hidden; background: var(--social-bg); }
.photo-button { display: block; padding: 0; border: 0; border-radius: 0; width: 100%; height: 230px; overflow: hidden; background: var(--code-bg); }
.photo-info { padding: 16px; }
.caption { color: var(--text-h); font-size: 15px; line-height: 1.7; margin-bottom: 8px; overflow-wrap: anywhere; white-space: pre-wrap; }
.status { display: inline-block; font-size: 12px; padding: 3px 9px; border-radius: 20px; background: var(--accent-bg); color: var(--accent); margin-bottom: 10px; }
.rejected { color: #b95143; background: #b9514312; }
.reason, .user-info { font-size: 12px; line-height: 1.7; overflow-wrap: anywhere; margin-top: 12px; }
.actions { margin-top: 14px; gap: 8px; }
.actions button { padding: 7px 12px; }
.empty { text-align: center; padding: 48px 20px; }
.empty p { margin-top: 12px; font-size: 14px; }
.pagination { justify-content: center; margin-top: 28px; font-size: 14px; }
.message { padding: 14px 18px; border-radius: 12px; border: 1px solid var(--border); margin-bottom: 20px; font-size: 14px; }
.error { color: #b95143; } .success { color: var(--accent); }
.image-dialog { width: min(1000px, 94vw); max-height: 92vh; border: 1px solid var(--border); border-radius: 16px; background: var(--bg); color: var(--text-h); padding: 16px; }
.image-dialog::backdrop { background: #000b; }
.image-dialog :deep(img) { max-height: 72vh; object-fit: contain; }
.close-preview { display: block; margin: 0 0 12px auto; }
.image-dialog p { font-size: 14px; padding-top: 12px; overflow-wrap: anywhere; }
@media (max-width: 900px) { .gallery-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 540px) { .gallery-page { padding: 18px 16px 48px; } .gallery-grid { grid-template-columns: 1fr; } .upload-card { padding: 18px; } .gallery-nav { gap: 18px; } .gallery-nav div { gap: 16px; } .photo-button { height: 270px; } header { padding-top: 28px; } }
</style>
