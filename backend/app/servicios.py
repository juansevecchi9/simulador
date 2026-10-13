"""Logica de aplicacion sobre la base de datos: estado del alumno, decisiones, metricas docentes.

Rendimiento: el contenido fijo (escenarios, opciones, parametros, inflacion) se
lee de la base una sola vez y queda en memoria (catalogo). Para cada alumno se
consulta solo la lista de opciones elegidas, en una unica consulta. Asi cada
pedido hace pocas idas y vueltas a la base, sin importar en que mes este.
"""
import random
from collections import Counter, defaultdict
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import contenido, motor
from .models import AvanceMensual, Decision, Escenario, Estudiante, InflacionMensual, Opcion, ParametroGlobal

SEVERIDAD = {"riesgosa": "nivel leve", "incorrecta": "nivel severo"}


# ------------------------------------------------------------------ catalogo en memoria

@dataclass(frozen=True)
class OpcionC:
    opcion_id: int
    escenario_id: int
    texto: str
    delta_ahorro: float
    delta_deuda: float
    clasificacion: str
    tipo_error: str | None
    consecuencia: str
    explicacion: str


@dataclass(frozen=True)
class EscenarioC:
    escenario_id: int
    mes: int
    orden: int
    eje: str
    texto: str
    opciones: tuple[OpcionC, ...]


class Catalogo:
    def __init__(self, db: Session):
        self.parametros = {p.clave: p.valor for p in db.scalars(select(ParametroGlobal))}
        self.inflacion = {i.mes: i.porcentaje for i in db.scalars(select(InflacionMensual))}
        ops_por_esc: dict[int, list[OpcionC]] = defaultdict(list)
        for o in db.scalars(select(Opcion).order_by(Opcion.opcion_id)):
            consecuencia, _, explicacion = o.mensaje_feedback.partition(contenido.SEPARADOR_FEEDBACK)
            ops_por_esc[o.escenario_id].append(OpcionC(
                o.opcion_id, o.escenario_id, o.texto_opcion, o.delta_ahorro, o.delta_deuda,
                o.clasificacion, o.tipo_error, consecuencia.strip(), explicacion.strip()))
        self.escenarios = [
            EscenarioC(e.escenario_id, e.mes, e.orden, e.eje_tematico, e.texto_situacion,
                       tuple(ops_por_esc[e.escenario_id]))
            for e in db.scalars(select(Escenario).order_by(Escenario.mes, Escenario.orden))
        ]
        self.escenario_por_id = {e.escenario_id: e for e in self.escenarios}
        self.opcion_por_id = {o.opcion_id: o for e in self.escenarios for o in e.opciones}


_catalogo: Catalogo | None = None


def catalogo(db: Session) -> Catalogo:
    global _catalogo
    if _catalogo is None:
        _catalogo = Catalogo(db)
    return _catalogo


def invalidar_catalogo() -> None:
    global _catalogo
    _catalogo = None


def parametros(db: Session) -> dict:
    return catalogo(db).parametros


def inflacion(db: Session) -> dict[int, float]:
    return catalogo(db).inflacion


def _a_motor(op: OpcionC) -> motor.OpcionMotor:
    return motor.OpcionMotor(op.opcion_id, op.delta_ahorro, op.delta_deuda, op.clasificacion, op.tipo_error)


def elegidas_de(db: Session, dni: int) -> list[tuple[OpcionC, Decision]]:
    """Decisiones del alumno en el orden del recorrido (una sola consulta)."""
    cat = catalogo(db)
    decs = list(db.scalars(select(Decision).where(Decision.estudiante_id == dni)))
    pares = [(cat.opcion_por_id[d.opcion_elegida_id], d) for d in decs]
    pares.sort(key=lambda p: (cat.escenario_por_id[p[0].escenario_id].mes,
                              cat.escenario_por_id[p[0].escenario_id].orden))
    return pares


def _simular(db: Session, pares) -> motor.Estado:
    return motor.simular(parametros(db), inflacion(db), [_a_motor(o) for o, _ in pares])


def _siguiente_escenario(db: Session, pares) -> EscenarioC | None:
    hechos = {o.escenario_id for o, _ in pares}
    return next((e for e in catalogo(db).escenarios if e.escenario_id not in hechos), None)


