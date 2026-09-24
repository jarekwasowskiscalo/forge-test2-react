import { fileURLToPath, URL } from 'node:url'

import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
  },
  server: {
    port: 5173,
    // The browser only ever talks to :5173, so /api requests stay same-origin
    // in dev exactly as they are in prod. This is what makes CORS middleware
    // unnecessary anywhere in the stack -- if a request is being blocked by
    // CORS, this proxy is misconfigured, not the backend.
    //
    // The target is overridable because Vite also runs inside a container
    // (docker-compose.yml's `frontend` service, used by
    // `scripts/start.sh --development`). There, `localhost` is the container,
    // not the machine running the backend, so compose passes
    // VITE_API_PROXY_TARGET=http://host.docker.internal:8000. On the host the
    // default is correct and nothing needs setting.
    proxy: { '/api': process.env.VITE_API_PROXY_TARGET ?? 'http://localhost:8000' },
  },
  build: {
    // The one coupling point between the two halves: FastAPI serves whatever
    // lands here (app/main.py). Gitignored, never edited by hand.
    outDir: '../app/static',
    emptyOutDir: true,
  },
})
