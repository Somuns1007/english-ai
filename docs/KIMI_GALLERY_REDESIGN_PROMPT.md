# Gallery 页面「太阳」主题视觉设计 — Kimi Prompt

把下面分隔线以下的全部内容粘贴给 Kimi：

---

## 世界观

这是一个大学生英语学习网站「阿Q的英语自习室」。整站采用**星辰宇宙主题**——首页是深空星野，中央有一个黑洞吸积盘（canvas 动画，粒子轨道旋转，橙金色热辐射光），紫蓝色星云漂浮，220 颗星星闪烁。整体视觉语言是：深空蓝黑 + 紫色主色调 + 粒子光效。

**每个板块对应一个天体：**

| 板块 | 天体 | 视觉方向 |
|---|---|---|
| 首页 | 黑洞 | 已完成：深空星野 + 吸积盘 + 星云 |
| 听力训练 | （待定） | 暂不改动 |
| 作文批改 | （待定） | 暂不改动 |
| **图片墙** | **太阳** ☀️ | **本次设计目标** |

## 本次任务

为「图片墙」页面设计**太阳主题**的视觉风格。输出一个完整的 Vue `<style scoped>` 代码块，直接替换现有样式。

### 太阳主题的视觉方向

想象从深空飞近太阳——

- **背景**：不要纯白或纯黑。用深暖色渐变底色（如 `#1a1005` → `#2a1a0a` → 透明），仿佛宇宙空间中被太阳照亮的区域。或者用径向渐变模拟太阳在页面上方发出的光辉
- **光晕效果**：页面顶部或 header 区域可以有一个大型的径向渐变光晕（金橙色 + 低透明度），像太阳的日冕（corona）
- **卡片**：玻璃拟态 + 暖色调边框微光。背景用半透明深色 + `backdrop-filter: blur()`，边框带金橙色微光（类似太阳光照射到玻璃上）。hover 时边框亮度增加，像被阳光照到
- **图片缩略图**：圆角更大（16-20px），hover 时微缩放（scale 1.03）+ 阴影扩散（像光在扩散）
- **排序标签（最新/最热）**：做成像太阳黑子的 pill 形态，active 态有内发光
- **点赞按钮 ❤️**：点击时有心跳脉冲动画（scale 弹跳）。liked 状态用暖红/橙红色，和太阳主题呼应
- **上传区**：虚线边框用金橙色渐变虚线，拖拽 hover 时整个区域有温暖的发光效果
- **整体色温**：在现有紫色主色调基础上，图片墙页面额外引入太阳的金橙色作为辅助色。但不要完全抛弃紫色——太阳的色球层也有紫色
- **文字**：保持可读性。标题可以有微妙的金色渐变，但正文保持 CSS 变量的默认色

### 关键氛围词

温暖、光辉、日冕、色球、太阳风、金橙、琥珀、余晖。不要可爱/卡通风格——要大气、宇宙尺度的壮美感。

## 全站 CSS 变量（必须使用，不要硬编码）

```css
/* 亮色模式 */
--text: #6b6375;
--text-h: #08060d;
--bg: #fff;
--border: #e5e4e7;
--code-bg: #f4f3ec;
--accent: #aa3bff;        /* 紫色主色 */
--accent-bg: rgba(170, 59, 255, 0.1);
--accent-border: rgba(170, 59, 255, 0.5);
--social-bg: rgba(244, 243, 236, 0.5);
--shadow: rgba(0,0,0,0.1) 0 10px 15px -3px, rgba(0,0,0,0.05) 0 4px 6px -2px;

/* 暗色模式（prefers-color-scheme: dark 自动切换）*/
--text: #9aa4bd;
--text-h: #eef1f8;
--bg: #131524;
--border: #2b2e40;
--code-bg: #1c1e2c;
--accent: #c084fc;
--accent-bg: rgba(192, 132, 252, 0.15);
--accent-border: rgba(192, 132, 252, 0.5);
--social-bg: rgba(44, 47, 66, 0.5);
```

**太阳主题可以在 scoped 样式里定义页面级 CSS 变量**（如 `--sun-glow`、`--sun-warm`、`--sun-corona`），覆盖在 `.gallery-page` 上，这样不影响全站。建议的太阳色板：

```
金橙: #f0a030 / rgba(240, 160, 48, ...)
琥珀: #d4820a
日冕红: #e8552a
深空暖底: #1a1005（暗色）/ #fdf6ee（亮色）
```

## 页面结构（不可改动 template）

4 个路由共用一个 GalleryView.vue：
- `/gallery` — 公开图片墙（最新/最热排序 + 图片网格 + 点赞 + 分页）
- `/gallery/upload` — 上传（拖拽区 + 预览 + 说明输入框）
- `/gallery/mine` — 我的图片（审核状态标签）
- `/admin/gallery` — 管理员审核

**页面元素**：
1. `.gallery-nav` — 顶部导航
2. `header` — 含 `.eyebrow`（小字）、`h1`（大标题）、`p`（副标题）
3. `.sort-tabs` — 最新/最热切换
4. `.gallery-grid` > `.photo-card` — 图片网格（3→2→1列响应式）
5. `.photo-card` 内部：`.photo-button`（缩略图）→ `.photo-info`（说明、点赞、日期）
6. `.like-btn` + `.like-btn.liked` — 点赞
7. `.upload-card` > `.drop-zone` — 上传区
8. `.image-dialog` — 大图弹窗
9. `.pagination` — 分页

## 约束

1. **只输出 `<style scoped>` 部分**的完整代码，我直接替换
2. **不改 `<template>` 和 `<script>`**，所有 CSS 类名保持不变
3. 必须使用全站 CSS 变量 `var(--accent)` 等，可以在 `.gallery-page` 上定义太阳专属变量
4. **同时支持亮色和暗色模式**（暗色是主要模式，因为太空背景）
5. transition 动画 200-400ms，加 ease-out
6. 保持可访问性：对比度足够、focus 可见
7. 保持响应式断点：900px（2列）、540px（1列）
8. 点赞心跳动画用 `@keyframes`

## 所有 CSS 类名（必须全部覆盖）

`.gallery-page` `.gallery-nav` `.gallery-grid` `.photo-card` `.photo-button` `.photo-info` `.caption` `.like-btn` `.like-btn.liked` `.sort-tabs` `.sort-tabs button` `.sort-tabs button.active` `.upload-card` `.drop-zone` `.drop-zone.dragging` `.upload-preview` `.upload-symbol` `.photo-meta` `.dialog-footer` `.pagination` `.message` `.error` `.success` `.image-dialog` `.image-dialog::backdrop` `.close-preview` `.empty` `.status` `.rejected` `.reason` `.user-info` `.actions` `.list-heading` `.file-input` `.primary` `.eyebrow` `.privacy-note` `.router-link-exact-active`

## 现有完整样式（供参考现有布局逻辑，你要完全重写视觉层）

```css
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
```

请输出完整的 `<style scoped>` 代码块，我直接替换到 GalleryView.vue。
