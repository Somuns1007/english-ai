<template>
  <div class="home">
    <canvas ref="cosmos" class="cosmos"></canvas>

    <div class="page">

      <!-- 顶部 -->
      <header>
        <div class="brand"><span class="dot"></span>阿Q的英语自习室</div>
        <div class="clock">{{ clock }}</div>
      </header>

      <!-- Hero -->
      <section class="hero">
        <div class="kicker">English Study Room</div>
        <h1>阿Q的英语自习室</h1>
        <p class="subtitle">日积月累<span class="sep">·</span>踏实的努力</p>

        <div class="cards">
          <div class="card" @click="go('/listening')" @mousemove="trackLight">
            <div class="card-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 14v-2a9 9 0 0 1 18 0v2"/>
                <path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/>
              </svg>
            </div>
            <h2>听力训练</h2>
            <p>四六级、雅思、高考英语听力训练，精听与跟读中打磨耳朵。</p>
            <span class="go">
              开始训练
              <svg class="arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 12h14M13 6l6 6-6 6"/>
              </svg>
            </span>
          </div>

          <div class="card" @click="go('/writing')" @mousemove="trackLight">
            <div class="card-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 20h9"/>
                <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>
              </svg>
            </div>
            <h2>作文批改</h2>
            <p>智能分析语法、词汇、逻辑和表达，逐句给出修改建议。</p>
            <span class="go">
              提交作文
              <svg class="arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 12h14M13 6l6 6-6 6"/>
              </svg>
            </span>
          </div>
        </div>
      </section>

      <footer>
        <span>© 2026 阿Q的英语自习室</span>
        <span>Slow is smooth, smooth is fast.</span>
      </footer>

    </div>
  </div>
</template>

