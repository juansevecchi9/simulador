"""Carga el contenido fijo (escenarios, opciones, inflacion, parametros) y un curso de ejemplo."""
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from . import contenido, servicios
from .db import Base, engine
from .models import Curso, Decision, Escenario, InflacionMensual, Opcion, ParametroGlobal

CURSO_DEMO = {"curso_id": 1001, "nombre": "5° A - Ciencias Sociales", "codigo_acceso": "DOCE2026"}


CAMPOS_OPCION = ("texto_opcion", "delta_ahorro", "delta_deuda", "clasificacion", "tipo_error", "mensaje_feedback")


def _campos(op: dict) -> dict:
    """Columnas de la tabla Opcion (las operaciones mes a mes viven en contenido.py)."""
    return {k: op[k] for k in CAMPOS_OPCION}


def cargar_contenido(db: Session) -> None:
    """Reemplaza escenarios/opciones/parametros por los de contenido.py (idempotente)."""
    if db.scalar(select(Escenario).limit(1)) is None:
        for i, esc in enumerate(contenido.ESCENARIOS, start=1):
            e = Escenario(escenario_id=i, mes=esc["mes"], orden=esc["orden"],
                          eje_tematico=esc["eje_tematico"], texto_situacion=esc["texto_situacion"])
            db.add(e)
            for j, op in enumerate(esc["opciones"], start=1):
                db.add(Opcion(opcion_id=i * 10 + j, escenario_id=i, **_campos(op)))
    else:  # actualizar textos y montos sin tocar ids (los docentes pueden pedir cambios de contenido)
        for i, esc in enumerate(contenido.ESCENARIOS, start=1):
            e = db.get(Escenario, i)
            e.texto_situacion = esc["texto_situacion"]
            for j, op in enumerate(esc["opciones"], start=1):
                o = db.get(Opcion, i * 10 + j)
                if o is None:  # opcion agregada despues de la primera carga
                    db.add(Opcion(opcion_id=i * 10 + j, escenario_id=i, **_campos(op)))
                    continue
                for k, v in _campos(op).items():
                    setattr(o, k, v)
        # Opciones que ya no estan en el contenido (se quitaron): se borran junto con
        # las decisiones de prueba que las eligieron.
        for i, esc in enumerate(contenido.ESCENARIOS, start=1):
            for o in list(db.scalars(select(Opcion).where(Opcion.escenario_id == i,
                                                          Opcion.opcion_id > i * 10 + len(esc["opciones"])))):
                db.execute(delete(Decision).where(Decision.opcion_elegida_id == o.opcion_id))
                db.delete(o)
    for mes, pct in contenido.INFLACION_MENSUAL.items():
        db.merge(InflacionMensual(mes=mes, porcentaje=pct))
    for clave, valor in contenido.PARAMETROS.items():
        db.merge(ParametroGlobal(clave=clave, valor=valor))
    if db.get(Curso, CURSO_DEMO["curso_id"]) is None:
        db.add(Curso(**CURSO_DEMO))
    db.commit()


def init_db(db: Session) -> None:
    Base.metadata.create_all(engine)
    cargar_contenido(db)
    servicios.invalidar_catalogo()
