import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api, pesos } from './api'
import {
  ACCESORIOS, avatarUri, CONFIG_INICIAL, codificar, COLORES_PELO, COLORES_ROPA, decodificar, EXPRESIONES,
  NOMBRE_EXPRESION, npcUri, PELOS, PIELES, ROPAS,
} from './avatar'
import { Emo, separarEmoji } from './emoji'
import Escena from './Escena'
import { Aviso, Encabezado, Hud, nombreMes, useAnimado } from './hud'

const SELLO = {
  acertada: { texto: 'Decisión acertada', clase: 'sello-ok', emoji: '✅' },
  riesgosa: { texto: 'Decisión riesgosa', clase: 'sello-warn', emoji: '⚠️' },
  incorrecta: { texto: 'Decisión incorrecta', clase: 'sello-bad', emoji: '❌' },
}

const primerNombre = (n) => (n || '').trim().split(/\s+/)[0].replace(/^./, (c) => c.toUpperCase())

// ------------------------------------------------------------------ ingreso

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

// ------------------------------------------------------------------ personaje (HU-017)

function Muestras({ etiqueta, valores, actual, onElegir, render }) {
  return (
    <fieldset className="muestras">
      <legend>{etiqueta}</legend>
      <div>
        {valores.map((v, i) => (
          <button type="button" key={i} aria-pressed={actual === i} className={actual === i ? 'activa' : ''} onClick={() => onElegir(i)}>
            {render(v, i)}
          </button>
        ))}
      </div>
    </fieldset>
  )
}

export function ElegirPersonaje({ vista, onElegido }) {
  const [c, setC] = useState(() => (vista.estudiante.variante_personaje?.includes('.')
    ? decodificar(vista.estudiante.variante_personaje) : CONFIG_INICIAL.mujer))
  const [error, setError] = useState('')
  const [guardando, setGuardando] = useState(false)
  const set = (k) => (v) => setC((x) => ({ ...x, [k]: v }))
  const nombre = primerNombre(vista.estudiante.nombre)

  async function confirmar() {
    setGuardando(true)
    try { onElegido(await api.elegirPersonaje(vista.estudiante.dni, codificar(c))) } catch (err) { setError(err.message) }
    setGuardando(false)
  }

  const miniatura = (cambio) => <img src={avatarUri({ ...c, ...cambio }, 'contento')} alt="" width="54" height="54" />

  return (
    <div className="personalizar">
      <div className="personalizar-vista">
        <div className="espejo"><img src={avatarUri(c, 'euforico')} alt={`Así se ve ${nombre}`} width="260" height="260" /></div>
        <h1>Así va a viajar {nombre}</h1>
        <p className="sub">Tu personaje cambia de cara según cómo vengan tus finanzas:</p>
        <div className="expresiones">
          {Object.keys(EXPRESIONES).map((e) => (
            <figure key={e}><img src={avatarUri(c, e)} alt="" width="58" height="58" /><figcaption>{NOMBRE_EXPRESION[e]}</figcaption></figure>
          ))}
        </div>
      </div>
      <div className="personalizar-opciones">
        <div className="segmentado" role="group" aria-label="Personaje">
          {['mujer', 'varon'].map((b) => (
            <button key={b} type="button" aria-pressed={c.base === b} className={c.base === b ? 'activa' : ''}
              onClick={() => setC((x) => ({ ...CONFIG_INICIAL[b], piel: x.piel, colorRopa: x.colorRopa }))}>
              {b === 'mujer' ? 'Mujer' : 'Varón'}
            </button>
          ))}
        </div>
        <Muestras etiqueta="Peinado" valores={PELOS[c.base]} actual={c.pelo} onElegir={set('pelo')} render={(_, i) => miniatura({ pelo: i })} />
        <Muestras etiqueta="Color de pelo" valores={COLORES_PELO} actual={c.colorPelo} onElegir={set('colorPelo')} render={(v) => <i className="color" style={{ background: `#${v}` }} />} />
        <Muestras etiqueta="Tono de piel" valores={PIELES} actual={c.piel} onElegir={set('piel')} render={(v) => <i className="color" style={{ background: `#${v}` }} />} />
        <Muestras etiqueta="Ropa" valores={ROPAS} actual={c.ropa} onElegir={set('ropa')} render={(_, i) => miniatura({ ropa: i })} />
        <Muestras etiqueta="Color de ropa" valores={COLORES_ROPA} actual={c.colorRopa} onElegir={set('colorRopa')} render={(v) => <i className="color" style={{ background: `#${v}` }} />} />
        <Muestras etiqueta="Anteojos" valores={ACCESORIOS} actual={c.accesorio} onElegir={set('accesorio')} render={(_, i) => miniatura({ accesorio: i })} />
        {error && <p className="error">{error}</p>}
        <button className="primario" onClick={confirmar} disabled={guardando}>{guardando ? 'Guardando…' : `Viajar con este personaje`}</button>
      </div>
    </div>
  )
}

