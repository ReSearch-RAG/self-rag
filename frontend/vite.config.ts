import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '^/(health|documents|chat|queries)(/|$)': {
        target: 'http://localhost:8009',
        changeOrigin: true,
      },
    },
  },
})
