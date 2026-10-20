<!-- ============================================================
     PlanetCanvas · 全站共享行星引擎 v3「辉光」
     用法：<PlanetCanvas planet="mars" /> 放在页面根元素内第一个子节点，
     页面根元素需 position: relative; z-index: 0（形成层叠上下文），
     canvas 以 fixed + z-index:-1 铺满视口，自身绘制不透明深空底，
     因此任何页面接入后都不会再露出 body 的浅色背景。

     v3 渲染哲学：不要素描，要辉光。
     每颗行星都有「本体」——带大气边缘光、星云团、亮星芒、流星：
       mars    —— 轨道视角的锈蚀星球弧面 + 大气火边 + 尘暴霾层 + 余烬尘粒
       jupiter —— 近轨视角的巨行星弧面（真实云带配色）+ 大红斑风暴
                  + 极光影帘 + 木卫二冰辉
       neptune —— 霓虹冰巨星本体 + 倾斜光环（前/后半环分层绘制）
                  + 超音速风纹 + 鼠标气流吹偏的钻石雨
     性能：rAF + DPR 封顶 1.5；shadowBlur 只用于少数关键发光体；
     prefers-reduced-motion 时只画一帧静态。
     ============================================================ -->
<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps<{ planet: 'mars' | 'jupiter' | 'neptune' }>()

const canvasRef = ref<HTMLCanvasElement | null>(null)
let raf: number | null = null
let resizeHandler: (() => void) | null = null
let pointerHandler: ((e: PointerEvent) => void) | null = null

interface Size { W: number; H: number; DPR: number }
type FrameFn = (t: number) => void

/* ---------------- 共享：星空 / 星云 / 流星 / 暗角 ---------------- */

interface Star { x: number; y: number; r: number; p: number; s: number; c: string; flare: boolean }

function makeStars(n: number, colors: string[], flareEvery = 9): Star[] {
  return Array.from({ length: n }, (_, i) => ({
    x: Math.random(), y: Math.random(),
    r: Math.random() * 1.1 + .3,
    p: Math.random() * Math.PI * 2,
    s: .15 + Math.random() * .5,
    c: colors[Math.floor(Math.random() * colors.length)],
    flare: i % flareEvery === 0
  }))
}

function drawStars(ctx: CanvasRenderingContext2D, size: Size, stars: Star[], t: number) {
  const { W, H, DPR } = size
  for (const s of stars) {
    const tw = .3 + .7 * Math.abs(Math.sin(t * s.s + s.p))
    const x = s.x * W, y = s.y * H
    if (s.flare) {
      /* 亮星：光晕 + 十字星芒 */
      const halo = ctx.createRadialGradient(x, y, 0, x, y, s.r * 7 * DPR)
      halo.addColorStop(0, `rgba(${s.c},${tw * .35})`)
      halo.addColorStop(1, `rgba(${s.c},0)`)
      ctx.fillStyle = halo
      ctx.beginPath()
      ctx.arc(x, y, s.r * 7 * DPR, 0, Math.PI * 2)
      ctx.fill()
      const sp = s.r * 5.5 * DPR
      ctx.beginPath()
      ctx.moveTo(x - sp, y); ctx.lineTo(x + sp, y)
      ctx.moveTo(x, y - sp); ctx.lineTo(x, y + sp)
      ctx.strokeStyle = `rgba(${s.c},${tw * .4})`
      ctx.lineWidth = .6 * DPR
      ctx.stroke()
    }
    ctx.beginPath()
    ctx.arc(x, y, s.r * DPR, 0, Math.PI * 2)
    ctx.fillStyle = `rgba(${s.c},${tw * .75})`
    ctx.fill()
  }
}

interface Blob { x: number; y: number; r: number; c: string; a: number; ph: number; sp: number }

function makeNebula(defs: Array<[number, number, number, string, number]>): Blob[] {
  return defs.map(([x, y, r, c, a]) => ({
    x, y, r, c, a, ph: Math.random() * Math.PI * 2, sp: .05 + Math.random() * .08
  }))
}

function drawNebula(ctx: CanvasRenderingContext2D, size: Size, blobs: Blob[], t: number) {
  const { W, H } = size
  ctx.save()
  ctx.globalCompositeOperation = 'lighter'
  for (const b of blobs) {
    const bx = (b.x + Math.sin(t * b.sp + b.ph) * .02) * W
    const by = (b.y + Math.cos(t * b.sp * .8 + b.ph) * .015) * H
    const br = b.r * Math.min(W, H)
    const pulse = b.a * (.8 + .2 * Math.sin(t * .3 + b.ph))
    const g = ctx.createRadialGradient(bx, by, 0, bx, by, br)
    g.addColorStop(0, `rgba(${b.c},${pulse})`)
    g.addColorStop(.55, `rgba(${b.c},${pulse * .4})`)
    g.addColorStop(1, `rgba(${b.c},0)`)
    ctx.fillStyle = g
    ctx.beginPath()
    ctx.arc(bx, by, br, 0, Math.PI * 2)
    ctx.fill()
  }
  ctx.restore()
}

