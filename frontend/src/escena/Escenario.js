// Escena principal del juego (Phaser): fondo del lugar, avatar, personaje de la
// historia, objeto de la situacion y animaciones de consecuencias, cierre y final.
import Phaser from 'phaser'
import { avatarUri, npcUri } from '../avatar'
import { codigoEmoji } from '../emoji'
import { dibujarFinal, dibujarFondo, dibujarRuta, emojiProps, estacion, H, W } from './fondos'

const EXTRA = ['🪙', '💸', '✨', '⭐', '🎆', '🎊', '❓', '💳', '🚌', '✈️', '☁️', '🌧️',
  // objetos de cada situacion
  '📋', '👟', '🚲', '🎉', '📈', '🎂', '🏦', '💻', '🏔️', '🐖', '⏱️', '🧾', '📷', '🧮', '🎓', '🚀', '🧺', '🧥', '🔺']
const MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
const FUENTE = 'Bricolage Grotesque Variable, sans-serif'

async function texturaSvg(scene, key, uri, size) {
  if (scene.textures.exists(key)) return key
  const img = new Image()
  img.src = uri
  await img.decode()
  const cv = document.createElement('canvas')
  cv.width = cv.height = size
  cv.getContext('2d').drawImage(img, 0, 0, size, size)
  if (!scene.textures.exists(key)) scene.textures.addCanvas(key, cv)
  return key
}

export default class Escenario extends Phaser.Scene {
  constructor() {
    super('escenario')
    this.actual = {}
    this.pendiente = null
    this.anunciados = new Set()
  }

  preload() {
    for (const e of new Set([...emojiProps(), ...EXTRA])) {
      this.load.svg(`emo-${e}`, `/emoji/${codigoEmoji(e)}.svg`, { width: 160, height: 160 })
    }
  }

  create() {
    const g = this.add.graphics()
    const colores = [0xffc857, 0x0f6e56, 0x378add, 0xe24b4a, 0x7f77dd, 0xff8fb1]
    colores.forEach((c, i) => g.fillStyle(c, 1).fillRect(i * 10, 0, 10, 16))
    g.generateTexture('confeti', 60, 16)
    const tex = this.textures.get('confeti')
    colores.forEach((_, i) => tex.add(i, 0, i * 10, 0, 10, 16))
    g.clear().fillStyle(0xffffff, 1).fillCircle(5, 5, 5); g.generateTexture('copo', 10, 10)
    g.clear().fillStyle(0x9fc4e6, 1).fillRect(0, 0, 3, 18); g.generateTexture('gota', 3, 18)
    g.clear().fillStyle(0xd9822b, 1).fillEllipse(8, 5, 16, 10); g.generateTexture('hoja', 16, 10)
    g.clear().fillStyle(0xffb3c7, 1).fillEllipse(6, 4, 12, 8); g.generateTexture('petalo', 12, 8)
    g.destroy()

    this.capaFondo = this.add.container(0, 0)
    this.capaClima = this.add.container(0, 0)
    this.capaObjeto = this.add.container(0, 0)
    this.capaPersonajes = this.add.container(0, 0)
    this.capaEfectos = this.add.container(0, 0)
    this.capaOverlay = this.add.container(0, 0)

    this.sombraAvatar = this.add.ellipse(215, H - 4, 220, 30, 0x000000, 0.18)
    this.avatar = this.add.image(215, H + 6, '__DEFAULT').setOrigin(0.5, 1).setVisible(false)
    this.sombraNpc = this.add.ellipse(750, H - 4, 200, 26, 0x000000, 0.16).setVisible(false)
    this.npc = this.add.image(750, H + 6, '__DEFAULT').setOrigin(0.5, 1).setFlipX(true).setVisible(false)
    this.etiquetaNpc = this.add.container(730, 140).setVisible(false)
    this.capaPersonajes.add([this.sombraAvatar, this.avatar, this.sombraNpc, this.npc, this.etiquetaNpc])

    this.listo = true
    const p = this.pendiente || this.registry.get('estado')
    if (p) this.aplicar(p)
  }