<script>
export default {
  name: 'HomeView',

  data() {
    return {
      clock: '',
      _raf: null,
      _clockTimer: null,
      _t0: 0
    }
  },

  methods: {
    go(path) {
      if (this.$router) this.$router.push(path)
    },

    trackLight(e) {
      const card = e.currentTarget
      const r = card.getBoundingClientRect()
      card.style.setProperty('--mx', (e.clientX - r.left) + 'px')
      card.style.setProperty('--my', (e.clientY - r.top) + 'px')
    },

    tickClock() {
      this.clock = new Date().toTimeString().slice(0, 8)
    },

    initCosmos() {
      const canvas = this.$refs.cosmos
      const ctx = canvas.getContext('2d')

      let W, H, DPR

      const resize = () => {
        DPR = Math.min(window.devicePixelRatio || 1, 2)
        W = canvas.width = innerWidth * DPR
        H = canvas.height = innerHeight * DPR
        canvas.style.width = innerWidth + 'px'
        canvas.style.height = innerHeight + 'px'
      }

      resize()
      this._resize = resize
      addEventListener('resize', resize)

      /* 星星 */
      // 设计师注：按真实星空的色温分布做了加权——冷白/淡蓝占约 3/4，淡金与淡紫只是稀疏点缀，
      // 四色均分会显得像彩灯，加权后才像银河。
      const STAR_COLORS = [
        ['232,238,248', .50],  /* 冷白 */
        ['168,200,255', .27],  /* 淡蓝 */
        ['255,228,160', .13],  /* 淡金 */
        ['212,186,255', .10]   /* 极淡紫 */
      ]
      const pickStarColor = () => {
        const roll = Math.random()
        let acc = 0
        for (const [c, w] of STAR_COLORS) {
          acc += w
          if (roll < acc) return c
        }
        return STAR_COLORS[0][0]
      }

      const stars = Array.from({ length: 220 }, () => ({
        x: Math.random(),
        y: Math.random(),
        r: Math.random() * 1.1 + .2,
        p: Math.random() * Math.PI * 2,
        s: .4 + Math.random() * .8,
        c: pickStarColor()
      }))

      /* 星云 */
      // 设计师注：四团星云按指定色相换成紫蓝/青绿/玫红紫/蓝白，alpha 提到 .12~.14，
      // 深空不再是黑房间，而是有气体云层次的星际空间。
      const nebulae = [
        { x: .18, y: .22, r: .42, c: '60,80,180',  a: .14, dx: .000021, ph: 0 },
        { x: .85, y: .30, r: .38, c: '20,140,120', a: .12, dx: .000017, ph: 2 },
        { x: .30, y: .85, r: .45, c: '160,60,140', a: .12, dx: .000013, ph: 4 },
        { x: .78, y: .80, r: .36, c: '80,120,200', a: .13, dx: .000025, ph: 1 }
      ]

      /* 黑洞吸积盘 */
      const TILT = 0.34
      const DISK_N = 1200

      const scale = () => Math.max(.55, Math.min(1.25, Math.min(innerWidth, innerHeight) / 900))

      const disk = Array.from({ length: DISK_N }, () => ({
        t: Math.random(),
        a: Math.random() * Math.PI * 2,
        size: .5 + Math.random() * 1.4,
        flick: Math.random() * Math.PI * 2
      }))

      const bhCenter = () => {
        const s = scale()
        return { x: W * .5, y: H * .29, R: 72 * s * DPR, rIn: 88 * s, rOut: 420 * s }
      }

      const drawDisk = (t, cx, cy, rIn, rOut, back) => {
        ctx.save()
        ctx.globalCompositeOperation = 'lighter'
        ctx.lineCap = 'round'

        for (const p of disk) {
          const r = (rIn + Math.pow(p.t, 1.7) * (rOut - rIn)) * DPR
          const heat = 1 - Math.pow(p.t, 1.4)
          const w = 30 / Math.pow(r / DPR, 1.4)
          const a = p.a + t * w
          const sinA = Math.sin(a)

          if (back ? sinA >= 0 : sinA < 0) continue

          const trail = .04 + .10 * heat
          const a2 = a - trail
          const x1 = cx + Math.cos(a) * r
          const y1 = cy + sinA * r * TILT
          const x2 = cx + Math.cos(a2) * r
          const y2 = cy + Math.sin(a2) * r * TILT
          const flick = .55 + .45 * Math.sin(t * 2.2 + p.flick)
          const alpha = (.08 + .6 * Math.pow(heat, 1.8)) * flick
          const cg = Math.round(150 + 92 * heat)
          const cb = Math.round(60 + 145 * Math.pow(heat, 2.6))

          ctx.beginPath()
          ctx.moveTo(x2, y2)
          ctx.lineTo(x1, y1)
          ctx.strokeStyle = `rgba(255,${cg},${cb},${alpha})`
          ctx.lineWidth = p.size * DPR * (.7 + heat * .8)
          ctx.stroke()
        }

        ctx.restore()
      }

      const frame = (now) => {
        const t = (now - this._t0) / 1000

        ctx.clearRect(0, 0, W, H)

        /* 深空底色 */
        // 设计师注：三段渐变整体推向蓝紫，中段最亮、上下沉暗，
        // 模拟视线穿过银道面时的微亮感，而不是三面纯黑墙。
        const bg = ctx.createLinearGradient(0, 0, 0, H)
        bg.addColorStop(0,   '#080B1C')
        bg.addColorStop(.55, '#0C0F24')
        bg.addColorStop(1,   '#05061A')
        ctx.fillStyle = bg
        ctx.fillRect(0, 0, W, H)

        /* 银河亮带 */
        // 设计师注（超出基线的加法）：一道极淡（alpha .045）的对角冷色亮带，
        // 这是"仰望夜空"与"盯着黑屏"之间最关键的一层——银河本身。
        ctx.save()
        ctx.translate(W / 2, H / 2)
        ctx.rotate(-.38)
        const mw = ctx.createLinearGradient(0, -H * .4, 0, H * .4)
        mw.addColorStop(0,  'rgba(150,170,255,0)')
        mw.addColorStop(.5, 'rgba(170,190,255,.045)')
        mw.addColorStop(1,  'rgba(150,170,255,0)')
        ctx.fillStyle = mw
        ctx.fillRect(-W, -H, W * 2, H * 2)
        ctx.restore()

        /* 星云 */
        for (const n of nebulae) {
          const nx = (n.x + Math.sin(t * n.dx * 900 + n.ph) * .03) * W
          const ny = (n.y + Math.cos(t * n.dx * 700 + n.ph) * .02) * H
          const nr = n.r * Math.max(W, H)
          const g = ctx.createRadialGradient(nx, ny, 0, nx, ny, nr)
          // 设计师注：星云径向渐变加了一个中间停止点，核心更聚、边缘更柔，
          // 单段线性衰减会显得像平涂的圆斑。
          g.addColorStop(0,   `rgba(${n.c},${n.a})`)
          g.addColorStop(.45, `rgba(${n.c},${n.a * .45})`)
          g.addColorStop(1,   `rgba(${n.c},0)`)
          ctx.fillStyle = g
          ctx.fillRect(0, 0, W, H)
        }

        /* 星星 */
        for (const s of stars) {
          const tw = .35 + .65 * Math.abs(Math.sin(t * s.s + s.p))
          const sx = s.x * W
          const sy = s.y * H
          const sr = s.r * DPR

          // 设计师注（超出基线的加法）：最亮的一小撮星（约 7%）补一层柔光晕和细十字芒，
          // 人眼在真实夜空里先看到的就是这几颗"锚点星"，星空因此有了纵深。
          if (s.r > 1.15) {
            ctx.beginPath()
            ctx.arc(sx, sy, sr * 3.2, 0, Math.PI * 2)
            ctx.fillStyle = `rgba(${s.c},${tw * .10})`
            ctx.fill()

            const sp = sr * 4.5
            ctx.beginPath()
            ctx.moveTo(sx - sp, sy)
            ctx.lineTo(sx + sp, sy)
            ctx.moveTo(sx, sy - sp)
            ctx.lineTo(sx, sy + sp)
            ctx.strokeStyle = `rgba(${s.c},${tw * .30})`
            ctx.lineWidth = .6 * DPR
            ctx.stroke()
          }

          ctx.beginPath()
          ctx.arc(sx, sy, sr, 0, Math.PI * 2)
          ctx.fillStyle = `rgba(${s.c},${tw * .75})`
          ctx.fill()
        }

        const { x: cx, y: cy, R, rIn, rOut } = bhCenter()

        /* 冷色引力晕 */
        // 设计师注：黑洞外圈先铺一层大范围蓝紫晕，再叠原有的暖晕——
        // 暖光像被"浸"在冷空间里，正是引力扭曲星光的感觉。
        const cool = ctx.createRadialGradient(cx, cy, R * 1.2, cx, cy, rOut * 1.9 * DPR)
        cool.addColorStop(0,   'rgba(140,160,255,.09)')
        cool.addColorStop(.55, 'rgba(120,140,240,.04)')
        cool.addColorStop(1,   'rgba(120,140,240,0)')
        ctx.fillStyle = cool
        ctx.beginPath()
        ctx.arc(cx, cy, rOut * 1.9 * DPR, 0, Math.PI * 2)
        ctx.fill()

        /* 背景晕光 */
        const halo = ctx.createRadialGradient(cx, cy, R, cx, cy, rOut * 1.3 * DPR)
        halo.addColorStop(0,   'rgba(232,167,92,.14)')
        halo.addColorStop(.5,  'rgba(180,110,60,.06)')
        halo.addColorStop(1,   'rgba(180,110,60,0)')
        ctx.fillStyle = halo
        ctx.beginPath()
        ctx.arc(cx, cy, rOut * 1.3 * DPR, 0, Math.PI * 2)
        ctx.fill()

        /* 吸积盘后半 */
        drawDisk(t, cx, cy, rIn, rOut, true)

        /* 黑洞本体 */
        ctx.beginPath()
        ctx.arc(cx, cy, R, 0, Math.PI * 2)
        ctx.fillStyle = '#000'
        ctx.fill()

        /* 光子环 */
        ctx.beginPath()
        ctx.arc(cx, cy, R * 1.1, 0, Math.PI * 2)
        ctx.strokeStyle = 'rgba(255,222,175,.9)'
        ctx.lineWidth = 1.6 * DPR
        ctx.shadowColor = 'rgba(255,200,130,.95)'
        ctx.shadowBlur = 18 * DPR
        ctx.stroke()
        ctx.shadowBlur = 0

        /* 引力透镜弧 */
        ctx.beginPath()
        ctx.ellipse(cx, cy - R * .05, R * 1.75, R * 1.02, 0, Math.PI * 1.08, Math.PI * 1.92)
        ctx.strokeStyle = 'rgba(255,208,145,.5)'
        ctx.lineWidth = 5 * DPR
        ctx.shadowColor = 'rgba(255,190,120,.9)'
        ctx.shadowBlur = 24 * DPR
        ctx.stroke()
        ctx.shadowBlur = 0

        /* 吸积盘前半 */
        drawDisk(t, cx, cy, rIn, rOut, false)
      }

      const loop = (now) => {
        frame(now)
        this._raf = requestAnimationFrame(loop)
      }

      this._t0 = performance.now()
      this._raf = requestAnimationFrame(loop)
    }
  },

  mounted() {
    this.initCosmos()
    this.tickClock()
    this._clockTimer = setInterval(this.tickClock, 1000)
  },

  beforeUnmount() {
    cancelAnimationFrame(this._raf)
    clearInterval(this._clockTimer)
    removeEventListener('resize', this._resize)
  },

  beforeDestroy() {
    cancelAnimationFrame(this._raf)
    clearInterval(this._clockTimer)
    removeEventListener('resize', this._resize)
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Noto+Serif+SC:wght@600;700&display=swap');

.home {
  --ink: #EDF0F8;
  --muted: rgba(210, 220, 245, .60);
  --faint: rgba(200, 212, 240, .34);
  --amber: #E8A75C;
  --star: #A8C0FF;
  --glass: rgba(255, 255, 255, .055);
  --glass-border: rgba(180, 200, 255, .12);

  font-family: 'Noto Sans SC', -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: #05061A;
  color: var(--ink);
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
  position: relative;
  overflow-x: hidden;
}

/* 设计师注（超出基线的加法）：选中文本时也保持星光蓝，细节处不穿帮。 */
.home ::selection {
  background: rgba(140, 165, 255, .28);
  color: #F4F7FF;
}

.cosmos {
  position: fixed;
  inset: 0;
  z-index: 0;
  display: block;
}

.page {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 24px;
}

header {
  width: 100%;
  max-width: 1100px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 28px 0;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: 'Noto Serif SC', serif;
  font-weight: 600;
  font-size: 16px;
  letter-spacing: 1px;
  color: var(--muted);
}

.brand .dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--amber);
  /* 设计师注：琥珀内核保留，外圈叠一层蓝紫晕——像一颗被星光照亮的暖星。 */
  box-shadow: 0 0 12px 2px rgba(232, 167, 92, .65), 0 0 16px 3px rgba(160, 180, 255, .5);
}

