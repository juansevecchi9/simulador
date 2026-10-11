import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['icon.svg', 'avatar/*.svg'],
      manifest: {
        name: 'Viaje de egresados — Simulador financiero',
        short_name: 'Simulador',
        description: 'Simulador de decisiones financieras para estudiantes de secundaria',
        lang: 'es-AR',
        theme_color: '#0F6E56',
        background_color: '#F4F4F2',
        display: 'standalone',
        start_url: '/',
        icons: [{ src: 'icon.svg', sizes: 'any', type: 'image/svg+xml', purpose: 'any' }],
      },
      workbox: { globPatterns: ['**/*.{js,css,html,svg,woff2}'], maximumFileSizeToCacheInBytes: 4_000_000 },
    }),
  ],
  server: { proxy: { '/api': 'http://127.0.0.1:8000' } },
})
