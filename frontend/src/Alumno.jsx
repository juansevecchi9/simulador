import { useEffect, useRef, useState } from 'react'
import { api, pesos } from './api'
import HudPhaser from './HudPhaser'

const CLASIF = {
  acertada: { texto: 'Decisión acertada', clase: 'tag-ok' },
  riesgosa: { texto: 'Decisión riesgosa', clase: 'tag-warn' },
  incorrecta: { texto: 'Decisión incorrecta', clase: 'tag-bad' },
}

function Encabezado({ economia, mes }) {
  if (!economia) return null
  return (
    <div className="encabezado">
      <span className="badge-mes">Mes {mes} / 12</span>
      <span>Inflación {economia.inflacion_mensual_pct}% mensual</span>
      <span>Dólar +{economia.suba_dolar_mensual_pct}% mensual</span>
      <span>Cuota viaje {pesos(economia.cuota_viaje)}</span>
    </div>
  )
}

function Leyenda() {
  return (
    <div className="leyenda">
      <span><b>$</b> Patrimonio neto</span><span><b>✈</b> Avance del viaje</span><span><b>◎</b> Criterio financiero</span>
    </div>
  )
}

function Delta({ antes, despues, formato }) {
  const d = Math.round(despues - antes)
  if (!d) return <span className="delta">sin cambios</span>
  return <span className={`delta ${d > 0 ? 'sube' : 'baja'}`}>{d > 0 ? '+' : ''}{formato(d)}</span>
}

export function IngresoAlumno({ onIngreso, volver }) {
  const [dni, setDni] = useState('')
  const [nombre, setNombre] = useState('')
  const [curso, setCurso] = useState('')
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  async function enviar(e) {
    e.preventDefault()
    if (!dni.trim() || !nombre.trim() || !curso.trim()) return setError('Completá DNI, nombre y código de curso.')
    if (!/^\d{7,8}$/.test(dni.trim())) return setError('El DNI tiene que tener 7 u 8 números, sin puntos.')
    setCargando(true)
    try { onIngreso(await api.ingresoAlumno(dni.trim(), nombre.trim(), curso.trim())) } catch (err) { setError(err.message) }
    setCargando(false)
  }

  return (
    <form className="pase" onSubmit={enviar} noValidate>
      <div className="pase-cabecera">
        <span className="pase-marca">Pase de embarque</span>
        <h1>Tu viaje de egresados</h1>
        <p>Si ya empezaste, seguís donde lo dejaste.</p>
      </div>
      <div className="pase-cuerpo">
        <label className="campo campo-ancho">Nombre
          <input value={nombre} onChange={(e) => { setNombre(e.target.value); setError('') }} placeholder="Juana" autoComplete="given-name" />
        </label>
        <label className="campo">DNI
          <input inputMode="numeric" value={dni} onChange={(e) => { setDni(e.target.value); setError('') }} placeholder="45123456" />
        </label>
        <label className="campo">Curso
          <input inputMode="numeric" value={curso} onChange={(e) => { setCurso(e.target.value); setError('') }} placeholder="1001" />
        </label>
      </div>
      <div className="pase-corte" aria-hidden="true" />
      <div className="pase-talon">
        {error && <p className="error">{error}</p>}
        <button className="primario" disabled={cargando}>{cargando ? 'Embarcando…' : 'Empezar a jugar'}</button>
        <button type="button" className="link" onClick={volver}>Volver</button>
      </div>
    </form>
  )
}

export function ElegirPersonaje({ dni, onElegido }) {
  const [error, setError] = useState('')
  async function elegir(v) {
    try { onElegido(await api.elegirPersonaje(dni, v)) } catch (err) { setError(err.message) }
  }
  return (
    <div className="tarjeta">
      <h1>Elegí tu personaje</h1>
      <p className="sub">Te va a acompañar durante los 12 meses y va a reflejar cómo vienen tus finanzas.</p>
      <div className="personajes">
        {['varon', 'mujer'].map((v) => (
          <button key={v} className="personaje" onClick={() => elegir(v)}>
            <img src={`/avatar/${v}_tranquilo.svg`} alt="" width="96" height="120" />
            <span>{v === 'varon' ? 'Varón' : 'Mujer'}</span>
          </button>
        ))}
      </div>
      {error && <p className="error">{error}</p>}
    </div>
  )
}

