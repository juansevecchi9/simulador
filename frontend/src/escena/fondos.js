// Fondos ilustrados de cada lugar de la historia, dibujados con Phaser.
// Cambian con la epoca del año (verano, otoño, invierno, primavera).
export const W = 960
export const H = 540
export const PISO = 455

export function estacion(mes) {
  if (mes <= 2 || mes === 12) return 'verano'
  if (mes <= 5) return 'otono'
  if (mes <= 8) return 'invierno'
  return 'primavera'
}

export const CIELOS = {
  verano: [0x6ec3f2, 0xd6f1ff],
  otono: [0xf2b880, 0xfde3c2],
  invierno: [0x9fb6cf, 0xe3ecf5],
  primavera: [0x8fd3ef, 0xe2f7ee],
}

const PROPS_EMOJI = ['🍕', '🔥', '🔧', '🔩', '🚲', '🛞', '🌎', '✈️', '🏔️', '🪴', '🛋️', '📺', '🖼️', '⏰', '📚', '✏️',
  '🛍️', '👗', '👟', '🚏', '🚌', '🌳', '🌲', '🏦', '💳', '🔔', '📱', '💬', '🌞', '🌧️', '❄️', '🍂', '🌸', '🎈', '🎉', '🧳', '🏠', '🗺️', '⛰️', '🌊', '🏫', '🧑‍🍳', '🍳', '☕']

export const emojiProps = () => PROPS_EMOJI

function cielo(g, est, x, y, w, h) {
  const [a, b] = CIELOS[est]
  g.fillGradientStyle(a, a, b, b, 1)
  g.fillRect(x, y, w, h)
}

function ventana(s, c, est, x, y, w, h) {
  const g = s.add.graphics()
  g.fillStyle(0xffffff, 1).fillRoundedRect(x - 10, y - 10, w + 20, h + 20, 10)
  cielo(g, est, x, y, w, h)
  // paisaje por la ventana
  g.fillStyle(est === 'invierno' ? 0xdfe8ef : est === 'otono' ? 0xd99a4e : 0x86c06c, 1)
  g.fillEllipse(x + w * 0.3, y + h, w * 0.9, h * 0.5)
  g.fillEllipse(x + w * 0.85, y + h, w * 0.7, h * 0.35)
  if (est === 'verano') g.fillStyle(0xffd54a, 1).fillCircle(x + w * 0.78, y + h * 0.28, 16)
  g.lineStyle(6, 0xffffff, 1).lineBetween(x + w / 2, y, x + w / 2, y + h).lineBetween(x, y + h / 2, x + w, y + h / 2)
  c.add(g)
  return g
}

function piso(g, color, alto = H - PISO) {
  g.fillStyle(color, 1).fillRect(0, PISO, W, alto)
}

function emoji(s, c, e, x, y, size, ang = 0) {
  const key = `emo-${e}`
  if (!s.textures.exists(key)) return null
  const img = s.add.image(x, y, key).setDisplaySize(size, size).setAngle(ang)
  c.add(img)
  return img
}

function texto(s, c, t, x, y, estilo) {
  const tx = s.add.text(x, y, t, { fontFamily: '"Baloo 2 Variable", sans-serif', fontStyle: '800', ...estilo })
  tx.setResolution(2)
  c.add(tx)
  return tx
}

