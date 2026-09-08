// Identity unit tests: compile the actual TypeScript in memory; never touch browser storage.
import { readFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import vm from 'node:vm'
import test from 'node:test'
import assert from 'node:assert/strict'
import ts from 'typescript'
import { computed, readonly, ref } from 'vue'

const require = createRequire(import.meta.url)
const source = readFileSync(new URL('../src/services/listeningEvents.ts', import.meta.url), 'utf8')
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText

function fixture(stored) {
  const account = ref(null)
  const values = new Map(stored ? [['aq_listening_student_id', stored]] : [])
  let writes = 0
  const context = {
    exports: {},
    require(name) {
      if (name === './authApi') return { currentUser: readonly(account) }
      if (name === './listeningApi') return { postBehaviorEvents: () => Promise.resolve() }
      return require(name)
    },
    crypto: { randomUUID: () => '00000000-1111-4222-8333-444444444444' },
    localStorage: {
      getItem: key => values.get(key) ?? null,
      setItem: (key, value) => { writes++; values.set(key, value) },
    },
  }
  vm.runInNewContext(compiled, context)
  return { account, values, getStudentId: context.exports.getStudentId, writes: () => writes }
}

test('existing anonymous ID survives login, account switching and logout', () => {
  const f = fixture('stu_existing')
  const id = computed(() => f.getStudentId())
  assert.equal(id.value, 'stu_existing')
  f.account.value = { id: 'account-a' }
  assert.equal(id.value, 'account-a')
  f.account.value = { id: 'account-b' }
  assert.equal(id.value, 'account-b')
  f.account.value = null
  assert.equal(id.value, 'stu_existing')
  assert.equal(f.writes(), 0)
})

test('new anonymous visitor uses the unchanged persistent ID format', () => {
  const f = fixture()
  assert.equal(f.getStudentId(), 'stu_000000001111')
  assert.equal(f.getStudentId(), 'stu_000000001111')
  assert.equal(f.writes(), 1)
})

test('authenticated visitor does not create or overwrite an anonymous ID', () => {
  const f = fixture()
  f.account.value = { id: 'account-a' }
  assert.equal(f.getStudentId(), 'account-a')
  assert.equal(f.values.size, 0)
  assert.equal(f.writes(), 0)
})
