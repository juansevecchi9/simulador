import { useEffect, useRef, useState } from 'react'
import { pesos } from './api'
import { Emo } from './emoji'

const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']
export const nombreMes = (m) => MESES[(m - 1) % 12]
export const NombreMes = (m) => nombreMes(m).charAt(0).toUpperCase() + nombreMes(m).slice(1)

/** Numero que se anima hasta su nuevo valor. */
export function useAnimado(valor, ms = 900) {
  const [v, setV] = useState(valor)
  const desde = useRef(valor)
  useEffect(() => {
    const ini = desde.current
    if (ini === valor) return
    const reduce = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    if (reduce) { setV(valor); desde.current = valor; return }
    const t0 = performance.now()
    let raf
    const paso = (t) => {
      const k = Math.min(1, (t - t0) / ms)
      const e = 1 - Math.pow(1 - k, 3)
      setV(ini + (valor - ini) * e)
      if (k < 1) raf = requestAnimationFrame(paso)
      else desde.current = valor
    }
    raf = requestAnimationFrame(paso)
    return () => { cancelAnimationFrame(raf); desde.current = valor }
  }, [valor, ms])
  return v
}

function Cambio({ antes, despues, formato }) {
  if (antes == null) return null
  const d = Math.round(despues - antes)
  if (!d) return null
  return <span key={despues} className={`cambio ${d > 0 ? 'sube' : 'baja'}`}>{d > 0 ? '+' : ''}{formato(d)}</span>
}

/** Encabezado con la economia del juego: cada dato con su propio grafico. */
export function Encabezado({ economia, mes, pagadas, atrasadas, onHistorial, hayHistorial }) {
  return (
    <header className="topbar">
      <div className="calendario" aria-label={`Mes ${mes} de 12`}>
        <span className="cal-arriba">Mes {mes}/12</span>
        <b>{NombreMes(mes).slice(0, 3)}</b>
      </div>
      <div className="mini-ruta" aria-label={`${pagadas} de 12 cuotas del viaje pagadas`}>
        <Emo e="🏠" size={20} />
        <div className="mini-ruta-tramos">
          {Array.from({ length: 12 }, (_, i) => (
            <i key={i} className={i < pagadas ? 'pagada' : i < pagadas + atrasadas ? 'debe' : i === mes - 1 ? 'hoy' : ''} />
          ))}
        </div>
        <Emo e="🏔️" size={22} />
      </div>
      <div className="chips">
        <div className="chip chip-inflacion" title="Los precios suben todos los meses: la plata guardada sin rendir compra cada vez menos.">
          <Emo e="🏷️" size={22} />
          <span><small>Precios</small><b>+{economia.inflacion_mensual_pct}% <em>por mes</em></b></span>
          <svg className="flecha-sube" viewBox="0 0 24 24" aria-hidden="true"><path d="M3 18 L10 11 L14 14 L21 6" /><path d="M15 6 H21 V12" /></svg>
        </div>
        <div className="chip chip-dolar" title="El dólar sube 1% por mes: menos que los precios.">
          <Emo e="💵" size={22} />
          <span><small>Dólar</small><b>+{economia.suba_dolar_mensual_pct}% <em>por mes</em></b></span>
        </div>
        <div className="chip chip-cuota" title="Cada mes, al cierre, se paga la cuota del viaje si te alcanza la plata.">
          <Emo e="✈️" size={22} />
          <span><small>Cuota del viaje</small><b>{pesos(economia.cuota_viaje)}</b></span>
        </div>
      </div>
      {onHistorial && (
        <button className="btn-historial" onClick={onHistorial} disabled={!hayHistorial}>
          <Emo e="📖" size={20} /><span>Mis decisiones</span>
        </button>
      )}
    </header>
  )
}

