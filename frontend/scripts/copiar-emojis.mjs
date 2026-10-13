// Copia a public/emoji solo los emojis de Twemoji (CC-BY 4.0) que usa el juego:
// los que aparecen en el frontend y en el contenido de los escenarios.
import fs from 'node:fs'
import path from 'node:path'

const raiz = path.resolve(import.meta.dirname, '..')
const fuentes = [
  ...fs.readdirSync(path.join(raiz, 'src'), { recursive: true })
    .filter((f) => /\.(jsx?|css)$/.test(f)).map((f) => path.join(raiz, 'src', f)),
  path.resolve(raiz, '../backend/app/contenido.py'),
]
const re = /\p{Extended_Pictographic}(️|‍\p{Extended_Pictographic}️?)*/gu
const codigo = (e) => {
  let cps = [...e].map((c) => c.codePointAt(0).toString(16))
  if (!cps.includes('200d')) cps = cps.filter((c) => c !== 'fe0f')
  return cps.join('-')
}
const destino = path.join(raiz, 'public', 'emoji')
fs.rmSync(destino, { recursive: true, force: true })
fs.mkdirSync(destino, { recursive: true })
const vistos = new Set()
for (const f of fuentes) for (const m of fs.readFileSync(f, 'utf8').matchAll(re)) vistos.add(codigo(m[0]))
let faltan = []
for (const c of vistos) {
  const origen = path.join(raiz, 'node_modules/@twemoji/svg', `${c}.svg`)
  if (fs.existsSync(origen)) fs.copyFileSync(origen, path.join(destino, `${c}.svg`))
  else faltan.push(c)
}
console.log(`emojis copiados: ${vistos.size - faltan.length}`, faltan.length ? `sin archivo: ${faltan}` : '')
