import { useEffect, useState } from 'react'
import { api } from './api'
import { Emo } from './emoji'

const aviso = (err) => alert(err.message === 'Not Found'
  ? 'El servidor todavía se está actualizando con la última versión. Probá de nuevo en un par de minutos.'
  : err.message)

/** Arma un CSV con las decisiones tomadas, para poder reproducir el recorrido. */
async function descargarCsv(dni) {
  const h = await api.historial(dni)
  const comillas = (x) => `"${String(x ?? '').replaceAll('"', '""')}"`
  const filas = [['decision', 'mes', 'orden', 'opcion_id', 'clasificacion', 'opcion_elegida', 'situacion']]
  for (const d of h) {
    const op = d.opciones.find((o) => o.opcion_id === d.elegida_id)
    filas.push([d.numero, d.mes, d.orden, d.elegida_id, d.clasificacion, op?.texto, d.texto_situacion])
  }
  const csv = '\ufeff' + filas.map((f) => f.map(comillas).join(';')).join('\n')
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  a.download = `decisiones-${dni}.csv`
  a.click()
  URL.revokeObjectURL(a.href)
}

const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

/** Solo para validar el contenido: reiniciar la partida o saltar a un mes. */
export default function ModoPrueba({ dni, onCambio, onBorrado }) {
  const [activo, setActivo] = useState(false)
  const [abierto, setAbierto] = useState(false)
  const [mes, setMes] = useState(2)
  const [trabajando, setTrabajando] = useState(false)
  useEffect(() => { api.salud().then((r) => setActivo(!!r.modo_prueba)).catch(() => {}) }, [])
  if (!activo || !dni) return null

  async function hacer(accion) {
    setTrabajando(true)
    try { onCambio(await accion()) } catch (err) { aviso(err) }
    setTrabajando(false)
    setAbierto(false)
  }

  return (
    <div className="modo-prueba">
      {abierto && (
        <div className="modo-prueba-panel">
          <b>Modo prueba</b>
          <small>Solo para revisar el contenido. Se apaga antes de la prueba piloto.</small>
          <button className="secundario" disabled={trabajando} onClick={async () => {
            setTrabajando(true)
            try { await api.borrar(dni); onBorrado() } catch (err) { aviso(err) }
            setTrabajando(false)
          }}>
            Empezar de cero (crear el usuario de nuevo)
          </button>
          <button className="secundario" disabled={trabajando} onClick={() => descargarCsv(dni).catch(aviso)}>
            Descargar mis decisiones (CSV)
          </button>
          <div className="modo-prueba-salto">
            <select value={mes} onChange={(e) => setMes(+e.target.value)} aria-label="Mes al que saltar">
              {MESES.map((m, i) => <option key={m} value={i + 1}>{m.charAt(0).toUpperCase() + m.slice(1)}</option>)}
              <option value={13}>Final del viaje</option>
            </select>
            <button className="primario" disabled={trabajando} onClick={() => hacer(() => api.saltar(dni, mes))}>
              {trabajando ? 'Saltando…' : 'Ir a ese mes'}
            </button>
          </div>
          <small>Para saltar, responde solo con la opción acertada todos los meses anteriores.</small>
        </div>
      )}
      <button className="modo-prueba-boton" onClick={() => setAbierto(!abierto)} aria-expanded={abierto}>
        <Emo e="🧪" size={16} /> Prueba
      </button>
    </div>
  )
}
