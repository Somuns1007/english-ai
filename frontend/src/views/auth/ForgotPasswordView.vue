<!-- Email-confirmed password recovery; never simulate successful delivery. -->
<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { getAuthCapabilities, resetPassword } from '../../services/authApi'
import EmailCodeField from '../../components/EmailCodeField.vue'
import './auth.css'
import PlanetCanvas from '../../components/PlanetCanvas.vue'
const available = ref(false), checking = ref(true), busy = ref(false)
const email = ref(''), password = ref(''), confirmation = ref(''), code = ref(''), error = ref(''), message = ref('')
onMounted(async () => {
  try { available.value = (await getAuthCapabilities()).email_available }
  catch { error.value = '无法连接服务器，请刷新后重试' }
  finally { checking.value = false }
})
async function submit() {
  if (busy.value || !available.value) return
  error.value = ''
  if (password.value !== confirmation.value) { error.value = '两次输入的密码不一致'; return }
  busy.value = true
  try {
    message.value = (await resetPassword(email.value, password.value, code.value)).message
    password.value = confirmation.value = code.value = ''
  } catch (e) { error.value = e instanceof Error ? e.message : '重置失败，请重新获取验证码' }
  finally { busy.value = false }
}
</script>

<template>
  <main class="auth-page"><PlanetCanvas planet="mars" /><section class="auth-card" aria-labelledby="forgot-title">
    <h1 id="forgot-title">找回密码</h1>
    <p v-if="checking">正在检查邮件服务…</p>
    <p v-else-if="!available">邮件服务尚未开通，请联系管理员重置密码。</p>
    <p v-else>通过注册邮箱验证身份。重置后，其他设备的旧登录状态也会失效。</p>
    <p v-if="error" class="auth-error" role="alert">{{ error }}</p>
    <p v-if="message" class="auth-success" role="status">{{ message }}</p>
    <form v-if="available && !message" class="auth-form" @submit.prevent="submit">
      <label>注册邮箱<input v-model="email" type="email" autocomplete="username" maxlength="254" required :disabled="busy" /></label>
      <EmailCodeField v-model="code" :email="email" purpose="reset" :disabled="busy" />
      <label>新密码<input v-model="password" type="password" autocomplete="new-password" minlength="8" maxlength="72" required :disabled="busy" /></label>
      <label>确认新密码<input v-model="confirmation" type="password" autocomplete="new-password" minlength="8" maxlength="72" required :disabled="busy" /></label>
      <button :disabled="busy">{{ busy ? '正在重置…' : '重置密码' }}</button>
    </form>
    <div class="auth-links"><RouterLink to="/login">返回登录</RouterLink><RouterLink to="/">返回首页</RouterLink></div>
  </section></main>
</template>
