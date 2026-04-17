#!/bin/bash
# Execute in: /Users/roshwinram/Desktop/National-Research-Graph/frontend/
# Target: IITGN Researcher Dashboard

echo "[BETA-1] React Frontend Sovereign Mesh"
# 1. Update Vite to use Kong directly
cat > vite.config.ts << 'EOF'
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
    outDir: '../dist/frontend',
    sourcemap: true,
    minify: 'terser'
  }
})
EOF

# 2. Build production frontend
npm install && npm run build

# 3. Serve with Node (IITGN prefers static serving)
npx serve -s dist -l 3000 &

echo "[BETA-1] Frontend Mesh Live at http://localhost:3000"