// ------------------------------------------------------------------ juego

function Dialogo({ escena, texto }) {
  const npc = escena.personaje
  return (
    <div className="dialogo">
      <div className="hablante">
        {npc
          ? <img src={npcUri(npc, 'contento')} alt="" width="52" height="52" />
          : <span className="hablante-lugar"><Emo e="📍" size={24} /></span>}
        <div>
          <b>{npc ? escena.personaje_nombre : escena.lugar_nombre}</b>
          <small>{npc ? escena.personaje_rol : 'Lo que está pasando'}</small>
        </div>
        {npc && escena.lugar_nombre && <span className="lugar-tag"><Emo e="📍" size={14} />{escena.lugar_nombre}</span>}
      </div>
      <p className="globo">{texto}</p>
    </div>
  )
}

function Opciones({ opciones, elegida, deshabilitado, onElegir }) {
  return (
    <div className="opciones" role="list">
      {opciones.map((o) => {
        const [e, t] = separarEmoji(o.texto)
        const estado = elegida == null ? '' : o.opcion_id === elegida ? 'elegida' : 'no-elegida'
        return (
          <button role="listitem" key={o.opcion_id} className={`opcion ${estado}`} disabled={deshabilitado} onClick={() => onElegir?.(o.opcion_id)}>
            <span className="opcion-emoji"><Emo e={e} size={30} /></span>
            <span>{t}</span>
          </button>
        )
      })}
    </div>
  )
}

function ImpactoChip({ emoji, etiqueta, antes, despues, formato, subirEsMalo = false }) {
  const d = Math.round(despues - antes)
  const bueno = subirEsMalo ? d < 0 : d > 0
  return (
    <div className={`impacto ${d === 0 ? '' : bueno ? 'sube' : 'baja'}`}>
      <Emo e={emoji} size={22} />
      <span>{etiqueta}</span>
      <b>{d === 0 ? 'sin cambios' : `${d > 0 ? '+' : ''}${formato(d)}`}</b>
    </div>
  )
}

function Resultado({ r, previo, onContinuar, textoBoton }) {
  const s = SELLO[r.clasificacion]
  return (
    <div className="resultado">
      <div className={`sello ${s.clase}`} role="status">
        <Emo e={s.emoji} size={30} /><span>{s.texto}</span>
      </div>
      <section className="historia">
        <h2><Emo e="🎬" size={22} /> Qué pasó en tu historia</h2>
        <p>{r.consecuencia}</p>
        <div className="impactos">
          <ImpactoChip emoji="💰" etiqueta="Patrimonio neto" antes={r.barras_antes.patrimonio_neto} despues={previo.patrimonio_neto} formato={pesos} />
          <ImpactoChip emoji="🐷" etiqueta="Plata para la cuota" antes={r.barras_antes.efectivo} despues={previo.efectivo} formato={pesos} />
          <ImpactoChip emoji="💳" etiqueta="Deuda" antes={r.barras_antes.deuda} despues={previo.deuda} formato={pesos} subirEsMalo />
          <ImpactoChip emoji="🧭" etiqueta="Criterio financiero" antes={r.barras_antes.criterio_financiero_pct} despues={previo.criterio_financiero_pct} formato={(d) => `${d} pts`} />
        </div>
      </section>
      <section className="porque">
        <h2><Emo e="💡" size={22} /> Por qué</h2>
        <p>{r.explicacion}</p>
      </section>
      <button className="primario" onClick={onContinuar}>{textoBoton}</button>
    </div>
  )
}

