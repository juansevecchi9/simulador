// Emojis dibujados con Twemoji (CC-BY 4.0) para que se vean igual en cualquier dispositivo.
const RE_INICIO = /^(\p{Extended_Pictographic}(️|‍\p{Extended_Pictographic}️?)*)\s*/u

export function codigoEmoji(e) {
  let cps = [...e].map((c) => c.codePointAt(0).toString(16))
  if (!cps.includes('200d')) cps = cps.filter((c) => c !== 'fe0f')
  return cps.join('-')
}

export const urlEmoji = (e) => `/emoji/${codigoEmoji(e)}.svg`

export function Emo({ e, size = 24, className = '' }) {
  if (!e) return null
  return <img className={`emo ${className}`} src={urlEmoji(e)} alt="" width={size} height={size} draggable="false" />
}

/** Separa el emoji inicial del texto de una opcion: "🐷 Usar..." -> ["🐷", "Usar..."] */
export function separarEmoji(texto) {
  const m = texto.match(RE_INICIO)
  return m ? [m[1], texto.slice(m[0].length)] : [null, texto]
}
