<!-- UI-only password recovery placeholder; no reset request is sent. -->
<script setup lang="ts">
import './auth.css'
</script>

<template>
  <main class="auth-page"><section class="auth-card" aria-labelledby="forgot-title">
    <h1 id="forgot-title">忘记密码</h1><p>请联系管理员重置密码</p>
    <div class="auth-links"><RouterLink to="/login">返回登录</RouterLink><RouterLink to="/">返回首页</RouterLink></div>
  </section></main>
</template>
