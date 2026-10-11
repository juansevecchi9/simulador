"""Modelo de datos segun el Diagrama Entidad-Relacion (Figura 4 de la tesis)."""
from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class Curso(Base):
    __tablename__ = "curso"
    curso_id: Mapped[int] = mapped_column(Integer, primary_key=True)  # codigo que escribe el alumno
    nombre: Mapped[str] = mapped_column(String(60))
    codigo_acceso: Mapped[str] = mapped_column(String(8), unique=True)  # codigo del docente

    estudiantes: Mapped[list["Estudiante"]] = relationship(back_populates="curso")


class Estudiante(Base):
    __tablename__ = "estudiante"
    estudiante_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)  # DNI
    nombre: Mapped[str] = mapped_column(String(60))
    curso_id: Mapped[int] = mapped_column(ForeignKey("curso.curso_id"))
    variante_personaje: Mapped[str | None] = mapped_column(String(10), nullable=True)
    mes_actual: Mapped[int] = mapped_column(Integer, default=1)
    fecha_inicio: Mapped[date] = mapped_column(Date, default=date.today)

    curso: Mapped[Curso] = relationship(back_populates="estudiantes")
    decisiones: Mapped[list["Decision"]] = relationship(back_populates="estudiante")
    avances: Mapped[list["AvanceMensual"]] = relationship(back_populates="estudiante")


class Escenario(Base):
    __tablename__ = "escenario"
    escenario_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mes: Mapped[int] = mapped_column(Integer)
    orden: Mapped[int] = mapped_column(Integer)  # 1 o 2
    eje_tematico: Mapped[str] = mapped_column(String(30))
    texto_situacion: Mapped[str] = mapped_column(Text)

    opciones: Mapped[list["Opcion"]] = relationship(back_populates="escenario", order_by="Opcion.opcion_id")


class Opcion(Base):
    __tablename__ = "opcion"
    opcion_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    escenario_id: Mapped[int] = mapped_column(ForeignKey("escenario.escenario_id"))
    texto_opcion: Mapped[str] = mapped_column(Text)
    delta_ahorro: Mapped[float] = mapped_column(Float)
    delta_deuda: Mapped[float] = mapped_column(Float)
    clasificacion: Mapped[str] = mapped_column(String(12))  # acertada | riesgosa | incorrecta
    tipo_error: Mapped[str | None] = mapped_column(String(40), nullable=True)
    mensaje_feedback: Mapped[str] = mapped_column(Text)

    escenario: Mapped[Escenario] = relationship(back_populates="opciones")


class Decision(Base):
    __tablename__ = "decision"
    decision_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    estudiante_id: Mapped[int] = mapped_column(ForeignKey("estudiante.estudiante_id"))
    opcion_elegida_id: Mapped[int] = mapped_column(ForeignKey("opcion.opcion_id"))
    fecha_hora: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    tiempo_resolucion: Mapped[int] = mapped_column(Integer, default=0)  # segundos

    estudiante: Mapped[Estudiante] = relationship(back_populates="decisiones")
    opcion: Mapped[Opcion] = relationship()


class AvanceMensual(Base):
    __tablename__ = "avance_mensual"
    avance_mensual_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    estudiante_id: Mapped[int] = mapped_column(ForeignKey("estudiante.estudiante_id"))
    mes: Mapped[int] = mapped_column(Integer)
    patrimonio_neto: Mapped[float] = mapped_column(Float)
    avance_viaje_pct: Mapped[float] = mapped_column(Float)
    criterio_financiero_pct: Mapped[float] = mapped_column(Float)
    cuota_pagada: Mapped[bool] = mapped_column(Boolean)

    estudiante: Mapped[Estudiante] = relationship(back_populates="avances")


class InflacionMensual(Base):
    __tablename__ = "inflacion_mensual"
    mes: Mapped[int] = mapped_column(Integer, primary_key=True)
    porcentaje: Mapped[float] = mapped_column(Float)


class ParametroGlobal(Base):
    __tablename__ = "parametro_global"
    clave: Mapped[str] = mapped_column(String(40), primary_key=True)
    valor: Mapped[float] = mapped_column(Float)