  /** Recibe el estado completo desde React y aplica solo lo que cambio. */
  aplicar(estado) {
    if (!this.listo) { this.pendiente = estado; return }
    const a = this.actual
    if (estado.modo !== a.modo || estado.lugar !== a.lugar || estado.mes !== a.mes || estado.llego !== a.llego) {
      this.cambiarFondo(estado)
    }
    if (estado.modo === 'escena' && (estado.objeto !== a.objeto || estado.modo !== a.modo)) this.ponerObjeto(estado.objeto)
    if (estado.modo !== 'escena') this.ponerObjeto(null)
    if (estado.personaje !== a.personaje || estado.modo !== a.modo) this.ponerNpc(estado.modo === 'escena' ? estado : {})
    if (estado.avatarConfig !== a.avatarConfig || estado.expresion !== a.expresion) {
      this.ponerAvatar(estado.avatarConfig, estado.expresion, a.expresion && estado.expresion !== a.expresion)
    }
    if (estado.modo === 'ruta' && (a.modo !== 'ruta' || estado.ruta?.mes !== a.ruta?.mes)) this.animarRuta(estado.ruta)
    if (estado.modo === 'final' && a.modo !== 'final') this.animarFinal(estado.final)
    if (estado.anuncioMes && !this.anunciados.has(estado.anuncioMes)) {
      this.anunciados.add(estado.anuncioMes)
      this.anunciarMes(estado.anuncioMes)
    }
    this.actual = { ...estado }
  }

  cambiarFondo(estado) {
    const viejo = this.capaFondo.list.slice()
    let nuevo
    this.capaClima.removeAll(true)
    this.capaOverlay.removeAll(true)
    if (estado.modo === 'ruta') {
      const r = dibujarRuta(this)
      nuevo = r.contenedor
      this.puntosRuta = r.puntos
    } else if (estado.modo === 'final') {
      nuevo = dibujarFinal(this, estado.llego)
    } else {
      nuevo = dibujarFondo(this, estado.lugar, estado.mes)
      this.clima(estado.lugar, estado.mes)
    }
    nuevo.setAlpha(0)
    this.capaFondo.add(nuevo)
    this.tweens.add({ targets: nuevo, alpha: 1, duration: 450, onComplete: () => viejo.forEach((v) => v.destroy()) })
    this.ubicarAvatar(estado.modo)
  }

  ubicarAvatar(modo) {
    this.tweens.killTweensOf(this.avatar)
    const x = modo === 'ruta' ? 110 : modo === 'final' ? W / 2 : 215
    const tam = modo === 'ruta' ? 170 : 310
    this.avatar.setPosition(x, H + 6).setAngle(0)
    if (this.avatar.texture.key !== '__DEFAULT') this.avatar.setDisplaySize(tam, tam)
    this.sombraAvatar.setPosition(x, H - 4).setVisible(modo !== 'ruta')
  }

  clima(lugar, mes) {
    if (!['parada'].includes(lugar)) return
    const est = estacion(mes)
    const tex = { invierno: 'copo', otono: 'hoja', primavera: 'petalo' }[est]
    if (!tex) return
    const e = this.add.particles(0, -20, tex, {
      x: { min: 0, max: W }, lifespan: 7000, speedY: { min: 40, max: 90 }, speedX: { min: -20, max: 20 },
      rotate: { min: 0, max: 360 }, frequency: 220, alpha: { start: 0.9, end: 0.4 },
    })
    this.capaClima.add(e)
  }