def opciones_mezcladas(esc: EscenarioC, dni: int) -> list[OpcionC]:
    """Orden de opciones distinto por alumno y estable entre recargas (sin revelar la correcta)."""
    ops = list(esc.opciones)
    random.Random(f"{dni}-{esc.escenario_id}").shuffle(ops)
    return ops


def _personalizar(texto: str, est: Estudiante) -> str:
    return texto.replace("{nombre}", est.nombre.split()[0].capitalize())


def _texto_docente(texto: str) -> str:
    t = texto.replace("¡Feliz cumpleaños, {nombre}! ", "").replace("{nombre}, ", "").replace("{nombre}", "el alumno")
    return t[:1].upper() + t[1:]


def encabezado_economia(db: Session) -> dict:
    p = parametros(db)
    inf = inflacion(db)
    return {
        "inflacion_mensual_pct": round(100 * inf.get(1, 0.02), 1),
        "suba_dolar_mensual_pct": round(100 * p["suba_dolar_mensual"], 1),
        "cuota_viaje": p["cuota_viaje"],
        "cantidad_cuotas": int(p["cantidad_cuotas"]),
        "costo_total_viaje": p["costo_total_viaje"],
        "sena_viaje": p["sena_viaje"],
        "gastos_fijos_mensuales": p["gastos_fijos_mensuales"],
        "ingreso_base_mensual": p["ingreso_base_mensual"],
        "tasa_deuda_abierta_pct": round(100 * p["tasa_deuda_abierta_mensual"], 1),
        "trabajo": contenido.TRABAJO,
        "destino": contenido.DESTINO,
    }


def _escena(esc: EscenarioC) -> dict:
    pres = contenido.presentacion(esc.mes, esc.orden)
    personaje = contenido.PERSONAJES.get(pres["personaje"]) if pres["personaje"] else None
    return {
        "lugar": pres["lugar"],
        "lugar_nombre": contenido.LUGARES.get(pres["lugar"], ""),
        "personaje": pres["personaje"],
        "personaje_nombre": personaje["nombre"] if personaje else None,
        "personaje_rol": personaje["rol"] if personaje else None,
        "objeto": pres["objeto"],
    }


def _escenario_para_alumno(db: Session, esc: EscenarioC, est: Estudiante) -> dict:
    p = parametros(db)
    return {
        "escenario_id": esc.escenario_id,
        "mes": esc.mes,
        "orden": esc.orden,
        "numero": (esc.mes - 1) * 2 + esc.orden,
        "texto_situacion": _personalizar(esc.texto, est),
        "nota_ingreso": contenido.NOTA_INGRESO.get(esc.mes) if esc.orden == 1 else None,
        "ingreso_del_mes": motor.ingreso_del_mes(p, esc.mes),
        "escena": _escena(esc),
        # Sin clasificacion ni eje: el alumno no debe saber que se evalua.
        "opciones": [{"opcion_id": o.opcion_id, "texto": o.texto} for o in opciones_mezcladas(esc, est.estudiante_id)],
    }


def _vista(db: Session, est: Estudiante, pares) -> dict:
    p = parametros(db)
    estado = _simular(db, pares)
    esc = _siguiente_escenario(db, pares)
    return {
        "estudiante": {"dni": est.estudiante_id, "nombre": est.nombre, "curso_id": est.curso_id,
                       "variante_personaje": est.variante_personaje},
        "barras": motor.barras(p, estado),
        "avatar": motor.estado_avatar(estado),
        "mes_actual": esc.mes if esc else 12,
        "decisiones_tomadas": estado.decisiones,
        "terminado": esc is None,
        "economia": encabezado_economia(db),
        "escenario": _escenario_para_alumno(db, esc, est) if esc else None,
    }


def vista_alumno(db: Session, est: Estudiante) -> dict:
    return _vista(db, est, elegidas_de(db, est.estudiante_id))