const DIBUJOS = {
  casa(s, c, est) {
    const g = s.add.graphics(); c.add(g)
    g.fillStyle(0xf6e7d2, 1).fillRect(0, 0, W, PISO)
    g.fillStyle(0xeed9bd, 1); for (let x = 0; x < W; x += 48) g.fillRect(x, 0, 24, PISO)
    piso(g, 0xc58d5c)
    g.fillStyle(0xb47c4c, 1); for (let x = 0; x < W; x += 80) g.fillRect(x, PISO, 2, H - PISO)
    ventana(s, c, est, 380, 70, 220, 160)
    // cuadro con el sueño: Bariloche
    const m = s.add.graphics(); c.add(m)
    m.fillStyle(0x5c3d2e, 1).fillRect(100, 90, 170, 120)
    cielo(m, est, 110, 100, 150, 100)
    m.fillStyle(0x6b8fae, 1).fillTriangle(110, 200, 165, 120, 220, 200)
    m.fillStyle(0xffffff, 1).fillTriangle(150, 142, 165, 120, 180, 142)
    m.fillStyle(0x4f7a9a, 1).fillTriangle(170, 200, 215, 135, 260, 200)
    texto(s, c, 'Bariloche', 185, 216, { fontSize: '16px', color: '#5c3d2e' }).setOrigin(0.5, 0)
    // sillon
    const so = s.add.graphics(); c.add(so)
    so.fillStyle(0x3d7d8f, 1).fillRoundedRect(640, 300, 260, 120, 24)
    so.fillStyle(0x4b93a7, 1).fillRoundedRect(660, 340, 220, 70, 16)
    so.fillStyle(0x2f6574, 1).fillRect(660, 420, 14, 36).fillRect(866, 420, 14, 36)
    emoji(s, c, '🪴', 600, 400, 90)
  },
  pizzeria(s, c) {
    const g = s.add.graphics(); c.add(g)
    g.fillStyle(0xb5533c, 1).fillRect(0, 0, W, PISO)
    g.fillStyle(0xa14732, 1)
    for (let y = 0; y < PISO; y += 28) for (let x = (y / 28) % 2 ? 0 : -30; x < W; x += 60) g.fillRect(x + 2, y + 2, 56, 24)
    // horno
    g.fillStyle(0x7b6a5e, 1).fillRoundedRect(600, 120, 300, 260, { tl: 150, tr: 150, bl: 0, br: 0 })
    g.fillStyle(0x2b1d17, 1).fillRoundedRect(680, 220, 140, 110, { tl: 70, tr: 70, bl: 0, br: 0 })
    g.fillStyle(0xff9b3d, 0.9).fillEllipse(750, 320, 110, 30)
    emoji(s, c, '🔥', 750, 300, 56)
    // cartel de neon
    const n = s.add.graphics(); c.add(n)
    n.fillStyle(0x2b1d17, 0.85).fillRoundedRect(150, 50, 330, 90, 18)
    texto(s, c, 'Don Tano', 230, 66, { fontSize: '44px', color: '#ffd54a' }).setShadow(0, 0, '#ff8a00', 14, true, true)
    emoji(s, c, '🍕', 190, 95, 54)
    // mostrador
    g.fillStyle(0xe9d3b0, 1).fillRect(0, 330, 560, 20)
    g.fillStyle(0x8a5a3b, 1).fillRect(0, 350, 560, PISO - 350)
    piso(g, 0xf2efe8)
    g.fillStyle(0x2d2d2d, 1)
    for (let x = 0; x < W; x += 60) for (let y = PISO; y < H; y += 60) if (((x + y) / 60) % 2) g.fillRect(x, y, 30, 30)
    emoji(s, c, '🍕', 120, 310, 60, -10)
    emoji(s, c, '☕', 480, 310, 46)
  },
  bicicleteria(s, c) {
    const g = s.add.graphics(); c.add(g)
    g.fillStyle(0x4f6d7a, 1).fillRect(0, 0, W, PISO)
    g.fillStyle(0xd9c9a3, 1).fillRoundedRect(80, 60, 360, 200, 10)
    g.fillStyle(0xbfae86, 1)
    for (let x = 100; x < 430; x += 26) for (let y = 80; y < 250; y += 26) g.fillCircle(x, y, 3)
    emoji(s, c, '🔧', 170, 130, 70, 30)
    emoji(s, c, '🔩', 290, 120, 50)
    emoji(s, c, '🛞', 380, 190, 80)
    texto(s, c, 'Bicicletería El Rayo', 520, 70, { fontSize: '30px', color: '#ffd54a' })
    piso(g, 0x39464d)
    emoji(s, c, '🚲', 640, 330, 170)
    emoji(s, c, '🚲', 860, 360, 120)
  },
  agencia(s, c, est) {
    const g = s.add.graphics(); c.add(g)
    g.fillStyle(0xe7f3f8, 1).fillRect(0, 0, W, PISO)
    // afiche grande
    g.fillStyle(0x12343f, 1).fillRoundedRect(90, 50, 380, 240, 14)
    cielo(g, est === 'verano' ? 'invierno' : est, 105, 65, 350, 170)
    g.fillStyle(0x5f86a6, 1).fillTriangle(105, 235, 200, 105, 300, 235)
    g.fillStyle(0xffffff, 1).fillTriangle(175, 140, 200, 105, 225, 140)
    g.fillStyle(0x3f6b8c, 1).fillTriangle(240, 235, 340, 95, 455, 235)
    g.fillStyle(0xffffff, 1).fillTriangle(312, 135, 340, 95, 368, 135)
    g.fillStyle(0x3fa3c9, 1).fillRect(105, 215, 350, 20)
    texto(s, c, 'BARILOCHE', 280, 240, { fontSize: '34px', color: '#ffc857' }).setOrigin(0.5, 0)
    texto(s, c, 'Egresados Sur', 560, 60, { fontSize: '40px', color: '#0f6e56' })
    emoji(s, c, '✈️', 860, 80, 70, -15)
    emoji(s, c, '🌎', 820, 230, 90)
    piso(g, 0xc9dfe6)
    g.fillStyle(0x0f6e56, 1).fillRoundedRect(560, 330, 360, 30, 8)
    g.fillStyle(0x0b5242, 1).fillRect(580, 360, 320, PISO - 360)
    emoji(s, c, '🧳', 600, 300, 64)
  },
  banco(s, c) {
    const g = s.add.graphics(); c.add(g)
    g.fillStyle(0xf1ede4, 1).fillRect(0, 0, W, PISO)
    g.fillStyle(0xe2dccd, 1)
    for (const x of [60, 300, 540, 780]) { g.fillRect(x, 60, 60, PISO - 60); g.fillRect(x - 12, 50, 84, 18) }
    g.fillStyle(0x12343f, 1).fillRoundedRect(330, 70, 300, 70, 12)
    texto(s, c, 'Banco del Sur', 480, 85, { fontSize: '32px', color: '#ffffff' }).setOrigin(0.5, 0)
    g.fillStyle(0xbfd8e0, 0.6).fillRect(160, 200, 640, 120)
    g.lineStyle(4, 0xa8b9bf, 1).strokeRect(160, 200, 640, 120)
    g.fillStyle(0x8f7a5b, 1).fillRect(140, 320, 680, 30)
    g.fillStyle(0x6d5c43, 1).fillRect(140, 350, 680, PISO - 350)
    piso(g, 0xd8d0bd)
    emoji(s, c, '🪴', 900, 400, 90)
    emoji(s, c, '🔔', 470, 300, 40)
  },
  colegio(s, c) {
    const g = s.add.graphics(); c.add(g)
    g.fillStyle(0xf3efd9, 1).fillRect(0, 0, W, PISO)
    g.fillStyle(0x7a5232, 1).fillRoundedRect(190, 50, 580, 250, 8)
    g.fillStyle(0x2f5d47, 1).fillRect(204, 64, 552, 222)
    texto(s, c, '5° A', 240, 85, { fontSize: '40px', color: '#f5f5f0' })
    texto(s, c, 'Viaje de egresados: ¡falta poco!', 240, 150, { fontSize: '30px', color: '#f5f5f0', fontStyle: '600' })
    texto(s, c, '12 cuotas = 1 sueño', 240, 210, { fontSize: '26px', color: '#ffc857', fontStyle: '600' })
    emoji(s, c, '⏰', 860, 90, 70)
    emoji(s, c, '📚', 90, 420, 70)
    piso(g, 0xb98d5f)
    g.fillStyle(0xd7b37d, 1).fillRect(330, 380, 300, 18)
    g.fillStyle(0x6d6d6d, 1).fillRect(345, 398, 10, 57).fillRect(605, 398, 10, 57)
    emoji(s, c, '✏️', 480, 370, 40, 70)
  },
  celular(s, c) {
    const g = s.add.graphics(); c.add(g)
    g.fillGradientStyle(0x5b3fd1, 0x5b3fd1, 0xd96bc4, 0xd96bc4, 1).fillRect(0, 0, W, H)
    g.fillStyle(0xffffff, 0.08)
    for (let i = 0; i < 18; i++) g.fillCircle((i * 157) % W, (i * 97) % H, 30 + (i % 4) * 18)
    // telefono gigante
    g.fillStyle(0x15151c, 1).fillRoundedRect(370, 30, 220, 420, 34)
    g.fillStyle(0xf4f6fb, 1).fillRoundedRect(382, 44, 196, 392, 26)
    g.fillStyle(0x15151c, 1).fillRoundedRect(450, 52, 60, 14, 7)
    for (let i = 0; i < 4; i++) {
      g.fillStyle(i % 2 ? 0xd9f3ea : 0xe3e8ff, 1).fillRoundedRect(396, 84 + i * 82, 168, 66, 14)
      g.fillStyle(0xb6bfd6, 1).fillRect(412, 100 + i * 82, 110, 9).fillRect(412, 118 + i * 82, 80, 9)
    }
    emoji(s, c, '💬', 300, 120, 70, -10)
    emoji(s, c, '🔔', 670, 140, 60, 15)
  },
  shopping(s, c) {
    const g = s.add.graphics(); c.add(g)
    g.fillStyle(0xfdf3e7, 1).fillRect(0, 0, W, PISO)
    const vidrieras = [[40, 0xffd6e0, '👗'], [340, 0xd6ecff, '👟'], [640, 0xe3f7d7, '🛍️']]
    for (const [x, col, e] of vidrieras) {
      g.fillStyle(0x12343f, 1).fillRect(x, 70, 280, 34)
      g.fillStyle(col, 1).fillRect(x, 104, 280, 250)
      g.lineStyle(6, 0xffffff, 1).strokeRect(x, 104, 280, 250)
      emoji(s, c, e, x + 140, 230, 110)
    }
    texto(s, c, 'MODA', 180, 74, { fontSize: '24px', color: '#ffffff' }).setOrigin(0.5, 0)
    texto(s, c, 'DEPORTES', 480, 74, { fontSize: '24px', color: '#ffffff' }).setOrigin(0.5, 0)
    texto(s, c, 'OUTLET', 780, 74, { fontSize: '24px', color: '#ffffff' }).setOrigin(0.5, 0)
    piso(g, 0xe9e1d6)
    g.fillStyle(0xddd3c5, 1); for (let x = 0; x < W; x += 90) g.fillRect(x, PISO, 45, H - PISO)
  },
  parada(s, c, est) {
    const g = s.add.graphics(); c.add(g)
    cielo(g, est, 0, 0, W, PISO)
    if (est === 'verano') g.fillStyle(0xffd54a, 1).fillCircle(820, 90, 40)
    g.fillStyle(0xa8b4c0, 1)
    for (const [x, w, h] of [[0, 160, 260], [170, 120, 200], [300, 180, 300], [500, 140, 230], [650, 170, 280], [830, 130, 210]]) g.fillRect(x, PISO - 60 - h, w, h)
    g.fillStyle(0xdfe6ec, 1)
    for (let x = 20; x < W; x += 46) for (let y = 160; y < 360; y += 50) g.fillRect(x, y, 18, 24)
    g.fillStyle(0x9aa3a8, 1).fillRect(0, PISO - 60, W, 60)
    piso(g, 0x5b6268)
    g.fillStyle(0xffffff, 1); for (let x = 0; x < W; x += 120) g.fillRect(x, PISO + 40, 60, 8)
    emoji(s, c, '🚏', 880, 330, 120)
    emoji(s, c, '🌳', 60, 330, 150)
  },
}