  ponerObjeto(e) {
    this.capaObjeto.removeAll(true)
    if (!e || !this.textures.exists(`emo-${e}`)) return
    const halo = this.add.circle(482, 392, 64, 0xffffff, 0.85).setStrokeStyle(4, 0x12343f)
    const img = this.add.image(482, 392, `emo-${e}`).setDisplaySize(92, 92)
    const escala = img.scaleX
    this.capaObjeto.add([halo, img])
    halo.setScale(0); img.setScale(0)
    this.tweens.add({ targets: halo, scale: 1, duration: 380, ease: 'Back.out' })
    this.tweens.add({ targets: img, scale: escala, duration: 420, ease: 'Back.out', delay: 80 })
    this.tweens.add({ targets: [img, halo], y: '-=10', duration: 1500, yoyo: true, repeat: -1, ease: 'Sine.inOut', delay: 500 })
  }

  async ponerNpc({ personaje, personaje_nombre: nombre, personaje_rol: rol }) {
    this.etiquetaNpc.removeAll(true)
    if (!personaje) {
      this.npc.setVisible(false); this.sombraNpc.setVisible(false); this.etiquetaNpc.setVisible(false)
      return
    }
    const key = await texturaSvg(this, `npc-${personaje}`, npcUri(personaje, 'contento'), 560)
    if (this.actual.personaje !== personaje) return
    this.npc.setTexture(key).setDisplaySize(290, 290).setVisible(true).setAlpha(0).setX(800)
    this.sombraNpc.setVisible(true)
    this.tweens.add({ targets: this.npc, alpha: 1, x: 750, duration: 450, ease: 'Cubic.out' })
    const t1 = this.add.text(0, 0, nombre, { fontFamily: FUENTE, fontSize: '26px', fontStyle: '800', color: '#12343f' }).setOrigin(0.5).setResolution(2)
    const t2 = this.add.text(0, 26, rol, { fontFamily: 'Figtree Variable, sans-serif', fontSize: '17px', color: '#4f6670' }).setOrigin(0.5).setResolution(2)
    const ancho = Math.max(t1.width, t2.width) + 36
    const fondo = this.add.graphics().fillStyle(0xffffff, 0.95).fillRoundedRect(-ancho / 2, -22, ancho, 66, 16)
    fondo.lineStyle(3, 0x12343f, 1).strokeRoundedRect(-ancho / 2, -22, ancho, 66, 16)
    this.etiquetaNpc.add([fondo, t1, t2]).setPosition(750, 205).setVisible(true).setAlpha(0)
    this.tweens.add({ targets: this.etiquetaNpc, alpha: 1, y: 192, duration: 400, delay: 250 })
  }

  async ponerAvatar(config, expresion = 'neutral', reaccionar = false) {
    if (!config) return
    const key = await texturaSvg(this, `av-${config}-${expresion}`, avatarUri(config, expresion), 600)
    const tam = this.actual.modo === 'ruta' ? 170 : 310
    this.avatar.setTexture(key).setDisplaySize(tam, tam).setVisible(true)
    if (reaccionar) {
      this.tweens.add({ targets: this.avatar, scaleX: this.avatar.scaleX * 1.08, scaleY: this.avatar.scaleY * 1.08, duration: 160, yoyo: true, ease: 'Quad.out' })
    }
  }

  /** Reaccion del avatar y efectos despues de decidir. */
  reaccion(clasificacion, delta = 0) {
    const x = this.avatar.x
    const y0 = this.avatar.y
    if (clasificacion === 'acertada') {
      this.tweens.add({ targets: this.avatar, y: y0 - 36, duration: 180, yoyo: true, repeat: 1, ease: 'Quad.out', onComplete: () => this.avatar.setY(y0) })
      this.estallido(x, 200, ['✨', '⭐'], 9)
    } else if (clasificacion === 'riesgosa') {
      this.tweens.add({ targets: this.avatar, angle: { from: -5, to: 5 }, duration: 140, yoyo: true, repeat: 2, onComplete: () => this.avatar.setAngle(0) })
      this.estallido(x + 80, 170, ['❓'], 2)
    } else {
      this.cameras.main.shake(260, 0.006)
      this.tweens.add({ targets: this.avatar, x: x + 12, duration: 60, yoyo: true, repeat: 4, onComplete: () => this.avatar.setX(x) })
      this.cameras.main.flash(220, 226, 75, 74, false)
    }
    if (delta > 0) this.monedas(x, '🪙', -1)
    if (delta < 0) this.monedas(x, '💸', 1)
  }

