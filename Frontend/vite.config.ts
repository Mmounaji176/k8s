import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vitejs.dev/config/

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        sourcemap: true,
      },
    },
    commonjsOptions: {
      include: [/node_modules/],
    },
  },
});