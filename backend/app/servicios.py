"""Logica de aplicacion sobre la base de datos: estado del alumno, decisiones, metricas docentes."""
import random
from collections import Counter, defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import contenido, motor
from .models import AvanceMensual, Decision, Escenario, Estudiante, InflacionMensual, Opcion, ParametroGlobal

SEVERIDAD = {"riesgosa": "nivel leve", "incorrecta": "nivel severo"}


def parametros(db: Session) -> dict:
    return {p.clave: p.valor for p in db.scalars(select(ParametroGlobal))}


def inflacion(db: Session) -> dict[int, float]:
    return {i.mes: i.porcentaje for i in db.scalars(select(InflacionMensual))}


def escenarios_ordenados(db: Session) -> list[Escenario]:
    return list(db.scalars(select(Escenario).order_by(Escenario.mes, Escenario.orden)))


def decisiones_de(db: Session, dni: int) -> list[Decision]:
    q = (select(Decision).join(Opcion, Decision.opcion_elegida_id == Opcion.opcion_id)
         .join(Escenario).where(Decision.estudiante_id == dni)
         .order_by(Escenario.mes, Escenario.orden))
    return list(db.scalars(q))


def _a_motor(op: Opcion) -> motor.OpcionMotor:
    return motor.OpcionMotor(op.opcion_id, op.delta_ahorro, op.delta_deuda, op.clasificacion, op.tipo_error)


def estado_de(db: Session, dni: int) -> motor.Estado:
    decs = decisiones_de(db, dni)
    return motor.simular(parametros(db), inflacion(db), [_a_motor(d.opcion) for d in decs])


def escenario_actual(db: Session, dni: int) -> Escenario | None:
    hechos = {d.opcion.escenario_id for d in decisiones_de(db, dni)}
    for e in escenarios_ordenados(db):
        if e.escenario_id not in hechos:
            return e
    return None


def opciones_mezcladas(esc: Escenario, dni: int) -> list[Opcion]:
    """Orden de opciones distinto por alumno y estable entre recargas (sin revelar la correcta)."""
    ops = list(esc.opciones)
    random.Random(f"{dni}-{esc.escenario_id}").shuffle(ops)
    return ops


def encabezado_economia(db: Session) -> dict:
    p = parametros(db)
    inf = inflacion(db)
    return {
        "inflacion_mensual_pct": round(100 * inf.get(1, 0.02), 1),
        "suba_dolar_mensual_pct": round(100 * p["suba_dolar_mensual"], 1),
        "cuota_viaje": p["cuota_viaje"],
        "costo_total_viaje": p["costo_total_viaje"],
        "sena_viaje": p["sena_viaje"],
        "gastos_fijos_mensuales": p["gastos_fijos_mensuales"],
        "tasa_deuda_abierta_pct": round(100 * p["tasa_deuda_abierta_mensual"], 1),
    }


def vista_alumno(db: Session, est: Estudiante) -> dict:
    p = parametros(db)
    estado = estado_de(db, est.estudiante_id)
    esc = escenario_actual(db, est.estudiante_id)
    escenario = None
    if esc is not None:
        escenario = {
            "escenario_id": esc.escenario_id,
            "mes": esc.mes,
            "orden": esc.orden,
            "texto_situacion": esc.texto_situacion,
            "nota_ingreso": contenido.NOTA_INGRESO.get(esc.mes) if esc.orden == 1 else None,
            "ingreso_del_mes": motor.ingreso_del_mes(p, esc.mes),
            # Sin clasificacion ni eje: el alumno no debe saber que se evalua.
            "opciones": [{"opcion_id": o.opcion_id, "texto": o.texto_opcion}
                         for o in opciones_mezcladas(esc, est.estudiante_id)],
        }
    return {
        "estudiante": {"dni": est.estudiante_id, "nombre": est.nombre, "curso_id": est.curso_id,
                       "variante_personaje": est.variante_personaje},
        "barras": motor.barras(p, estado),
        "avatar": motor.estado_avatar(estado),
        "mes_actual": esc.mes if esc else 12,
        "decisiones_tomadas": estado.decisiones,
        "terminado": esc is None,
        "economia": encabezado_economia(db),
        "escenario": escenario,
    }