export function Intro({ vista, onEmpezar }) {
  const e = vista.economia
  return (
    <div className="tarjeta">
      <h1>Tu meta: el viaje de egresados</h1>
      <p>El viaje cuesta <b>{pesos(e.costo_total_viaje)}</b>. Ya pagaste la seña de {pesos(e.sena_viaje)} con tus ahorros,
        y te quedan <b>12 cuotas de {pesos(e.cuota_viaje)}</b>, una por mes.</p>
      <p>Cada mes cobrás tu changa y pagás {pesos(e.gastos_fijos_mensuales)} de gastos fijos. Vas a tomar dos decisiones por mes.
        Al cierre de cada mes, si te alcanza la plata, la cuota se paga sola.</p>
      <p>Tené en cuenta: los precios suben <b>{e.inflacion_mensual_pct}% por mes</b>, el dólar sube <b>{e.suba_dolar_mensual_pct}% por mes</b>,
        y la deuda que dejes sin pagar crece {e.tasa_deuda_abierta_pct}% por mes.</p>
      <Leyenda />
      <p className="aviso">Este simulador es educativo: no brinda asesoramiento financiero real ni recomienda productos financieros.</p>
      <button className="primario" onClick={onEmpezar}>Empezar</button>
    </div>
  )
}

export function Juego({ vistaInicial, onTerminar }) {
  const [vista, setVista] = useState(vistaInicial)
  const [resultado, setResultado] = useState(null)
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState('')
  const inicio = useRef(Date.now())
  const esc = vista.escenario
  const dni = vista.estudiante.dni

  useEffect(() => { inicio.current = Date.now() }, [esc?.escenario_id])

  async function elegir(opcionId) {
    if (enviando) return
    setEnviando(true)
    setError('')
    try {
      const segundos = Math.round((Date.now() - inicio.current) / 1000)
      const r = await api.decidir(dni, opcionId, segundos)
      setResultado(r)
      setVista((v) => ({ ...v, barras: r.barras, avatar: r.avatar }))
    } catch (err) { setError(err.message) }
    setEnviando(false)
  }

  async function continuar() {
    if (resultado.terminado) return onTerminar()
    setVista(await api.estado(dni))
    setResultado(null)
    window.scrollTo(0, 0)
  }

  return (
    <div className="pantalla-juego">
      <Encabezado economia={vista.economia} mes={resultado?.cierre_mes?.mes ?? esc?.mes ?? 12} />
      <HudPhaser barras={vista.barras} avatar={vista.avatar} variante={vista.estudiante.variante_personaje} />
      <Leyenda />
      <div className="contenido">
        {!resultado && esc && (
          <>
            {esc.nota_ingreso && <p className="nota">{esc.nota_ingreso}</p>}
            <div className="globo"><p>{esc.texto_situacion}</p></div>
            <div className="opciones">
              {esc.opciones.map((o) => (
                <button key={o.opcion_id} className="opcion" disabled={enviando} onClick={() => elegir(o.opcion_id)}>
                  <span className="chevron" aria-hidden="true">›</span><span>{o.texto}</span>
                </button>
              ))}
            </div>
            {error && <p className="error">{error}</p>}
          </>
        )}
        {resultado && (
          <>
            <span className={`tag ${CLASIF[resultado.clasificacion].clase}`}>{CLASIF[resultado.clasificacion].texto}</span>
            <div className="globo"><p>{resultado.mensaje}</p></div>
            <div className="cambios">
              <div><span>Patrimonio neto</span><Delta antes={resultado.barras_antes.patrimonio_neto} despues={resultado.barras.patrimonio_neto} formato={pesos} /></div>
              <div><span>Avance del viaje</span><Delta antes={resultado.barras_antes.avance_viaje_pct} despues={resultado.barras.avance_viaje_pct} formato={(d) => `${d}%`} /></div>
              <div><span>Criterio financiero</span><Delta antes={resultado.barras_antes.criterio_financiero_pct} despues={resultado.barras.criterio_financiero_pct} formato={(d) => `${d}%`} /></div>
            </div>
            {resultado.cierre_mes && <CierreMes c={resultado.cierre_mes} />}
            <button className="primario" onClick={continuar}>{resultado.terminado ? 'Ver resumen final' : 'Continuar'}</button>
          </>
        )}
      </div>
    </div>
  )
}

