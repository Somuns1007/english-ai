import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      // 本地开发把 /api 代理到 FastAPI; 线上由 Nginx 反代, 不受影响
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
