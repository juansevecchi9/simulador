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

export function Aviso() {
  return (
    <footer className="aviso-fijo">
      <Emo e="ℹ️" size={16} />
      <span>Simulador educativo: no es asesoramiento financiero ni ofrece productos financieros. Personas, bancos, apps y precios son ficticios.</span>
    </footer>
  )
}
