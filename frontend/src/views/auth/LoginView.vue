<!-- Email/password sign-in; the server stores the JWT in an HttpOnly cookie. -->
<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { login } from '../../services/authApi'
import './auth.css'

const route = useRoute()
const router = useRouter()
const email = ref('')
const password = ref('')
const busy = ref(false)
const error = ref('')
async function submit() {
  if (busy.value) return
  busy.value = true
  error.value = ''
  try {
    await login(email.value, password.value)
    password.value = ''
    await router.push('/')
  } catch (e) { error.value = e instanceof Error ? e.message : '登录失败' }
  finally { busy.value = false }
}
</script>

<template>
  <main class="auth-page"><section class="auth-card" aria-labelledby="login-title">
    <h1 id="login-title">欢迎回来</h1><p>登录阿Q的英语自习室，继续今天的学习。</p>
    <p v-if="route.query.registered === '1'" class="auth-success" role="status">注册成功，请登录。</p>
    <form class="auth-form" @submit.prevent="submit">
      <label for="login-email">邮箱<input id="login-email" v-model="email" type="email" autocomplete="username" maxlength="254" required :disabled="busy" /></label>
      <label for="login-password">密码<input id="login-password" v-model="password" type="password" autocomplete="current-password" required :disabled="busy" /></label>
      <p v-if="error" class="auth-error" role="alert">{{ error }}</p>
      <button :disabled="busy" type="submit">{{ busy ? '正在登录…' : '登录' }}</button>
    </form>
    <div class="auth-links"><RouterLink to="/register">还没有账号？注册</RouterLink><RouterLink to="/forgot-password">忘记密码？</RouterLink><RouterLink to="/">返回首页</RouterLink></div>
  </section></main>
</template>
