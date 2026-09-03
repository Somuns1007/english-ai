<template>
  <!--
    听力后词汇采集面板 (Work Order E)
    D3 红线：本组件只能在提交后被渲染（父级保证 gateId 有效）

    props:
      - blocks: { label?: string; transcript: string }[] — 各 unit 原文
      - studentId: string
      - gateType: 'exam_attempt' | 'cp_session'
      - gateId: string — attempt_id 或 session_id（已提交/已 result_final）
  -->
  <div class="harvest-panel">
    <div class="panel-header">
      <span class="panel-title">⑤ 词汇采集</span>
      <span class="panel-sub">点击高亮词汇加入你的复习队列</span>
    </div>

    <div v-if="fetchingItems" class="ph-status">加载词库……</div>
    <div v-else-if="fetchError" class="ph-status error">词库加载失败：{{ fetchError }}</div>

    <template v-else>
      <!-- 逐 unit 展示 transcript -->
      <div
        v-for="(block, bi) in blocks"
        :key="bi"
        class="transcript-block"
      >
        <p v-if="block.label" class="block-label">{{ block.label }}</p>
        <p class="transcript-text">
          <template v-for="(tok, ti) in tokenize(block.transcript)" :key="`${bi}-${ti}`">
            <!-- 可采集词 -->
            <button
              v-if="tok.item"
              class="lex-token"
              :class="{
                ready: !harvestedSet.has(tok.item.item_id),
                done:   harvestedSet.has(tok.item.item_id),
                loading: pendingId === tok.item.item_id,
              }"
              :title="tok.item.gloss || tok.item.surface"
              :disabled="pendingId === tok.item.item_id"
              @click="doHarvest(tok.item)"
            >{{ tok.text }}</button>
            <!-- 普通文本 -->
            <span v-else>{{ tok.text }}</span>
          </template>
        </p>
      </div>

      <!-- 采集袋 -->
      <div v-if="harvestedWords.length" class="harvest-bag">
        <p class="bag-title">已加入复习 · {{ harvestedWords.length }} 词</p>
        <div class="chip-row">
          <span v-for="w in harvestedWords" :key="w.item_id" class="word-chip">
            {{ w.surface }}
          </span>
        </div>
      </div>

      <p v-if="!blocks.length || allEmpty" class="ph-status">
        （本套题暂无可用文本）
      </p>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

// ── props ─────────────────────────────────────────────────────────────

interface TranscriptBlock {
  label?: string
  transcript: string
}

const props = defineProps<{
  blocks: TranscriptBlock[]
  studentId: string
  gateType: 'exam_attempt' | 'cp_session'
  gateId: string
}>()

// ── state ─────────────────────────────────────────────────────────────

interface LexItem {
  item_id: string
  layer: string
  surface: string
  gloss: string | null
}

interface Token {
  text: string
  item: LexItem | null
}

const fetchingItems = ref(true)
const fetchError = ref<string | null>(null)
const allItems = ref<LexItem[]>([])
const harvestedSet = ref<Set<string>>(new Set())
const harvestedWords = ref<{ item_id: string; surface: string }[]>([])
const pendingId = ref<string | null>(null)

// 词条匹配正则（最长优先，整词，不区分大小写）
const matchRegex = computed<RegExp | null>(() => {
  if (!allItems.value.length) return null
  const sorted = [...allItems.value].sort(
    (a, b) => b.surface.length - a.surface.length
  )
  const escaped = sorted.map((it) =>
    it.surface.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  )
  return new RegExp(`(${escaped.join('|')})`, 'gi')
})

// 词条表（小写 surface → LexItem）
const itemMap = computed<Map<string, LexItem>>(() => {
  const m = new Map<string, LexItem>()
  for (const it of allItems.value) {
    m.set(it.surface.toLowerCase(), it)
  }
  return m
})

const allEmpty = computed(() =>
  props.blocks.every((b) => !b.transcript.trim())
)

// ── 初始化：获取全量 lex_items ─────────────────────────────────────────

