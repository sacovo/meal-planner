import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vite.dev/config/
export default defineConfig({
  base: "/static/",
  plugins: [vue()],
  build: {
    manifest: "manifest.json",
    outDir: resolve("./assets"),
    rollupOptions: {
      input: {
        "main": "./src/main.ts"
      }
    }
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test-setup.ts']
  }
})
