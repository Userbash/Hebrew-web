import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    chunkSizeWarningLimit: 500,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes('/node_modules/')) return undefined;

          if (id.includes('/node_modules/react/') || id.includes('/node_modules/react-dom/') || id.includes('/node_modules/scheduler/')) {
            return 'react-core';
          }
          if (id.includes('/node_modules/react-router/') || id.includes('/node_modules/react-router-dom/')) {
            return 'router-vendor';
          }
          if (id.includes('/node_modules/@tanstack/react-query/')) {
            return 'query-vendor';
          }
          if (id.includes('/node_modules/react-bootstrap/') || id.includes('/node_modules/bootstrap/')) {
            return 'ui-vendor';
          }
          if (id.includes('/node_modules/lucide-react/')) {
            return 'icons-vendor';
          }
          return 'vendor';
        },
      },
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:3001',
        changeOrigin: true,
      },
    },
  },
})
