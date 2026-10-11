import { useEffect, useState } from 'react'
import { api, pesos } from './api'

const FRANJAS = [
  ['bien_encaminados', 'Bien encaminados', 'ok'],
  ['en_riesgo', 'En riesgo', 'warn'],
  ['necesitan_intervencion', 'Necesitan intervención', 'bad'],
]

export function IngresoDocente({ onIngreso, volver }) {
  const [codigo, setCodigo] = useState('')
  const [error, setError] = useState('')
  async function enviar(e) {
    e.preventDefault()
    if (!codigo.trim()) return setError('Ingresá el código de acceso de tu curso.')
    try { onIngreso({ ...(await api.ingresoDocente(codigo.trim())), codigo: codigo.trim().toUpperCase() }) } catch (err) { setError(err.message) }
  }
  return (
    <form className="tarjeta" onSubmit={enviar} noValidate>
      <h1>Panel docente</h1>
      <p className="sub">Ingresá con el código de acceso de tu curso.</p>
      <label>Código de acceso<input value={codigo} onChange={(e) => { setCodigo(e.target.value); setError('') }} placeholder="ABCD2026" /></label>
      {error && <p className="error">{error}</p>}
      <button className="primario">Ingresar</button>
      <button type="button" className="link" onClick={volver}>Volver</button>
    </form>
  )
}

function Apilada({ a, r, i }) {
  return (
    <div className="barra-apilada">
      <i className="ok" style={{ width: `${a}%` }} /><i className="warn" style={{ width: `${r}%` }} /><i className="bad" style={{ width: `${i}%` }} />
    </div>
  )
}

export function Panel({ sesion, onSalir }) {
  const [vista, setVista] = useState({ nivel: 1 })
  const [general, setGeneral] = useState(null)
  const [ejes, setEjes] = useState(null)
  const [error, setError] = useState('')
  const { curso_id: cursoId, codigo } = sesion

  useEffect(() => {
    Promise.all([api.panelGeneral(cursoId, codigo), api.panelEjes(cursoId, codigo)])
      .then(([g, e]) => { setGeneral(g); setEjes(e) })
      .catch((err) => setError(err.message))
  }, [cursoId, codigo])

  if (error) return <p className="error">{error}</p>
  if (!general) return <p className="cargando">Cargando…</p>

  return (
    <div className="panel">
      <div className="panel-top">
        <div><h1>{sesion.nombre}</h1><span className="sub">{general.cantidad_alumnos} alumnos</span></div>
        <button className="link" onClick={onSalir}>Salir</button>
      </div>
      <nav className="tabs">
        <button className={vista.nivel === 1 ? 'activo' : ''} onClick={() => setVista({ nivel: 1 })}>Curso</button>
        <button className={vista.nivel === 2 || vista.nivel === 3 ? 'activo' : ''} onClick={() => setVista({ nivel: 2 })}>Temas</button>
        <button className={vista.nivel === 4 ? 'activo' : ''} onClick={() => setVista({ nivel: 4, dni: null })}>Alumnos</button>
      </nav>
      {vista.nivel === 1 && <Nivel1 g={general} irAlumno={(dni) => setVista({ nivel: 4, dni })} />}
      {vista.nivel === 2 && <Nivel2 ejes={ejes} abrir={(eje) => setVista({ nivel: 3, eje })} />}
      {vista.nivel === 3 && <Nivel3 cursoId={cursoId} codigo={codigo} eje={vista.eje} volver={() => setVista({ nivel: 2 })} />}
      {vista.nivel === 4 && <Nivel4 cursoId={cursoId} codigo={codigo} alumnos={general.alumnos} dni={vista.dni}
        elegir={(dni) => setVista({ nivel: 4, dni })} />}
    </div>
  )
}