def _cierre_dict(c: motor.CierreMes, p: dict) -> dict:
    return {
        "mes": c.mes,
        "cuota_viaje": p["cuota_viaje"],
        "cuota_del_mes_pagada": c.cuota_del_mes_pagada,
        "cuotas_pagadas_en_cierre": c.cuotas_pagadas_en_cierre,
        "cuotas_pagadas_total": c.cuotas_pagadas_total,
        "cuotas_atrasadas": c.cuotas_atrasadas,
        "efectivo_antes_cuota": c.efectivo_antes_cuota,
        "efectivo_final": c.efectivo_final,
        "perdida_inflacion": c.perdida_inflacion,
        "deuda_antes_interes": c.deuda_antes_interes,
        "interes_deuda": c.interes_deuda,
        "deuda_final": c.deuda_final,
        "tasa_deuda_pct": round(100 * p["tasa_deuda_abierta_mensual"], 1),
        "avance_viaje_pct": c.avance_viaje_pct,
    }


def registrar_decision(db: Session, est: Estudiante, opcion_id: int, tiempo: int) -> dict:
    pares = elegidas_de(db, est.estudiante_id)
    esc = _siguiente_escenario(db, pares)
    if esc is None:
        raise ValueError("El recorrido ya terminó.")
    op = catalogo(db).opcion_por_id.get(opcion_id)
    if op is None or op.escenario_id != esc.escenario_id:
        raise ValueError("La opción no corresponde al escenario actual.")
    p = parametros(db)
    antes = motor.barras(p, _simular(db, pares))
    dec = Decision(estudiante_id=est.estudiante_id, opcion_elegida_id=opcion_id,
                   tiempo_resolucion=max(0, int(tiempo)))
    db.add(dec)
    pares = pares + [(op, dec)]
    estado = _simular(db, pares)
    despues = motor.barras(p, estado)
    cierre = None
    if esc.orden == 2:  # el mes se cerro: guardar snapshot (AvanceMensual)
        c = estado.cierres[-1]
        db.add(AvanceMensual(estudiante_id=est.estudiante_id, mes=c.mes, patrimonio_neto=c.patrimonio_neto,
                             avance_viaje_pct=c.avance_viaje_pct,
                             criterio_financiero_pct=c.criterio_financiero_pct,
                             cuota_pagada=c.cuota_del_mes_pagada))
        cierre = _cierre_dict(c, p)
    sig = _siguiente_escenario(db, pares)
    est.mes_actual = sig.mes if sig else 13
    db.commit()
    return {
        "clasificacion": op.clasificacion,
        "tipo_error": contenido.TIPOS_ERROR.get(op.tipo_error) if op.tipo_error else None,
        "consecuencia": _personalizar(op.consecuencia, est),
        "explicacion": _personalizar(op.explicacion, est),
        "opcion_elegida": op.texto,
        "barras_antes": antes,
        "barras": despues,
        "avatar": motor.estado_avatar(estado),
        "cierre_mes": cierre,
        "terminado": sig is None,
        "siguiente": _vista(db, est, pares),
    }


def historial(db: Session, est: Estudiante) -> list[dict]:
    """Decisiones ya tomadas, para volver a mirarlas (sin poder cambiarlas)."""
    cat = catalogo(db)
    out = []
    for op, _ in elegidas_de(db, est.estudiante_id):
        esc = cat.escenario_por_id[op.escenario_id]
        out.append({
            **_escenario_para_alumno(db, esc, est),
            "elegida_id": op.opcion_id,
            "clasificacion": op.clasificacion,
            "consecuencia": _personalizar(op.consecuencia, est),
            "explicacion": _personalizar(op.explicacion, est),
        })
    return out


def _conteo_por_eje(opciones: list[OpcionC], cat: Catalogo) -> dict[str, Counter]:
    por_eje: dict[str, Counter] = defaultdict(Counter)
    for o in opciones:
        por_eje[cat.escenario_por_id[o.escenario_id].eje][o.clasificacion] += 1
    return por_eje


