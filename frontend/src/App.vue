<script setup lang="ts">
import AuthStatus from './components/AuthStatus.vue'
</script>

<template>
  <AuthStatus />
  <RouterView />
  <footer class="site-footer">
    <a
      href="https://beian.miit.gov.cn/"
      target="_blank"
      rel="noopener noreferrer"
    >浙ICP备2026045018号-2</a>
  </footer>
</template>

<style scoped>
.site-footer {
  position: relative;
  width: 100%;
  padding: 20px 16px;
  border-top: 1px solid var(--border, #272a32);
  background: var(--bg, #0b0d12);
  color: var(--text, #a7a8b1);
  text-align: center;
  font-size: 12px;
  line-height: 1.8;
}

.site-footer a {
  color: inherit;
  text-decoration: none;
}

.site-footer a:hover,
.site-footer a:focus-visible {
  color: var(--accent, #e8b477);
  text-decoration: underline;
}
</style>
