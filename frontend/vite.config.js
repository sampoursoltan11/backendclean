import { defineConfig } from 'vite';
import legacy from '@vitejs/plugin-legacy';
import { resolve } from 'path';

export default defineConfig({
  plugins: [
    legacy({
      targets: ['defaults', 'not IE 11']
    })
  ],
  root: '.',
  publicDir: 'assets',
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: true,
    minify: 'terser',
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'enterprise_tra_home_clean.html')
      },
      output: {
        manualChunks: {
          'vendor': ['alpinejs', 'dompurify']
        }
      }
    }
  },
  server: {
    port: 3000,
    open: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, './assets/js'),
      '@css': resolve(__dirname, './assets/css'),
      '@utils': resolve(__dirname, './assets/js/utils'),
      '@services': resolve(__dirname, './assets/js/services'),
      '@components': resolve(__dirname, './assets/js/components'),
      '@stores': resolve(__dirname, './assets/js/stores'),
      '@config': resolve(__dirname, './assets/js/config')
    }
  }
});