def resumen_final(db: Session, est: Estudiante) -> dict:
    p = parametros(db)
    cat = catalogo(db)
    pares = elegidas_de(db, est.estudiante_id)
    estado = _simular(db, pares)
    b = motor.barras(p, estado)
    por_eje = _conteo_por_eje([o for o, _ in pares], cat)
    filas = []
    for eje, nombre in contenido.EJES.items():
        c = por_eje.get(eje, Counter())
        filas.append({"eje": eje, "nombre": nombre, "acertadas": c["acertada"],
                      "riesgosas": c["riesgosa"], "incorrectas": c["incorrecta"]})

    def puntaje(f):
        return (f["acertadas"] - f["incorrectas"], -f["incorrectas"])

    mejor = max(puntaje(f) for f in filas)
    peor = min(puntaje(f) for f in filas)
    con_importancia = (lambda f: {**f, "importancia": contenido.IMPORTANCIA_EJE[f["eje"]]})
    viaje_ok = b["avance_viaje_pct"] >= 100
    sano = b["patrimonio_neto"] >= 0
    if viaje_ok and sano:
        mensaje = "Cubriste el 100% del viaje y terminaste con tus finanzas en orden."
    elif viaje_ok:
        mensaje = "Cubriste el 100% del viaje, aunque terminaste con deudas que superan lo que tenés."
    elif sano:
        mensaje = "No llegaste a cubrir todo el viaje, aunque terminaste sin deudas que superen lo que tenés."
    else:
        mensaje = "No llegaste a cubrir todo el viaje y terminaste con deudas que superan lo que tenés."
    return {
        "nombre": est.nombre.split()[0].capitalize(),
        "barras": b,
        "avatar": motor.estado_avatar(estado),
        "mensaje": mensaje,
        "acertadas": estado.acertadas, "riesgosas": estado.riesgosas, "incorrectas": estado.incorrectas,
        "por_eje": filas,
        # Si hay empate, se muestran todos los ejes empatados. Un eje sin ninguna
        # decision acertada neta no se muestra como fuerte, y uno perfecto no como debil.
        "puntos_fuertes": [con_importancia(f) for f in filas if puntaje(f) == mejor] if mejor[0] > 0 else [],
        "puntos_debiles": [con_importancia(f) for f in filas if puntaje(f) == peor]
        if (peor != mejor or mejor[0] <= 0) and not (peor[0] == 4) else [],
        "terminado": estado.terminado,
        "economia": encabezado_economia(db),
    }


# ------------------------------------------------------------------ docente

def _franja(criterio: float) -> str:
    if criterio >= 70:
        return "bien_encaminados"
    if criterio >= 40:
        return "en_riesgo"
    return "necesitan_intervencion"


def _decisiones_curso(db: Session, curso_id: int) -> list[Decision]:
    q = select(Decision).join(Estudiante).where(Estudiante.curso_id == curso_id)
    return list(db.scalars(q))


def _resumen_alumnos(db: Session, curso_id: int) -> list[dict]:
    p = parametros(db)
    cat = catalogo(db)
    por_alumno: dict[int, list] = defaultdict(list)
    for d in _decisiones_curso(db, curso_id):
        por_alumno[d.estudiante_id].append((cat.opcion_por_id[d.opcion_elegida_id], d))
    out = []
    for est in db.scalars(select(Estudiante).where(Estudiante.curso_id == curso_id).order_by(Estudiante.nombre)):
        pares = sorted(por_alumno.get(est.estudiante_id, []),
                       key=lambda pr: (cat.escenario_por_id[pr[0].escenario_id].mes,
                                       cat.escenario_por_id[pr[0].escenario_id].orden))
        estado = _simular(db, pares)
        b = motor.barras(p, estado)
        n = len(pares)
        out.append({
            "dni": est.estudiante_id, "nombre": est.nombre, "decisiones": n,
            "finalizacion_pct": round(100 * n / motor.TOTAL_DECISIONES, 1),
            "estado": "completo" if n >= motor.TOTAL_DECISIONES else ("en_curso" if n else "no_inicio"),
            "franja": _franja(b["criterio_financiero_pct"]) if n else None,
            "tiempo_promedio_seg": round(sum(d.tiempo_resolucion for _, d in pares) / n, 1) if n else None,
            **b,
        })
    return out


def panel_general(db: Session, curso_id: int) -> dict:
    alumnos = _resumen_alumnos(db, curso_id)
    activos = [a for a in alumnos if a["decisiones"]]

    def prom(k):
        return round(sum(a[k] for a in activos) / len(activos), 1) if activos else 0

    return {
        "cantidad_alumnos": len(alumnos),
        "avance_promedio_pct": round(sum(a["finalizacion_pct"] for a in alumnos) / len(alumnos), 1) if alumnos else 0,
        "patrimonio_neto_promedio": prom("patrimonio_neto"),
        "avance_viaje_promedio_pct": prom("avance_viaje_pct"),
        "criterio_financiero_promedio_pct": prom("criterio_financiero_pct"),
        "franjas": dict(Counter(a["franja"] for a in activos)),
        "estados": dict(Counter(a["estado"] for a in alumnos)),
        "alumnos": alumnos,
    }


