import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const apiProxyTarget = process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000'
const apiTokenHeader = process.env.VITE_API_TOKEN_HEADER || 'Authorization'
const MAX_CHUNK_BYTES = 500 * 1024
const MAX_TOTAL_BYTES = 2 * 1024 * 1024

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

const bundleBudgetPlugin = () => ({
  name: 'nrg-bundle-budget',
  generateBundle(_options: unknown, bundle: Record<string, any>) {
    let totalBytes = 0
    const oversized: string[] = []

    for (const [fileName, item] of Object.entries(bundle)) {
      if (fileName.endsWith('.map')) continue
      const isChunk = item.type === 'chunk'
      const isBudgetedAsset = item.type === 'asset' && /\.css$/.test(fileName)
      if (!isChunk && !isBudgetedAsset) continue

      const size = isChunk
        ? Buffer.byteLength(item.code || '', 'utf8')
        : Buffer.byteLength(String(item.source || ''), 'utf8')

      totalBytes += size
      if (size > MAX_CHUNK_BYTES) oversized.push(`${fileName} ${(size / 1024).toFixed(1)}KB`)
    }

    if (oversized.length > 0 || totalBytes > MAX_TOTAL_BYTES) {
      const totalKb = (totalBytes / 1024).toFixed(1)
      this.error([
        'NRG frontend bundle budget exceeded.',
        oversized.length ? `Oversized chunks: ${oversized.join(', ')}` : null,
        `Total JS/CSS budgeted size: ${totalKb}KB`,
        'Limits: each chunk <=500KB, total <=2048KB',
      ].filter(Boolean).join('\n'))
    }
  }
})

const manualChunks = (id: string) => {
  const normalized = id.replace(/\\/g, '/')
  if (!normalized.includes('/node_modules/')) return undefined
  if (normalized.includes('/node_modules/react/') || normalized.includes('/node_modules/react-dom/') || normalized.includes('/node_modules/scheduler/')) {
    return 'vendor-react'
  }
  if (normalized.includes('/node_modules/framer-motion/')) return 'vendor-motion'
  if (normalized.includes('/node_modules/victory-vendor/')) return 'vendor-victory'
  if (normalized.includes('/node_modules/d3-')) return 'vendor-d3'
  if (normalized.includes('/node_modules/recharts/')) return 'vendor-recharts'
  return undefined
}

export default defineConfig({
  define: {
    __NRG_API_TOKEN_HEADER__: JSON.stringify(apiTokenHeader),
  },
  plugins: [react(), deferredAppEntryPlugin(), bundleBudgetPlugin()],
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
      output: { manualChunks }
    }
  }
})
