import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'
import { fileURLToPath, URL } from 'url'

export default defineConfig({
  plugins: [uni()],

  resolve: {
    alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) }
  },

  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `
         /* 引入 uview-plus 必需的主题变量 */
         @import "uview-plus/theme.scss";
       `,
        silenceDeprecations: ['legacy-js-api', 'import']
      }
    }
  },

  /* -------- dev server，代理到医疗AI后端 -------- */
  server: {
    host: '0.0.0.0',
    port: 3000,
    cors: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',  // 使用IPv4地址避免IPv6问题
        changeOrigin: true,
        secure: false,
        ws: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('proxy error', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('Sending Request to the Target:', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
          });
        }
      }
    }
  },

  /* -------- build 拆包 -------- */
  build: {
    target: 'es2015',
    sourcemap: process.env.NODE_ENV === 'development',
    rollupOptions: {
      output: {
        // 只拆 uview，一个即可
        manualChunks: {
          uview: ['uview-plus']
        }
      }
    }
  },

  /* -------- 依赖优化 -------- */
  optimizeDeps: {
    include: ['uview-plus']
  }
})
