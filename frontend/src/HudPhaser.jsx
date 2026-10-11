import { useEffect, useRef } from 'react'
import Phaser from 'phaser'
import { pesos } from './api'

const ANCHO = 340
const ALTO = 230
const BARRAS = [
  { clave: 'patrimonio', icono: '$', color: 0x378add, texto: '#0C447C' },
  { clave: 'viaje', icono: '✈', color: 0x7f77dd, texto: '#3C3489' },
  { clave: 'criterio', icono: '◎', color: 0x1d9e75, texto: '#0F6E56' },
]
const ESTADOS = ['tranquilo', 'neutral', 'alerta']

// Escala visual del patrimonio: 0 a 400.000 llena la barra.
const fraccionPatrimonio = (p) => Math.max(0, Math.min(1, p / 400000))

class EscenaHud extends Phaser.Scene {
  constructor() {
    super('hud')
    this.barras = {}
  }

  preload() {
    for (const g of ['varon', 'mujer'])
      for (const s of ESTADOS) this.load.svg(`${g}_${s}`, `/avatar/${g}_${s}.svg`, { width: 96, height: 120 })
  }

  create() {
    this.cameras.main.setBackgroundColor('#DCEEF2')
    BARRAS.forEach((b, i) => {
      const y = 22 + i * 24
      this.add.text(14, y - 9, b.icono, { fontFamily: 'Arial', fontSize: '15px', fontStyle: 'bold', color: b.texto })
      this.add.rectangle(36, y, 210, 9, 0x000000, 0.08).setOrigin(0, 0.5)
      const relleno = this.add.rectangle(36, y, 0, 9, b.color).setOrigin(0, 0.5)
      const valor = this.add.text(326, y - 8, '', { fontFamily: 'Arial', fontSize: '13px', color: b.texto }).setOrigin(1, 0)
      this.barras[b.clave] = { relleno, valor }
    })
    this.add.ellipse(ANCHO / 2, ALTO - 14, 70, 14, 0x000000, 0.12)
    this.avatar = this.add.image(ANCHO / 2, ALTO - 18, 'varon_neutral').setOrigin(0.5, 1)
    // Animacion liviana por codigo (tweens): balanceo y parpadeo, sin archivos extra.
    this.tweens.add({ targets: this.avatar, angle: { from: -2.5, to: 2.5 }, duration: 1400, yoyo: true, repeat: -1, ease: 'Sine.inOut' })
    this.time.addEvent({
      delay: 3200, loop: true,
      callback: () => this.tweens.add({ targets: this.avatar, scaleY: 0.96, duration: 90, yoyo: true }),
    })
    this.listo = true
    const inicial = this.registry.get('datos')
    if (inicial) this.actualizar(inicial)
  }

  actualizar({ barras, avatar, variante }) {
    if (!this.listo) return
    const datos = {
      patrimonio: [fraccionPatrimonio(barras.patrimonio_neto), pesos(barras.patrimonio_neto)],
      viaje: [barras.avance_viaje_pct / 100, `${Math.round(barras.avance_viaje_pct)}%`],
      criterio: [barras.criterio_financiero_pct / 100, `${Math.round(barras.criterio_financiero_pct)}%`],
    }
    for (const [clave, [frac, texto]] of Object.entries(datos)) {
      const b = this.barras[clave]
      this.tweens.add({ targets: b.relleno, width: 210 * Math.max(0, Math.min(1, frac)), duration: 700, ease: 'Cubic.out' })
      b.valor.setText(texto)
    }
    const textura = `${variante || 'varon'}_${avatar || 'neutral'}`
    if (this.avatar.texture.key !== textura) {
      this.avatar.setTexture(textura)
      this.tweens.add({ targets: this.avatar, scale: { from: 0.85, to: 1 }, duration: 350, ease: 'Back.out' })
    }
  }
}

export default function HudPhaser({ barras, avatar, variante }) {
  const contenedor = useRef(null)
  const juego = useRef(null)

  useEffect(() => {
    juego.current = new Phaser.Game({
      type: Phaser.AUTO,
      parent: contenedor.current,
      width: ANCHO,
      height: ALTO,
      transparent: false,
      scene: EscenaHud,
      scale: { mode: Phaser.Scale.FIT, autoCenter: Phaser.Scale.CENTER_HORIZONTALLY },
    })
    return () => juego.current?.destroy(true)
  }, [])

  useEffect(() => {
    const g = juego.current
    if (!g || !barras) return
    const datos = { barras, avatar, variante }
    g.registry.set('datos', datos) // la escena lo lee al terminar de cargar
    const escena = g.scene.keys?.hud
    if (escena?.listo) escena.actualizar(datos)
  }, [barras, avatar, variante])

  return <div className="hud" ref={contenedor} aria-label="Indicadores: patrimonio neto, avance del viaje y criterio financiero" />
}
