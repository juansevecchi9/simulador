"""Carga el contenido fijo (escenarios, opciones, inflacion, parametros) y un curso de ejemplo."""
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from . import contenido, servicios
from .db import Base, engine
from .models import AvanceMensual, Curso, Decision, Escenario, Estudiante, InflacionMensual, Opcion, ParametroGlobal

CURSO_DEMO = {"curso_id": 1001, "nombre": "5° A - Ciencias Sociales", "codigo_acceso": "DOCE2026"}


CAMPOS_OPCION = ("texto_opcion", "delta_ahorro", "delta_deuda", "clasificacion", "tipo_error", "mensaje_feedback")


def _campos(op: dict) -> dict:
    """Columnas de la tabla Opcion (las operaciones mes a mes viven en contenido.py)."""
    return {k: op[k] for k in CAMPOS_OPCION}


def cargar_contenido(db: Session) -> None:
    """Reemplaza escenarios/opciones/parametros por los de contenido.py (idempotente).

    Trae todo en pocas consultas (no una por fila): con la base remota (Turso) cada
    consulta es un viaje por la red, y esto corre cada vez que arranca el servidor."""
    escenarios = {e.escenario_id: e for e in db.scalars(select(Escenario))}
    opciones = {o.opcion_id: o for o in db.scalars(select(Opcion))}
    list(db.scalars(select(InflacionMensual)))  # quedan en memoria para los merge de abajo
    list(db.scalars(select(ParametroGlobal)))
    for i, esc in enumerate(contenido.ESCENARIOS, start=1):
        e = escenarios.get(i)
        if e is None:
            db.add(Escenario(escenario_id=i, mes=esc["mes"], orden=esc["orden"],
                             eje_tematico=esc["eje_tematico"], texto_situacion=esc["texto_situacion"]))
        elif e.texto_situacion != esc["texto_situacion"]:  # los docentes pueden pedir cambios de contenido
            e.texto_situacion = esc["texto_situacion"]
        for j, op in enumerate(esc["opciones"], start=1):
            o = opciones.get(i * 10 + j)
            if o is None:
                db.add(Opcion(opcion_id=i * 10 + j, escenario_id=i, **_campos(op)))
                continue
            for k, v in _campos(op).items():
                if getattr(o, k) != v:
                    setattr(o, k, v)
    # Opciones que ya no estan en el contenido (se quitaron): se borran junto con
    # las decisiones de prueba que las eligieron.
    for oid, o in opciones.items():
        i, j = divmod(oid, 10)
        if i > len(contenido.ESCENARIOS) or j > len(contenido.ESCENARIOS[i - 1]["opciones"]):
            db.execute(delete(Decision).where(Decision.opcion_elegida_id == oid))
            db.delete(o)
    for mes, pct in contenido.INFLACION_MENSUAL.items():
        db.merge(InflacionMensual(mes=mes, porcentaje=pct))
    for clave, valor in contenido.PARAMETROS.items():
        db.merge(ParametroGlobal(clave=clave, valor=valor))
    if db.get(Curso, CURSO_DEMO["curso_id"]) is None:
        db.add(Curso(**CURSO_DEMO))
    db.commit()


# Cambiar este valor borra, una sola vez al arrancar el servidor, todos los alumnos y
# sus decisiones (los cursos y el contenido quedan). Sirve para empezar de cero antes
# de una prueba con alumnos.
REINICIO_DATOS = 20261016
CLAVE_REINICIO = "reinicio_datos"


def reiniciar_datos_si_corresponde(db: Session) -> None:
    marca = db.get(ParametroGlobal, CLAVE_REINICIO)
    if marca is not None and int(marca.valor) == REINICIO_DATOS:
        return
    db.execute(delete(AvanceMensual))
    db.execute(delete(Decision))
    db.execute(delete(Estudiante))
    db.merge(ParametroGlobal(clave=CLAVE_REINICIO, valor=REINICIO_DATOS))
    db.commit()


def init_db(db: Session) -> None:
    Base.metadata.create_all(engine)
    cargar_contenido(db)
    reiniciar_datos_si_corresponde(db)
    servicios.invalidar_catalogo()
