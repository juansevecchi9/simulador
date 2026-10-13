"""Reproduce un recorrido a partir del CSV que descarga el modo prueba.

Uso: python scripts/reproducir.py decisiones-12345678.csv
Muestra, mes a mes, cada cierre (movimientos, efectivo, deuda, patrimonio) y la cartera final.
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import contenido, motor  # noqa: E402


def opcion(opcion_id: int) -> dict:
    esc, j = divmod(opcion_id, 10)
    return contenido.ESCENARIOS[esc - 1]["opciones"][j - 1]


def main(ruta: str) -> None:
    with open(ruta, encoding="utf-8-sig") as f:
        filas = list(csv.DictReader(f, delimiter=";"))
    ops = []
    for fila in filas:
        o = opcion(int(fila["opcion_id"]))
        ops.append(motor.OpcionMotor(int(fila["opcion_id"]), o["delta_ahorro"], o["delta_deuda"],
                                     o["clasificacion"], o["tipo_error"], o.get("ops")))
    estado = motor.simular(contenido.PARAMETROS, contenido.INFLACION_MENSUAL, ops)
    for c in estado.cierres:
        print(f"Mes {c.mes}: efectivo {c.efectivo_final}, deuda {c.deuda_final}, patrimonio {c.patrimonio_neto}, "
              f"cuotas {c.cuotas_pagadas_total}/12")
        for m in c.movimientos:
            print(f"   {m['posicion']}: {m['texto']}")
    print("Barras:", motor.barras(contenido.PARAMETROS, estado))
    for x in motor.cartera(estado):
        print(f"   {x['nombre']}: {x['valor']} ({x['detalle']})")


if __name__ == "__main__":
    main(sys.argv[1])
