import os
import re
from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from . import contenido, servicios
from .db import SessionLocal, get_db
from .models import Curso, Decision, Estudiante
from .seed import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    with SessionLocal() as db:
        init_db(db)
    yield


app = FastAPI(title="Simulador de decisiones financieras", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


class IngresoAlumno(BaseModel):
    dni: int = Field(gt=0, lt=100_000_000)
    nombre: str = Field(min_length=1, max_length=60)
    curso_id: int


class Personaje(BaseModel):
    variante: str


class NuevaDecision(BaseModel):
    opcion_id: int
    tiempo_resolucion: int = 0


class IngresoDocente(BaseModel):
    codigo_acceso: str = Field(min_length=1)


def _estudiante(db: Session, dni: int) -> Estudiante:
    est = db.get(Estudiante, dni)
    if est is None:
        raise HTTPException(404, "No encontramos un alumno con ese DNI.")
    return est


def _curso_por_codigo(db: Session, codigo: str) -> Curso:
    curso = db.query(Curso).filter(Curso.codigo_acceso == codigo.strip().upper()).first()
    if curso is None:
        raise HTTPException(401, "El código de acceso no es válido.")
    return curso


@app.get("/api/salud")
def salud():
    return {"ok": True, "modo_prueba": MODO_PRUEBA}


# ----------------------------------------------------------------- modo prueba
# Herramientas para validar el contenido sin jugar todo de nuevo. Se apagan
# definiendo la variable de entorno MODO_PRUEBA=0 (antes de la prueba piloto).
MODO_PRUEBA = os.getenv("MODO_PRUEBA", "1") != "0"


class Salto(BaseModel):
    mes: int = Field(ge=1, le=13)


def _solo_prueba():
    if not MODO_PRUEBA:
        raise HTTPException(403, "El modo prueba está apagado.")


@app.post("/api/prueba/{dni}/reiniciar")
def prueba_reiniciar(dni: int, db: Session = Depends(get_db)):
    _solo_prueba()
    est = _estudiante(db, dni)
    servicios.reiniciar(db, est)
    return servicios.vista_alumno(db, est)


@app.post("/api/prueba/{dni}/borrar")
def prueba_borrar(dni: int, db: Session = Depends(get_db)):
    """Borra al alumno con todo su recorrido, para volver a crearlo desde el ingreso."""
    _solo_prueba()
    est = _estudiante(db, dni)
    servicios.reiniciar(db, est)
    db.delete(est)
    db.commit()
    return {"ok": True}


@app.post("/api/prueba/{dni}/saltar")
def prueba_saltar(dni: int, body: Salto, db: Session = Depends(get_db)):
    """Reinicia y responde automaticamente con la opcion acertada hasta el mes pedido."""
    _solo_prueba()
    est = _estudiante(db, dni)
    servicios.reiniciar(db, est)
    servicios.responder_acertadas_hasta(db, est, body.mes)
    return servicios.vista_alumno(db, est)


# ----------------------------------------------------------------- alumno

@app.post("/api/alumnos/ingreso")
def ingreso_alumno(body: IngresoAlumno, db: Session = Depends(get_db)):
    nombre = body.nombre.strip()
    if not nombre:
        raise HTTPException(422, "Completá todos los campos.")
    if db.get(Curso, body.curso_id) is None:
        raise HTTPException(404, "No existe un curso con ese código.")
    est = db.get(Estudiante, body.dni)
    if est is None:
        est = Estudiante(estudiante_id=body.dni, nombre=nombre, curso_id=body.curso_id,
                         mes_actual=1, fecha_inicio=date.today())
        db.add(est)
        db.commit()
    elif est.curso_id != body.curso_id:
        raise HTTPException(409, "Ese DNI ya está registrado en otro curso.")
    return servicios.vista_alumno(db, est)


@app.post("/api/alumnos/{dni}/personaje")
def elegir_personaje(dni: int, body: Personaje, db: Session = Depends(get_db)):
    if not re.fullmatch(r"(varon|mujer)(\.[0-9]{1,2}){0,6}", body.variante):
        raise HTTPException(422, "Variante de personaje inválida.")
    est = _estudiante(db, dni)
    # Se puede ajustar la apariencia antes de la primera decision; despues se mantiene (HU-017).
    if est.variante_personaje is None or not db.query(Decision).filter(Decision.estudiante_id == dni).first():
        est.variante_personaje = body.variante
        db.commit()
    return servicios.vista_alumno(db, est)


@app.get("/api/alumnos/{dni}/estado")
def estado_alumno(dni: int, db: Session = Depends(get_db)):
    return servicios.vista_alumno(db, _estudiante(db, dni))


@app.post("/api/alumnos/{dni}/decisiones")
def decidir(dni: int, body: NuevaDecision, db: Session = Depends(get_db)):
    est = _estudiante(db, dni)
    try:
        return servicios.registrar_decision(db, est, body.opcion_id, body.tiempo_resolucion)
    except ValueError as e:
        raise HTTPException(409, str(e))


@app.get("/api/alumnos/{dni}/historial")
def historial(dni: int, db: Session = Depends(get_db)):
    return servicios.historial(db, _estudiante(db, dni))


@app.get("/api/alumnos/{dni}/resumen")
def resumen(dni: int, db: Session = Depends(get_db)):
    return servicios.resumen_final(db, _estudiante(db, dni))


# ----------------------------------------------------------------- docente

@app.post("/api/docente/ingreso")
def ingreso_docente(body: IngresoDocente, db: Session = Depends(get_db)):
    curso = _curso_por_codigo(db, body.codigo_acceso)
    return {"curso_id": curso.curso_id, "nombre": curso.nombre}


def _curso_autorizado(db: Session, curso_id: int, codigo: str) -> Curso:
    curso = _curso_por_codigo(db, codigo)
    if curso.curso_id != curso_id:
        raise HTTPException(403, "Ese código no corresponde a este curso.")
    return curso


@app.get("/api/docente/cursos/{curso_id}/general")
def docente_general(curso_id: int, codigo: str, db: Session = Depends(get_db)):
    curso = _curso_autorizado(db, curso_id, codigo)
    return {"curso": {"curso_id": curso.curso_id, "nombre": curso.nombre},
            **servicios.panel_general(db, curso_id)}


@app.get("/api/docente/cursos/{curso_id}/ejes")
def docente_ejes(curso_id: int, codigo: str, db: Session = Depends(get_db)):
    _curso_autorizado(db, curso_id, codigo)
    return servicios.panel_ejes(db, curso_id)


@app.get("/api/docente/cursos/{curso_id}/ejes/{eje}")
def docente_eje(curso_id: int, eje: str, codigo: str, db: Session = Depends(get_db)):
    _curso_autorizado(db, curso_id, codigo)
    if eje not in contenido.EJES:
        raise HTTPException(404, "Eje inexistente.")
    return {"eje": eje, "nombre": contenido.EJES[eje], "escenas": servicios.panel_eje_detalle(db, curso_id, eje)}


@app.get("/api/docente/cursos/{curso_id}/alumnos/{dni}")
def docente_alumno(curso_id: int, dni: int, codigo: str, db: Session = Depends(get_db)):
    _curso_autorizado(db, curso_id, codigo)
    est = _estudiante(db, dni)
    if est.curso_id != curso_id:
        raise HTTPException(404, "El alumno no pertenece a este curso.")
    return servicios.panel_alumno(db, est)
