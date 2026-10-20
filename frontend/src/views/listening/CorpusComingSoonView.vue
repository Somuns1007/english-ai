<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import nailong from '../../assets/nailong-reading.jpg'

const router = useRouter()

const plutoCanvas = ref<HTMLCanvasElement | null>(null)
let plutoRaf: number | null = null
let plutoResize: (() => void) | null = null

function initPluto() {
  const canvas = plutoCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  /* 减少动态偏好：只画一帧静止的冥王星 */
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches

  let W = 0, H = 0, DPR = 1
  const resize = () => {
    DPR = Math.min(window.devicePixelRatio || 1, 1.75)
    W = canvas.width = Math.floor(innerWidth * DPR)
    H = canvas.height = Math.floor(innerHeight * DPR)
    canvas.style.width = innerWidth + 'px'
    canvas.style.height = innerHeight + 'px'
  }
  resize()
  plutoResize = resize
  addEventListener('resize', resize)

  /* 星：极稀疏、极慢——冥王星的天空要比太阳页安静一个量级 */
  const STAR_COLORS = ['226,236,248', '226,236,248', '168,196,240', '238,214,226']
  const stars = Array.from({ length: 110 }, () => ({
    x: Math.random(),
    y: Math.random(),
    r: Math.random() * 1 + .3,
    p: Math.random() * Math.PI * 2,
    s: .08 + Math.random() * .3,
    c: STAR_COLORS[Math.floor(Math.random() * STAR_COLORS.length)]
  }))

  /* 慢速浮尘：若有似无 */
  const motes = Array.from({ length: 14 }, () => ({
    x: Math.random(),
    y: Math.random(),
    v: .00004 + Math.random() * .00008,
    r: .8 + Math.random() * 1.6,
    p: Math.random() * Math.PI * 2
  }))

  /* 冥王星表面斑纹：New Horizons 增强色——
     托林红棕、氮冰蓝、暗黑克苏鲁区、亮白冰原 */
  const maria = [
    { dx: -.38, dy: -.18, r: .34, c: '148,62,48',   a: .55 },
    { dx: .30,  dy: -.34, r: .26, c: '96,138,185',  a: .45 },
    { dx: -.10, dy: .42,  r: .30, c: '120,52,40',   a: .50 },
    { dx: .42,  dy: .30,  r: .20, c: '58,44,52',    a: .45 },
    { dx: -.45, dy: .18,  r: .18, c: '205,225,240', a: .35 },
    { dx: .05,  dy: -.48, r: .16, c: '170,190,215', a: .30 }
  ]

  /* 冷调星云：若有似无的两团 */
  const nebulae = [
    { x: .18, y: .68, r: .38, c: '60,80,160',  a: .07, ph: 1.3 },
    { x: .84, y: .60, r: .32, c: '90,60,140',  a: .06, ph: 4.1 }
  ]

  /* 冥王星悬在页面上方：奶龙的舷窗正好被它的冷光照到 */
  const pluto = () => {
    const s = Math.min(Math.max(Math.min(innerWidth, innerHeight) / 1000, .55), 1.15)
    return { x: W * .5, y: H * .18, R: 88 * s * DPR }
  }

  const drawHeart = (hx: number, hy: number, s: number) => {
    ctx.beginPath()
    ctx.moveTo(hx, hy + s * .95)
    ctx.bezierCurveTo(hx - s * 1.15, hy + s * .12, hx - s * .82, hy - s * .82, hx, hy - s * .26)
    ctx.bezierCurveTo(hx + s * .82, hy - s * .82, hx + s * 1.15, hy + s * .12, hx, hy + s * .95)
    ctx.closePath()
  }

  const frame = (now: number) => {
    const t = now / 1000
    const { x: px, y: py, R } = pluto()
    const breath = .5 + .5 * Math.sin(t * .4)

    ctx.clearRect(0, 0, W, H)

    /* 深空底：冷调、极远、极暗 */
    const bg = ctx.createLinearGradient(0, 0, 0, H)
    bg.addColorStop(0, '#05070d')
    bg.addColorStop(.55, '#04060c')
    bg.addColorStop(1, '#020308')
    ctx.fillStyle = bg
    ctx.fillRect(0, 0, W, H)

    /* 远方的太阳：针尖大小，但极亮——光要走五个半小时 */
    const sunX = W * .14, sunY = H * .18
    const sunGlow = ctx.createRadialGradient(sunX, sunY, 0, sunX, sunY, 52 * DPR)
    sunGlow.addColorStop(0, 'rgba(255,250,235,.65)')
    sunGlow.addColorStop(.4, 'rgba(255,245,220,.18)')
    sunGlow.addColorStop(1, 'rgba(255,250,235,0)')
    ctx.fillStyle = sunGlow
    ctx.beginPath()
    ctx.arc(sunX, sunY, 52 * DPR, 0, Math.PI * 2)
    ctx.fill()
    ctx.beginPath()
    ctx.arc(sunX, sunY, 1.8 * DPR, 0, Math.PI * 2)
    ctx.fillStyle = 'rgba(255,253,245,1)'
    ctx.fill()
    const spike = 14 * DPR
    ctx.beginPath()
    ctx.moveTo(sunX - spike, sunY)
    ctx.lineTo(sunX + spike, sunY)
    ctx.moveTo(sunX, sunY - spike)
    ctx.lineTo(sunX, sunY + spike)
    ctx.strokeStyle = 'rgba(255,250,235,.5)'
    ctx.lineWidth = .8 * DPR
    ctx.stroke()

    /* 冷调星云 */
    ctx.save()
    ctx.globalCompositeOperation = 'lighter'
    for (const nb of nebulae) {
      const nx = (nb.x + Math.sin(t * .06 + nb.ph) * .015) * W
      const ny = (nb.y + Math.cos(t * .05 + nb.ph) * .012) * H
      const nr = nb.r * Math.min(W, H)
      const ng = ctx.createRadialGradient(nx, ny, 0, nx, ny, nr)
      ng.addColorStop(0, `rgba(${nb.c},${nb.a})`)
      ng.addColorStop(1, `rgba(${nb.c},0)`)
      ctx.fillStyle = ng
      ctx.beginPath()
      ctx.arc(nx, ny, nr, 0, Math.PI * 2)
      ctx.fill()
    }
    ctx.restore()

    /* 星：每 8 颗里挑一颗亮星，给它光晕和星芒 */
    for (let si = 0; si < stars.length; si++) {
      const st = stars[si]
      const tw = .25 + .75 * Math.abs(Math.sin(t * st.s + st.p))
      const sx2 = st.x * W, sy2 = st.y * H
      if (si % 8 === 0) {
        const halo = ctx.createRadialGradient(sx2, sy2, 0, sx2, sy2, st.r * 7 * DPR)
        halo.addColorStop(0, `rgba(${st.c},${tw * .3})`)
        halo.addColorStop(1, `rgba(${st.c},0)`)
        ctx.fillStyle = halo
        ctx.beginPath()
        ctx.arc(sx2, sy2, st.r * 7 * DPR, 0, Math.PI * 2)
        ctx.fill()
        const sp2 = st.r * 5 * DPR
        ctx.beginPath()
        ctx.moveTo(sx2 - sp2, sy2)
        ctx.lineTo(sx2 + sp2, sy2)
        ctx.moveTo(sx2, sy2 - sp2)
        ctx.lineTo(sx2, sy2 + sp2)
        ctx.strokeStyle = `rgba(${st.c},${tw * .35})`
        ctx.lineWidth = .6 * DPR
        ctx.stroke()
      }
      ctx.beginPath()
      ctx.arc(sx2, sy2, st.r * DPR, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(${st.c},${tw * .6})`
      ctx.fill()
    }

    /* 浮尘 */
    for (const m of motes) {
      m.y -= m.v
      if (m.y < -.02) { m.y = 1.02; m.x = Math.random() }
      ctx.beginPath()
      ctx.arc(m.x * W, m.y * H, m.r * DPR, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(190,205,235,${.05 + .05 * Math.sin(t * .3 + m.p)})`
      ctx.fill()
    }

    /* 冥王星的冷光洒向下方，正好落在奶龙的舷窗上 */
    const wash = ctx.createRadialGradient(px, py, R, px, py, R * 6.5)
    wash.addColorStop(0, 'rgba(150,175,225,.07)')
    wash.addColorStop(.5, 'rgba(140,165,215,.03)')
    wash.addColorStop(1, 'rgba(140,165,215,0)')
    ctx.fillStyle = wash
    ctx.fillRect(0, 0, W, H)

    /* 卡戎：第二个更暗的小球，约 80 秒绕行一周 */
    const ca = t * (Math.PI * 2 / 80) + 1.2
    const chX = px + Math.cos(ca) * R * 2.3
    const chY = py + Math.sin(ca) * R * 1.05
    const chR = R * .18
    const charonBehind = Math.sin(ca) < 0

    const drawCharon = () => {
      const g = ctx.createRadialGradient(chX - chR * .3, chY - chR * .3, chR * .1, chX, chY, chR)
      g.addColorStop(0, '#8a8fa2')
      g.addColorStop(.6, '#565b70')
      g.addColorStop(1, '#232636')
      ctx.beginPath()
      ctx.arc(chX, chY, chR, 0, Math.PI * 2)
      ctx.fillStyle = g
      ctx.fill()
    }

    if (charonBehind) drawCharon()

    /* 蓝色薄雾大气（New Horizons 看到的那层）——加强到看得见的辉光 */
    ctx.save()
    ctx.globalCompositeOperation = 'lighter'
    const haze = ctx.createRadialGradient(px, py, R * .92, px, py, R * 1.65)
    haze.addColorStop(0, 'rgba(140,175,255,.28)')
    haze.addColorStop(.45, 'rgba(130,165,245,.10)')
    haze.addColorStop(1, 'rgba(140,170,255,0)')
    ctx.fillStyle = haze
    ctx.beginPath()
    ctx.arc(px, py, R * 1.65, 0, Math.PI * 2)
    ctx.fill()
    ctx.restore()

    /* 冥王星本体，光来自左上方的远日：奶油高光 → 托林红棕 → 夜面 */
    ctx.save()
    ctx.beginPath()
    ctx.arc(px, py, R, 0, Math.PI * 2)
    ctx.clip()

    const body = ctx.createRadialGradient(px - R * .45, py - R * .45, R * .1, px, py, R * 1.15)
    body.addColorStop(0, '#efe4d2')
    body.addColorStop(.3, '#cfa88e')
    body.addColorStop(.55, '#9a6a58')
    body.addColorStop(.78, '#4c3648')
    body.addColorStop(1, '#1c1626')
    ctx.fillStyle = body
    ctx.fillRect(px - R, py - R, R * 2, R * 2)

    for (const m of maria) {
      const g = ctx.createRadialGradient(px + m.dx * R, py + m.dy * R, 0, px + m.dx * R, py + m.dy * R, m.r * R)
      g.addColorStop(0, `rgba(${m.c},${m.a})`)
      g.addColorStop(1, `rgba(${m.c},0)`)
      ctx.fillStyle = g
      ctx.beginPath()
      ctx.arc(px + m.dx * R, py + m.dy * R, m.r * R, 0, Math.PI * 2)
      ctx.fill()
    }

    /* 冥王星之心（斯普特尼克冰原）：功能还没到，心已经在那里了 */
    const hx = px + R * .16, hy = py + R * .14, hs = R * .46
    ctx.save()
    ctx.translate(hx, hy)
    ctx.rotate(-.2)
    ctx.translate(-hx, -hy)
    drawHeart(hx, hy, hs)
    const hg = ctx.createRadialGradient(hx, hy, 0, hx, hy, hs * 1.3)
    hg.addColorStop(0, `rgba(252,244,232,${.72 + breath * .22})`)
    hg.addColorStop(.6, `rgba(245,228,214,${.38 + breath * .12})`)
    hg.addColorStop(1, 'rgba(246,230,222,0)')
    ctx.fillStyle = hg
    ctx.shadowColor = `rgba(255,244,228,${.55 + breath * .35})`
    ctx.shadowBlur = 26 * DPR
    ctx.fill()
    ctx.restore()

    /* 背光面压暗 */
    const shade = ctx.createLinearGradient(px - R, py - R, px + R, py + R)
    shade.addColorStop(.55, 'rgba(4,6,12,0)')
    shade.addColorStop(1, 'rgba(4,6,12,.55)')
    ctx.fillStyle = shade
    ctx.fillRect(px - R, py - R, R * 2, R * 2)

    ctx.restore()

    /* 受光侧临边：带辉光的晨昏线 */
    ctx.save()
    ctx.shadowColor = 'rgba(160,190,255,.9)'
    ctx.shadowBlur = 16 * DPR
    ctx.beginPath()
    ctx.arc(px, py, R * 1.005, Math.PI * .9, Math.PI * 1.7)
    ctx.strokeStyle = 'rgba(200,220,255,.6)'
    ctx.lineWidth = 1.4 * DPR
    ctx.stroke()
    ctx.restore()

    if (!charonBehind) drawCharon()
  }

  if (reduced) {
    frame(0)
  } else {
    const loop = (now: number) => { frame(now); plutoRaf = requestAnimationFrame(loop) }
    plutoRaf = requestAnimationFrame(loop)
  }
}

onMounted(initPluto)
onBeforeUnmount(() => {
  if (plutoRaf !== null) cancelAnimationFrame(plutoRaf)
  if (plutoResize) removeEventListener('resize', plutoResize)
})
</script>

<template>
  <main class="corpus-coming-soon">
    <canvas ref="plutoCanvas" class="pluto-canvas" aria-hidden="true"></canvas>

    <div class="stage">
      <p class="eyebrow">PLUTO · 39.5 AU</p>

      <h1>这个功能<br />等以后再来探索吧</h1>

      <p class="sub">
        冥王星离太阳很远，连光都要走五个半小时。<br />
        奶龙已经先一步到了，正坐在舷窗边预习——<br />
        等它读完这本书，这里就开放。
      </p>

      <figure class="porthole">
        <img :src="nailong" alt="戴着黑框眼镜的奶龙坐在桌前，认真读一本《如何变成一只可爱的奶龙》" />
      </figure>
      <p class="caption">《如何变成一只可爱的奶龙》· 阅读中</p>

      <nav class="links" aria-label="返回导航">
        <button type="button" class="link-btn" @click="router.push('/listening')">← 返回听力首页</button>
        <button type="button" class="link-btn" @click="router.push('/listening/expressions')">表达迁移训练 →</button>
      </nav>
    </div>
  </main>
</template>

<style scoped>
@keyframes rise {
  from { opacity: 0; transform: translateY(16px); }
}
@keyframes plutoLight {
  0%, 100% {
    box-shadow:
      0 0 0 6px rgba(120, 150, 210, .05),
      0 0 60px -8px rgba(140, 170, 255, .22),
      0 24px 60px -20px rgba(0, 0, 0, .8),
      inset 0 18px 30px -18px rgba(210, 228, 255, .30);
  }
  50% {
    box-shadow:
      0 0 0 6px rgba(120, 150, 210, .07),
      0 0 74px -8px rgba(140, 170, 255, .34),
      0 24px 60px -20px rgba(0, 0, 0, .8),
      inset 0 18px 30px -18px rgba(210, 228, 255, .42);
  }
}

.corpus-coming-soon {
  --pl-ink: #e9eef8;
  --pl-muted: rgba(210, 222, 244, .68);
  --pl-faint: rgba(200, 214, 240, .52);
  --pl-cold: #a9c3ee;
  --pl-border: rgba(160, 190, 240, .16);

  position: relative;
  min-height: 100vh;
  background: #04060c;
  color: var(--pl-ink);
  color-scheme: dark;
  overflow-x: hidden;
}
.corpus-coming-soon, .corpus-coming-soon * { box-sizing: border-box; }

.pluto-canvas {
  position: fixed;
  inset: 0;
  z-index: 0;
  display: block;
}

.stage {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 30vh 24px 48px;
}

.eyebrow {
  font-size: 12px;
  letter-spacing: 5px;
  color: var(--pl-faint);
  animation: rise 1s cubic-bezier(.2, .7, .3, 1) both;
}

h1 {
  font-size: clamp(30px, 5.6vw, 52px);
  font-weight: 600;
  letter-spacing: 8px;
  line-height: 1.6;
  margin: 18px 0 0;
  color: var(--pl-ink);
  text-shadow: 0 0 40px rgba(140, 170, 255, .25);
  animation: rise 1s .15s cubic-bezier(.2, .7, .3, 1) both;
}

.sub {
  margin: 20px 0 0;
  font-size: 15px;
  line-height: 2.1;
  letter-spacing: 1.5px;
  color: var(--pl-muted);
  animation: rise 1s .3s cubic-bezier(.2, .7, .3, 1) both;
}

/* 舷窗：奶龙坐在自己的小星球里，被冥王星的光照亮 */
.porthole {
  position: relative;
  width: min(280px, 62vw);
  aspect-ratio: 1;
  margin: 42px 0 0;
  animation: rise 1.1s .45s cubic-bezier(.2, .7, .3, 1) both;
}
.porthole img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
  display: block;
  border: 1px solid rgba(170, 195, 240, .28);
  animation: plutoLight 9s ease-in-out infinite;
}
/* 舷窗下方的一小片冷光池 */
.porthole::after {
  content: '';
  position: absolute;
  left: 50%;
  top: 106%;
  transform: translateX(-50%);
  width: 130%;
  height: 44px;
  background: radial-gradient(ellipse at center, rgba(140, 170, 255, .14), transparent 70%);
  pointer-events: none;
}

