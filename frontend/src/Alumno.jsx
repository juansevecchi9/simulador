import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api, pesos } from './api'
import {
  ACCESORIOS, avatarUri, CONFIG_INICIAL, codificar, COLORES_PELO, COLORES_ROPA, decodificar, EXPRESIONES,
  NOMBRE_EXPRESION, npcUri, PELOS, PIELES, ROPAS,
} from './avatar'
import { Emo, separarEmoji } from './emoji'
import Escena from './Escena'
import { Aviso, Encabezado, nombreMes, useAnimado } from './hud'
import HudPhaser from './HudPhaser'
import Cartera from './Cartera'

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
        <div className="segmentado" role="group" aria-label="Sexo del personaje">
          {['mujer', 'varon'].map((b) => (
            <button key={b} type="button" aria-pressed={c.base === b} aria-label={b === 'mujer' ? 'Femenino' : 'Masculino'} className={c.base === b ? 'activa' : ''}
              onClick={() => setC((x) => ({ ...CONFIG_INICIAL[b], piel: x.piel, colorRopa: x.colorRopa }))}>
              {b === 'mujer' ? 'F' : 'M'}
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



// Cada decision vale lo mismo, 50 / 24 puntos: suma si es acertada y resta si no.
const PUNTOS = { acertada: 50 / 24, riesgosa: -50 / 24, incorrecta: -50 / 24 }
const coma = (n, d = 1) => n.toFixed(d).replace('.', ',')
const firmado = (n, f = (x) => x) => (n > 0 ? `+${f(n)}` : n < 0 ? `-${f(-n)}` : f(0))

/** Las 4 etapas de cada mes, con la actual resaltada. */
function RitmoMes({ etapa }) {
  const etapas = [['cobro', '💵', 'Cobrás'], ['d1', '🤔', 'Decisión 1'], ['d2', '🤔', 'Decisión 2'], ['cierre', '📆', 'Cierre']]
  const i = etapas.findIndex(([k]) => k === etapa)
  return (
    <ol className="ritmo" aria-label="Etapas del mes">
      {etapas.map(([k, e, t], n) => (
        <li key={k} className={n < i ? 'hecha' : n === i ? 'actual' : ''} aria-current={n === i ? 'step' : undefined}>
          <span className="ritmo-icono"><Emo e={n < i ? '✅' : e} size={18} /></span><span>{t}</span>
        </li>
      ))}
    </ol>
  )
}

/** Lo que trae el mes: cobro, extras y lo que va a pasar en el cierre. */
function InicioMes({ esc, economia, barras, cartera = [] }) {
  const atrasadas = barras.cuotas_atrasadas || 0
  const cuota = economia.cuota_viaje * (1 + atrasadas)
  const extra = esc.ingreso_del_mes - economia.ingreso_base_mensual
  const aportes = cartera.filter((x) => x.tipo === 'inversion' && /le sumás/.test(x.detalle))
  const delMes = cartera.filter((x) => x.tipo !== 'efectivo' && x.tipo !== 'deuda_abierta' && /este mes/.test(x.detalle))
  const abierta = cartera.find((x) => x.tipo === 'deuda_abierta')
  return (
    <div className="inicio-mes">
      <h2><Emo e="🗓️" size={22} /> Así arranca {nombreMes(esc.mes)}</h2>
      <ul>
        <li className="sube"><Emo e="🍕" size={20} /><span>{extra > 0 ? `Sueldo de la pizzería y ${pesos(extra)} extra` : extra < 0 ? `Sueldo de la pizzería, con ${pesos(-extra)} menos` : 'Sueldo de la pizzería'}</span><b>{firmado(esc.ingreso_del_mes, pesos)}</b></li>
        <li className="baja"><Emo e="🧾" size={20} /><span>Gastos fijos (celular, transporte, comida)</span><b>{firmado(-economia.gastos_fijos_mensuales, pesos)}</b></li>
        {aportes.map((x) => <li key={x.id}><Emo e={x.emoji} size={20} /><span>Separaste para {x.nombre.toLowerCase()}</span><b>{x.detalle.match(/\$[\d.]+/)?.[0]}</b></li>)}
      </ul>
      {esc.nota_ingreso && <p className="nota-mes"><Emo e="🎁" size={18} /> {esc.nota_ingreso}</p>}
      <p className="al-cierre">Al cierre del mes, después de tus dos decisiones:</p>
      <ul>
        <li><Emo e="✈️" size={20} /><span>Se paga {atrasadas ? `la cuota y ${atrasadas} atrasada${atrasadas > 1 ? 's' : ''}` : 'la cuota del viaje'}, si te alcanza</span><b>{pesos(cuota)}</b></li>
        {delMes.map((x) => <li key={x.id} className={x.tipo === 'a_cobrar' || x.tipo === 'inversion' ? 'sube' : 'baja'}><Emo e={x.emoji} size={20} /><span>{x.nombre}: {x.detalle.charAt(0).toLowerCase() + x.detalle.slice(1)}</span><b /></li>)}
        {abierta && <li className="baja"><Emo e="💳" size={20} /><span>Tu deuda de tarjeta suma {economia.tasa_deuda_abierta_pct}% de interés; lo que te sobre la va cancelando</span><b>+{pesos(Math.round(abierta.valor * economia.tasa_deuda_abierta_pct / 100))}</b></li>}
        <li><Emo e="🏷️" size={20} /><span>Los precios suben {economia.inflacion_mensual_pct}%: tu plata e inversiones en pesos compran {economia.inflacion_mensual_pct}% menos</span><b>-{economia.inflacion_mensual_pct}%</b></li>
      </ul>
    </div>
  )
}

/** Explica en palabras como cambio cada indicador con la decision. */
function CambiosTablero({ r, previo, economia }) {
  const a = r.barras_antes
  const dEf = Math.round(previo.efectivo - a.efectivo)
  const disp = previo.disponible ?? previo.efectivo
  const dDisp = Math.round(disp - (a.disponible ?? a.efectivo))
  const dDeuda = Math.round(previo.deuda - a.deuda)
  const dInv = Math.round((previo.inversiones || 0) - (a.inversiones || 0))
  const dPn = Math.round(previo.patrimonio_neto - a.patrimonio_neto)
  const dCr = Math.round(10 * (previo.criterio_financiero_pct - a.criterio_financiero_pct)) / 10
  const partes = []
  if (dEf < 0) partes.push(`salieron ${pesos(-dEf)} de tu plata`)
  if (dEf > 0) partes.push(`entraron ${pesos(dEf)} a tu plata`)
  if (dInv > 0) partes.push(`pusiste ${pesos(dInv)} en ${dInv === -dEf ? 'una inversión, que sigue siendo tuya' : 'inversiones o plata a cobrar'}`)
  if (dInv < 0) partes.push(`tus inversiones bajaron ${pesos(-dInv)}`)
  if (dDeuda > 0) partes.push(`tu deuda subió ${pesos(dDeuda)}`)
  if (dDeuda < 0) partes.push(`cancelaste ${pesos(-dDeuda)} de deuda`)
  const necesita = economia.cuota_viaje * (1 + (previo.cuotas_atrasadas || 0))
  const falta = necesita - disp
  const cierraAhora = !!r.cierre_mes
  const filas = [
    ['💰', 'Patrimonio neto', firmado(dPn, pesos), dPn,
      partes.length ? `Porque ${partes.join(', ').replace(/, ([^,]*)$/, ' y $1')}. El patrimonio es lo que tenés (plata e inversiones) menos lo que debés.` : 'Esta decisión no movió tu plata, tus inversiones ni tu deuda.'],
    ['🐷', 'Disponible para la cuota', firmado(dDisp, pesos), dDisp,
      falta > 0 ? `Tenés ${pesos(disp)} disponibles (efectivo e inversiones que sacás en el día) y al cierre se pagan ${pesos(necesita)}: faltan ${pesos(falta)}. Si no llegás, la cuota queda atrasada.`
        : `Tenés ${pesos(disp)} disponibles (efectivo e inversiones que sacás en el día) y al cierre se pagan ${pesos(necesita)}: por ahora te alcanza.`],
    ['✈️', 'Viaje', cierraAhora ? 'se define ahora' : 'sin cambios', 0,
      cierraAhora ? 'Con esta decisión se cierra el mes: ahora se ve si la cuota se paga.' : 'Las cuotas se pagan en el cierre del mes, después de tu próxima decisión.'],
    ['🧭', 'Criterio financiero', dCr ? `${dCr > 0 ? '+' : '-'}${coma(Math.abs(dCr))}` : '0', dCr,
      `Una decisión ${r.clasificacion} ${PUNTOS[r.clasificacion] > 0 ? 'suma' : 'resta'} ${coma(Math.abs(PUNTOS[r.clasificacion]))}. Todas valen lo mismo, 50 ÷ 24 = 2,1 puntos: la acertada suma y la riesgosa o incorrecta restan. Solo llegás a 100 si acertás las 24.`],
  ]
  return (
    <div className="tablero">
      <h3>Cómo cambiaron tus indicadores</h3>
      {filas.map(([e, t, v, d, texto]) => (
        <div className="tablero-fila" key={t}>
          <Emo e={e} size={22} />
          <div><b>{t}</b><p>{texto}</p></div>
          <span className={`tablero-valor ${d > 0 ? 'sube' : d < 0 ? 'baja' : ''}`}>{v}</span>
        </div>
      ))}
    </div>
  )
}

/** Grafico de cascada: como paso el patrimonio del inicio al final del mes. */
function CascadaMes({ c }) {
  const pagadas = c.cuotas_pagadas_en_cierre
  const cuotas = pagadas * c.cuota_viaje
  const preCierre = c.patrimonio_final - c.rendimientos + c.interes_deuda + c.compras + cuotas + c.perdida_inflacion
  const pasos = [
    ['Sueldo menos gastos fijos', c.cobro_neto],
    ['Tus dos decisiones', preCierre - c.patrimonio_inicio - c.cobro_neto],
    ['Lo que rindieron tus inversiones', c.rendimientos],
    ['Intereses de la tarjeta', -c.interes_deuda],
    ['Compras programadas', -c.compras],
    [pagadas ? `Cuota${pagadas > 1 ? 's' : ''} del viaje` : 'Cuota del viaje (no se pagó)', -cuotas],
    ['Inflación', -c.perdida_inflacion],
  ].filter(([, d], i) => i < 2 || i === 5 || i === 6 || Math.round(d) !== 0)
  let acum = c.patrimonio_inicio
  const filas = [['Empezaste el mes con', 0, acum, true]]
  for (const [t, d] of pasos) { filas.push([t, acum, acum + d, false]); acum += d }
  filas.push(['Terminaste el mes con', 0, c.patrimonio_final, true])
  const valores = filas.flatMap(([, x, y]) => [x, y])
  const min = Math.min(0, ...valores)
  const max = Math.max(0, ...valores)
  const pos = (v) => (100 * (v - min)) / (max - min || 1)
  return (
    <div className="cascada">
      <h3>Así cambió tu patrimonio en {nombreMes(c.mes)}</h3>
      {filas.map(([t, desde, hasta, total], i) => {
        const d = Math.round(hasta - desde)
        const izq = Math.min(pos(desde), pos(hasta))
        const ancho = Math.max(0.6, Math.abs(pos(hasta) - pos(desde)))
        return (
          <div className={`cascada-fila ${total ? 'total' : d > 0 ? 'sube' : d < 0 ? 'baja' : 'cero'}`} key={i} style={{ animationDelay: `${i * 0.12}s` }}>
            <span>{t}</span>
            <div className="cascada-pista"><i className="cero" style={{ left: `${pos(0)}%` }} /><i className="barra" style={{ left: `${izq}%`, width: `${ancho}%` }} /></div>
            <b>{total ? pesos(hasta) : firmado(d, pesos)}</b>
          </div>
        )
      })}
      {pagadas > 0 && <p className="cascada-nota"><Emo e="✈️" size={16} /> Pagar la cuota baja tu plata, pero suma al viaje: ya llevás {c.cuotas_pagadas_total} de 12.</p>}
    </div>
  )
}

/** Parte un texto largo en parrafos cortos (una idea por parrafo). */
function Parrafos({ texto }) {
  // Explicacion por bloques (separados por una linea en blanco): cada bloque que empieza
  // con un emoji es una opcion y va en su propia tarjeta; los demas son texto corrido.
  if ((texto || '').includes('\n\n')) {
    return (
      <div className="parrafos">
        {texto.split(/\n\n+/).map((bloque, i) => {
          const [primera, ...resto] = bloque.split('\n')
          const [e, titulo] = separarEmoji(primera)
          if (!e) return bloque.split('\n').map((l, k) => <p key={`${i}-${k}`}>{l}</p>)
          return (
            <div className="tarjeta-opcion" key={i}>
              <p className="tarjeta-titulo"><Emo e={e} size={22} /><b>{titulo}</b></p>
              {resto.map((l, k) => <p key={k} className={/=/.test(l) ? 'calc' : ''}>{l}</p>)}
            </div>
          )
        })}
      </div>
    )
  }
  // Si el texto trae renglones (cuentas), cada renglon va aparte; si no, se parte por oraciones.
  if ((texto || '').includes('\n')) {
    return (
      <div className="parrafos">
        {texto.split('\n').map((l, i) => <p key={i} className={/=/.test(l) ? 'cuenta' : ''}>{l}</p>)}
      </div>
    )
  }
  const oraciones = (texto || '').split(/(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ¿¡])/)
  const grupos = []
  for (const o of oraciones) {
    const ultimo = grupos[grupos.length - 1]
    if (ultimo && o.length < 40) grupos[grupos.length - 1] = `${ultimo} ${o}`
    else grupos.push(o)
  }
  return <div className="parrafos">{grupos.map((g, i) => <p key={i}>{g}</p>)}</div>
}

function Resultado({ r, previo, onContinuar, textoBoton, economia }) {
  const s = SELLO[r.clasificacion]
  return (
    <div className="resultado">
      <div className={`sello ${s.clase}`} role="status">
        <Emo e={s.emoji} size={30} /><span>{s.texto}</span>
      </div>
      <section className="historia">
        <h2><Emo e="🎬" size={22} /> Qué pasó en tu historia</h2>
        <Parrafos texto={r.consecuencia} />
        <CambiosTablero r={r} previo={previo} economia={economia} />
      </section>
      <section className="porque">
        <h2><Emo e="💡" size={22} /> Por qué</h2>
        <Parrafos texto={r.explicacion} />
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

const TONO_MOV = { rinde: 'sube', vence: 'neutro', cobro: 'sube', pago: 'neutro', compra: 'baja', interes: 'baja', rescate: 'neutro', pago_deuda: 'sube', impago: 'baja', aporte: 'neutro' }

function Cierre({ c, mesSiguiente, onContinuar, terminado }) {
  const [paso, setPaso] = useState(0)
  useEffect(() => {
    const ts = [1, 2, 3, 4].map((n) => setTimeout(() => setPaso(n), n * 1000))
    return () => ts.forEach(clearTimeout)
  }, [])
  const pagadas = c.cuotas_pagadas_en_cierre
  const escalaEf = Math.max(c.efectivo_antes_cuota, c.cuota_viaje, 1)
  const efPostCuota = c.efectivo_antes_cuota - pagadas * c.cuota_viaje
  const movs = c.movimientos || []
  return (
    <div className="cierre">
      <RitmoMes etapa="cierre" />
      <h2 className="cierre-titulo"><Emo e="📆" size={28} /> Cierre de {nombreMes(c.mes)}</h2>
      <PasoCierre visible={paso >= 1} emoji="💼" titulo={movs.length ? 'Tus inversiones y deudas este mes' : 'Sin inversiones ni deudas que se movieran'} tono="neutro">
        {movs.length ? (
          <ul className="movimientos">
            {movs.map((m, i) => (
              <li key={i} className={TONO_MOV[m.tipo] || ''} style={{ animationDelay: `${0.15 * i}s` }}>
                <Emo e={m.emoji} size={20} /><span><b>{m.posicion}</b>{m.texto}</span>
              </li>
            ))}
          </ul>
        ) : <p>No tenías inversiones, préstamos ni deudas de tarjeta: este mes no hubo nada que rindiera o se pagara.</p>}
      </PasoCierre>
      <PasoCierre visible={paso >= 2} emoji="✈️" titulo={c.cuota_del_mes_pagada
        ? `Cuota del viaje pagada${pagadas > 1 ? ` (y ${pagadas - 1} atrasada${pagadas > 2 ? 's' : ''})` : ''}`
        : 'No alcanzó para la cuota del viaje'} tono={c.cuota_del_mes_pagada ? 'ok' : 'bad'}>
        <p>{c.cuota_del_mes_pagada
          ? `Salieron ${pesos(pagadas * c.cuota_viaje)} de tu plata. Ya pagaste ${c.cuotas_pagadas_total} de 12 cuotas.`
          : `Tenías ${pesos(c.efectivo_antes_cuota)} y la cuota es de ${pesos(c.cuota_viaje)}. ${c.cuotas_atrasadas > 1 ? `Quedan ${c.cuotas_atrasadas} cuotas sin pagar: se pagan` : 'Queda 1 cuota sin pagar: se paga'} cuando te alcance.`}</p>
        <BarraAnimada desde={c.efectivo_antes_cuota} hasta={efPostCuota} max={escalaEf} clase="b-cuota" />
      </PasoCierre>
      <PasoCierre visible={paso >= 3} emoji="🏷️" titulo="Los precios subieron 2%" tono="warn">
        <p>{c.perdida_inflacion > 0
          ? `Tu plata y tus inversiones en pesos compran 2% menos: perdiste ${pesos(c.perdida_inflacion)} de poder de compra. Lo que debés sigue siendo la misma cantidad de pesos, igual que tu sueldo.`
          : 'No tenías plata guardada ni inversiones en pesos: la inflación no te sacó poder de compra este mes.'}</p>
      </PasoCierre>
      <div className={`cierre-acciones ${paso >= 4 ? 'visible' : ''}`}>
        {paso >= 4 && <CascadaMes c={c} />}
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
      <section className="historia"><h2><Emo e="🎬" size={22} /> Qué pasó en tu historia</h2><Parrafos texto={h.consecuencia} /></section>
      <section className="porque"><h2><Emo e="💡" size={22} /> Por qué</h2><Parrafos texto={h.explicacion} /></section>
      <button className="primario" onClick={onVolver}>{textoVolver}</button>
    </div>
  )
}

/** Barras intermedias (antes del cierre) a partir de los datos del cierre del mes. */
function barrasPrevias(r) {
  if (r.barras_previas) return r.barras_previas
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
    // el patrimonio incluye las inversiones y lo que te deben, no solo el efectivo
    patrimonio_neto: c.patrimonio_final,
    inversiones: c.patrimonio_final - c.efectivo_final + c.deuda_final,
    disponible: c.efectivo_final + (c.cartera || []).filter((x) => x.tipo === 'inversion' && x.liquida).reduce((t, x) => t + x.valor, 0),
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
  // Cada paso nuevo (pregunta, resultado, cierre) arranca desde arriba, sin que el alumno
  // tenga que volver a subir. En celular la que se desplaza es la pagina; en compu, el panel.
  useEffect(() => {
    panel.current?.scrollTo?.({ top: 0 })
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' })
  }, [fase, esc?.escenario_id, indiceHist])

  const previo = resultado ? barrasPrevias(resultado) : null
  const barras = fase === 'resultado' ? previo : fase === 'cierre' ? barrasCierre(resultado) : vista.barras
  const barrasAntes = fase === 'resultado' ? resultado.barras_antes : fase === 'cierre' ? previo : fase === 'pregunta' ? antesMes : null
  const expresion = resultado && fase !== 'pregunta' ? resultado.avatar : vista.avatar
  const cartera = fase === 'resultado' ? resultado.cartera_previa : fase === 'cierre' ? resultado.cierre_mes?.cartera : vista.cartera
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
        <HudPhaser barras={barras} antes={barrasAntes} economia={vista.economia} enCierre={fase === 'cierre'} cartera={cartera} />
        <div className="solo-ancho"><Cartera items={cartera} compacta /></div>
      </div>
      <div className="panel-juego" ref={panel}>
        <div className="solo-angosto"><Cartera items={cartera} compacta /></div>
        {fase === 'intro' && (
          <div className="intro">
            <Dialogo escena={{ personaje: 'cami', personaje_nombre: 'Cami', personaje_rol: 'tu mejor amiga del curso', lugar_nombre: 'Tu casa' }}
              texto={`¡${nombre}! Ya pagamos la seña de ${pesos(vista.economia.sena_viaje)} del viaje a Bariloche. Ahora quedan ${vista.economia.cantidad_cuotas} cuotas de ${pesos(vista.economia.cuota_viaje)}, una por mes. ¿Llegamos?`} />
            <ul className="reglas">
              <li><Emo e="🍕" size={26} /><span>Trabajás los fines de semana en la <b>{vista.economia.trabajo.nombre}</b>: cobrás {pesos(vista.economia.ingreso_base_mensual)} por mes y pagás {pesos(vista.economia.gastos_fijos_mensuales)} de gastos fijos.</span></li>
              <li className="regla-cuenta"><Emo e="💰" size={26} /><span>
                <b>Por qué arrancás con {pesos(vista.barras.patrimonio_neto)} de patrimonio:</b>
                <span className="mini-cuenta">Ahorros que tenías: {pesos(vista.economia.efectivo_inicial)}</span>
                <span className="mini-cuenta">Seña del viaje, ya pagada: -{pesos(vista.economia.sena_viaje)}</span>
                <span className="mini-cuenta">Sueldo de enero: +{pesos(vista.economia.ingreso_base_mensual)}</span>
                <span className="mini-cuenta">Gastos fijos de enero: -{pesos(vista.economia.gastos_fijos_mensuales)}</span>
                Las 12 cuotas no se restan de entrada: se pagan una por mes, en cada cierre.
              </span></li>
              <li><Emo e="🗓️" size={26} /><span>Cada mes tomás <b>dos decisiones</b>. Al cierre, si te alcanza la plata, la cuota del viaje se paga sola.</span></li>
              <li><Emo e="🏷️" size={26} /><span>Los precios suben <b>{vista.economia.inflacion_mensual_pct}% por mes</b> y el dólar <b>{vista.economia.suba_dolar_mensual_pct}% por mes</b>. Lo que tengas ahorrado en pesos compra {vista.economia.inflacion_mensual_pct}% menos cada mes.</span></li>
              <li><Emo e="💳" size={26} /><span>La deuda de tarjeta suma <b>{vista.economia.tasa_deuda_abierta_pct}% de interés por mes</b>. Al cierre, lo que te sobra después de la cuota la va cancelando.</span></li>
              <li><Emo e="💼" size={26} /><span>Tus inversiones y préstamos evolucionan mes a mes: los vas a ver siempre en <b>tu cartera</b>. Tu sueldo, la cuota y lo que debas quedan fijos en pesos.</span></li>
            </ul>
            <button className="primario" onClick={() => setFase('pregunta')}>Arrancar en enero</button>
          </div>
        )}
        {fase === 'pregunta' && esc && (
          <div className="pregunta" key={esc.escenario_id}>
            <RitmoMes etapa={esc.orden === 1 ? 'd1' : 'd2'} />
            <div className="paso-num">Decisión {esc.numero} de 24</div>
            {esc.orden === 1 && <InicioMes esc={esc} economia={vista.economia} barras={vista.barras} cartera={vista.cartera} />}
            <Dialogo escena={esc.escena} texto={esc.texto_situacion} />
            <Opciones opciones={esc.opciones} deshabilitado={enviando} onElegir={elegir} />
            {error && <p className="error">{error}</p>}
          </div>
        )}
        {fase === 'resultado' && resultado && (
          <Resultado r={resultado} previo={previo} onContinuar={avanzar} economia={vista.economia}
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
  useEffect(() => { window.scrollTo({ top: 0, left: 0, behavior: 'instant' }) }, [])
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
        <div className="solo-ancho"><Cartera items={r.cartera} compacta /></div>
      </div>
      <div className="panel-juego">
        {hist && <Historial items={hist} indice={indice} setIndice={setIndice} onVolver={() => setHist(null)} textoVolver="Volver al final del viaje" />}
        {!hist && <div className="solo-angosto"><Cartera items={r.cartera} compacta /></div>}
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

