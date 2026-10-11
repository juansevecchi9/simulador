const BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

async function pedir(ruta, opciones = {}) {
  const res = await fetch(`${BASE}${ruta}`, {
    headers: { 'Content-Type': 'application/json' },
    ...opciones,
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const detalle = Array.isArray(data.detail) ? 'Revisá los datos ingresados.' : data.detail
    throw new Error(detalle || 'No pudimos conectar con el servidor. Probá de nuevo en unos segundos.')
  }
  return data
}

const post = (ruta, body) => pedir(ruta, { method: 'POST', body: JSON.stringify(body) })

export const api = {
  ingresoAlumno: (dni, nombre, cursoId) => post('/api/alumnos/ingreso', { dni: Number(dni), nombre, curso_id: Number(cursoId) }),
  elegirPersonaje: (dni, variante) => post(`/api/alumnos/${dni}/personaje`, { variante }),
  estado: (dni) => pedir(`/api/alumnos/${dni}/estado`),
  decidir: (dni, opcionId, tiempo) => post(`/api/alumnos/${dni}/decisiones`, { opcion_id: opcionId, tiempo_resolucion: tiempo }),
  resumen: (dni) => pedir(`/api/alumnos/${dni}/resumen`),
  ingresoDocente: (codigo) => post('/api/docente/ingreso', { codigo_acceso: codigo }),
  panelGeneral: (cursoId, codigo) => pedir(`/api/docente/cursos/${cursoId}/general?codigo=${encodeURIComponent(codigo)}`),
  panelEjes: (cursoId, codigo) => pedir(`/api/docente/cursos/${cursoId}/ejes?codigo=${encodeURIComponent(codigo)}`),
  panelEje: (cursoId, eje, codigo) => pedir(`/api/docente/cursos/${cursoId}/ejes/${eje}?codigo=${encodeURIComponent(codigo)}`),
  panelAlumno: (cursoId, dni, codigo) => pedir(`/api/docente/cursos/${cursoId}/alumnos/${dni}?codigo=${encodeURIComponent(codigo)}`),
}

export const pesos = (n) => {
  const v = Math.round(n)
  return (v < 0 ? '-$' : '$') + Math.abs(v).toLocaleString('es-AR')
}
