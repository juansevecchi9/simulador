import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@fontsource-variable/baloo-2'
import '@fontsource-variable/lexend'
import './index.css'
import App from './App.jsx'

// Las escenas de Phaser dibujan texto en un lienzo: cargamos las fuentes antes de empezar.
const fuentes = Promise.all([
  document.fonts?.load('800 24px "Baloo 2 Variable"'),
  document.fonts?.load('400 16px "Lexend Variable"'),
  document.fonts?.load('700 16px "Lexend Variable"'),
]).catch(() => {})
Promise.race([fuentes, new Promise((r) => setTimeout(r, 1500))]).then(() => {
  createRoot(document.getElementById('root')).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
})