function Nivel1({ g, irAlumno }) {
  const activos = Object.values(g.franjas).reduce((a, b) => a + b, 0) || 1
  return (
    <>
      <div className="grid2">
        <div className="metrica"><span>Avance promedio del recorrido</span><b>{Math.round(g.avance_promedio_pct)}%</b></div>
        <div className="metrica"><span>Patrimonio neto promedio</span><b>{pesos(g.patrimonio_neto_promedio)}</b></div>
        <div className="metrica"><span>Avance del viaje promedio</span><b>{Math.round(g.avance_viaje_promedio_pct)}%</b></div>
        <div className="metrica"><span>Criterio financiero promedio</span><b>{Math.round(g.criterio_financiero_promedio_pct)}%</b></div>
      </div>
      <div className="caja">
        <p className="seccion">Alumnos por criterio financiero</p>
        <Apilada a={100 * (g.franjas.bien_encaminados || 0) / activos} r={100 * (g.franjas.en_riesgo || 0) / activos}
          i={100 * (g.franjas.necesitan_intervencion || 0) / activos} />
        {FRANJAS.map(([k, t, c]) => <p key={k} className="leyenda-item"><i className={`punto ${c}`} />{t} ({g.franjas[k] || 0})</p>)}
        <p className="ayuda">Bien encaminados: 70% o más de decisiones acertadas. En riesgo: entre 40% y 69%. Necesitan intervención: menos de 40%.</p>
      </div>
      <div className="grid3">
        <div className="mini"><b>{g.estados.completo || 0}</b><span>Completaron</span></div>
        <div className="mini"><b>{g.estados.en_curso || 0}</b><span>En curso</span></div>
        <div className="mini"><b>{g.estados.no_inicio || 0}</b><span>No iniciaron</span></div>
      </div>
      <p className="seccion">Alumnos que necesitan intervención</p>
      {g.alumnos.filter((a) => a.franja === 'necesitan_intervencion').map((a) => (
        <button key={a.dni} className="fila-alumno" onClick={() => irAlumno(a.dni)}>
          <span>{a.nombre}</span><small>Criterio {Math.round(a.criterio_financiero_pct)}% · {Math.round(a.finalizacion_pct)}% del recorrido</small>
        </button>
      ))}
    </>
  )
}

function Nivel2({ ejes, abrir }) {
  return (
    <>
      <p className="ayuda">Temas ordenados de peor a mejor desempeño del curso. Tocá un tema para ver sus 4 escenas.</p>
      {ejes.map((e) => (
        <button key={e.eje} className="fila-eje" onClick={() => abrir(e.eje)}>
          <div className="fila-eje-top"><b>{e.nombre}</b><small>{e.acertadas_pct}% acertadas · {e.total} decisiones</small></div>
          <Apilada a={e.acertadas_pct} r={e.riesgosas_pct} i={e.incorrectas_pct} />
        </button>
      ))}
      <p className="ayuda">Verde: acertadas · Ámbar: riesgosas · Rojo: incorrectas.</p>
    </>
  )
}

function Nivel3({ cursoId, codigo, eje, volver }) {
  const [d, setD] = useState(null)
  useEffect(() => { api.panelEje(cursoId, eje, codigo).then(setD) }, [cursoId, eje, codigo])
  if (!d) return <p className="cargando">Cargando…</p>
  return (
    <>
      <button className="link" onClick={volver}>‹ Volver a temas</button>
      <h2>{d.nombre}</h2>
      {d.escenas.map((s) => (
        <div className="caja" key={s.escenario_id}>
          <div className="fila-eje-top"><b>Escena {s.escena} · mes {s.mes}</b><small>{s.acertadas_pct}% acertadas · {s.total} respuestas</small></div>
          <p className="situacion">{s.texto_situacion}</p>
          <Apilada a={s.acertadas_pct} r={s.riesgosas_pct} i={s.incorrectas_pct} />
          {s.error_dominante && (
            <p className="error-dominante">Error dominante: <b>{s.error_dominante.tipo_error}, {s.error_dominante.severidad}</b>.
              Opción más elegida entre quienes fallaron: «{s.error_dominante.opcion_mas_elegida}»</p>
          )}
        </div>
      ))}
    </>
  )
}

