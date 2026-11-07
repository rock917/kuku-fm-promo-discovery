import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const azureApiUrl = env.VITE_API_URL || 'https://kuku-fm-rg-f4bsfnb0ejcbdkeb.centralindia-01.azurewebsites.net';

  return {
    plugins: [react()],
    define: {
      'import.meta.env.VITE_API_URL': JSON.stringify(azureApiUrl),
    },
    server: {
      port: 3000,
      proxy: {
        '/api': {
          target: azureApiUrl,
          changeOrigin: true,
        },
      },
    },
  };
});