/** Barras del cierre del mes, cada paso con su propia animacion. */
function PasoCierre({ visible, emoji, titulo, children, tono }) {
  return (
    <div className={`paso-cierre tono-${tono || 'neutro'} ${visible ? 'visible' : ''}`} aria-hidden={!visible}>
      <span className="paso-icono"><Emo e={emoji} size={30} /></span>
      <div><b>{titulo}</b>{children}</div>
    </div>
  )
}

function BarraAnimada({ desde, hasta, max, clase }) {
  const [w, setW] = useState((100 * Math.max(0, desde)) / max)
  useEffect(() => { const t = setTimeout(() => setW((100 * Math.max(0, hasta)) / max), 250); return () => clearTimeout(t) }, [hasta, max])
  return (
    <div className={`barra-cierre ${clase || ''}`}>
      <i className="fantasma" style={{ width: `${Math.min(100, (100 * Math.max(0, desde)) / max)}%` }} />
      <i className="relleno" style={{ width: `${Math.min(100, w)}%` }} />
    </div>
  )
}

function Cierre({ c, mesSiguiente, onContinuar, terminado }) {
  const [paso, setPaso] = useState(0)
  useEffect(() => {
    const ts = [1, 2, 3, 4].map((n) => setTimeout(() => setPaso(n), n * 1100))
    return () => ts.forEach(clearTimeout)
  }, [])
  const pagadas = c.cuotas_pagadas_en_cierre
  const escalaEf = Math.max(c.efectivo_antes_cuota, c.cuota_viaje, 1)
  const efPostCuota = c.efectivo_antes_cuota - pagadas * c.cuota_viaje
  const ef = useAnimado(paso >= 2 ? c.efectivo_final : efPostCuota)
  const escalaDeuda = Math.max(c.deuda_final, 1)
  return (
    <div className="cierre">
      <h2 className="cierre-titulo"><Emo e="📆" size={28} /> Cierre de {nombreMes(c.mes)}</h2>
      <PasoCierre visible={paso >= 1} emoji="✈️" titulo={c.cuota_del_mes_pagada
        ? `Cuota del viaje pagada${pagadas > 1 ? ` (y ${pagadas - 1} atrasada${pagadas > 2 ? 's' : ''})` : ''}`
        : 'No alcanzó para la cuota del viaje'} tono={c.cuota_del_mes_pagada ? 'ok' : 'bad'}>
        <p>{c.cuota_del_mes_pagada
          ? `Salieron ${pesos(pagadas * c.cuota_viaje)} de tu plata. Ya pagaste ${c.cuotas_pagadas_total} de 12 cuotas.`
          : `Tenías ${pesos(c.efectivo_antes_cuota)} y la cuota es de ${pesos(c.cuota_viaje)}. ${c.cuotas_atrasadas > 1 ? `Quedan ${c.cuotas_atrasadas} cuotas sin pagar: se pagan` : 'Queda 1 cuota sin pagar: se paga'} cuando te alcance.`}</p>
        <BarraAnimada desde={c.efectivo_antes_cuota} hasta={efPostCuota} max={escalaEf} clase="b-cuota" />
      </PasoCierre>
      <PasoCierre visible={paso >= 2} emoji="🏷️" titulo="La inflación achicó tu plata" tono="warn">
        <p>{c.perdida_inflacion > 0
          ? `Los precios subieron 2%: tus ${pesos(efPostCuota)} guardados ahora compran lo que antes compraban ${pesos(c.efectivo_final)}. Perdiste ${pesos(c.perdida_inflacion)} de poder de compra.`
          : 'No tenías plata guardada, así que la inflación no te quitó nada este mes.'}</p>
        <BarraAnimada desde={efPostCuota} hasta={c.efectivo_final} max={escalaEf} clase="b-inflacion" />
        <span className="cifra-viva">{pesos(ef)}</span>
      </PasoCierre>
      <PasoCierre visible={paso >= 3} emoji="💳" titulo={c.deuda_antes_interes > 0 ? 'Tu deuda creció sola' : 'Sin deudas que crezcan'} tono={c.deuda_antes_interes > 0 ? 'bad' : 'ok'}>
        {c.deuda_antes_interes > 0 ? (
          <>
            <p>Debías {pesos(c.deuda_antes_interes)}. Con el {c.tasa_deuda_pct}% de interés de este mes, ahora debés <b>{pesos(c.deuda_final)}</b> (+{pesos(c.interes_deuda)}), aunque no hayas gastado nada nuevo. El mes que viene, el {c.tasa_deuda_pct}% se calcula sobre {pesos(c.deuda_final)}.</p>
            <BarraAnimada desde={c.deuda_antes_interes} hasta={c.deuda_final} max={escalaDeuda} clase="b-deuda" />
          </>
        ) : <p>No tenés tarjeta ni préstamos pendientes: nada te cobra intereses.</p>}
      </PasoCierre>
      <div className={`cierre-acciones ${paso >= 4 ? 'visible' : ''}`}>
        <button className="primario" onClick={onContinuar} disabled={paso < 3}>
          {terminado ? 'Ver cómo terminó el viaje' : `Empezar ${nombreMes(mesSiguiente)}`}
        </button>
      </div>
    </div>
  )
}

