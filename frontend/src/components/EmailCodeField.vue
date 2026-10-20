<!-- Shared registration/reset OTP field; server remains authoritative for all quotas. -->
<script setup lang="ts">
import { onBeforeUnmount, ref } from 'vue'
import { sendEmailCode } from '../services/authApi'
const props = defineProps<{ email: string; purpose: 'register' | 'reset'; modelValue: string; disabled?: boolean }>()
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()
const remaining = ref(0), sending = ref(false), error = ref(''), message = ref('')
let timer: ReturnType<typeof setInterval> | undefined
async function send() {
  if (remaining.value || sending.value || props.disabled) return
  error.value = ''; message.value = ''
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(props.email.trim())) { error.value = '请先填写正确的邮箱'; return }
  sending.value = true
  try {
    message.value = (await sendEmailCode(props.email.trim(), props.purpose)).message
    remaining.value = 60
    timer = setInterval(() => { if (--remaining.value <= 0) clearInterval(timer) }, 1000)
  } catch (e) { error.value = e instanceof Error ? e.message : '发送失败，请稍后重试' }
  finally { sending.value = false }
}
onBeforeUnmount(() => clearInterval(timer))
</script>
<template>
  <label>邮箱验证码
    <input :value="modelValue" @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      inputmode="numeric" autocomplete="one-time-code" pattern="[0-9]{6}" maxlength="6" required :disabled="disabled" placeholder="6 位数字，10 分钟有效" />
  </label>
  <button type="button" :disabled="disabled || sending || remaining > 0" @click="send">{{ sending ? '正在发送…' : remaining ? `${remaining} 秒后可重发` : '发送验证码' }}</button>
  <p v-if="error" class="auth-error" role="alert">{{ error }}</p>
  <p v-if="message" class="auth-success" role="status">{{ message }}</p>
</template>
