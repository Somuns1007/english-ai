# Kimi 自由发挥版 — 图片墙「太阳」重设计 Prompt

把下面分隔线以下的全部内容粘贴给 Kimi。

---

你是世界顶级的前端视觉设计师。这次不给你条条框框——我要你自由发挥你的高级审美，做一个让人打开就"哇"出来的页面。

## 世界观：一个以天体为章节的宇宙

这是一个大学生英语学习网站「阿Q的英语自习室」。整站是**星辰宇宙主题**，每个板块对应一个天体：

- **首页 = 黑洞**（已完成）：全屏 canvas 深空星野，背景色从 `#080B1C` → `#0C0F24` → `#05061A`，220 颗按色温分布的星星闪烁，4 团紫蓝色星云漂浮，中央一个黑洞——1200 个粒子组成的吸积盘轨道旋转，橙金色热辐射，引力透镜光弧，光子环。大气、深邃、宇宙尺度的壮美。
- **图片墙 = 太阳** ☀️ ← **这次你来设计**

图片墙是学生分享生活照片的地方（猫猫狗狗、校园风景、生活里的小美好）。太阳是这个宇宙里最温暖的地方——学生学习累了，来这里晒晒太阳，看点可爱的。**情绪基调：温暖、治愈、光辉、生命力。但视觉必须是宇宙尺度的壮美，不要可爱卡通风。**

## 上次失败的教训（务必避开）

上一版设计是"白底 + 一点金橙渐变"，用户原话："这什么几把玩意"、"你不能只是白底上加点颜色吧"。

**硬规则：**

1. **必须是深色页面。** 底色用深空暖黑（如 `#130f08` / `#0e0a06` 一类），绝对不要白色或浅色背景。这是宇宙中的太阳，不是白纸上的太阳。
2. **背景必须铺满整个视口**，不能只覆盖内容列（内容列 max-width 1160px，两侧不能露白）。可以用 `position: fixed; inset: 0; z-index: -1` 的伪元素或独立 div 铺底。
3. **太阳必须"在场"。** 打开页面要能感觉到自己在飞向太阳——不管你用大面积日冕径向渐变、canvas 画一个呼吸的太阳、CSS 动画的日珥光弧、还是页面顶部一轮悬浮的恒星，由你决定。但不能只是"色调偏暖"，要有一个视觉主角。
4. 图片是页面的内容主角，太阳氛围是舞台——光效不能压过照片本身，网格区域保持克制，让照片好看。

## 你的自由度（这次全放开）

- **`<template>` 可以随便重构**：加装饰性 DOM 层、canvas 元素、SVG、重新组织结构、加 aria 属性，都行
- **可以写 canvas 动画**：如果你想画一个有呼吸感的太阳/日冕粒子/太阳风，把 canvas 初始化代码写在一个独立的 `<script>` 内联函数或组合式函数里给我（见下方约束第 2 条的交接方式）
- 字体排印、微交互、hover 光效、入场动画、滚动视差——发挥你的审美
- 性能意识：动画用 `requestAnimationFrame` + 离屏降帧，`prefers-reduced-motion` 时全部静止

## 不可触碰的约束

1. **`<script setup>` 的现有业务逻辑一行都不能改**（下面附完整代码）。你可以**新增**代码（如 canvas 初始化的 ref 和 onMounted 逻辑），但不能改动或删除现有的任何函数、ref、watch。
2. 输出**完整的单文件组件**（template + 你新增的 script 片段说明 + style scoped），我来合并。新增 script 代码请单独标注"【新增】"。
3. Template 里所有的数据绑定、事件、v-if/v-for 逻辑必须全部保留（可以移动位置、换包裹结构，但功能一个都不能丢）。四个路由共用这一个组件：`/gallery`（公开墙）、`/gallery/upload`（上传）、`/gallery/mine`（我的图片）、`/admin/gallery`(审核后台)，四种形态都要设计到位。
4. `<GalleryPhoto>` 是现成的图片组件，用法保持 `:url` `:admin` `:alt` 三个 prop 不变。
5. `<dialog>` 大图弹窗的 `ref="modal"`、`@close`、`@click` 关闭逻辑保持。
6. 样式必须 `<style scoped>`。页面级颜色直接在 `.gallery-page` 上定义变量即可，**这个页面强制深色，不需要适配亮色模式**（不要写 `prefers-color-scheme: light` 分支）。
7. 可访问性：对比度达标（正文文字在深底上至少 4.5:1）、focus-visible 可见、`prefers-reduced-motion` 尊重。
8. 响应式：900px 断点网格 3→2 列，540px 断点 2→1 列，移动端不能溢出。
9. 中文文案全部保留原样。

## 现有完整代码

### `<script setup>`（不可改，只可新增）

```ts
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
// …（verifyAdmin / unlock / load / submit / review / like / openImage / date 等函数
//    以及 watch/onMounted/onBeforeUnmount，业务逻辑齐全，此处省略——你不需要动它们）
```

### `<template>`（可自由重构，绑定必须全保留）

```html
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
```

## 可参考的全站变量（可用可不用，页面强制深色所以你也可以自建色板）

```css
--accent: #c084fc;  /* 全站紫（深色模式值）——太阳页可以用它做色球层点缀，保持宇宙同源 */
--sans: system-ui, 'Segoe UI', Roboto, sans-serif;
```

## 交付格式

1. 完整 `<template>`（重构后的）
2. 【新增】script 代码块（如有 canvas/动效逻辑），说明插在哪里
3. 完整 `<style scoped>`

三块分开给我，我直接合并进 GalleryView.vue。

放手去做。我要的是：打开页面的瞬间，感觉自己站在一艘飞船的舷窗前，正朝着太阳飞去——而窗台上贴满了同学们分享的生活照片，被阳光照得发亮。
