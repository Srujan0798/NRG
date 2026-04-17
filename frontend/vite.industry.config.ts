import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  define: {
    'import.meta.env.VITE_PERSONA': JSON.stringify('industry')
  },
  server: {
    port: 3003,
    proxy: {
      '/login': {
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
      }
    }
  },
  build: {
    outDir: '../dist/industry',
    sourcemap: true,
    minify: 'terser',
    rollupOptions: {
      input: 'src/App.tsx'
    }
  }
})