function Historial({ items, indice, setIndice, onVolver, textoVolver = 'Volver a la decisión actual' }) {
  const h = items[indice]
  const s = SELLO[h.clasificacion]
  return (
    <div className="historial">
      <div className="historial-nav">
        <button className="secundario" onClick={() => setIndice(indice - 1)} disabled={indice === 0} aria-label="Decisión anterior">◀</button>
        <span>Decisión {h.numero} de 24, {nombreMes(h.mes)}</span>
        <button className="secundario" onClick={() => setIndice(indice + 1)} disabled={indice === items.length - 1} aria-label="Decisión siguiente">▶</button>
      </div>
      <Dialogo escena={h.escena} texto={h.texto_situacion} />
      <Opciones opciones={h.opciones} elegida={h.elegida_id} deshabilitado />
      <div className={`sello sello-chico ${s.clase}`}><Emo e={s.emoji} size={22} /><span>{s.texto}</span></div>
      <section className="historia"><h2><Emo e="🎬" size={22} /> Qué pasó en tu historia</h2><p>{h.consecuencia}</p></section>
      <section className="porque"><h2><Emo e="💡" size={22} /> Por qué</h2><p>{h.explicacion}</p></section>
      <button className="primario" onClick={onVolver}>{textoVolver}</button>
    </div>
  )
}

/** Barras intermedias (antes del cierre) a partir de los datos del cierre del mes. */
function barrasPrevias(r) {
  const c = r.cierre_mes
  if (!c) return r.barras
  const pagadas = c.cuotas_pagadas_total - c.cuotas_pagadas_en_cierre
  const atrasadas = Math.max(0, c.cuotas_atrasadas + c.cuotas_pagadas_en_cierre - 1)
  return {
    ...r.barras,
    efectivo: c.efectivo_antes_cuota,
    deuda: c.deuda_antes_interes,
    patrimonio_neto: c.efectivo_antes_cuota - c.deuda_antes_interes,
    cuotas_pagadas: pagadas,
    cuotas_atrasadas: atrasadas,
    avance_viaje_pct: r.barras_antes.avance_viaje_pct,
  }
}

/** Barras despues del cierre del mes (antes de cobrar el sueldo siguiente). */
function barrasCierre(r) {
  const c = r.cierre_mes
  if (!c) return r.barras
  return {
    ...r.barras,
    efectivo: c.efectivo_final,
    deuda: c.deuda_final,
    patrimonio_neto: c.efectivo_final - c.deuda_final,
    cuotas_pagadas: c.cuotas_pagadas_total,
    cuotas_atrasadas: c.cuotas_atrasadas,
    avance_viaje_pct: c.avance_viaje_pct,
  }
}