def panel_ejes(db: Session, curso_id: int) -> list[dict]:
    cat = catalogo(db)
    elegidas = [cat.opcion_por_id[d.opcion_elegida_id] for d in _decisiones_curso(db, curso_id)]
    por_eje = _conteo_por_eje(elegidas, cat)
    filas = []
    for eje, nombre in contenido.EJES.items():
        c = por_eje.get(eje, Counter())
        total = sum(c.values())
        pct = (lambda k: round(100 * c[k] / total, 1) if total else 0)
        filas.append({"eje": eje, "nombre": nombre, "total": total, "acertadas_pct": pct("acertada"),
                      "riesgosas_pct": pct("riesgosa"), "incorrectas_pct": pct("incorrecta")})
    return sorted(filas, key=lambda f: (f["acertadas_pct"], -f["incorrectas_pct"]))  # peor primero


def panel_eje_detalle(db: Session, curso_id: int, eje: str) -> list[dict]:
    cat = catalogo(db)
    elegidas = [cat.opcion_por_id[d.opcion_elegida_id] for d in _decisiones_curso(db, curso_id)]
    escenas = []
    for n, esc in enumerate([e for e in cat.escenarios if e.eje == eje], start=1):
        ds = [o for o in elegidas if o.escenario_id == esc.escenario_id]
        c = Counter(o.clasificacion for o in ds)
        fallidas = [o for o in ds if o.clasificacion != "acertada"]
        dominante = None
        if fallidas:
            sev = Counter(o.clasificacion for o in fallidas).most_common(1)[0][0]
            opc = Counter(o.texto for o in fallidas).most_common(1)[0][0]
            dominante = {"tipo_error": contenido.TIPOS_ERROR[contenido.TIPO_ERROR_POR_EJE[eje]],
                         "severidad": SEVERIDAD[sev], "opcion_mas_elegida": opc}
        total = len(ds)
        escenas.append({
            "escena": n, "escenario_id": esc.escenario_id, "mes": esc.mes,
            "texto_situacion": _texto_docente(esc.texto),
            "total": total,
            "acertadas_pct": round(100 * c["acertada"] / total, 1) if total else 0,
            "riesgosas_pct": round(100 * c["riesgosa"] / total, 1) if total else 0,
            "incorrectas_pct": round(100 * c["incorrecta"] / total, 1) if total else 0,
            "error_dominante": dominante,
        })
    return escenas


def panel_alumno(db: Session, est: Estudiante) -> dict:
    p = parametros(db)
    cat = catalogo(db)
    pares = elegidas_de(db, est.estudiante_id)
    estado = _simular(db, pares)
    reincidencia = []
    por_eje = _conteo_por_eje([o for o, _ in pares], cat)
    for eje, nombre in contenido.EJES.items():
        c = por_eje.get(eje, Counter())
        reincidencia.append({"eje": nombre, "tipo_error": contenido.TIPOS_ERROR[contenido.TIPO_ERROR_POR_EJE[eje]],
                             "veces": c["riesgosa"] + c["incorrecta"], "leve": c["riesgosa"],
                             "severo": c["incorrecta"], "oportunidades": sum(c.values())})
    n = len(pares)
    return {
        "dni": est.estudiante_id, "nombre": est.nombre,
        "barras": motor.barras(p, estado),
        "trayectoria": [{"mes": c.mes, "patrimonio_neto": c.patrimonio_neto, "avance_viaje_pct": c.avance_viaje_pct,
                         "criterio_financiero_pct": c.criterio_financiero_pct,
                         "cuota_pagada": c.cuota_del_mes_pagada} for c in estado.cierres],
        "cuotas_impagas_en_cierre": sum(1 for c in estado.cierres if not c.cuota_del_mes_pagada),
        "reincidencia": reincidencia,
        "tiempo_promedio_seg": round(sum(d.tiempo_resolucion for _, d in pares) / n, 1) if n else None,
        "finalizacion_pct": round(100 * n / motor.TOTAL_DECISIONES, 1),
    }
