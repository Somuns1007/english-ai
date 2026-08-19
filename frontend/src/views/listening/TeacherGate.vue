<template>
  <div v-if="!authed" class="gate">
    <div class="gate-card">
      <h2>教师口令</h2>
      <p class="gate-hint">
        教师审核区域需要口令。口令由服务端管理, 不内置于前端。
      </p>
      <input
        v-model="token"
        type="password"
        placeholder="输入教师口令"
        @keyup.enter="verify"
      />
      <button class="gate-btn" :disabled="checking" @click="verify">
        {{ checking ? '验证中……' : '进入' }}
      </button>
      <p v-if="error" class="gate-error">{{ error }}</p>
    </div>
  </div>
  <slot v-else />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import {
  getTeacherToken,
  setTeacherToken,
  clearTeacherToken,
  teacherFetchExpressions
} from '../../services/listeningApi'

const token = ref('')
const checking = ref(false)
const error = ref('')
// sessionStorage 有 token 不代表有效, 仍需一次接口验证
const authed = ref(false)

async function verify() {
  if (!token.value && !getTeacherToken()) return
  checking.value = true
  error.value = ''
  try {
    if (token.value) setTeacherToken(token.value)
    await teacherFetchExpressions()
    authed.value = true
  } catch (e) {
    clearTeacherToken()
    error.value = e instanceof Error ? e.message : '验证失败'
  } finally {
    checking.value = false
  }
}

// 已有会话 token 时自动验证一次
if (getTeacherToken()) verify()
</script>

<style scoped>
.gate {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #06070c;
  color: #f2efe9;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.gate-card {
  width: 340px;
  background: rgba(255, 255, 255, 0.045);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 18px;
  padding: 32px;
  text-align: center;
}

.gate-card h2 { margin: 0 0 10px; }

.gate-hint {
  font-size: 12.5px;
  color: rgba(242, 239, 233, 0.5);
  line-height: 1.7;
}

.gate-card input {
  width: 100%;
  margin-top: 14px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 10px;
  color: #f2efe9;
  padding: 10px 12px;
  font-size: 14px;
  box-sizing: border-box;
}

.gate-btn {
  margin-top: 14px;
  width: 100%;
  border: none;
  border-radius: 10px;
  padding: 11px;
  background: #e8a75c;
  color: #17120c;
  font-weight: 600;
  cursor: pointer;
}

.gate-btn:disabled { opacity: 0.5; }

.gate-error {
  margin-top: 10px;
  font-size: 12.5px;
  color: #e8907a;
}
</style>