export function Juego({ vistaInicial, onTerminar, intro }) {
  const [vista, setVista] = useState(vistaInicial)
  const [fase, setFase] = useState(intro ? 'intro' : 'pregunta')
  const [resultado, setResultado] = useState(null)
  const [enviando, setEnviando] = useState(false)
  const [error, setError] = useState('')
  const [historial, setHistorial] = useState(null)
  const [indiceHist, setIndiceHist] = useState(0)
  const [anuncio, setAnuncio] = useState(vistaInicial.escenario?.mes ?? null)
  const [antesMes, setAntesMes] = useState(null)
  const escenaRef = useRef(null)
  const inicio = useRef(Date.now())
  const panel = useRef(null)
  const esc = vista.escenario
  const dni = vista.estudiante.dni
  const nombre = primerNombre(vista.estudiante.nombre)
  const config = vista.estudiante.variante_personaje

  useEffect(() => { inicio.current = Date.now() }, [esc?.escenario_id])
  useEffect(() => { panel.current?.scrollTo?.({ top: 0, behavior: 'smooth' }) }, [fase, esc?.escenario_id, indiceHist])

  const previo = resultado ? barrasPrevias(resultado) : null
  const barras = fase === 'resultado' ? previo : fase === 'cierre' ? barrasCierre(resultado) : vista.barras
  const barrasAntes = fase === 'resultado' ? resultado.barras_antes : fase === 'cierre' ? previo : fase === 'pregunta' ? antesMes : null
  const expresion = resultado && fase !== 'pregunta' ? resultado.avatar : vista.avatar
  const mesMostrado = fase === 'historial' && historial ? historial[indiceHist].mes : (resultado?.cierre_mes?.mes ?? esc?.mes ?? 12)

  const estadoEscena = useMemo(() => {
    const base = { avatarConfig: config, expresion }
    if (fase === 'cierre' && resultado?.cierre_mes) {
      const c = resultado.cierre_mes
      return { ...base, modo: 'ruta', mes: c.mes, ruta: { mes: c.mes, pagadasAntes: c.cuotas_pagadas_total - c.cuotas_pagadas_en_cierre, pagadas: c.cuotas_pagadas_total, atrasadas: c.cuotas_atrasadas } }
    }
    if (fase === 'intro') return { ...base, modo: 'escena', lugar: 'casa', mes: 1, personaje: 'cami', personaje_nombre: 'Cami', personaje_rol: 'tu mejor amiga del curso', objeto: '✈️' }
    const e = fase === 'historial' && historial ? historial[indiceHist] : esc
    if (!e) return { ...base, modo: 'escena', lugar: 'casa', mes: 12 }
    return { ...base, modo: 'escena', mes: e.mes, ...e.escena, anuncioMes: fase === 'pregunta' ? anuncio : null }
  }, [fase, resultado, historial, indiceHist, esc, config, expresion, anuncio])

  async function elegir(opcionId) {
    if (enviando) return
    setEnviando(true)
    setError('')
    try {
      const segundos = Math.round((Date.now() - inicio.current) / 1000)
      const r = await api.decidir(dni, opcionId, segundos)
      setResultado(r)
      setAntesMes(null)
      setFase('resultado')
      const p = barrasPrevias(r)
      escenaRef.current?.reaccion(r.clasificacion, p.patrimonio_neto - r.barras_antes.patrimonio_neto)
    } catch (err) { setError(err.message) }
    setEnviando(false)
  }

  function avanzar() {
    if (fase === 'resultado' && resultado.cierre_mes) return setFase('cierre')
    if (resultado.terminado) return onTerminar()
    const sig = resultado.siguiente
    setAntesMes(resultado.cierre_mes ? barrasCierre(resultado) : null)
    setVista(sig)
    setResultado(null)
    setFase('pregunta')
    if (sig.escenario && sig.escenario.orden === 1) setAnuncio(sig.escenario.mes)
    setHistorial(null)
  }

  const abrirHistorial = useCallback(async () => {
    try {
      const h = await api.historial(dni)
      if (!h.length) return
      setHistorial(h)
      setIndiceHist(h.length - 1)
      setFase('historial')
    } catch (err) { setError(err.message) }
  }, [dni])

  const pagadas = barras.cuotas_pagadas
  return (
    <div className="pantalla-juego">
      <Encabezado economia={vista.economia} mes={mesMostrado} pagadas={pagadas} atrasadas={barras.cuotas_atrasadas || 0}
        onHistorial={fase === 'pregunta' ? abrirHistorial : null} hayHistorial={vista.decisiones_tomadas > 0} />
      <div className="escenario-col">
        <Escena ref={escenaRef} estado={estadoEscena} />
        <Hud barras={barras} antes={barrasAntes} economia={vista.economia} />
      </div>
      <div className="panel-juego" ref={panel}>
        {fase === 'intro' && (
          <div className="intro">
            <Dialogo escena={{ personaje: 'cami', personaje_nombre: 'Cami', personaje_rol: 'tu mejor amiga del curso', lugar_nombre: 'Tu casa' }}
              texto={`¡${nombre}! Ya pagamos la seña de ${pesos(vista.economia.sena_viaje)} del viaje a Bariloche. Ahora quedan ${vista.economia.cantidad_cuotas} cuotas de ${pesos(vista.economia.cuota_viaje)}, una por mes. ¿Llegamos?`} />
            <ul className="reglas">
              <li><Emo e="🍕" size={26} /><span>Trabajás los fines de semana en la <b>{vista.economia.trabajo.nombre}</b>: cobrás {pesos(vista.economia.ingreso_base_mensual)} por mes y pagás {pesos(vista.economia.gastos_fijos_mensuales)} de gastos fijos.</span></li>
              <li><Emo e="🗓️" size={26} /><span>Cada mes tomás <b>dos decisiones</b>. Al cierre, si te alcanza la plata, la cuota del viaje se paga sola.</span></li>
              <li><Emo e="🏷️" size={26} /><span>Los precios suben <b>{vista.economia.inflacion_mensual_pct}% por mes</b> y el dólar <b>{vista.economia.suba_dolar_mensual_pct}% por mes</b>.</span></li>
              <li><Emo e="💳" size={26} /><span>La deuda que no pagues crece <b>{vista.economia.tasa_deuda_abierta_pct}% por mes</b>, sola.</span></li>
            </ul>
            <button className="primario" onClick={() => setFase('pregunta')}>Arrancar en enero</button>
          </div>
        )}
        {fase === 'pregunta' && esc && (
          <div className="pregunta" key={esc.escenario_id}>
            <div className="paso-num">Decisión {esc.numero} de 24</div>
            {esc.orden === 1 && esc.mes > 1 && (
              <div className="cobro">
                <Emo e="🍕" size={24} />
                <span>Cobraste tu sueldo: <b className="sube">+{pesos(esc.ingreso_del_mes)}</b> y pagaste los gastos fijos: <b className="baja">-{pesos(vista.economia.gastos_fijos_mensuales)}</b></span>
              </div>
            )}
            {esc.nota_ingreso && <div className="cobro cobro-extra"><Emo e="🎁" size={24} /><span>{esc.nota_ingreso}</span></div>}
            <Dialogo escena={esc.escena} texto={esc.texto_situacion} />
            <Opciones opciones={esc.opciones} deshabilitado={enviando} onElegir={elegir} />
            {error && <p className="error">{error}</p>}
          </div>
        )}
        {fase === 'resultado' && resultado && (
          <Resultado r={resultado} previo={previo} onContinuar={avanzar}
            textoBoton={resultado.cierre_mes ? `Cerrar ${nombreMes(resultado.cierre_mes.mes)}` : 'Seguir con el mes'} />
        )}
        {fase === 'cierre' && resultado?.cierre_mes && (
          <Cierre c={resultado.cierre_mes} mesSiguiente={resultado.cierre_mes.mes + 1} terminado={resultado.terminado} onContinuar={avanzar} />
        )}
        {fase === 'historial' && historial && (
          <Historial items={historial} indice={indiceHist} setIndice={setIndiceHist} onVolver={() => setFase('pregunta')} />
        )}
      </div>
      <Aviso />
    </div>
  )
}

