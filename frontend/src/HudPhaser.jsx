// Barras de indicadores del alumno (HU-005) dibujadas y animadas con Phaser.
// El lienzo usa el tamaño real de su contenedor (modo RESIZE), asi los textos
// se ven nitidos y legibles tanto en la computadora como en el celular.
import { useEffect, useRef } from 'react'
import Phaser from 'phaser'
import { pesos } from './api'
import { codigoEmoji } from './emoji'

const FUENTE = '"Baloo 2 Variable", sans-serif'
const TEXTO = '"Lexend Variable", sans-serif'
const C = {
  papel: 0xffffff, niebla: 0xeef4f5, tinta: '#12343f', suave: '#4f6670', borde: 0xcfdfe3,
  azul: 0x378add, violeta: 0x7f77dd, verde: 0x1d9e75, sol: 0xffc857, warn: 0xef9f27, rojo: 0xe24b4a,
}
const ICONOS = ['💰', '✈️', '🧭', '🐷']
const DPR = Math.min(3, window.devicePixelRatio || 1)

class HudEscena extends Phaser.Scene {
  constructor() {
    super('hud')
    this.v = null // valores animados
  }

  preload() {
    for (const e of ICONOS) this.load.svg(`hud-${e}`, `/emoji/${codigoEmoji(e)}.svg`, { width: 64, height: 64 })
  }

  create() {
    this.listo = true
    this.scale.on('resize', () => { this.construir(); this.pintar() })
    const d = this.registry.get('hud')
    if (d) this.actualizar(d)
  }

  actualizar(d) {
    if (!this.listo) return
    const destino = { pn: d.barras.patrimonio_neto, cr: d.barras.criterio_financiero_pct, ef: d.barras.efectivo }
    const nuevo = !this.v
    this.d = d
    if (nuevo) this.v = { ...destino }
    this.construir()
    if (!nuevo) this.tweens.add({ targets: this.v, ...destino, duration: 900, ease: 'Cubic.out', onUpdate: () => this.pintar() })
    else this.pintar()
  }

  texto(x, y, t, tam, color, peso = '700', fuente = TEXTO) {
    return this.add.text(x, y, t, { fontFamily: fuente, fontSize: `${tam}px`, fontStyle: peso, color }).setResolution(DPR)
  }

  construir() {
    if (!this.d) return
    this.children.removeAll(true)
    const W = this.scale.width
    const H = this.scale.height
    const chico = H < 90
    const gap = chico ? 6 : 10
    const tw = (W - gap * 3) / 4
    const pad = chico ? 7 : 12
    const colores = [C.azul, C.violeta, C.verde, C.sol]
    const etiquetas = ['Patrimonio neto', 'Viaje', 'Criterio financiero', 'Plata para la cuota']
    this.tiles = []
    for (let i = 0; i < 4; i++) {
      const x = i * (tw + gap)
      const g = this.add.graphics()
      g.fillStyle(colores[i], 1).fillRoundedRect(x, 0, tw, H, chico ? 12 : 16)
      g.fillStyle(C.papel, 1).fillRoundedRect(x, 0, tw, H - 4, chico ? 12 : 16)
      const ic = chico ? 16 : 20
      this.add.image(x + pad + ic / 2, pad + ic / 2, `hud-${ICONOS[i]}`).setDisplaySize(ic, ic)
      const t = { x, w: tw, pad, chico }
      if (!chico) t.etiqueta = this.texto(x + pad + ic + 6, pad + 2, etiquetas[i], 12, C.suave)
      const yValor = chico ? pad + ic + 2 : pad + ic + 6
      t.valor = this.texto(x + pad, yValor, '', chico ? 14 : 22, C.tinta, '800', FUENTE)
      t.yBarra = chico ? H - 4 - pad - 8 : yValor + 32
      t.hBarra = chico ? 7 : 10
      t.barra = this.add.graphics()
      if (!chico) t.ayuda = this.texto(x + pad, t.yBarra + 16, '', 11, C.suave, '500').setWordWrapWidth(tw - pad * 2)
      t.chip = this.add.container(0, 0)
      this.tiles.push(t)
    }
    this.chips()
  }

