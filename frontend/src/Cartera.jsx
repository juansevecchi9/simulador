import { pesos } from './api'
import { Emo } from './emoji'

const ES_DEUDA = new Set(['deuda_cuotas', 'deuda_abierta'])
const TITULO = { efectivo: 'Plata', inversion: 'Inversión', a_cobrar: 'A cobrar', deuda_cuotas: 'Deuda en cuotas', deuda_abierta: 'Deuda', compra: 'Compra pendiente' }

/** Todo lo que el alumno tiene y debe, siempre a la vista. */
export default function Cartera({ items, compacta = false }) {
  if (!items) return null
  const tiene = items.filter((x) => !ES_DEUDA.has(x.tipo) && x.tipo !== 'compra').reduce((a, x) => a + x.valor, 0)
  const debe = items.filter((x) => ES_DEUDA.has(x.tipo)).reduce((a, x) => a + x.valor, 0)
  const lista = (
    <div className="cartera-lista" role="list">
      {items.map((x) => {
        const clase = ES_DEUDA.has(x.tipo) ? 'debe' : x.tipo === 'compra' ? 'compra' : x.tipo === 'efectivo' ? 'plata' : 'tiene'
        return (
          <div className={`cartera-item ${clase}`} role="listitem" key={`${x.tipo}-${x.id}`}>
            <div className="cartera-cab"><Emo e={x.emoji} size={20} /><small>{TITULO[x.tipo]}</small></div>
            <b className="cartera-nombre" title={x.nombre}>{x.nombre}</b>
            <span className="cartera-valor">{ES_DEUDA.has(x.tipo) ? '-' : ''}{pesos(x.valor)}</span>
            <small className="cartera-detalle">{x.detalle}</small>
          </div>
        )
      })}
    </div>
  )
  const resumen = (
    <span className="cartera-totales">
      <span className="t-tiene">Tenés {pesos(tiene)}</span>
      <span className="t-debe">Debés {pesos(debe)}</span>
    </span>
  )
  if (compacta) {
    return (
      <details className="cartera cartera-compacta">
        <summary><Emo e="💼" size={18} /> <b>Tu cartera</b>{resumen}</summary>
        {lista}
      </details>
    )
  }
  return (
    <section className="cartera" aria-label="Tu cartera: lo que tenés y lo que debés">
      <div className="cartera-titulo"><Emo e="💼" size={18} /><b>Tu cartera</b>{resumen}</div>
      {lista}
    </section>
  )
}