/** Indicadores del alumno (HU-005): patrimonio, viaje, criterio y plata para la cuota. */
export function Hud({ barras, antes, economia }) {
  const pn = useAnimado(barras.patrimonio_neto)
  const cr = useAnimado(barras.criterio_financiero_pct)
  const ef = useAnimado(barras.efectivo)
  const necesita = economia.cuota_viaje * (1 + (barras.cuotas_atrasadas || 0))
  const fraccionPn = Math.max(-1, Math.min(1, pn / 400000))
  const alcanza = barras.efectivo >= necesita
  return (
    <div className="hud" role="group" aria-label="Tus indicadores">
      <div className={`hud-tile t-patrimonio ${pn < 0 ? 'negativo' : ''}`}>
        <div className="hud-cab"><Emo e="💰" size={20} /><span>Patrimonio neto</span><Cambio antes={antes?.patrimonio_neto} despues={barras.patrimonio_neto} formato={pesos} /></div>
        <b className="hud-valor">{pesos(pn)}</b>
        <div className="barra-cero" aria-hidden="true">
          <i className="cero" />
          <i className="relleno" style={fraccionPn >= 0 ? { left: '33.3%', width: `${fraccionPn * 66.7}%` } : { right: '66.7%', width: `${-fraccionPn * 33.3}%` }} />
        </div>
        <small className="hud-ayuda">Lo que tenés menos lo que debés</small>
      </div>
      <div className="hud-tile t-viaje">
        <div className="hud-cab"><Emo e="✈️" size={20} /><span>Viaje</span><Cambio antes={antes?.avance_viaje_pct} despues={barras.avance_viaje_pct} formato={(d) => `${d}%`} /></div>
        <b className="hud-valor">{barras.cuotas_pagadas}<small>/12 cuotas</small></b>
        <div className="cuotas" aria-hidden="true">
          {Array.from({ length: 12 }, (_, i) => (
            <i key={i} className={i < barras.cuotas_pagadas ? 'pagada' : i < barras.cuotas_pagadas + (barras.cuotas_atrasadas || 0) ? 'debe' : ''} />
          ))}
        </div>
        <small className="hud-ayuda">{barras.cuotas_atrasadas ? `${barras.cuotas_atrasadas} cuota${barras.cuotas_atrasadas > 1 ? 's' : ''} atrasada${barras.cuotas_atrasadas > 1 ? 's' : ''}` : `${Math.round(barras.avance_viaje_pct)}% pagado, seña incluida`}</small>
      </div>
      <div className="hud-tile t-criterio">
        <div className="hud-cab"><Emo e="🧭" size={20} /><span>Criterio financiero</span><Cambio antes={antes?.criterio_financiero_pct} despues={barras.criterio_financiero_pct} formato={(d) => `${d}`} /></div>
        <b className="hud-valor">{Math.round(cr)}<small>/100</small></b>
        <div className="barra" aria-hidden="true"><i className="relleno" style={{ width: `${cr}%` }} /><i className="marca50" /></div>
        <small className="hud-ayuda">Arranca en 50</small>
      </div>
      <div className={`hud-tile t-cuota ${alcanza ? 'alcanza' : 'falta'}`}>
        <div className="hud-cab"><Emo e="🐷" size={20} /><span>Plata para la cuota</span></div>
        <b className="hud-valor">{pesos(ef)}<small> de {pesos(necesita)}</small></b>
        <div className="barra" aria-hidden="true"><i className="relleno" style={{ width: `${Math.min(100, (100 * Math.max(0, ef)) / necesita)}%` }} /></div>
        {barras.deuda > 0
          ? <small className="hud-deuda"><Emo e="💳" size={14} /> Debés {pesos(barras.deuda)}: crece {economia.tasa_deuda_abierta_pct}% por mes</small>
          : <small className="hud-ayuda">{alcanza ? 'Hoy te alcanza para la cuota' : 'Hoy no te alcanza para la cuota'}</small>}
      </div>
    </div>
  )
}

export function Aviso() {
  return (
    <footer className="aviso-fijo">
      <Emo e="ℹ️" size={16} />
      <span>Simulador educativo: no es asesoramiento financiero ni ofrece productos financieros. Personas, bancos, apps y precios son ficticios.</span>
    </footer>
  )
}
