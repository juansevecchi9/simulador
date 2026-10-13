// Avatares a partir del paquete de arte gratuito Avataaars (Pablo Stanley),
// generados en el navegador con DiceBear: no hace falta descargar imagenes.
import { createAvatar } from '@dicebear/core'
import * as avataaars from '@dicebear/avataaars'

export const PIELES = ['f8d25c', 'fd9841', 'ffdbb4', 'edb98a', 'd08b5b', 'ae5d29', '614335']
export const COLORES_PELO = ['2c1b18', '4a312c', '724133', 'a55728', 'b58143', 'd6b370', 'c93305', 'e8e1e1']
export const COLORES_ROPA = ['262e33', '3c4f5c', '65c9ff', '5199e4', '25557c', 'ff5c5c', 'ff488e', 'a7ffc4', 'ffdeb5', 'ffffb1']
export const PELOS = {
  varon: ['shortFlat', 'shortWaved', 'shortCurly', 'theCaesar', 'theCaesarAndSidePart', 'sides', 'dreads01', 'shaggy', 'frizzle', 'shortRound'],
  mujer: ['straight01', 'longButNotTooLong', 'curly', 'bob', 'bun', 'curvy', 'bigHair', 'miaWallace', 'straightAndStrand', 'fro'],
}
export const ROPAS = ['hoodie', 'shirtCrewNeck', 'graphicShirt', 'collarAndSweater', 'overall', 'shirtVNeck', 'blazerAndShirt']
export const ACCESORIOS = [null, 'round', 'prescription02', 'wayfarers', 'sunglasses']

// Cinco expresiones (HU-008): cambian ojos, cejas y boca.
export const EXPRESIONES = {
  euforico: { eyes: 'happy', eyebrows: 'raisedExcitedNatural', mouth: 'smile' },
  contento: { eyes: 'default', eyebrows: 'defaultNatural', mouth: 'twinkle' },
  neutral: { eyes: 'default', eyebrows: 'flatNatural', mouth: 'serious' },
  preocupado: { eyes: 'side', eyebrows: 'sadConcernedNatural', mouth: 'concerned' },
  triste: { eyes: 'cry', eyebrows: 'sadConcernedNatural', mouth: 'sad' },
}
export const NOMBRE_EXPRESION = {
  euforico: 'Eufórico', contento: 'Contento', neutral: 'Neutral', preocupado: 'Preocupado', triste: 'Triste',
}

export const CONFIG_INICIAL = {
  varon: { base: 'varon', piel: 3, pelo: 0, colorPelo: 0, ropa: 0, colorRopa: 2, accesorio: 0 },
  mujer: { base: 'mujer', piel: 3, pelo: 0, colorPelo: 1, ropa: 0, colorRopa: 6, accesorio: 0 },
}

const CLAVES = ['piel', 'pelo', 'colorPelo', 'ropa', 'colorRopa', 'accesorio']

export function codificar(c) {
  return [c.base, ...CLAVES.map((k) => c[k])].join('.')
}

export function decodificar(texto) {
  const [base, ...nums] = (texto || 'varon').split('.')
  const b = base === 'mujer' ? 'mujer' : 'varon'
  const c = { ...CONFIG_INICIAL[b] }
  CLAVES.forEach((k, i) => { if (nums[i] !== undefined && !Number.isNaN(+nums[i])) c[k] = +nums[i] })
  return c
}

const cache = new Map()

function svg(opciones) {
  const clave = JSON.stringify(opciones)
  if (!cache.has(clave)) {
    cache.set(clave, createAvatar(avataaars, {
      seed: 'viaje', accessoriesProbability: opciones.accessories ? 100 : 0,
      facialHairProbability: opciones.facialHair ? 100 : 0, ...opciones,
    }).toDataUri())
  }
  return cache.get(clave)
}

export function avatarUri(config, expresion = 'neutral') {
  const c = typeof config === 'string' ? decodificar(config) : config
  const e = EXPRESIONES[expresion] || EXPRESIONES.neutral
  const pelos = PELOS[c.base]
  const acc = ACCESORIOS[c.accesorio % ACCESORIOS.length]
  return svg({
    top: [pelos[c.pelo % pelos.length]],
    hairColor: [COLORES_PELO[c.colorPelo % COLORES_PELO.length]],
    skinColor: [PIELES[c.piel % PIELES.length]],
    clothing: [ROPAS[c.ropa % ROPAS.length]],
    clothesColor: [COLORES_ROPA[c.colorRopa % COLORES_ROPA.length]],
    clothingGraphic: ['pizza'],
    ...(acc ? { accessories: [acc], accessoriesColor: ['262e33'] } : {}),
    eyes: [e.eyes], eyebrows: [e.eyebrows], mouth: [e.mouth],
  })
}

// Personajes de la historia (mismo paquete de arte).
const NPC = {
  tano: { top: ['sides'], hairColor: ['e8e1e1'], skinColor: ['edb98a'], facialHair: ['moustacheMagnum'], facialHairColor: ['e8e1e1'], clothing: ['shirtCrewNeck'], clothesColor: ['ff5c5c'] },
  ruben: { top: ['shortRound'], hairColor: ['4a312c'], skinColor: ['d08b5b'], facialHair: ['beardMedium'], facialHairColor: ['4a312c'], clothing: ['collarAndSweater'], clothesColor: ['25557c'], accessories: ['prescription01'], accessoriesColor: ['262e33'] },
  cami: { top: ['curly'], hairColor: ['a55728'], skinColor: ['ffdbb4'], clothing: ['hoodie'], clothesColor: ['a7ffc4'] },
  nico: { top: ['shaggyMullet'], hairColor: ['2c1b18'], skinColor: ['edb98a'], clothing: ['graphicShirt'], clothingGraphic: ['diamond'], clothesColor: ['262e33'] },
  sofi: { top: ['bob'], hairColor: ['2c1b18'], skinColor: ['ae5d29'], clothing: ['blazerAndShirt'], clothesColor: ['5199e4'] },
  laura: { top: ['straight01'], hairColor: ['b58143'], skinColor: ['ffdbb4'], clothing: ['blazerAndSweater'], clothesColor: ['3c4f5c'], accessories: ['round'], accessoriesColor: ['262e33'] },
  carlitos: { top: ['shortCurly'], hairColor: ['b58143'], skinColor: ['d08b5b'], clothing: ['hoodie'], clothesColor: ['ff5c5c'] },
  flor: { top: ['bigHair'], hairColor: ['c93305'], skinColor: ['edb98a'], clothing: ['shirtVNeck'], clothesColor: ['ff488e'], accessories: ['wayfarers'], accessoriesColor: ['ff488e'] },
}

export function npcUri(clave, expresion = 'contento') {
  const base = NPC[clave]
  if (!base) return null
  const e = EXPRESIONES[expresion]
  return svg({ ...base, eyes: [e.eyes], eyebrows: [e.eyebrows], mouth: [e.mouth] })
}

export const PERSONAJES_NPC = Object.keys(NPC)