function Linea({ puntos, clave, color, etiqueta, formato }) {
  if (!puntos.length) return null
  const vals = puntos.map((p) => p[clave])
  const min = Math.min(0, ...vals), max = Math.max(1, ...vals)
  const x = (i) => 10 + (i * 280) / 11
  const y = (v) => 70 - ((v - min) / (max - min)) * 60
  return (
    <div className="linea">
      <div className="fila-eje-top"><b>{etiqueta}</b><small>mes {puntos.at(-1).mes}: {formato(vals.at(-1))}</small></div>
      <svg viewBox="0 0 300 80" role="img" aria-label={`Trayectoria de ${etiqueta}`}>
        {min < 0 && <line x1="10" x2="290" y1={y(0)} y2={y(0)} stroke="#ccc" strokeDasharray="3 3" />}
        <polyline fill="none" stroke={color} strokeWidth="2.5" points={puntos.map((p, i) => `${x(i)},${y(p[clave])}`).join(' ')} />
        {puntos.map((p, i) => <circle key={i} cx={x(i)} cy={y(p[clave])} r="3" fill={color} />)}
      </svg>
    </div>
  )
}

function Nivel4({ cursoId, codigo, alumnos, dni, elegir }) {
  const [d, setD] = useState(null)
  useEffect(() => { setD(null); if (dni) api.panelAlumno(cursoId, dni, codigo).then(setD) }, [cursoId, dni, codigo])
  if (!dni) {
    return alumnos.map((a) => (
      <button key={a.dni} className="fila-alumno" onClick={() => elegir(a.dni)}>
        <span>{a.nombre}</span>
        <small>{a.decisiones ? `Criterio ${Math.round(a.criterio_financiero_pct)}% · ${Math.round(a.finalizacion_pct)}% del recorrido` : 'No inició'}</small>
      </button>
    ))
  }
  if (!d) return <p className="cargando">Cargando…</p>
  return (
    <>
      <button className="link" onClick={() => elegir(null)}>‹ Volver a alumnos</button>
      <h2>{d.nombre}</h2>
      <div className="grid2">
        <div className="metrica"><span>Finalización</span><b>{Math.round(d.finalizacion_pct)}%</b></div>
        <div className="metrica"><span>Tiempo promedio por decisión</span><b>{d.tiempo_promedio_seg ?? '—'} s</b></div>
        <div className="metrica"><span>Patrimonio neto</span><b>{pesos(d.barras.patrimonio_neto)}</b></div>
        <div className="metrica"><span>Meses con cuota impaga</span><b>{d.cuotas_impagas_en_cierre}</b></div>
      </div>
      <p className="seccion">Trayectoria mes a mes</p>
      <Linea puntos={d.trayectoria} clave="patrimonio_neto" color="#378ADD" etiqueta="Patrimonio neto" formato={pesos} />
      <Linea puntos={d.trayectoria} clave="avance_viaje_pct" color="#7F77DD" etiqueta="Avance del viaje" formato={(v) => `${Math.round(v)}%`} />
      <Linea puntos={d.trayectoria} clave="criterio_financiero_pct" color="#1D9E75" etiqueta="Criterio financiero" formato={(v) => `${Math.round(v)}%`} />
      <p className="seccion">Reincidencia por tipo de error</p>
      <table className="tabla">
        <thead><tr><th>Tipo de error</th><th>Veces</th><th>Leve</th><th>Severo</th></tr></thead>
        <tbody>
          {d.reincidencia.map((r) => (
            <tr key={r.tipo_error} className={r.veces >= 3 ? 'resaltar' : ''}>
              <td>{r.tipo_error}<small> · {r.eje}</small></td><td>{r.veces} de {r.oportunidades}</td><td>{r.leve}</td><td>{r.severo}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="ayuda">Leve: decisión riesgosa. Severo: decisión incorrecta. Resaltado: 3 o más veces en el mismo tipo de error.</p>
    </>
  )
}
