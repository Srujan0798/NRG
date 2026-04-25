import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const apiProxyTarget = process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/login': {
        target: apiProxyTarget,
        changeOrigin: true
      },
      '/refresh': {
        target: apiProxyTarget,
        changeOrigin: true
      },
      '/logout': {
        target: apiProxyTarget,
        changeOrigin: true
      },
      '/query': {
        target: apiProxyTarget,
        changeOrigin: true
      },
      '/researchers': {
        target: apiProxyTarget,
        changeOrigin: true
      },
      '/health': {
        target: apiProxyTarget,
        changeOrigin: true
      },
      '/stats': {
        target: apiProxyTarget,
        changeOrigin: true
      },
      '/publications': {
        target: apiProxyTarget,
        changeOrigin: true
      },
      '/query/graph': {
        target: apiProxyTarget,
        changeOrigin: true
      },
      '/api/query/stream': {
        target: apiProxyTarget,
        changeOrigin: true,
        ws: true
      },
      '/me/': {
        target: apiProxyTarget,
        changeOrigin: true
      },
      '/consent': {
        target: apiProxyTarget,
        changeOrigin: true
      },
      '/audit/': {
        target: apiProxyTarget,
        changeOrigin: true
      },
      '/health/llm': {
        target: apiProxyTarget,
        changeOrigin: true
      },
      '/health/db': {
        target: apiProxyTarget,
        changeOrigin: true
      },
      '/health/qdrant': {
        target: apiProxyTarget,
        changeOrigin: true
      },
      '/projects': {
        target: apiProxyTarget,
        changeOrigin: true
      },
      '/patents': {
        target: apiProxyTarget,
        changeOrigin: true
      },
      '/collaborations': {
        target: apiProxyTarget,
        changeOrigin: true
      },
      '/funding': {
        target: apiProxyTarget,
        changeOrigin: true
      },
      '/labs': {
        target: apiProxyTarget,
        changeOrigin: true
      },
      '/research-documents': {
        target: apiProxyTarget,
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: '../dist/frontend',
    sourcemap: true,
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom'],
          'vendor-d3': ['d3-force', 'd3-zoom', 'd3-drag', 'd3-selection'],
          'vendor-recharts': ['recharts'],
          'vendor-motion': ['framer-motion'],
        }
      }
    }
  }
})
