import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const apiProxyTarget = process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000'

const deferredAppEntryPlugin = () => ({
  name: 'nrg-deferred-app-entry',
  transformIndexHtml: {
    order: 'post' as const,
    handler(html: string, context: { bundle?: Record<string, unknown> }) {
      const bundle = context.bundle ?? {}
      const appChunk = Object.values(bundle).find((item) => {
        if (!item || typeof item !== 'object' || !('type' in item)) return false
        const chunk = item as { type?: string; facadeModuleId?: string | null; fileName?: string }
        return chunk.type === 'chunk' && chunk.facadeModuleId?.replace(/\\/g, '/').endsWith('/src/main.tsx')
      }) as { fileName?: string } | undefined
      const entry = appChunk?.fileName ? `/${appChunk.fileName}` : '/src/main.tsx'
      return html.replace(/__NRG_APP_ENTRY__/g, entry)
    }
  }
})

export default defineConfig({
  plugins: [react(), deferredAppEntryPlugin()],
  server: {
    port: 3000,
    proxy: {
      '/login': {
        target: apiProxyTarget,
        changeOrigin: true,
        bypass: (req) => req.method === 'GET' ? '/index.html' : undefined,
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
      '/api/telemetry': {
        target: apiProxyTarget,
        changeOrigin: true
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
      input: {
        index: 'index.html',
        app: 'src/main.tsx',
      },
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom', 'react/jsx-runtime', 'react/jsx-dev-runtime'],
          'vendor-d3': ['d3-force', 'd3-zoom', 'd3-drag', 'd3-selection'],
          'vendor-recharts': ['recharts'],
          'vendor-motion': ['framer-motion'],
        }
      }
    }
  }
})