def registrar_decision(db: Session, est: Estudiante, opcion_id: int, tiempo: int) -> dict:
    esc = escenario_actual(db, est.estudiante_id)
    if esc is None:
        raise ValueError("El recorrido ya terminó.")
    op = db.get(Opcion, opcion_id)
    if op is None or op.escenario_id != esc.escenario_id:
        raise ValueError("La opción no corresponde al escenario actual.")
    p = parametros(db)
    antes = motor.barras(p, estado_de(db, est.estudiante_id))
    db.add(Decision(estudiante_id=est.estudiante_id, opcion_elegida_id=opcion_id,
                    tiempo_resolucion=max(0, int(tiempo))))
    db.flush()
    estado = estado_de(db, est.estudiante_id)
    despues = motor.barras(p, estado)
    cierre = None
    if esc.orden == 2:  # el mes se cerro: guardar snapshot (AvanceMensual)
        c = estado.cierres[-1]
        db.add(AvanceMensual(estudiante_id=est.estudiante_id, mes=c.mes, patrimonio_neto=c.patrimonio_neto,
                             avance_viaje_pct=c.avance_viaje_pct,
                             criterio_financiero_pct=c.criterio_financiero_pct,
                             cuota_pagada=c.cuota_del_mes_pagada))
        cierre = {
            "mes": c.mes,
            "cuota_del_mes_pagada": c.cuota_del_mes_pagada,
            "cuotas_pagadas_en_cierre": c.cuotas_pagadas_en_cierre,
            "cuotas_atrasadas": c.cuotas_atrasadas,
            "interes_deuda": c.interes_deuda,
            "perdida_inflacion": c.perdida_inflacion,
        }
    sig = escenario_actual(db, est.estudiante_id)
    est.mes_actual = sig.mes if sig else 13
    db.commit()
    return {
        "clasificacion": op.clasificacion,
        "tipo_error": contenido.TIPOS_ERROR.get(op.tipo_error) if op.tipo_error else None,
        "mensaje": op.mensaje_feedback,
        "barras_antes": antes,
        "barras": despues,
        "avatar": motor.estado_avatar(estado),
        "cierre_mes": cierre,
        "terminado": sig is None,
    }


def _conteo_por_eje(decs: list[Decision]) -> dict[str, Counter]:
    por_eje: dict[str, Counter] = defaultdict(Counter)
    for d in decs:
        por_eje[d.opcion.escenario.eje_tematico][d.opcion.clasificacion] += 1
    return por_eje


def resumen_final(db: Session, est: Estudiante) -> dict:
    p = parametros(db)
    estado = estado_de(db, est.estudiante_id)
    b = motor.barras(p, estado)
    decs = decisiones_de(db, est.estudiante_id)
    por_eje = _conteo_por_eje(decs)
    filas = []
    for eje, nombre in contenido.EJES.items():
        c = por_eje.get(eje, Counter())
        filas.append({"eje": eje, "nombre": nombre, "acertadas": c["acertada"],
                      "riesgosas": c["riesgosa"], "incorrectas": c["incorrecta"]})

    def puntaje(f):
        return (f["acertadas"] - f["incorrectas"], -f["incorrectas"])

    mejor = max(filas, key=puntaje)
    peor = min(filas, key=puntaje)
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
        "barras": b,
        "avatar": motor.estado_avatar(estado),
        "mensaje": mensaje,
        "por_eje": filas,
        "punto_fuerte": {**mejor, "importancia": contenido.IMPORTANCIA_EJE[mejor["eje"]]},
        "punto_debil": {**peor, "importancia": contenido.IMPORTANCIA_EJE[peor["eje"]]},
        "terminado": estado.terminado,
    }


# ------------------------------------------------------------------ docente

def _franja(criterio: float) -> str:
    if criterio >= 70:
        return "bien_encaminados"
    if criterio >= 40:
        return "en_riesgo"
    return "necesitan_intervencion"