// ------------------------------------------------------------------ final (HU-009)

function nivelFinal(b) {
  const llego = b.avance_viaje_pct >= 100
  if (llego && b.patrimonio_neto >= 100000 && b.criterio_financiero_pct >= 70) return 'total'
  if (llego && b.patrimonio_neto >= 0) return 'bien'
  if (llego) return 'con_deudas'
  return b.cuotas_pagadas >= 10 ? 'cerca' : 'lejos'
}

const TITULO_FINAL = {
  total: (n) => `¡${n} llegó a Bariloche con plata de sobra!`,
  bien: (n) => `¡${n} llegó a Bariloche!`,
  con_deudas: (n) => `${n} llegó a Bariloche, pero con deudas`,
  cerca: (n) => `${n} se quedó a las puertas del viaje`,
  lejos: (n) => `${n} no pudo viajar esta vez`,
}

export function Resumen({ dni, vista, onSalir }) {
  const [r, setR] = useState(null)
  const [hist, setHist] = useState(null)
  const [indice, setIndice] = useState(0)
  useEffect(() => { api.resumen(dni).then(setR) }, [dni])
  async function verHistorial() {
    const h = await api.historial(dni)
    setHist(h); setIndice(0)
  }
  const nivel = r ? nivelFinal(r.barras) : null
  const pn = useAnimado(r ? r.barras.patrimonio_neto : 0, 1600)
  const estado = useMemo(() => r && ({
    modo: 'final', llego: r.barras.avance_viaje_pct >= 100, final: { nivel },
    avatarConfig: vista.estudiante.variante_personaje, expresion: r.avatar,
  }), [r, nivel, vista])
  if (!r) return <p className="cargando">Cargando…</p>
  const b = r.barras
  return (
    <div className="pantalla-juego pantalla-final">
      <Encabezado economia={r.economia} mes={12} pagadas={b.cuotas_pagadas} atrasadas={b.cuotas_atrasadas} onHistorial={hist ? null : verHistorial} hayHistorial />
      <div className="escenario-col">
        <Escena estado={hist ? { ...estado, modo: 'escena', mes: hist[indice].mes, ...hist[indice].escena } : estado} />
      </div>
      <div className="panel-juego">
        {hist && <Historial items={hist} indice={indice} setIndice={setIndice} onVolver={() => setHist(null)} textoVolver="Volver al final del viaje" />}
        {!hist && <div className={`final final-${nivel}`}>
          <h1>{TITULO_FINAL[nivel](r.nombre)}</h1>
          <p className="final-mensaje">{r.mensaje}</p>
          <div className="final-numeros">
            <div><Emo e="💰" size={26} /><small>Patrimonio neto</small><b className={pn < 0 ? 'baja' : ''}>{pesos(pn)}</b></div>
            <div><Emo e="✈️" size={26} /><small>Viaje</small><b>{b.cuotas_pagadas}/12 cuotas</b></div>
            <div><Emo e="🧭" size={26} /><small>Criterio financiero</small><b>{Math.round(b.criterio_financiero_pct)}/100</b></div>
            <div><Emo e="💳" size={26} /><small>Deuda pendiente</small><b>{pesos(b.deuda)}</b></div>
          </div>
          <div className="final-decisiones">
            <span className="d-ok">{r.acertadas} acertadas</span>
            <span className="d-warn">{r.riesgosas} riesgosas</span>
            <span className="d-bad">{r.incorrectas} incorrectas</span>
          </div>
          <h2>Cómo te fue en cada tema</h2>
          {r.por_eje.map((f) => (
            <div className="eje-fila" key={f.eje}>
              <span>{f.nombre}</span>
              <div className="barra-apilada" title={`${f.acertadas} acertadas, ${f.riesgosas} riesgosas, ${f.incorrectas} incorrectas`}>
                <i className="ok" style={{ width: `${25 * f.acertadas}%` }} />
                <i className="warn" style={{ width: `${25 * f.riesgosas}%` }} />
                <i className="bad" style={{ width: `${25 * f.incorrectas}%` }} />
              </div>
              <small>{f.acertadas}/4</small>
            </div>
          ))}
          {r.puntos_fuertes.length > 0 && (
            <div className="callout ok">
              <b><Emo e="💪" size={22} /> {r.puntos_fuertes.length > 1 ? 'Tus puntos más fuertes' : 'Tu punto más fuerte'}</b>
              {r.puntos_fuertes.map((f) => <p key={f.eje}><b>{f.nombre}.</b> {f.importancia}</p>)}
            </div>
          )}
          {r.puntos_debiles.length > 0 && (
            <div className="callout warn">
              <b><Emo e="🎯" size={22} /> {r.puntos_debiles.length > 1 ? 'Las áreas en las que más te costó decidir bien' : 'El área en la que más te costó decidir bien'}</b>
              {r.puntos_debiles.map((f) => <p key={f.eje}><b>{f.nombre}.</b> {f.importancia}</p>)}
            </div>
          )}
          <button className="secundario" onClick={verHistorial}><Emo e="📖" size={18} /> Repasar mis 24 decisiones</button>
          <button className="link" onClick={onSalir}>Salir</button>
        </div>}
      </div>
      <Aviso />
    </div>
  )
}