.clock {
  font-family: 'Fraunces', serif;
  font-size: 14px;
  letter-spacing: 2px;
  color: var(--faint);
}

.hero {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  width: 100%;
  padding-top: 43vh;
  padding-bottom: 20px;
}

.kicker {
  font-size: 12px;
  letter-spacing: 6px;
  text-transform: uppercase;
  color: var(--faint);
  font-weight: 500;
  margin-bottom: 22px;
}

h1 {
  font-family: 'Noto Serif SC', serif;
  font-size: clamp(38px, 6.5vw, 68px);
  font-weight: 700;
  letter-spacing: 6px;
  line-height: 1.15;
  /* 设计师注：双层光晕——近处一圈窄而亮的冷白勾边，远处一团宽而淡的蓝紫氛围，
     单层 80px 光晕会糊成雾，双层才有"星星在发光"的锐利核心。 */
  text-shadow: 0 0 24px rgba(190, 205, 255, .22), 0 0 80px rgba(140, 160, 255, .30);
  animation: rise 1.1s .1s cubic-bezier(.2, .7, .3, 1) both;
}

.subtitle {
  margin-top: 20px;
  font-size: 15px;
  letter-spacing: 5px;
  color: var(--muted);
  animation: rise 1.1s .3s cubic-bezier(.2, .7, .3, 1) both;
}