interface Meteor { x: number; y: number; vx: number; vy: number; life: number; max: number }

function makeMeteorShower(interval: [number, number]) {
  let next = interval[0] + Math.random() * (interval[1] - interval[0])
  const actives: Meteor[] = []
  return {
    update(ctx: CanvasRenderingContext2D, size: Size, _t: number, dt: number, c: string) {
      const { W, H, DPR } = size
      next -= dt
      if (next <= 0) {
        next = interval[0] + Math.random() * (interval[1] - interval[0])
        const ang = Math.PI * (.72 + Math.random() * .12)   /* 左下方向划过 */
        const sp = (.35 + Math.random() * .3)
        actives.push({
          x: .55 + Math.random() * .45, y: Math.random() * .3,
          vx: Math.cos(ang) * sp, vy: -Math.sin(ang) * sp * .55,
          life: 0, max: .9 + Math.random() * .5
        })
      }
      ctx.save()
      ctx.globalCompositeOperation = 'lighter'
      ctx.lineCap = 'round'
      for (let i = actives.length - 1; i >= 0; i--) {
        const m = actives[i]
        m.life += dt
        m.x += m.vx * dt; m.y += m.vy * dt
        if (m.life > m.max) { actives.splice(i, 1); continue }
        const fade = Math.sin((m.life / m.max) * Math.PI)
        const hx = m.x * W, hy = m.y * H
        const tx = hx - m.vx * W * .12, ty = hy - m.vy * H * .12
        const tail = ctx.createLinearGradient(hx, hy, tx, ty)
        tail.addColorStop(0, `rgba(${c},${.8 * fade})`)
        tail.addColorStop(1, `rgba(${c},0)`)
        ctx.beginPath()
        ctx.moveTo(hx, hy); ctx.lineTo(tx, ty)
        ctx.strokeStyle = tail
        ctx.lineWidth = 1.4 * DPR
        ctx.stroke()
        const glow = ctx.createRadialGradient(hx, hy, 0, hx, hy, 6 * DPR)
        glow.addColorStop(0, `rgba(255,255,255,${.7 * fade})`)
        glow.addColorStop(1, `rgba(${c},0)`)
        ctx.fillStyle = glow
        ctx.beginPath()
        ctx.arc(hx, hy, 6 * DPR, 0, Math.PI * 2)
        ctx.fill()
      }
      ctx.restore()
    }
  }
}

function drawVignette(ctx: CanvasRenderingContext2D, size: Size) {
  const { W, H } = size
  const v = ctx.createRadialGradient(W * .5, H * .5, Math.min(W, H) * .42, W * .5, H * .5, Math.max(W, H) * .78)
  v.addColorStop(0, 'rgba(0,0,0,0)')
  v.addColorStop(1, 'rgba(0,0,0,.38)')
  ctx.fillStyle = v
  ctx.fillRect(0, 0, W, H)
}

