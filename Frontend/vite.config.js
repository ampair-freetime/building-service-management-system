import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// Image links from the API are relative (/api/v1/images/...). In production Nginx forwards
// /api to the backend; this does the same for the dev server so <img> works at :5173.
const apiProxyTarget = process.env.DEV_API_PROXY_TARGET ?? 'http://localhost:8000'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': apiProxyTarget,
    },
  },
})
