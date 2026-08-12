import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';
// https://vitejs.dev/config/
export default defineConfig({
    // APP_BASE: 子路径部署时传入(如云端 /llm-cultivation-path/), 默认 '/' 本地零影响
    base: process.env.APP_BASE || '/',
    plugins: [react()],
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src'),
            '@shared': path.resolve(__dirname, '../shared'),
        },
    },
    server: {
        port: 3200,
        proxy: {
            '/api': {
                target: 'http://localhost:4200',
                changeOrigin: true,
            },
        },
    },
});
