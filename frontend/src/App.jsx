import { useEffect, useState } from 'react'
import { api } from './api'
import { ElegirPersonaje, IngresoAlumno, Intro, Juego, Resumen } from './Alumno'
import { IngresoDocente, Panel } from './Docente'

const leer = (k) => { try { return JSON.parse(localStorage.getItem(k)) } catch { return null } }
const guardar = (k, v) => { try { v == null ? localStorage.removeItem(k) : localStorage.setItem(k, JSON.stringify(v)) } catch { /* sin storage */ } }

export default function App() {
  const [pantalla, setPantalla] = useState('inicio')
  const [vista, setVista] = useState(null)
  const [sesionDocente, setSesionDocente] = useState(null)

  useEffect(() => {
    const dni = leer('dni')
    if (dni) api.estado(dni).then(irSegunVista).catch(() => guardar('dni', null))
  }, [])

  function irSegunVista(v) {
    setVista(v)
    guardar('dni', v.estudiante.dni)
    if (!v.estudiante.variante_personaje) setPantalla('personaje')
    else if (v.terminado) setPantalla('resumen')
    else if (v.decisiones_tomadas === 0) setPantalla('intro')
    else setPantalla('juego')
  }

  function salir() {
    guardar('dni', null)
    setVista(null)
    setSesionDocente(null)
    setPantalla('inicio')
  }

  return (
    <main className="app">
      {pantalla === 'inicio' && (
        <div className="tarjeta">
          <img src="/icon.svg" alt="" width="56" height="56" />
          <h1>Viaje de egresados</h1>
          <p className="sub">Un simulador para practicar decisiones financieras durante 12 meses.</p>
          <button className="primario" onClick={() => setPantalla('ingreso')}>Soy alumno</button>
          <button className="secundario" onClick={() => setPantalla('docente')}>Soy docente</button>
        </div>
      )}
      {pantalla === 'ingreso' && <IngresoAlumno onIngreso={irSegunVista} volver={() => setPantalla('inicio')} />}
      {pantalla === 'personaje' && <ElegirPersonaje dni={vista.estudiante.dni} onElegido={irSegunVista} />}
      {pantalla === 'intro' && <Intro vista={vista} onEmpezar={() => setPantalla('juego')} />}
      {pantalla === 'juego' && <Juego vistaInicial={vista} onTerminar={() => setPantalla('resumen')} />}
      {pantalla === 'resumen' && <Resumen dni={vista.estudiante.dni} variante={vista.estudiante.variante_personaje} onSalir={salir} />}
      {pantalla === 'docente' && !sesionDocente && <IngresoDocente onIngreso={setSesionDocente} volver={() => setPantalla('inicio')} />}
      {pantalla === 'docente' && sesionDocente && <Panel sesion={sesionDocente} onSalir={salir} />}
    </main>
  )
}
