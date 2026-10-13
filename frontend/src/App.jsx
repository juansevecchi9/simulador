import { useEffect, useState } from 'react'
import { api } from './api'
import { ElegirPersonaje, IngresoAlumno, Juego, Resumen } from './Alumno'
import { IngresoDocente, Panel } from './Docente'
import Escena from './Escena'
import ModoPrueba from './ModoPrueba'

// Escenas de fondo de las pantallas de entrada (sin avatar del alumno todavia).
const ESCENAS_ENTRADA = {
  inicio: { modo: 'escena', lugar: 'agencia', mes: 1, personaje: 'sofi', personaje_nombre: 'Sofi', personaje_rol: 'de la agencia Egresados Sur', objeto: '✈️' },
  ingreso: { modo: 'escena', lugar: 'casa', mes: 1, personaje: 'cami', personaje_nombre: 'Cami', personaje_rol: 'tu mejor amiga del curso', objeto: '🧳' },
  docente: { modo: 'escena', lugar: 'colegio', mes: 3, personaje: null, objeto: '📊' },
}

const leer = (k) => { try { return JSON.parse(localStorage.getItem(k)) } catch { return null } }
const guardar = (k, v) => { try { v == null ? localStorage.removeItem(k) : localStorage.setItem(k, JSON.stringify(v)) } catch { /* sin storage */ } }

export default function App() {
  const [pantalla, setPantalla] = useState('inicio')
  const [vista, setVista] = useState(null)
  const [sesionDocente, setSesionDocente] = useState(null)
  const [partida, setPartida] = useState(0) // cambia al reiniciar o saltar (modo prueba)

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

  const entrada = pantalla === 'inicio' || pantalla === 'ingreso' || (pantalla === 'docente' && !sesionDocente)
  const pantallaJuego = entrada || ['juego', 'intro', 'resumen'].includes(pantalla)
  return (
    <main className={pantallaJuego ? 'app app-juego' : pantalla === 'personaje' ? 'app app-ancha' : pantalla === 'docente' && sesionDocente ? 'app app-panel' : 'app'}>
      {entrada && (
        <div className={`entrada entrada-${pantalla}`}>
          <div className="entrada-escena">
            <div className="entrada-marca"><img src="/icon.svg" alt="" width="34" height="34" /><b>Viaje de egresados</b><span>Simulador financiero</span></div>
            <Escena estado={ESCENAS_ENTRADA[pantalla]} />
            <p className="entrada-pie">Simulador educativo: no es asesoramiento financiero ni ofrece productos financieros.</p>
          </div>
          <div className="entrada-panel">
            {pantalla === 'inicio' && (
              <section className="portada">
                <h1>Tu viaje de egresados empieza con tu plata</h1>
                <p>Doce meses, veinticuatro decisiones y una meta: llegar a Bariloche sin hundirte en deudas.</p>
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
            {pantalla === 'docente' && <IngresoDocente onIngreso={setSesionDocente} volver={() => setPantalla('inicio')} />}
          </div>
        </div>
      )}
      {pantalla === 'personaje' && <ElegirPersonaje vista={vista} onElegido={irSegunVista} />}
      {(pantalla === 'intro' || pantalla === 'juego') && <Juego key={partida} vistaInicial={vista} intro={pantalla === 'intro'} onTerminar={() => setPantalla('resumen')} />}
      {pantalla === 'resumen' && <Resumen key={partida} dni={vista.estudiante.dni} vista={vista} onSalir={salir} />}
      {pantalla === 'docente' && sesionDocente && <Panel sesion={sesionDocente} onSalir={salir} />}
      {['intro', 'juego', 'resumen'].includes(pantalla) && vista && (
        <ModoPrueba dni={vista.estudiante.dni} onCambio={(v) => { setPartida((n) => n + 1); irSegunVista(v) }} />
      )}
    </main>
  )
}
