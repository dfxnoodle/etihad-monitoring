import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  base: '/monitoring/',
  server: {
    proxy: {
      '/monitoring/api': {
        target: {
          socketPath: '/tmp/etihad-monitoring.sock'
        },
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/monitoring\/api/, '/api')
      }
    }
  }
})