def _resumen_alumnos(db: Session, curso_id: int) -> list[dict]:
    p = parametros(db)
    inf = inflacion(db)
    out = []
    for est in db.scalars(select(Estudiante).where(Estudiante.curso_id == curso_id).order_by(Estudiante.nombre)):
        decs = decisiones_de(db, est.estudiante_id)
        estado = motor.simular(p, inf, [_a_motor(d.opcion) for d in decs])
        b = motor.barras(p, estado)
        n = len(decs)
        out.append({
            "dni": est.estudiante_id, "nombre": est.nombre, "decisiones": n,
            "finalizacion_pct": round(100 * n / motor.TOTAL_DECISIONES, 1),
            "estado": "completo" if n >= motor.TOTAL_DECISIONES else ("en_curso" if n else "no_inicio"),
            "franja": _franja(b["criterio_financiero_pct"]) if n else None,
            "tiempo_promedio_seg": round(sum(d.tiempo_resolucion for d in decs) / n, 1) if n else None,
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


def _decisiones_curso(db: Session, curso_id: int) -> list[Decision]:
    q = select(Decision).join(Estudiante).where(Estudiante.curso_id == curso_id)
    return list(db.scalars(q))


def panel_ejes(db: Session, curso_id: int) -> list[dict]:
    por_eje = _conteo_por_eje(_decisiones_curso(db, curso_id))
    filas = []
    for eje, nombre in contenido.EJES.items():
        c = por_eje.get(eje, Counter())
        total = sum(c.values())
        pct = (lambda k: round(100 * c[k] / total, 1) if total else 0)
        filas.append({"eje": eje, "nombre": nombre, "total": total, "acertadas_pct": pct("acertada"),
                      "riesgosas_pct": pct("riesgosa"), "incorrectas_pct": pct("incorrecta")})
    return sorted(filas, key=lambda f: (f["acertadas_pct"], -f["incorrectas_pct"]))  # peor primero


def panel_eje_detalle(db: Session, curso_id: int, eje: str) -> list[dict]:
    decs = _decisiones_curso(db, curso_id)
    escenas = []
    escs = [e for e in escenarios_ordenados(db) if e.eje_tematico == eje]
    for n, esc in enumerate(escs, start=1):
        ds = [d for d in decs if d.opcion.escenario_id == esc.escenario_id]
        c = Counter(d.opcion.clasificacion for d in ds)
        fallidas = [d for d in ds if d.opcion.clasificacion != "acertada"]
        dominante = None
        if fallidas:
            sev = Counter(d.opcion.clasificacion for d in fallidas).most_common(1)[0][0]
            opc = Counter(d.opcion.texto_opcion for d in fallidas).most_common(1)[0][0]
            dominante = {"tipo_error": contenido.TIPOS_ERROR[contenido.TIPO_ERROR_POR_EJE[eje]],
                         "severidad": SEVERIDAD[sev], "opcion_mas_elegida": opc}
        total = len(ds)
        escenas.append({
            "escena": n, "escenario_id": esc.escenario_id, "mes": esc.mes,
            "texto_situacion": esc.texto_situacion, "total": total,
            "acertadas_pct": round(100 * c["acertada"] / total, 1) if total else 0,
            "riesgosas_pct": round(100 * c["riesgosa"] / total, 1) if total else 0,
            "incorrectas_pct": round(100 * c["incorrecta"] / total, 1) if total else 0,
            "error_dominante": dominante,
        })
    return escenas


def panel_alumno(db: Session, est: Estudiante) -> dict:
    p = parametros(db)
    decs = decisiones_de(db, est.estudiante_id)
    estado = motor.simular(p, inflacion(db), [_a_motor(d.opcion) for d in decs])
    reincidencia = []
    por_eje = _conteo_por_eje(decs)
    for eje, nombre in contenido.EJES.items():
        c = por_eje.get(eje, Counter())
        reincidencia.append({"eje": nombre, "tipo_error": contenido.TIPOS_ERROR[contenido.TIPO_ERROR_POR_EJE[eje]],
                             "veces": c["riesgosa"] + c["incorrecta"], "leve": c["riesgosa"],
                             "severo": c["incorrecta"], "oportunidades": sum(c.values())})
    n = len(decs)
    return {
        "dni": est.estudiante_id, "nombre": est.nombre,
        "barras": motor.barras(p, estado),
        "trayectoria": [{"mes": c.mes, "patrimonio_neto": c.patrimonio_neto, "avance_viaje_pct": c.avance_viaje_pct,
                         "criterio_financiero_pct": c.criterio_financiero_pct,
                         "cuota_pagada": c.cuota_del_mes_pagada} for c in estado.cierres],
        "cuotas_impagas_en_cierre": sum(1 for c in estado.cierres if not c.cuota_del_mes_pagada),
        "reincidencia": reincidencia,
        "tiempo_promedio_seg": round(sum(d.tiempo_resolucion for d in decs) / n, 1) if n else None,
        "finalizacion_pct": round(100 * n / motor.TOTAL_DECISIONES, 1),
    }