  estallido(x, y, emojis, n) {
    for (let i = 0; i < n; i++) {
      const e = emojis[i % emojis.length]
      const img = this.add.image(x, y, `emo-${e}`).setDisplaySize(34, 34)
      this.capaEfectos.add(img)
      const ang = (Math.PI * 2 * i) / n
      this.tweens.add({ targets: img, x: x + Math.cos(ang) * 150, y: y + Math.sin(ang) * 110, alpha: 0, angle: 180, duration: 900, ease: 'Cubic.out', onComplete: () => img.destroy() })
    }
  }

  monedas(x, e, sentido) {
    for (let i = 0; i < 6; i++) {
      const img = this.add.image(x + (i - 3) * 22, sentido < 0 ? 330 : 250, `emo-${e}`).setDisplaySize(40, 40).setAlpha(0)
      this.capaEfectos.add(img)
      this.tweens.add({ targets: img, alpha: 1, y: img.y + sentido * 120 - 40, x: img.x + (sentido > 0 ? 60 : -30), duration: 900, delay: i * 70, ease: 'Quad.out', onComplete: () => this.tweens.add({ targets: img, alpha: 0, duration: 250, onComplete: () => img.destroy() }) })
    }
  }

  anunciarMes(mes) {
    const c = this.add.container(W / 2, -200)
    const g = this.add.graphics()
    g.fillStyle(0x000000, 0.15).fillRoundedRect(-150, -96, 300, 210, 22)
    g.fillStyle(0xffffff, 1).fillRoundedRect(-156, -104, 300, 210, 22)
    g.fillStyle(0xe24b4a, 1).fillRoundedRect(-156, -104, 300, 62, { tl: 22, tr: 22, bl: 0, br: 0 })
    g.fillStyle(0x12343f, 1).fillCircle(-96, -104, 9).fillCircle(84, -104, 9)
    const t1 = this.add.text(-6, -73, `Mes ${mes} de 12`, { fontFamily: FUENTE, fontSize: '26px', fontStyle: '800', color: '#ffffff' }).setOrigin(0.5).setResolution(2)
    const t2 = this.add.text(-6, 30, MESES[mes - 1], { fontFamily: FUENTE, fontSize: '50px', fontStyle: '800', color: '#12343f' }).setOrigin(0.5).setResolution(2)
    c.add([g, t1, t2])
    this.capaOverlay.add(c)
    this.tweens.chain({
      targets: c,
      tweens: [
        { y: H / 2 - 20, angle: { from: -8, to: 2 }, duration: 520, ease: 'Back.out' },
        { angle: 0, duration: 200 },
        { y: H / 2 - 20, duration: 900 },
        { y: -220, alpha: 0, duration: 420, ease: 'Cubic.in', onComplete: () => c.destroy() },
      ],
    })
  }