function CierreMes({ c }) {
  return (
    <div className="cierre">
      <b>Cierre del mes {c.mes}</b>
      <ul>
        <li>{c.cuota_del_mes_pagada
          ? `Se pagó la cuota del viaje${c.cuotas_pagadas_en_cierre > 1 ? ` (y ${c.cuotas_pagadas_en_cierre - 1} atrasada${c.cuotas_pagadas_en_cierre > 2 ? 's' : ''})` : ''}.`
          : `No alcanzó la plata para la cuota: quedan ${c.cuotas_atrasadas} cuota${c.cuotas_atrasadas > 1 ? 's' : ''} sin pagar.`}</li>
        {c.interes_deuda > 0 && <li>Tu deuda generó {pesos(c.interes_deuda)} de intereses.</li>}
        {c.perdida_inflacion > 0 && <li>La inflación le quitó {pesos(c.perdida_inflacion)} de valor a tu efectivo guardado.</li>}
      </ul>
    </div>
  )
}

export function Resumen({ dni, variante, onSalir }) {
  const [r, setR] = useState(null)
  useEffect(() => { api.resumen(dni).then(setR) }, [dni])
  if (!r) return <p className="cargando">Cargando…</p>
  return (
    <div className="pantalla-juego">
      <div className="resumen-cabecera">
        <img src={`/avatar/${variante || 'varon'}_${r.avatar}.svg`} alt="" width="88" height="110" />
        <h1>Llegaste al mes 12</h1>
        <p>{r.mensaje}</p>
      </div>
      <div className="contenido">
        <div className="grid2">
          <div className="metrica"><span>Patrimonio neto final</span><b>{pesos(r.barras.patrimonio_neto)}</b></div>
          <div className="metrica"><span>Avance del viaje</span><b>{Math.round(r.barras.avance_viaje_pct)}%</b></div>
          <div className="metrica"><span>Criterio financiero</span><b>{Math.round(r.barras.criterio_financiero_pct)}%</b></div>
          <div className="metrica"><span>Deuda pendiente</span><b>{pesos(r.barras.deuda)}</b></div>
        </div>
        <p className="seccion">Desempeño por eje</p>
        {r.por_eje.map((f) => {
          const t = f.acertadas + f.riesgosas + f.incorrectas || 1
          return (
            <div className="eje-fila" key={f.eje}>
              <span>{f.nombre}</span>
              <div className="barra-apilada" title={`${f.acertadas} acertadas, ${f.riesgosas} riesgosas, ${f.incorrectas} incorrectas`}>
                <i className="ok" style={{ width: `${100 * f.acertadas / t}%` }} />
                <i className="warn" style={{ width: `${100 * f.riesgosas / t}%` }} />
                <i className="bad" style={{ width: `${100 * f.incorrectas / t}%` }} />
              </div>
              <small>{f.acertadas}/{f.riesgosas}/{f.incorrectas}</small>
            </div>
          )
        })}
        <p className="ayuda">Acertadas / riesgosas / incorrectas en las 4 decisiones de cada eje.</p>
        <div className="callout ok"><b>Tu punto más fuerte: {r.punto_fuerte.nombre}</b><p>{r.punto_fuerte.importancia}</p></div>
        <div className="callout warn"><b>El área en la que más te costó decidir bien: {r.punto_debil.nombre}</b><p>{r.punto_debil.importancia}</p></div>
        <button className="link" onClick={onSalir}>Salir</button>
      </div>
    </div>
  )
}
