# 任务：为 `/listening/corpus` 做一个「冥王星」主题的"敬请期待"整页

你是世界第一的前端设计师兼工程师。这是一个 Vue 3 + TypeScript + Vite 的英语学习网站（"阿Q的英语自习室"），全站有一套**天体世界观**：

- 首页 = **黑洞**（canvas 动画，深空黑）
- 图片墙 = **太阳**（canvas 动画：呼吸的恒星、日冕、尘埃粒子、太阳风、日珥，暖黑底 `#0a0704`）
- 这次要做的「真实语料库」页面 = **冥王星**

"真实语料库"这个功能暂时不开放。请把这一页做成一张**全屏沉浸式的"这个功能等以后再来探索吧"**页面，而不是一个空列表。

## 一、必须做到的事（硬约束）

1. **新建文件** `frontend/src/views/listening/CorpusComingSoonView.vue`，作为完整的 SFC（`<script setup lang="ts">` + template + `<style scoped>`）。
2. 根元素必须带 class **`corpus-coming-soon`**（全局 `style.css` 会用 `#app:has(.corpus-coming-soon)` 去掉容器宽度限制、边线，并把顶部导航调透明——这部分我们自己加，你不用管，但 class 名必须一致）。
3. 页面正中偏下要放**这张图片**：`frontend/src/assets/nailong-reading.jpg`（920×962，一只戴黑框眼镜的黄色卡通生物"奶龙"，坐在桌前认真读一本书《如何变成一只可爱的奶龙》，背景是蓝色塑料椅）。用 `import nailong from '../../assets/nailong-reading.jpg'` 引入。这张图是页面的**情感核心**——它在读书、在学习、在准备——请让整个构图围绕它。它需要一个有设计感的容器（例如：圆形舷窗、带柔和外发光的卡片、被冥王星微弱的光照亮的样子——由你决定），不要生硬地贴一张方图。
4. 主文案（中文）必须包含这一句，可以由你排版和拆行：
   **「这个功能等以后再来探索吧」**
   副文案由你写，语气：温柔、有一点幽默、不说抱歉、不写"建设中"这类工程词。可以顺着"冥王星离太阳很远、光要走五个多小时才能到"的意象写。可选加一小行英文 eyebrow（例如 `PLUTO · 39.5 AU`）。
5. 保留两个可点击的返回入口：
   - `← 返回听力首页` → `$router.push('/listening')`
   - `表达迁移训练 →` → `$router.push('/listening/expressions')`
   样式由你决定，但要在深色背景上清晰可见、可点击（z-index 在 canvas 之上）。
6. **强制深色**。背景必须是冥王星式的深空——冷调、极远、极暗。不要写浅色模式分支，忽略 `prefers-color-scheme`。
7. 页面不请求任何 API，不 import 任何 service。纯静态 + 动画。
8. 所有动画用 `requestAnimationFrame`，在 `onBeforeUnmount` 里 `cancelAnimationFrame` 并移除 resize 监听（参考下面太阳页的收尾方式）。`<canvas>` 用 `position: fixed; inset: 0; z-index: 0`，内容层 `position: relative; z-index: 1`。
9. 尊重 `prefers-reduced-motion: reduce`：命中时把粒子/呼吸动画降到静态或极慢。
10. 必须通过 `vue-tsc --noEmit --project tsconfig.app.json`（不留未使用变量/导入）。
11. 移动端可用（≤ 640px 时图片缩小、文案换行、按钮不重叠）。

## 二、自由发挥的部分（这才是重点）

冥王星是**矮行星、被"降级"过、离家最远、最冷、最安静、但依旧有心**——它表面真的有一个巨大的心形亮区（Tombaugh Regio / "冥王星之心"）。这是这一页的灵魂：**功能还没到，但心已经在那里了**。

请用 canvas（或 canvas + CSS 结合）表达它。以下只是提示，不是要求，你完全可以推翻：

- 一颗冷色的冥王星（灰蓝、灰褐、略带一点淡粉——真实照片就是这样），表面有一块隐约的心形亮区，微微发光、缓慢呼吸。
- 远处一个**极小极亮**的太阳——只是一个针尖大小的点，暗示距离。
- 卡戎（Charon）可以作为第二个更暗的小球缓慢绕行，或者不要。
- 极稀疏、极慢的星尘。冥王星的宇宙应该比太阳页**安静一个量级**——太阳页是热闹的，这里是**寂静**的。
- 可以有一层极淡的蓝紫色的大气雾（New Horizons 拍到的冥王星蓝色薄雾）。
- 字体排版本身就是设计：大字号、宽字距、克制的层级。
- 奶龙图片与冥王星之间要有关系（在它身边、被它照亮、或者它坐在冥王星上），而不是两个不相关的元素叠在一起。

**审美方向**：安静、辽远、温柔、一点点可爱、完全不廉价。想象一个人在深夜点开这个页面，看到远方的星和一只认真读书的奶龙，会心一笑然后退回去。

## 三、参考：太阳页的收尾写法（保证一致）

```ts
const sunCanvas = ref<HTMLCanvasElement | null>(null)
let sunRaf: number | null = null
let sunResize: (() => void) | null = null
function initSun() { /* ... */ }
onMounted(initSun)
onBeforeUnmount(() => {
  if (sunRaf !== null) cancelAnimationFrame(sunRaf)
  if (sunResize) removeEventListener('resize', sunResize)
})
```

## 四、交付

只交付一个文件：`CorpusComingSoonView.vue` 的**完整内容**，可直接落盘。路由改动、全局 `style.css` 的 `:has()` 覆盖、旧的 `CorpusClipsView.vue` 保留——这些由我们这边处理，你不用碰。