  /** Etiqueta con el cambio respecto del paso anterior (+$X, -3...). */
  chips() {
    const { barras: b, antes: a } = this.d
    if (!a) return
    const cambios = [
      [b.patrimonio_neto - a.patrimonio_neto, (n) => pesos(n)],
      [b.avance_viaje_pct - a.avance_viaje_pct, (n) => `${n}%`],
      [b.criterio_financiero_pct - a.criterio_financiero_pct, (n) => `${n}`],
      [null],
    ]
    cambios.forEach(([d, f], i) => {
      const t = this.tiles[i]
      const r = Math.round(d ?? 0)
      if (!r) return
      const sube = r > 0
      const tx = this.texto(0, 0, `${sube ? '+' : ''}${f(r)}`, t.chico ? 10 : 12, sube ? '#1a7a4c' : '#a32d2d', '800').setOrigin(1, 0)
      const fondo = this.add.graphics().fillStyle(sube ? 0xd9f2e3 : 0xfcebeb, 1)
        .fillRoundedRect(-tx.width - 6, -1, tx.width + 12, tx.height + 2, 8)
      t.chip.add([fondo, tx.setX(0)]).setPosition(t.x + t.w - t.pad - 6, t.pad + (t.chico ? 0 : 2))
      t.chip.setScale(0.6).setAlpha(0)
      this.tweens.add({ targets: t.chip, scale: 1, alpha: 1, duration: 380, ease: 'Back.out' })
      if (t.etiqueta && t.etiqueta.x + t.etiqueta.width > t.chip.x - tx.width - 10) t.etiqueta.setText(t.etiqueta.text.split(' ')[0])
    })
  }