export function dibujarFondo(s, lugar, mes) {
  const c = s.add.container(0, 0)
  ;(DIBUJOS[lugar] || DIBUJOS.casa)(s, c, estacion(mes))
  return c
}

/** Mapa de la ruta del viaje: 12 paradas desde tu casa hasta Bariloche. */
export function dibujarRuta(s) {
  const c = s.add.container(0, 0)
  const g = s.add.graphics(); c.add(g)
  g.fillGradientStyle(0xe6f2e4, 0xe6f2e4, 0xcfe6f2, 0xcfe6f2, 1).fillRect(0, 0, W, H)
  g.fillStyle(0xbfdcb4, 1).fillEllipse(200, 420, 500, 220).fillEllipse(720, 120, 420, 200)
  g.fillStyle(0x9cc3dd, 1).fillEllipse(820, 420, 260, 120)
  const puntos = []
  for (let i = 0; i <= 12; i++) {
    const t = i / 12
    puntos.push({ x: 90 + t * 760, y: 300 + Math.sin(t * Math.PI * 2.2) * 110 })
  }
  g.lineStyle(8, 0xffffff, 1)
  for (let i = 0; i < 12; i++) g.lineBetween(puntos[i].x, puntos[i].y, puntos[i + 1].x, puntos[i + 1].y)
  emoji(s, c, '🏠', puntos[0].x, puntos[0].y - 10, 64)
  emoji(s, c, '🏔️', puntos[12].x + 10, puntos[12].y - 30, 96)
  texto(s, c, 'Bariloche', puntos[12].x + 10, puntos[12].y + 24, { fontSize: '22px', color: '#12343f' }).setOrigin(0.5, 0)
  return { contenedor: c, puntos }
}

