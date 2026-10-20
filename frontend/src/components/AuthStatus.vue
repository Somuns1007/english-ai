<!-- Global account status, independent of the anonymous listening student ID. -->
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { currentUser, getMe, logout } from '../services/authApi'
import { clearTeacherToken } from '../services/listeningApi'

const checking = ref(true)
const busy = ref(false)
const error = ref('')
async function refresh() {
  checking.value = true
  error.value = ''
  try { await getMe() } catch { error.value = '无法获取登录状态' }
  finally { checking.value = false }
}
async function signOut() {
  busy.value = true
  error.value = ''
  try { await logout(); clearTeacherToken() } catch { error.value = '登出失败，请重试' }
  finally { busy.value = false }
}
onMounted(refresh)
</script>

<template>
  <nav class="account-nav" aria-label="账户">
    <RouterLink to="/gallery">图片墙</RouterLink>
    <span v-if="checking" role="status">正在检查登录状态…</span>
    <template v-else-if="currentUser">
      <span class="account-email">{{ currentUser.email }}</span>
      <template v-if="currentUser.role === 'admin'">
        <RouterLink to="/admin/gallery">图片管理</RouterLink>
        <RouterLink to="/listening/teacher/expressions">听力管理</RouterLink>
        <RouterLink to="/listening/teacher/corpus">语料管理</RouterLink>
      </template>
      <button type="button" :disabled="busy" @click="signOut">{{ busy ? '正在登出…' : '登出' }}</button>
    </template>
    <RouterLink v-else to="/login">登录</RouterLink>
    <span v-if="error" role="alert">{{ error }} <button type="button" @click="refresh">重试</button></span>
  </nav>
</template>

<style scoped>
.account-nav { z-index: 2; } /* Stay clickable above the existing homepage's fixed canvas. */
/* 强制深色：全站内容页基本都是硬编码深空底色，不跟随 prefers-color-scheme；
   这里如果继续用 --bg/--text 变量，用户系统是浅色模式时导航条就会变白，和下面的深色页面打架。
   直接写死颜色，不再依赖 --bg/--text。 */
.account-nav { position: relative; display: flex; justify-content: flex-end; align-items: center; flex-wrap: wrap; gap: 12px; padding: 12px 24px; background: #0b0d12; color: #a7a8b1; border-bottom: 1px solid #272a32; font-size: 13px; }
.account-email { overflow-wrap: anywhere; }
a, button { color: var(--accent, #e8b477); border: 1px solid var(--accent-border, #e8b47755); border-radius: 8px; background: var(--accent-bg, #e8b47712); padding: 6px 14px; text-decoration: none; }
</style>