/* ---------------- 火星 · 轨道锈蚀 ---------------- */
function makeMars(ctx: CanvasRenderingContext2D, size: Size): FrameFn {
  const stars = makeStars(110, ['255,236,220', '255,236,220', '255,214,180', '230,240,255'])
  const nebula = makeNebula([
    [.18, .22, .42, '120,40,30', .10],
    [.82, .12, .36, '160,70,35', .08],
    [.55, .05, .30, '90,50,70', .07]
  ])
  const meteors = makeMeteorShower([7, 16])
  /* 余烬尘粒：被风暴卷起的沙尘，发光、向右下飘 */
  const embers = Array.from({ length: 130 }, () => ({
    x: Math.random(), y: Math.random(),
    v: .0004 + Math.random() * .0014,
    vy: .00006 + Math.random() * .0003,
    r: .5 + Math.random() * 1.6,
    ph: Math.random() * Math.PI * 2,
    hot: Math.random() < .18
  }))
  /* 尘暴霾层：三片横移的奶油色霾 */
  const haze = Array.from({ length: 3 }, (_, i) => ({
    y: .30 + i * .18, sp: .006 + i * .004, ph: i * 2.1
  }))
  let last = 0

  return (t) => {
    const dt = Math.min(t - last, .05); last = t
    const { W, H, DPR } = size
    ctx.clearRect(0, 0, W, H)

    const bg = ctx.createLinearGradient(0, 0, 0, H)
    bg.addColorStop(0, '#0a0507')
    bg.addColorStop(.55, '#0d0605')
    bg.addColorStop(1, '#120705')
    ctx.fillStyle = bg
    ctx.fillRect(0, 0, W, H)

    drawNebula(ctx, size, nebula, t)
    drawStars(ctx, size, stars, t)

    /* 火星本体：巨大弧面从底部升起（轨道视角） */
    const cx = W * .5, cy = H * 2.30, R = H * 1.72
    /* 大气火边：先画光晕，再压本体 */
    ctx.save()
    ctx.globalCompositeOperation = 'lighter'
    const atmo = ctx.createRadialGradient(cx, cy, R * .97, cx, cy, R * 1.14)
    atmo.addColorStop(0, 'rgba(255,120,50,.30)')
    atmo.addColorStop(.4, 'rgba(240,90,40,.12)')
    atmo.addColorStop(1, 'rgba(240,90,40,0)')
    ctx.fillStyle = atmo
    ctx.beginPath()
    ctx.arc(cx, cy, R * 1.14, 0, Math.PI * 2)
    ctx.fill()
    ctx.restore()

    ctx.save()
    ctx.beginPath()
    ctx.arc(cx, cy, R, 0, Math.PI * 2)
    ctx.clip()
    const body = ctx.createRadialGradient(cx, cy - R * .55, R * .1, cx, cy, R * 1.05)
    body.addColorStop(0, '#8a3d22')
    body.addColorStop(.35, '#5e2716')
    body.addColorStop(.7, '#2e130c')
    body.addColorStop(1, '#160a07')
    ctx.fillStyle = body
    ctx.fillRect(0, 0, W, H)
    /* 表面暗斑（Acidalia / Syrtis 的意象） */
    for (const [mx, my, mr, ma] of [[.30, .68, .16, .5], [.62, .60, .10, .4], [.48, .74, .20, .35]] as const) {
      const g = ctx.createRadialGradient(W * mx, H * my, 0, W * mx, H * my, mr * W)
      g.addColorStop(0, `rgba(20,8,5,${ma})`)
      g.addColorStop(1, 'rgba(20,8,5,0)')
      ctx.fillStyle = g
      ctx.beginPath()
      ctx.arc(W * mx, H * my, mr * W, 0, Math.PI * 2)
      ctx.fill()
    }
    ctx.restore()

    /* 晨昏线火边：沿弧顶的亮边，带辉光 */
    ctx.save()
    ctx.shadowColor = 'rgba(255,140,60,.9)'
    ctx.shadowBlur = 22 * DPR
    ctx.beginPath()
    ctx.arc(cx, cy, R * 1.002, Math.PI * 1.18, Math.PI * 1.82)
    ctx.strokeStyle = 'rgba(255,160,90,.75)'
    ctx.lineWidth = 1.6 * DPR
    ctx.stroke()
    ctx.restore()

    /* 尘暴霾层 */
    ctx.save()
    ctx.globalCompositeOperation = 'lighter'
    for (const hz of haze) {
      const hy = hz.y * H + Math.sin(t * .2 + hz.ph) * H * .01
      const off = (t * hz.sp) % 1
      const g = ctx.createLinearGradient(0, hy - H * .05, 0, hy + H * .05)
      g.addColorStop(0, 'rgba(226,150,90,0)')
      g.addColorStop(.5, `rgba(226,150,90,${.05 + .02 * Math.sin(t * .5 + hz.ph)})`)
      g.addColorStop(1, 'rgba(226,150,90,0)')
      ctx.fillStyle = g
      ctx.fillRect(-W * off, hy - H * .05, W * 2, H * .1)
    }
    ctx.restore()

    /* 余烬尘粒：阵风周期 */
    const gust = .55 + .45 * Math.sin(t * .11 + 1)
    ctx.save()
    ctx.globalCompositeOperation = 'lighter'
    for (const d of embers) {
      d.x -= d.v * (.4 + gust)
      d.y += d.vy * (.4 + gust)
      if (d.x < -.02) { d.x = 1.02; d.y = Math.random() }
      if (d.y > 1.02) { d.y = -.02; d.x = Math.random() }
      const x = d.x * W, y = d.y * H
      const a = (.12 + .18 * Math.sin(t * 1.3 + d.ph) ** 2) * (.35 + gust * .65)
      if (d.hot) {
        const g = ctx.createRadialGradient(x, y, 0, x, y, d.r * 4 * DPR)
        g.addColorStop(0, `rgba(255,170,90,${a * 1.6})`)
        g.addColorStop(1, 'rgba(255,120,50,0)')
        ctx.fillStyle = g
        ctx.beginPath()
        ctx.arc(x, y, d.r * 4 * DPR, 0, Math.PI * 2)
        ctx.fill()
      }
      ctx.beginPath()
      ctx.arc(x, y, d.r * DPR, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(240,150,90,${a})`
      ctx.fill()
    }
    ctx.restore()

    meteors.update(ctx, size, t, dt, '255,190,130')
    drawVignette(ctx, size)
  }
}

/* ---------------- 木星 · 巨行星之耳 ---------------- */
function makeJupiter(ctx: CanvasRenderingContext2D, size: Size): FrameFn {
  const stars = makeStars(100, ['240,235,225', '240,235,225', '200,210,255', '255,230,200'])
  const nebula = makeNebula([
    [.15, .15, .40, '70,50,110', .09],
    [.85, .25, .34, '110,60,90', .07],
    [.50, .08, .28, '50,70,120', .06]
  ])
  const meteors = makeMeteorShower([9, 20])
  /* 云带粒子：附着在星球弧面上的湍流 */
  const BANDS = [
    { y: .745, c: '232,217,192', dir: 1,  sp: .00040 },
    { y: .775, c: '199,123,74',  dir: -1, sp: .00055 },
    { y: .810, c: '226,172,110', dir: 1,  sp: .00032 },
    { y: .850, c: '232,217,192', dir: -1, sp: .00048 },
    { y: .895, c: '176,110,70',  dir: 1,  sp: .00036 },
    { y: .940, c: '226,172,110', dir: -1, sp: .00042 }
  ]
  const streams = BANDS.flatMap((_, bi) =>
    Array.from({ length: 26 }, () => ({
      band: bi, x: Math.random(),
      yo: (Math.random() - .5) * .9,
      v: .6 + Math.random() * .8,
      len: 10 + Math.random() * 26,
      r: .6 + Math.random() * 1.2,
      ph: Math.random() * Math.PI * 2
    }))
  )
  /* 大红斑涡旋 */
  const vortex = Array.from({ length: 110 }, () => ({
    a: Math.random() * Math.PI * 2,
    d: .15 + Math.random() * .85,
    w: .12 + Math.random() * .25,
    r: .7 + Math.random() * 1.6,
    c: Math.random() < .55 ? '224,110,64' : (Math.random() < .5 ? '240,200,150' : '200,80,50')
  }))
  let last = 0

  return (t) => {
    const dt = Math.min(t - last, .05); last = t
    const { W, H, DPR } = size
    ctx.clearRect(0, 0, W, H)

    const bg = ctx.createLinearGradient(0, 0, 0, H)
    bg.addColorStop(0, '#0a0710')
    bg.addColorStop(.55, '#080610')
    bg.addColorStop(1, '#060409')
    ctx.fillStyle = bg
    ctx.fillRect(0, 0, W, H)

    drawNebula(ctx, size, nebula, t)
    drawStars(ctx, size, stars, t)

    /* 木卫二：冰蓝色小球，带辉光，缓慢漂移 */
    const euX = W * (.16 + Math.sin(t * .05) * .01), euY = H * .20, euR = Math.min(W, H) * .016
    ctx.save()
    ctx.globalCompositeOperation = 'lighter'
    const euHalo = ctx.createRadialGradient(euX, euY, 0, euX, euY, euR * 4)
    euHalo.addColorStop(0, 'rgba(190,220,255,.35)')
    euHalo.addColorStop(1, 'rgba(190,220,255,0)')
    ctx.fillStyle = euHalo
    ctx.beginPath(); ctx.arc(euX, euY, euR * 4, 0, Math.PI * 2); ctx.fill()
    ctx.restore()
    const euBody = ctx.createRadialGradient(euX - euR * .3, euY - euR * .3, 0, euX, euY, euR)
    euBody.addColorStop(0, '#dfeafa')
    euBody.addColorStop(.7, '#9db8d8')
    euBody.addColorStop(1, '#4a5a72')
    ctx.beginPath(); ctx.arc(euX, euY, euR, 0, Math.PI * 2)
    ctx.fillStyle = euBody; ctx.fill()

    /* 极光影帘：木星是太阳系最强射电源 */
    ctx.save()
    ctx.globalCompositeOperation = 'lighter'
    for (let i = 0; i < 9; i++) {
      const ax = ((i + .5) / 9 + Math.sin(t * .23 + i * 1.7) * .015) * W
      const ah = H * (.13 + .06 * Math.sin(t * .31 + i * 2.3))
      const alpha = .05 + .035 * Math.sin(t * .7 + i * 1.3)
      const ag = ctx.createLinearGradient(0, 0, 0, ah)
      ag.addColorStop(0, `rgba(150,170,255,${alpha})`)
      ag.addColorStop(.55, `rgba(192,132,252,${alpha * .6})`)
      ag.addColorStop(1, 'rgba(192,132,252,0)')
      ctx.fillStyle = ag
      ctx.fillRect(ax - W * .04, 0, W * .08, ah)
    }
    ctx.restore()

    /* 木星本体：近轨视角的巨大弧面 */
    const cx = W * .5, cy = H * 2.45, R = H * 1.78
    /* 弧顶大气亮边（先画辉光） */
    ctx.save()
    ctx.globalCompositeOperation = 'lighter'
    const limb = ctx.createRadialGradient(cx, cy, R * .97, cx, cy, R * 1.10)
    limb.addColorStop(0, 'rgba(255,220,170,.28)')
    limb.addColorStop(.5, 'rgba(230,180,120,.10)')
    limb.addColorStop(1, 'rgba(230,180,120,0)')
    ctx.fillStyle = limb
    ctx.beginPath(); ctx.arc(cx, cy, R * 1.10, 0, Math.PI * 2); ctx.fill()
    ctx.restore()

    ctx.save()
    ctx.beginPath()
    ctx.arc(cx, cy, R, 0, Math.PI * 2)
    ctx.clip()
    /* 云带：一条多停点垂直渐变 = 整颗行星的纬向条带 */
    const bands = ctx.createLinearGradient(0, H * .70, 0, H * 1.05)
    bands.addColorStop(0, '#c8935e')
    bands.addColorStop(.12, '#e6d3b4')
    bands.addColorStop(.24, '#b06a3c')
    bands.addColorStop(.38, '#e2ac6e')
    bands.addColorStop(.52, '#d9c6a6')
    bands.addColorStop(.66, '#a05a34')
    bands.addColorStop(.80, '#c8935e')
    bands.addColorStop(1, '#7a4426')
    ctx.fillStyle = bands
    ctx.fillRect(0, 0, W, H)
    /* 云带湍流粒子 */
    ctx.globalCompositeOperation = 'lighter'
    ctx.lineCap = 'round'
    for (const p of streams) {
      const b = BANDS[p.band]
      p.x += b.dir * b.sp * p.v
      if (p.x > 1.05) p.x = -.05
      if (p.x < -.05) p.x = 1.05
      const px = p.x * W
      const py = (b.y + p.yo * .012) * H
      const a = .12 + .14 * Math.sin(t * .9 + p.ph) ** 2
      ctx.beginPath()
      ctx.moveTo(px, py)
      ctx.lineTo(px + b.dir * p.len * DPR, py)
      ctx.strokeStyle = `rgba(${b.c},${a})`
      ctx.lineWidth = p.r * DPR
      ctx.stroke()
    }
    ctx.globalCompositeOperation = 'source-over'
    /* 大红斑：发光的风暴之眼 */
    const gx = W * .665, gy = H * .865
    const RX = Math.min(W, H) * .105, RY = RX * .52
    const grsGlow = ctx.createRadialGradient(gx, gy, 0, gx, gy, RX * 1.8)
    grsGlow.addColorStop(0, 'rgba(230,110,60,.30)')
    grsGlow.addColorStop(.6, 'rgba(210,90,50,.10)')
    grsGlow.addColorStop(1, 'rgba(210,90,50,0)')
    ctx.fillStyle = grsGlow
    ctx.beginPath(); ctx.arc(gx, gy, RX * 1.8, 0, Math.PI * 2); ctx.fill()
    const grsBody = ctx.createRadialGradient(gx, gy, 0, gx, gy, RX)
    grsBody.addColorStop(0, '#d4693c')
    grsBody.addColorStop(.55, '#a84a28')
    grsBody.addColorStop(1, 'rgba(120,50,30,.35)')
    ctx.beginPath(); ctx.ellipse(gx, gy, RX, RY, 0, 0, Math.PI * 2)
    ctx.fillStyle = grsBody; ctx.fill()
    /* 大红斑涡旋粒子：越靠内转得越快 */
    ctx.globalCompositeOperation = 'lighter'
    for (const p of vortex) {
      p.a += p.w * (1.3 - p.d) * .016
      const px = gx + Math.cos(p.a) * p.d * RX
      const py = gy + Math.sin(p.a) * p.d * RY
      ctx.beginPath()
      ctx.arc(px, py, p.r * DPR, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(${p.c},${(1 - p.d) * .5 + .10})`
      ctx.fill()
    }
    ctx.globalCompositeOperation = 'source-over'
    /* 大红斑的奶油色亮环 */
    ctx.beginPath()
    ctx.ellipse(gx, gy, RX * 1.06, RY * 1.08, 0, 0, Math.PI * 2)
    ctx.strokeStyle = 'rgba(240,215,180,.35)'
    ctx.lineWidth = 1.2 * DPR
    ctx.stroke()
    /* 底部压暗，让星球有体积感 */
    const shade = ctx.createLinearGradient(0, H * .70, 0, H * 1.02)
    shade.addColorStop(0, 'rgba(10,5,8,0)')
    shade.addColorStop(1, 'rgba(10,5,8,.45)')
    ctx.fillStyle = shade
    ctx.fillRect(0, 0, W, H)
    ctx.restore()

    /* 弧顶晨昏线 */
    ctx.save()
    ctx.shadowColor = 'rgba(255,215,160,.8)'
    ctx.shadowBlur = 18 * DPR
    ctx.beginPath()
    ctx.arc(cx, cy, R * 1.002, Math.PI * 1.15, Math.PI * 1.85)
    ctx.strokeStyle = 'rgba(255,225,180,.6)'
    ctx.lineWidth = 1.4 * DPR
    ctx.stroke()
    ctx.restore()

    meteors.update(ctx, size, t, dt, '230,200,255')
    drawVignette(ctx, size)
  }
}

/* ---------------- 海王星 · 霓虹冰巨星 ---------------- */
function makeNeptune(ctx: CanvasRenderingContext2D, size: Size, mouse: { vx: number }): FrameFn {
  const stars = makeStars(110, ['225,242,255', '225,242,255', '170,200,255', '200,255,245'])
  const nebula = makeNebula([
    [.15, .70, .44, '40,70,160', .11],
    [.85, .75, .36, '70,40,140', .09],
    [.30, .15, .30, '30,120,150', .07],
    [.70, .10, .26, '50,60,150', .06]
  ])
  const meteors = makeMeteorShower([8, 18])
  /* 超音速风纹：三层视差，发光的卷云 */
  const LAYER_SPEED = [.30, .17, .09]
  const LAYER_ALPHA = [.20, .13, .08]
  const LAYER_COLOR = ['150,210,250', '125,235,215', '210,235,255']
  const streaks = Array.from({ length: 120 }, () => {
    const layer = Math.floor(Math.random() * 3)
    return {
      layer,
      x: Math.random(), y: Math.random(),
      len: (40 + Math.random() * 120) * (1 + layer * .5),
      w: .5 + Math.random() * 1.2
    }
  })
  /* 钻石雨 */
  const rain = Array.from({ length: 80 }, () => ({
    x: Math.random(), y: Math.random(),
    v: .0004 + Math.random() * .0009,
    drift: (Math.random() - .5) * .0002,
    r: .6 + Math.random() * 1.3,
    ph: Math.random() * Math.PI * 2,
    sparkle: Math.random() < .16
  }))
  /* 大暗斑涡旋（在星球本体上） */
  const storm = Array.from({ length: 60 }, () => ({
    a: Math.random() * Math.PI * 2,
    d: .25 + Math.random() * .75,
    w: .06 + Math.random() * .12,
    r: .5 + Math.random() * 1.2
  }))
  let last = 0

  return (t) => {
    const dt = Math.min(t - last, .05); last = t
    const { W, H, DPR } = size
    ctx.clearRect(0, 0, W, H)

    const bg = ctx.createLinearGradient(0, 0, 0, H)
    bg.addColorStop(0, '#050d1f')
    bg.addColorStop(.5, '#040b18')
    bg.addColorStop(1, '#020610')
    ctx.fillStyle = bg
    ctx.fillRect(0, 0, W, H)

    drawNebula(ctx, size, nebula, t)
    drawStars(ctx, size, stars, t)

    /* ===== 海王星本体：霓虹冰巨星 ===== */
    const px = W * .76, py = H * .34
    const R = Math.min(W, H) * .21
    const ringTilt = -.38

    /* 外层大气辉光 */
    ctx.save()
    ctx.globalCompositeOperation = 'lighter'
    const halo = ctx.createRadialGradient(px, py, R * .8, px, py, R * 2.4)
    halo.addColorStop(0, 'rgba(90,180,255,.22)')
    halo.addColorStop(.45, 'rgba(70,140,255,.08)')
    halo.addColorStop(1, 'rgba(70,140,255,0)')
    ctx.fillStyle = halo
    ctx.beginPath(); ctx.arc(px, py, R * 2.4, 0, Math.PI * 2); ctx.fill()
    ctx.restore()

    /* 光环后半（在星球背面）：霓虹双环 */
    const drawRing = (front: boolean) => {
      ctx.save()
      ctx.translate(px, py)
      ctx.rotate(ringTilt)
      ctx.globalCompositeOperation = 'lighter'
      const start = front ? 0 : Math.PI
      const end = front ? Math.PI : Math.PI * 2
      /* 外环：品红-橙霓虹 */
      ctx.beginPath()
      ctx.ellipse(0, 0, R * 1.75, R * .48, 0, start, end)
      ctx.strokeStyle = front ? 'rgba(255,120,200,.40)' : 'rgba(255,120,200,.16)'
      ctx.lineWidth = 2.2 * DPR
      ctx.shadowColor = 'rgba(255,100,190,.8)'
      ctx.shadowBlur = (front ? 14 : 8) * DPR
      ctx.stroke()
      /* 内环：青白 */
      ctx.beginPath()
      ctx.ellipse(0, 0, R * 1.45, R * .40, 0, start, end)
      ctx.strokeStyle = front ? 'rgba(160,240,255,.55)' : 'rgba(160,240,255,.20)'
      ctx.lineWidth = 1.4 * DPR
      ctx.shadowColor = 'rgba(120,220,255,.9)'
      ctx.shadowBlur = (front ? 12 : 6) * DPR
      ctx.stroke()
      ctx.restore()
    }
    drawRing(false)

    /* 星球本体 */
    ctx.save()
    ctx.beginPath()
    ctx.arc(px, py, R, 0, Math.PI * 2)
    ctx.clip()
    const body = ctx.createRadialGradient(px - R * .4, py - R * .45, R * .08, px, py, R * 1.2)
    body.addColorStop(0, '#9fdcf8')
    body.addColorStop(.3, '#4fa8e8')
    body.addColorStop(.62, '#1e5aaa')
    body.addColorStop(.88, '#0c2450')
    body.addColorStop(1, '#060f28')
    ctx.fillStyle = body
    ctx.fillRect(px - R, py - R, R * 2, R * 2)
    /* 纬向云带 */
    for (const [dy, h, c, a] of [
      [-.45, .16, '190,230,255', .18], [-.12, .12, '120,190,245', .16],
      [.18, .14, '230,245,255', .14], [.48, .12, '90,150,220', .16]
    ] as const) {
      const band = ctx.createLinearGradient(0, py + (dy - h) * R, 0, py + (dy + h) * R)
      band.addColorStop(0, `rgba(${c},0)`)
      band.addColorStop(.5, `rgba(${c},${a})`)
      band.addColorStop(1, `rgba(${c},0)`)
      ctx.fillStyle = band
      ctx.fillRect(px - R, py + (dy - h) * R, R * 2, h * 2 * R)
    }
    /* 大暗斑 + 涡旋 */
    const sx = px + R * .28, sy = py + R * .30
    const SR = R * .26
    ctx.beginPath()
    ctx.ellipse(sx, sy, SR, SR * .62, -.2, 0, Math.PI * 2)
    ctx.fillStyle = 'rgba(8,16,40,.55)'
    ctx.fill()
    ctx.globalCompositeOperation = 'lighter'
    for (const p of storm) {
      p.a += p.w * .016
      ctx.beginPath()
      ctx.arc(sx + Math.cos(p.a) * p.d * SR, sy + Math.sin(p.a) * p.d * SR * .62, p.r * DPR, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(140,190,250,${(1 - p.d) * .25 + .05})`
      ctx.fill()
    }
    ctx.globalCompositeOperation = 'source-over'
    /* 甲烷卷云：星球上的白色亮纹 */
    ctx.strokeStyle = 'rgba(230,245,255,.35)'
    ctx.lineCap = 'round'
    for (const [cxy, cyy, cl] of [[-.35, -.28, .30], [.1, -.5, .22], [-.15, .55, .26]] as const) {
      ctx.beginPath()
      ctx.moveTo(px + cxy * R, py + cyy * R)
      ctx.lineTo(px + (cxy + cl) * R, py + (cyy - .03) * R)
      ctx.lineWidth = 1.6 * DPR
      ctx.stroke()
    }
    ctx.restore()

    /* 边缘光：被背后的太阳点亮的大气 */
    ctx.save()
    ctx.shadowColor = 'rgba(120,220,255,1)'
    ctx.shadowBlur = 26 * DPR
    ctx.beginPath()
    ctx.arc(px, py, R * 1.005, Math.PI * .85, Math.PI * 1.75)
    ctx.strokeStyle = 'rgba(160,235,255,.85)'
    ctx.lineWidth = 2 * DPR
    ctx.stroke()
    ctx.restore()

    /* 光环前半（压在星球前方） */
    drawRing(true)

    /* ===== 超音速风纹：发光卷云横扫 ===== */
    ctx.save()
    ctx.globalCompositeOperation = 'lighter'
    ctx.lineCap = 'round'
    for (const s of streaks) {
      s.x += LAYER_SPEED[s.layer] * .016
      if (s.x * W > W + s.len * DPR) { s.x = -s.len * DPR / W; s.y = Math.random() }
      const x0 = s.x * W, y0 = s.y * H
      const x1 = x0 + s.len * DPR
      const g = ctx.createLinearGradient(x0, y0, x1, y0)
      g.addColorStop(0, `rgba(${LAYER_COLOR[s.layer]},0)`)
      g.addColorStop(.7, `rgba(${LAYER_COLOR[s.layer]},${LAYER_ALPHA[s.layer]})`)
      g.addColorStop(1, `rgba(${LAYER_COLOR[s.layer]},${LAYER_ALPHA[s.layer] * 1.8})`)
      ctx.beginPath()
      ctx.moveTo(x0, y0); ctx.lineTo(x1, y0)
      ctx.strokeStyle = g
      ctx.lineWidth = s.w * DPR
      ctx.stroke()
    }
    ctx.restore()

    /* ===== 钻石雨：斜落冰晶，被鼠标气流吹偏 ===== */
    mouse.vx *= .92
    ctx.save()
    ctx.globalCompositeOperation = 'lighter'
    for (const d of rain) {
      d.y += d.v
      d.x += d.drift + mouse.vx * .0007
      if (d.y > 1.02) { d.y = -.02; d.x = Math.random() }
      if (d.x > 1.02) d.x = -.02
      if (d.x < -.02) d.x = 1.02
      const x = d.x * W, y = d.y * H
      const a = .22 + .28 * Math.sin(t * 1.6 + d.ph) ** 2
      if (d.sparkle) {
        const g = ctx.createRadialGradient(x, y, 0, x, y, d.r * 5 * DPR)
        g.addColorStop(0, `rgba(220,245,255,${a * .9})`)
        g.addColorStop(1, 'rgba(180,220,255,0)')
        ctx.fillStyle = g
        ctx.beginPath(); ctx.arc(x, y, d.r * 5 * DPR, 0, Math.PI * 2); ctx.fill()
        const sp = d.r * 4 * DPR
        ctx.beginPath()
        ctx.moveTo(x - sp, y); ctx.lineTo(x + sp, y)
        ctx.moveTo(x, y - sp); ctx.lineTo(x, y + sp)
        ctx.strokeStyle = `rgba(230,248,255,${a * .7})`
        ctx.lineWidth = .6 * DPR
        ctx.stroke()
      }
      ctx.beginPath()
      ctx.arc(x, y, d.r * DPR, 0, Math.PI * 2)
      ctx.fillStyle = `rgba(215,240,255,${a})`
      ctx.fill()
    }
    ctx.restore()

    meteors.update(ctx, size, t, dt, '170,220,255')
    drawVignette(ctx, size)
  }
}

/* ---------------- 装配 ---------------- */
function initPlanet() {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches
  const size: Size = { W: 0, H: 0, DPR: 1 }
  const mouse = { vx: 0 }
  let lastX = 0

  const resize = () => {
    size.DPR = Math.min(window.devicePixelRatio || 1, 1.5)
    size.W = canvas.width = Math.floor(innerWidth * size.DPR)
    size.H = canvas.height = Math.floor(innerHeight * size.DPR)
    canvas.style.width = innerWidth + 'px'
    canvas.style.height = innerHeight + 'px'
  }
  resize()
  resizeHandler = resize
  addEventListener('resize', resize)

  pointerHandler = (e: PointerEvent) => { mouse.vx = e.clientX - lastX; lastX = e.clientX }
  addEventListener('pointermove', pointerHandler)

  const frame: FrameFn =
    props.planet === 'mars' ? makeMars(ctx, size) :
    props.planet === 'jupiter' ? makeJupiter(ctx, size) :
    makeNeptune(ctx, size, mouse)

  if (reduced) {
    frame(0)
  } else {
    const loop = (now: number) => { frame(now / 1000); raf = requestAnimationFrame(loop) }
    raf = requestAnimationFrame(loop)
  }
}

onMounted(initPlanet)
onBeforeUnmount(() => {
  if (raf !== null) cancelAnimationFrame(raf)
  if (resizeHandler) removeEventListener('resize', resizeHandler)
  if (pointerHandler) removeEventListener('pointermove', pointerHandler)
})
</script>

<template>
  <canvas ref="canvasRef" class="planet-canvas" aria-hidden="true"></canvas>
</template>

<style scoped>
.planet-canvas {
  position: fixed;
  inset: 0;
  z-index: -1;
  display: block;
  pointer-events: none;
}
</style>