/** Destino final: Bariloche (si se completo el viaje) o la casa con lluvia (si no). */
export function dibujarFinal(s, llego) {
  const c = s.add.container(0, 0)
  const g = s.add.graphics(); c.add(g)
  if (llego) {
    g.fillGradientStyle(0x7cc8f2, 0x7cc8f2, 0xe4f6ff, 0xe4f6ff, 1).fillRect(0, 0, W, H)
    g.fillStyle(0xffd54a, 1).fillCircle(820, 90, 46)
    g.fillStyle(0x6f8fae, 1).fillTriangle(-40, 380, 220, 90, 470, 380)
    g.fillStyle(0xffffff, 1).fillTriangle(160, 160, 220, 90, 280, 160)
    g.fillStyle(0x4d7393, 1).fillTriangle(330, 380, 600, 60, 900, 380)
    g.fillStyle(0xffffff, 1).fillTriangle(530, 140, 600, 60, 670, 140)
    g.fillStyle(0x86a6c2, 1).fillTriangle(700, 380, 900, 170, 1100, 380)
    g.fillStyle(0x3aa0c8, 1).fillRect(0, 370, W, 90)
    g.fillStyle(0x6fbf73, 1).fillRect(0, PISO, W, H - PISO)
    for (const x of [60, 140, 860, 920]) emoji(s, c, '🌲', x, 400, 110)
  } else {
    g.fillStyle(0x6d7f8c, 1).fillRect(0, 0, W, PISO)
    g.fillStyle(0xffffff, 1).fillRoundedRect(330, 60, 300, 210, 10)
    g.fillStyle(0x56677a, 1).fillRect(340, 70, 280, 190)
    g.fillStyle(0x3b4a57, 1).fillRect(340, 200, 280, 60)
    g.lineStyle(6, 0xffffff, 1).lineBetween(480, 70, 480, 260)
    piso(g, 0x8a6a4f)
  }
  return c
}
