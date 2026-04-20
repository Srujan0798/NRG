import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/login': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/refresh': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/logout': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/query': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/researchers': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/stats': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/publications': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/query/graph': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/me/': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/consent': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/audit/': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/health/llm': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/health/db': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/health/qdrant': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: '../dist/frontend',
    sourcemap: true,
    minify: 'terser'
  }
})