.caption {
  margin: 22px 0 0;
  font-size: 12px;
  letter-spacing: 2px;
  color: var(--pl-faint);
  animation: rise 1s .55s cubic-bezier(.2, .7, .3, 1) both;
}

.links {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  justify-content: center;
  margin-top: 34px;
  animation: rise 1s .7s cubic-bezier(.2, .7, .3, 1) both;
}
.link-btn {
  font: inherit;
  font-size: 14px;
  letter-spacing: 1px;
  color: var(--pl-cold);
  background: rgba(140, 170, 230, .06);
  border: 1px solid var(--pl-border);
  border-radius: 999px;
  padding: 11px 20px;
  cursor: pointer;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  transition: border-color .3s ease-out, box-shadow .3s ease-out,
              color .3s ease-out, transform .3s ease-out;
}
.link-btn:hover {
  border-color: rgba(170, 200, 250, .45);
  box-shadow: 0 0 24px -8px rgba(150, 180, 240, .5);
  color: #dfe9fb;
  transform: translateY(-2px);
}
.link-btn:focus-visible {
  outline: 2px solid var(--pl-cold);
  outline-offset: 3px;
}

@media (prefers-reduced-motion: reduce) {
  .corpus-coming-soon *, .corpus-coming-soon *::before, .corpus-coming-soon *::after {
    animation-duration: .01ms !important;
    transition-duration: .01ms !important;
  }
}

@media (max-width: 640px) {
  .stage { padding-top: 24vh; }
  h1 { letter-spacing: 4px; }
  .sub { font-size: 14px; }
  .porthole { width: min(220px, 60vw); }
  .links { flex-direction: column; align-items: stretch; width: min(320px, 100%); }
}
</style>