  pintar() {
    if (!this.tiles) return
    const { barras: b, economia: e, enCierre } = this.d
    const v = this.v
    const [tP, tV, tC, tQ] = this.tiles
    const ancho = (t) => t.w - t.pad * 2
    const fondoBarra = (t) => t.barra.clear().fillStyle(C.niebla, 1).fillRoundedRect(t.x + t.pad, t.yBarra, ancho(t), t.hBarra, t.hBarra / 2)

    // Patrimonio neto: barra con el cero marcado (negativo hacia la izquierda, en rojo)
    tP.valor.setText(pesos(v.pn)).setColor(v.pn < 0 ? '#c53030' : C.tinta)
    fondoBarra(tP)
    const cero = tP.x + tP.pad + ancho(tP) / 3
    const f = Math.max(-1, Math.min(1, v.pn / 400000))
    if (f >= 0) tP.barra.fillStyle(C.azul, 1).fillRect(cero, tP.yBarra, f * ancho(tP) * 2 / 3, tP.hBarra)
    else tP.barra.fillStyle(C.rojo, 1).fillRect(cero + f * ancho(tP) / 3, tP.yBarra, -f * ancho(tP) / 3, tP.hBarra)
    tP.barra.fillStyle(0x12343f, 0.45).fillRect(cero - 1, tP.yBarra - 2, 2, tP.hBarra + 4)
    tP.ayuda?.setText('Lo que tenés menos lo que debés')

    // Viaje: 12 casilleros, uno por cuota
    const pagadas = b.cuotas_pagadas
    const atrasadas = b.cuotas_atrasadas || 0
    tV.valor.setText(`${pagadas}/12${tV.chico ? '' : ' cuotas'}`)
    tV.barra.clear()
    const seg = (ancho(tV) - 11 * 2) / 12
    for (let i = 0; i < 12; i++) {
      const x = tV.x + tV.pad + i * (seg + 2)
      if (i < pagadas) tV.barra.fillStyle(C.violeta, 1).fillRoundedRect(x, tV.yBarra, seg, tV.hBarra, 2)
      else if (i < pagadas + atrasadas) tV.barra.fillStyle(0xffffff, 1).fillRoundedRect(x, tV.yBarra, seg, tV.hBarra, 2).lineStyle(2, C.rojo, 1).strokeRoundedRect(x + 1, tV.yBarra + 1, seg - 2, tV.hBarra - 2, 2)
      else tV.barra.fillStyle(C.niebla, 1).fillRoundedRect(x, tV.yBarra, seg, tV.hBarra, 2)
    }
    tV.ayuda?.setText(atrasadas ? `${atrasadas} cuota${atrasadas > 1 ? 's' : ''} atrasada${atrasadas > 1 ? 's' : ''}` : `${Math.round(b.avance_viaje_pct)}% pagado, seña incluida`).setColor(atrasadas ? '#a32d2d' : C.suave)

    // Criterio financiero: 0 a 100, con la marca del 50 inicial
    tC.valor.setText(`${Math.round(v.cr)}/100`)
    fondoBarra(tC)
    tC.barra.fillStyle(C.verde, 1).fillRoundedRect(tC.x + tC.pad, tC.yBarra, Math.max(tC.hBarra, ancho(tC) * v.cr / 100), tC.hBarra, tC.hBarra / 2)
    tC.barra.fillStyle(0x12343f, 0.35).fillRect(tC.x + tC.pad + ancho(tC) / 2 - 1, tC.yBarra - 2, 2, tC.hBarra + 4)
    tC.ayuda?.setText('Arranca en 50')

    // Plata para la cuota: efectivo frente a lo que hay que pagar al cierre
    const necesita = e.cuota_viaje * (1 + atrasadas)
    const alcanza = enCierre || b.efectivo >= necesita
    tQ.valor.setText(tQ.chico ? pesos(v.ef) : `${pesos(v.ef)} de ${pesos(necesita)}`).setColor(alcanza ? C.tinta : '#b45309')
    if (!tQ.chico && tQ.valor.width > ancho(tQ)) tQ.valor.setText(pesos(v.ef))
    fondoBarra(tQ)
    const fq = Math.min(1, Math.max(0, v.ef) / necesita)
    if (fq > 0) tQ.barra.fillStyle(alcanza ? C.sol : C.warn, 1).fillRoundedRect(tQ.x + tQ.pad, tQ.yBarra, Math.max(tQ.hBarra, ancho(tQ) * fq), tQ.hBarra, tQ.hBarra / 2)
    if (tQ.ayuda) {
      if (b.deuda > 0) tQ.ayuda.setText(`Debés ${pesos(b.deuda)}: crece ${e.tasa_deuda_abierta_pct}% por mes`).setColor('#a32d2d').setFontStyle('700')
      else tQ.ayuda.setText(enCierre ? 'Antes de cobrar el próximo sueldo' : alcanza ? 'Hoy te alcanza para la cuota' : 'Hoy no te alcanza para la cuota').setColor(C.suave).setFontStyle('500')
    }
  }
}

export default function HudPhaser({ barras, antes, economia, enCierre }) {
  const contenedor = useRef(null)
  const juego = useRef(null)

  useEffect(() => {
    juego.current = new Phaser.Game({
      type: Phaser.AUTO,
      parent: contenedor.current,
      transparent: true,
      scene: HudEscena,
      scale: { mode: Phaser.Scale.RESIZE, width: contenedor.current.clientWidth, height: contenedor.current.clientHeight },
      audio: { noAudio: true },
      banner: false,
    })
    return () => { juego.current?.destroy(true); juego.current = null }
  }, [])

  // Solo se redibuja cuando cambian los datos (no en cada render de React).
  const firma = JSON.stringify({ barras, antes, enCierre })
  useEffect(() => {
    const g = juego.current
    if (!g || !barras) return
    const datos = { barras, antes, economia, enCierre }
    g.registry.set('hud', datos)
    g.scene.keys?.hud?.actualizar(datos)
  }, [firma]) // eslint-disable-line react-hooks/exhaustive-deps

  const b = barras
  return (
    <div className="hud-phaser" ref={contenedor} role="img"
      aria-label={`Patrimonio neto ${pesos(b.patrimonio_neto)}. Viaje: ${b.cuotas_pagadas} de 12 cuotas pagadas. Criterio financiero ${Math.round(b.criterio_financiero_pct)} de 100. Plata para la cuota ${pesos(b.efectivo)}.`} />
  )
}
