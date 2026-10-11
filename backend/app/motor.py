"""Motor de escenarios y de calculo de consecuencias.

El estado financiero del alumno (efectivo, deuda, cuotas pagadas) no se
guarda como dato suelto: se recalcula reproduciendo sus decisiones sobre los
parametros globales y la inflacion mensual. Asi el resultado es siempre
consistente con el contenido parametrizado y con el registro de decisiones.

Ciclo de cada mes:
  1. Cobro: efectivo += ingreso del mes - gastos fijos.
  2. Decision 1 y decision 2: se aplican delta_ahorro y delta_deuda de la
     opcion elegida. Si el efectivo queda negativo, el faltante pasa a deuda
     (giro en descubierto). Un delta_deuda negativo cancela deuda existente
     hasta lo que se deba; el sobrante vuelve al efectivo.
  3. Cierre: se paga la cuota del viaje (y las atrasadas) si el efectivo
     alcanza; la deuda abierta crece con la tasa mensual; el efectivo
     guardado pierde la inflacion del mes.
"""
from dataclasses import dataclass, field

# Tabla de secuencia de ejes (12 meses x 2 decisiones; cada eje aparece 4 veces).
SECUENCIA_EJES = {
    1: ("presupuesto", "deuda_credito"),
    2: ("intereses", "inflacion"),
    3: ("presupuesto", "riesgo_inversion"),
    4: ("intereses", "ahorro"),
    5: ("deuda_credito", "riesgo_inversion"),
    6: ("inflacion", "ahorro"),
    7: ("presupuesto", "inflacion"),
    8: ("intereses", "deuda_credito"),
    9: ("presupuesto", "ahorro"),
    10: ("intereses", "riesgo_inversion"),
    11: ("deuda_credito", "ahorro"),
    12: ("inflacion", "riesgo_inversion"),
}

TOTAL_DECISIONES = 24


@dataclass
class OpcionMotor:
    opcion_id: int
    delta_ahorro: float
    delta_deuda: float
    clasificacion: str
    tipo_error: str | None


@dataclass
class CierreMes:
    mes: int
    cuotas_pagadas_en_cierre: int
    cuota_del_mes_pagada: bool
    cuotas_atrasadas: int
    interes_deuda: float
    perdida_inflacion: float
    patrimonio_neto: float
    avance_viaje_pct: float
    criterio_financiero_pct: float


@dataclass
class Estado:
    efectivo: float = 0.0
    deuda: float = 0.0
    cuotas_pagadas: int = 0
    cuotas_atrasadas: int = 0
    decisiones: int = 0
    acertadas: int = 0
    mes_actual: int = 1
    orden_actual: int = 1
    terminado: bool = False
    patrimonio_mes_anterior: float = 0.0
    cierres: list[CierreMes] = field(default_factory=list)

    def patrimonio_neto(self) -> float:
        return self.efectivo - self.deuda


def avance_viaje_pct(p: dict, cuotas_pagadas: int) -> float:
    pagado = p["sena_viaje"] + cuotas_pagadas * p["cuota_viaje"]
    return round(100 * pagado / p["costo_total_viaje"], 1)


def criterio_pct(estado: Estado) -> float:
    if estado.decisiones == 0:
        return 0.0
    return round(100 * estado.acertadas / estado.decisiones, 1)


def ingreso_del_mes(p: dict, mes: int) -> float:
    return p["ingreso_base_mensual"] + p.get(f"ingreso_extra_mes_{mes}", 0)


def aplicar_opcion(estado: Estado, op: OpcionMotor) -> None:
    estado.efectivo += op.delta_ahorro
    if op.delta_deuda < 0:
        cancelado = min(-op.delta_deuda, estado.deuda)
        estado.deuda -= cancelado
        estado.efectivo += -op.delta_deuda - cancelado  # lo no usado vuelve
    else:
        estado.deuda += op.delta_deuda
    if estado.efectivo < 0:  # giro en descubierto
        estado.deuda += -estado.efectivo
        estado.efectivo = 0.0
    estado.decisiones += 1
    if op.clasificacion == "acertada":
        estado.acertadas += 1


def cerrar_mes(estado: Estado, p: dict, mes: int, inflacion: float) -> CierreMes:
    estado.cuotas_atrasadas += 1
    pagadas = 0
    while estado.cuotas_atrasadas > 0 and estado.efectivo >= p["cuota_viaje"]:
        estado.efectivo -= p["cuota_viaje"]
        estado.cuotas_pagadas += 1
        estado.cuotas_atrasadas -= 1
        pagadas += 1
    interes = estado.deuda * p["tasa_deuda_abierta_mensual"]
    estado.deuda += interes
    perdida = estado.efectivo * inflacion
    estado.efectivo -= perdida
    cierre = CierreMes(
        mes=mes,
        cuotas_pagadas_en_cierre=pagadas,
        cuota_del_mes_pagada=estado.cuotas_atrasadas == 0,
        cuotas_atrasadas=estado.cuotas_atrasadas,
        interes_deuda=round(interes),
        perdida_inflacion=round(perdida),
        patrimonio_neto=round(estado.patrimonio_neto()),
        avance_viaje_pct=avance_viaje_pct(p, estado.cuotas_pagadas),
        criterio_financiero_pct=criterio_pct(estado),
    )
    estado.cierres.append(cierre)
    return cierre


def simular(p: dict, inflacion: dict[int, float], opciones_elegidas: list[OpcionMotor]) -> Estado:
    """Reproduce el recorrido a partir de las opciones elegidas, en orden."""
    estado = Estado(efectivo=p["efectivo_inicial"] - p["sena_viaje"])
    pendientes = list(opciones_elegidas)
    for mes in range(1, 13):
        estado.mes_actual, estado.orden_actual = mes, 1
        estado.patrimonio_mes_anterior = estado.patrimonio_neto()
        estado.efectivo += ingreso_del_mes(p, mes) - p["gastos_fijos_mensuales"]
        for orden in (1, 2):
            estado.orden_actual = orden
            if not pendientes:
                return estado
            aplicar_opcion(estado, pendientes.pop(0))
        cerrar_mes(estado, p, mes, inflacion[mes])
    estado.terminado = True
    estado.mes_actual, estado.orden_actual = 12, 2
    return estado


def estado_avatar(estado: Estado) -> str:
    """tranquilo / neutral / alerta segun el patrimonio neto (HU-008)."""
    patrimonio = estado.patrimonio_neto()
    if patrimonio < 0:
        return "alerta"
    if patrimonio > estado.patrimonio_mes_anterior and patrimonio > 20_000:
        return "tranquilo"
    return "neutral"


def barras(p: dict, estado: Estado) -> dict:
    return {
        "patrimonio_neto": round(estado.patrimonio_neto()),
        "efectivo": round(estado.efectivo),
        "deuda": round(estado.deuda),
        "avance_viaje_pct": avance_viaje_pct(p, estado.cuotas_pagadas),
        "criterio_financiero_pct": criterio_pct(estado),
    }