.subtitle .sep { margin: 0 10px; color: var(--faint); }

.cards {
  margin-top: 46px;
  display: flex;
  gap: 24px;
  justify-content: center;
  flex-wrap: wrap;
  width: 100%;
  max-width: 860px;
  animation: rise 1.1s .5s cubic-bezier(.2, .7, .3, 1) both;
}

.card {
  position: relative;
  flex: 1;
  min-width: 280px;
  max-width: 400px;
  padding: 32px 32px 26px;
  border-radius: 20px;
  background: var(--glass);
  border: 1px solid var(--glass-border);
  /* 设计师注（超出基线的加法）：顶部一道极淡的内高光，玻璃才有"厚度"，
     否则在亮星云背景前卡片会显平。 */
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, .06);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  cursor: pointer;
  transition: transform .35s cubic-bezier(.2, .7, .3, 1), border-color .35s, box-shadow .35s;
  overflow: hidden;
}

.card::before {
  content: '';
  position: absolute;
  inset: 0;
  /* 设计师注：鼠标光斑从琥珀换成冷月光蓝——琥珀留给黑洞，UI 层统一归星光。 */
  background: radial-gradient(420px circle at var(--mx, 50%) var(--my, 50%), rgba(170, 195, 255, .10), transparent 45%);
  opacity: 0;
  transition: opacity .35s;
  pointer-events: none;
}

