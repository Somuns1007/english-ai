<!-- Account registration with password confirmation; successful registration leads to login. -->
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { register, getAuthCapabilities, type AuthCapabilities } from '../../services/authApi'
import EmailCodeField from '../../components/EmailCodeField.vue'
import './auth.css'
import PlanetCanvas from '../../components/PlanetCanvas.vue'

const router = useRouter()
const email = ref('')
const password = ref('')
const confirmation = ref('')
const busy = ref(false)
const error = ref('')
const code = ref('')
const capabilities = ref<AuthCapabilities | null>(null)
onMounted(async () => {
  try { capabilities.value = await getAuthCapabilities() }
  catch { error.value = '无法检查注册服务，请刷新后重试' }
})
async function submit() {
  if (busy.value) return
  error.value = ''
  if (password.value !== confirmation.value) { error.value = '两次输入的密码不一致'; return }
  if (password.value.length < 8 || new TextEncoder().encode(password.value).length > 72) {
    error.value = '密码至少 8 个字符，且 UTF-8 长度不超过 72 字节'; return
  }
  busy.value = true
  try {
    await register(email.value, password.value, capabilities.value?.registration_code_required ? code.value : undefined)
    password.value = confirmation.value = ''
    await router.push({ path: '/login', query: { registered: '1' } })
  } catch (e) { error.value = e instanceof Error ? e.message : '注册失败' }
  finally { busy.value = false }
}
</script>

<template>
  <main class="auth-page"><PlanetCanvas planet="mars" /><section class="auth-card" aria-labelledby="register-title">
    <h1 id="register-title">创建账号</h1><p>使用邮箱注册。密码至少 8 个字符，最多 72 字节。</p>
    <form class="auth-form" @submit.prevent="submit">
      <label for="register-email">邮箱<input id="register-email" v-model="email" type="email" autocomplete="username" maxlength="254" required :disabled="busy" /></label>
      <EmailCodeField v-if="capabilities?.registration_code_required" v-model="code" :email="email" purpose="register" :disabled="busy || !capabilities.email_available" />
      <p v-if="capabilities?.registration_code_required && !capabilities.email_available" class="auth-error">邮件服务尚未配置，暂时无法注册，请联系管理员。</p>
      <label for="register-password">密码<input id="register-password" v-model="password" type="password" autocomplete="new-password" minlength="8" maxlength="72" required :disabled="busy" /></label>
      <label for="register-confirm">确认密码<input id="register-confirm" v-model="confirmation" type="password" autocomplete="new-password" minlength="8" maxlength="72" required :disabled="busy" /></label>
      <p v-if="error" class="auth-error" role="alert">{{ error }}</p>
      <button :disabled="busy || !capabilities || (capabilities.registration_code_required && !capabilities.email_available)" type="submit">{{ busy ? '正在注册…' : '注册' }}</button>
    </form>
    <div class="auth-links"><RouterLink to="/login">已有账号？登录</RouterLink><RouterLink to="/">返回首页</RouterLink></div>
  </section></main>
</template>