onMounted(async () => {
  try {
    const res = await fetch('/api/listening/lexicon/items')
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const json = await res.json()
    allItems.value = json.data as LexItem[]
  } catch (e: unknown) {
    fetchError.value = e instanceof Error ? e.message : String(e)
  } finally {
    fetchingItems.value = false
  }
})

// ── tokenize：将 transcript 拆成 [text, item|null] 列表 ───────────────

function tokenize(transcript: string): Token[] {
  if (!transcript) return []
  const re = matchRegex.value
  if (!re) return [{ text: transcript, item: null }]

  const tokens: Token[] = []
  let lastIdx = 0
  re.lastIndex = 0

  let m: RegExpExecArray | null
  while ((m = re.exec(transcript)) !== null) {
    if (m.index > lastIdx) {
      tokens.push({ text: transcript.slice(lastIdx, m.index), item: null })
    }
    const surface = m[0]
    const item = itemMap.value.get(surface.toLowerCase()) ?? null
    tokens.push({ text: surface, item })
    lastIdx = re.lastIndex
  }
  if (lastIdx < transcript.length) {
    tokens.push({ text: transcript.slice(lastIdx), item: null })
  }
  return tokens
}

// ── 采集操作 ──────────────────────────────────────────────────────────

async function doHarvest(item: LexItem) {
  if (harvestedSet.value.has(item.item_id)) return
  pendingId.value = item.item_id
  try {
    const res = await fetch('/api/listening/lexicon/harvest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_id: props.studentId,
        item_id: item.item_id,
        gate_type: props.gateType,
        gate_id: props.gateId,
      }),
    })
    if (!res.ok) {
      console.warn('[harvest] blocked', res.status, await res.text())
      return
    }
    const json = await res.json()
    const data = json.data
    if (data.harvested || data.already_tracked) {
      harvestedSet.value = new Set([...harvestedSet.value, item.item_id])
      if (!harvestedWords.value.find((w) => w.item_id === item.item_id)) {
        harvestedWords.value.push({ item_id: item.item_id, surface: item.surface })
      }
    }
  } catch (e) {
    console.error('[harvest] fetch error', e)
  } finally {
    pendingId.value = null
  }
}
</script>

<style scoped>
.harvest-panel {
  margin-top: 36px;
  padding: 24px 28px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 18px;
}

.panel-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 20px;
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  color: rgba(242, 239, 233, 0.92);
}

.panel-sub {
  font-size: 13px;
  color: rgba(242, 239, 233, 0.45);
}

.ph-status {
  font-size: 14px;
  color: rgba(242, 239, 233, 0.45);
  padding: 8px 0;
}

.ph-status.error {
  color: rgba(232, 100, 90, 0.8);
}

.transcript-block {
  margin-bottom: 20px;
}

.block-label {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: rgba(242, 239, 233, 0.35);
  margin: 0 0 8px;
}

.transcript-text {
  font-size: 14px;
  line-height: 1.85;
  color: rgba(242, 239, 233, 0.72);
  margin: 0;
}

/* 可采集词 */
.lex-token {
  display: inline;
  padding: 1px 3px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-size: inherit;
  font-family: inherit;
  line-height: inherit;
  transition: background 0.15s, color 0.15s;
}

.lex-token.ready {
  background: rgba(232, 167, 92, 0.14);
  color: #e8a75c;
}

.lex-token.ready:hover {
  background: rgba(232, 167, 92, 0.28);
}

.lex-token.done {
  background: rgba(100, 200, 140, 0.14);
  color: #64c88c;
  cursor: default;
}

.lex-token.loading {
  opacity: 0.5;
  cursor: wait;
}

/* 采集袋 */
.harvest-bag {
  margin-top: 24px;
  padding-top: 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.07);
}

.bag-title {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: rgba(242, 239, 233, 0.4);
  margin: 0 0 10px;
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.word-chip {
  display: inline-block;
  padding: 3px 10px;
  background: rgba(100, 200, 140, 0.1);
  border: 1px solid rgba(100, 200, 140, 0.25);
  border-radius: 20px;
  font-size: 13px;
  color: #64c88c;
}
</style>
