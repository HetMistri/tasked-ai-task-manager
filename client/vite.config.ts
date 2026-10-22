import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// During local development Vite proxies API calls to the two backend services.
// In Docker, nginx (see nginx.conf) performs the same routing, so the browser
// only ever talks to one origin and never to Docker-internal hostnames.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/ai': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
})