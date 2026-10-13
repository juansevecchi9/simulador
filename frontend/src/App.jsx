import { useEffect, useState } from 'react'
import { api } from './api'
import { ElegirPersonaje, IngresoAlumno, Juego, Resumen } from './Alumno'
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
    if (!v.estudiante.variante_personaje || (!v.estudiante.variante_personaje.includes('.') && v.decisiones_tomadas === 0)) setPantalla('personaje')
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

  const pantallaJuego = ['juego', 'intro', 'resumen'].includes(pantalla)
  return (
    <main className={pantallaJuego ? 'app app-juego' : pantalla === 'personaje' ? 'app app-ancha' : pantalla === 'docente' && sesionDocente ? 'app app-panel' : 'app'}>
      {pantalla === 'inicio' && (
        <section className="portada">
          <img src="/icon.svg" alt="" width="64" height="64" />
          <h1>Tu viaje de egresados empieza con tu plata</h1>
          <p>Doce meses, veinticuatro decisiones y una meta: llegar al viaje sin hundirte en deudas.</p>
          <div className="boletos">
            <button className="boleto" onClick={() => setPantalla('ingreso')}>
              <b>Soy alumno</b><span>Jugar el recorrido</span>
            </button>
            <button className="boleto boleto-docente" onClick={() => setPantalla('docente')}>
              <b>Soy docente</b><span>Ver el panel del curso</span>
            </button>
          </div>
        </section>
      )}
      {pantalla === 'ingreso' && <IngresoAlumno onIngreso={irSegunVista} volver={() => setPantalla('inicio')} />}
      {pantalla === 'personaje' && <ElegirPersonaje vista={vista} onElegido={irSegunVista} />}
      {(pantalla === 'intro' || pantalla === 'juego') && <Juego vistaInicial={vista} intro={pantalla === 'intro'} onTerminar={() => setPantalla('resumen')} />}
      {pantalla === 'resumen' && <Resumen dni={vista.estudiante.dni} vista={vista} onSalir={salir} />}
      {pantalla === 'docente' && !sesionDocente && <IngresoDocente onIngreso={setSesionDocente} volver={() => setPantalla('inicio')} />}
      {pantalla === 'docente' && sesionDocente && <Panel sesion={sesionDocente} onSalir={salir} />}
    </main>
  )
}
