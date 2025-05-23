import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current directory.
  // Set the third parameter to '' to load all env regardless of the `VITE_` prefix.
  const env = loadEnv(mode, process.cwd(), '')

  // Use BACKEND_URL from environment variables if available, otherwise use localhost
  const backendUrl = env.BACKEND_URL || 'http://localhost:8000'

  console.log(`Building for ${mode} mode with API URL: ${env.VITE_API_URL || '/api'}`)

  return {
    plugins: [react()],
    define: {
      // Define process.env for backward compatibility
      'process.env': {
        REACT_APP_API_URL: JSON.stringify(env.VITE_API_URL || '/api'),
        NODE_ENV: JSON.stringify(mode),
      },
    },
    server: {
      port: 3000,
      proxy: {
        '/api': {
          target: backendUrl,
          changeOrigin: true,
          secure: false,
          configure: (proxy, _options) => {
            proxy.on('error', (err, _req, _res) => {
              console.log('proxy error', err);
            });
            proxy.on('proxyReq', (_, req, _res) => {
              console.log('Sending Request to the Target:', req.method, req.url);
            });
            proxy.on('proxyRes', (proxyRes, req, _res) => {
              console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
            });
          },
        },
        '/ws': {
          target: backendUrl,
          ws: true,
          changeOrigin: true,
          secure: false,
        }
      }
    },
    build: {
      outDir: 'dist',
      sourcemap: false,
      // Reduce chunk size
      chunkSizeWarningLimit: 1600,
      minify: 'terser',
      terserOptions: {
        compress: {
          drop_console: true,
          drop_debugger: true,
        },
      },
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom'],
            ui: ['framer-motion', '@heroicons/react'],
          },
        },
      },
    },
  }
})