.card:hover {
  transform: translateY(-5px);
  border-color: rgba(180, 200, 255, .35);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, .08),
    0 20px 50px -20px rgba(2, 4, 16, .8),
    0 0 46px -12px rgba(140, 170, 255, .22);
}

.card:hover::before { opacity: 1; }

.card-icon {
  width: 46px;
  height: 46px;
  border-radius: 13px;
  display: grid;
  place-items: center;
  /* 设计师注：图标底从平涂琥珀换成蓝→紫 135° 渐变，与星云色相呼应，比单色更有"星尘"感。 */
  background: linear-gradient(135deg, rgba(120, 160, 255, .14), rgba(170, 130, 255, .10));
  border: 1px solid rgba(150, 180, 255, .22);
  color: #B4C8FF;
  margin-bottom: 22px;
  transition: box-shadow .35s;
}

/* 设计师注（超出基线的加法）：悬停时图标轻轻发光，给卡片一个视觉重心。 */
.card:hover .card-icon {
  box-shadow: 0 0 24px -6px rgba(140, 170, 255, .35);
}

.card h2 {
  font-family: 'Noto Serif SC', serif;
  font-size: 21px;
  font-weight: 600;
  letter-spacing: 2px;
}

.card p {
  margin-top: 10px;
  font-size: 14px;
  line-height: 1.8;
  color: var(--muted);
  letter-spacing: .5px;
}

.card .go {
  margin-top: 24px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13.5px;
  letter-spacing: 2px;
  color: var(--star);
  transition: text-shadow .35s;
}

/* 设计师注（超出基线的加法）：悬停时链接泛起微光，像被点亮的小星。 */
.card:hover .go { text-shadow: 0 0 18px rgba(150, 180, 255, .45); }

.card .go .arrow { transition: transform .3s cubic-bezier(.2, .7, .3, 1); }
.card:hover .go .arrow { transform: translateX(5px); }

footer {
  width: 100%;
  max-width: 1100px;
  padding: 26px 0;
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 12px;
  letter-spacing: 1.5px;
  color: var(--faint);
}

@keyframes rise {
  from { opacity: 0; transform: translateY(26px); }
  to   { opacity: 1; transform: none; }
}

@media (max-width: 640px) {
  header { padding: 20px 0; }
  .clock { display: none; }
  h1 { letter-spacing: 3px; }
  .subtitle { letter-spacing: 3px; font-size: 14px; }
  .cards { margin-top: 44px; gap: 16px; }
}
</style>
