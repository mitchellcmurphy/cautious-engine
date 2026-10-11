/// <reference types="vitest/config" />
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// FastAPI (uvicorn) default port. Override with API_PROXY_TARGET=http://host:port.
const apiTarget = process.env.API_PROXY_TARGET ?? 'http://localhost:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/quotes': { target: apiTarget, changeOrigin: true },
      '/filings': { target: apiTarget, changeOrigin: true },
      '/portfolio': { target: apiTarget, changeOrigin: true },
      '/recommendations': { target: apiTarget, changeOrigin: true },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
})