  animarRuta({ pagadasAntes = 0, pagadas = 0, atrasadas = 0 }) {
    const pts = this.puntosRuta
    if (!pts) return
    const g = this.add.graphics()
    this.capaOverlay.add(g)
    for (let i = 1; i <= 12; i++) {
      const p = pts[i]
      const pagada = i <= pagadas
      const debe = !pagada && i <= pagadas + atrasadas
      g.fillStyle(pagada ? 0x0f6e56 : debe ? 0xe24b4a : 0xffffff, 1).fillCircle(p.x, p.y, 13)
      g.lineStyle(3, debe ? 0xe24b4a : 0x12343f, 1).strokeCircle(p.x, p.y, 13)
    }
    const desde = pts[pagadasAntes]
    const hasta = pts[pagadas]
    const avion = this.add.image(desde.x, desde.y - 34, 'emo-✈️').setDisplaySize(64, 64)
    this.capaOverlay.add(avion)
    if (pagadas > pagadasAntes) {
      this.tweens.add({ targets: avion, x: hasta.x, y: hasta.y - 34, duration: 1300, delay: 300, ease: 'Sine.inOut' })
      this.time.delayedCall(1500, () => this.estallido(hasta.x, hasta.y, ['✨', '⭐'], 6))
    } else {
      this.tweens.add({ targets: avion, angle: { from: -8, to: 8 }, duration: 200, yoyo: true, repeat: 3 })
      const x = this.add.image(pts[pagadas + 1].x, pts[pagadas + 1].y - 40, 'emo-❓').setDisplaySize(44, 44)
      this.capaOverlay.add(x)
    }
  }

  animarFinal({ nivel }) {
    const cx = W / 2
    if (nivel === 'total' || nivel === 'bien' || nivel === 'con_deudas') {
      const cantidad = nivel === 'total' ? 4 : nivel === 'bien' ? 2 : 1
      const e = this.add.particles(0, -20, 'confeti', {
        x: { min: 0, max: W }, lifespan: 4500, speedY: { min: 90, max: 200 }, speedX: { min: -60, max: 60 },
        rotate: { start: 0, end: 540 }, frequency: 90 / cantidad, quantity: cantidad,
        frame: [0, 1, 2, 3, 4, 5],
      })
      this.capaClima.add(e)
      this.tweens.add({ targets: this.avatar, y: H - 24, duration: 300, yoyo: true, repeat: nivel === 'total' ? -1 : 3, ease: 'Quad.out', repeatDelay: 200 })
      const avion = this.add.image(-80, 90, 'emo-✈️').setDisplaySize(80, 80)
      this.capaOverlay.add(avion)
      this.tweens.add({ targets: avion, x: W + 80, y: 50, duration: 4200, repeat: -1, repeatDelay: 1500 })
      if (nivel === 'total') {
        for (let i = 0; i < 3; i++) this.time.addEvent({ delay: 700 + i * 900, loop: true, callback: () => this.estallido(150 + Math.random() * 660, 90 + Math.random() * 120, ['🎆', '✨', '⭐'], 8) })
      }
      if (nivel === 'con_deudas') {
        const nube = this.add.image(cx + 120, 120, 'emo-☁️').setDisplaySize(110, 110)
        const tarjeta = this.add.image(cx + 120, 125, 'emo-💳').setDisplaySize(44, 44)
        this.capaOverlay.add([nube, tarjeta])
        this.tweens.add({ targets: [nube, tarjeta], x: '+=16', duration: 1800, yoyo: true, repeat: -1, ease: 'Sine.inOut' })
      }
    } else {
      const lluvia = this.add.particles(0, -20, 'gota', {
        x: { min: 0, max: W }, lifespan: 1800, speedY: { min: 420, max: 560 }, speedX: -40,
        frequency: nivel === 'lejos' ? 10 : 25, alpha: 0.7,
      })
      this.capaClima.add(lluvia)
      const bus = this.add.image(560, 200, 'emo-🚌').setDisplaySize(130, 130).setFlipX(true)
      const cartel = this.add.text(560, 120, 'Bariloche', { fontFamily: FUENTE, fontSize: '22px', fontStyle: '800', color: '#ffffff' }).setOrigin(0.5).setResolution(2)
      this.capaOverlay.add([bus, cartel])
      this.tweens.add({ targets: [bus, cartel], x: '+=260', alpha: 0.2, duration: 5000, ease: 'Sine.in' })
      this.tweens.add({ targets: this.avatar, angle: -3, y: H + 20, duration: 1800, yoyo: true, repeat: -1, ease: 'Sine.inOut' })
    }
  }
}
