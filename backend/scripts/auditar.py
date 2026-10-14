"""Auditoria del motor: juega miles de recorridos al azar y verifica que la plata cierre.

Uso: python scripts/auditar.py [cantidad]
Chequea, despues de cada decision y de cada cierre:
  - que no haya efectivo, inversiones ni deudas negativas, ni valores invalidos;
  - patrimonio = efectivo + inversiones (y lo que te deben) - deudas;
  - disponible = efectivo + inversiones que se sacan en el dia;
  - la cartera suma lo mismo que el patrimonio;
  - la cascada del cierre: inicio + sueldo + decisiones + rendimientos - intereses - compras - cuotas - inflacion = final;
  - cuotas pagadas + atrasadas = meses cerrados; si quedo una cuota atrasada es porque no alcanzaba;
  - si quedo deuda de tarjeta es porque no quedaba efectivo ni inversiones liquidas;
  - criterio = 50 + 50/24 x (acertadas - incorrectas - riesgosas/3): 100 solo si acierta las 24.
Ademas compara, escenario por escenario, el resultado final de cada opcion contra la acertada.
"""
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import contenido, motor  # noqa: E402

P, INF = contenido.PARAMETROS, contenido.INFLACION_MENSUAL
ESC = contenido.ESCENARIOS
TOL = 1.0


def a_motor(o):
    return motor.OpcionMotor(0, o["delta_ahorro"], o["delta_deuda"], o["clasificacion"], o["tipo_error"], o.get("ops"))


errores = defaultdict(list)


def falla(tipo, detalle):
    if len(errores[tipo]) < 5:
        errores[tipo].append(detalle)
    else:
        errores[tipo].append(None)


def revisar_estado(e, donde):
    for x in [e.efectivo] + [p.saldo() for p in e.posiciones]:
        if not math.isfinite(x):
            falla("valor invalido", donde)
    if e.efectivo < -TOL:
        falla("efectivo negativo", (donde, e.efectivo))
    for p in e.posiciones:
        if p.saldo() < -TOL:
            falla("posicion negativa", (donde, p.nombre, p.saldo()))
    b = motor.barras(P, e)
    if abs(b["patrimonio_neto"] - (b["efectivo"] + b["inversiones"] - b["deuda"])) > 2:
        falla("patrimonio no cierra", (donde, b))
    liquido = sum(p.valor for p in e.de_tipo("inversion") if p.liquida)
    if abs(b["disponible"] - (e.efectivo + liquido)) > 1:
        falla("disponible no cierra", (donde, b))
    cart = motor.cartera(e)
    tiene = sum(x["valor"] for x in cart if x["tipo"] in ("efectivo", "inversion", "a_cobrar"))
    debe = sum(x["valor"] for x in cart if x["tipo"] in ("deuda_cuotas", "deuda_abierta"))
    if abs((tiene - debe) - b["patrimonio_neto"]) > len(cart) + 1:
        falla("cartera no suma el patrimonio", (donde, tiene, debe, b["patrimonio_neto"]))
    crit = round(50 + 50 / 24 * (e.acertadas - e.incorrectas - e.riesgosas / 3), 1)
    if abs(crit - motor.criterio_pct(e)) > 0.05 or not 0 <= crit <= 100:
        falla("criterio mal calculado", donde)


def jugar(elecciones):
    """Juega paso a paso para poder revisar despues de cada decision y de cada cierre."""
    ops = [a_motor(ESC[i]["opciones"][j]) for i, j in enumerate(elecciones)]
    for n in range(1, len(ops) + 1):  # despues de cada decision, antes del cierre
        e = motor.simular(P, INF, ops[:n], cerrar_ultimo=False)
        revisar_estado(e, f"decision {n}")
    final = motor.simular(P, INF, ops)
    revisar_estado(final, "final")
    for c in final.cierres:
        previo = motor.simular(P, INF, ops[:2 * c.mes], cerrar_ultimo=False)
        pre = previo.patrimonio_neto()
        decisiones = pre - c.patrimonio_inicio - c.cobro_neto
        cuotas = c.cuotas_pagadas_en_cierre * P["cuota_viaje"]
        calculado = (c.patrimonio_inicio + c.cobro_neto + decisiones + c.rendimientos - c.interes_deuda
                     - c.compras - cuotas - c.perdida_inflacion)
        if abs(calculado - c.patrimonio_neto) > 6:
            falla("cascada del cierre no cierra", (c.mes, round(calculado), c.patrimonio_neto))
        if c.cuotas_pagadas_total + c.cuotas_atrasadas != c.mes:
            falla("cuotas no cuentan los meses", (c.mes, c.cuotas_pagadas_total, c.cuotas_atrasadas))
        if c.perdida_inflacion < -1:
            falla("la inflacion sumo plata", (c.mes, c.perdida_inflacion))
    # reglas del cierre, mes por mes
    for mes in range(1, 13):
        e = motor.simular(P, INF, ops[:2 * mes])
        e_cerrado = e.cierres[-1]
        liquido = sum(x["valor"] for x in e_cerrado.cartera if x["tipo"] == "inversion" and x["liquida"])
        deuda_tarjeta = sum(x["valor"] for x in e_cerrado.cartera if x["tipo"] == "deuda_abierta")
        if e_cerrado.cuotas_atrasadas and (e_cerrado.efectivo_antes_cuota >= P["cuota_viaje"] * 1.0001
                                           and e_cerrado.cuotas_pagadas_en_cierre == 0):
            falla("cuota impaga habiendo plata", (mes, e_cerrado.efectivo_antes_cuota))
        if deuda_tarjeta > TOL and (e_cerrado.efectivo_final > TOL or liquido > TOL):
            falla("quedo deuda de tarjeta habiendo plata", (mes, deuda_tarjeta, e_cerrado.efectivo_final, liquido))
        if deuda_tarjeta > TOL and not any(m["tipo"] == "impago" for m in e_cerrado.movimientos):
            falla("quedo deuda de tarjeta sin aviso", mes)
    return final


def main(n):
    rng = random.Random(2026)
    perfiles = ["azar", "bueno", "malo", "riesgoso", "mixto"]
    llegan = 0
    for k in range(n):
        perfil = perfiles[k % len(perfiles)]
        elecciones = []
        for e in ESC:
            ops = e["opciones"]
            if perfil == "azar":
                j = rng.randrange(len(ops))
            else:
                pref = {"bueno": "acertada", "malo": "incorrecta", "riesgoso": "riesgosa"}.get(perfil)
                if perfil == "mixto" or rng.random() < 0.25:
                    pref = rng.choice(["acertada", "riesgosa", "incorrecta"])
                j = next(i for i, o in enumerate(ops) if o["clasificacion"] == pref)
            elecciones.append(j)
        final = jugar(elecciones)
        llegan += final.cuotas_pagadas == 12
    print(f"Recorridos simulados: {n}. Completaron el viaje: {100 * llegan / n:.1f}%")
    if errores:
        print("\nINCONSISTENCIAS:")
        for t, ej in errores.items():
            print(f"  {t}: {len(ej)} casos. Ejemplos: {[x for x in ej if x][:3]}")
    else:
        print("Sin inconsistencias.")

    # Cada opcion contra la acertada, con el resto del recorrido igual. Se mide la plata
    # final mas las cuotas del viaje pagadas (una cuota impaga no es plata ganada).
    print("\nCada opcion frente a la acertada (promedio sobre 300 recorridos al azar):")
    bases = [[rng.randrange(len(e["opciones"])) for e in ESC] for _ in range(300)]

    def valor(elec):
        fin = motor.simular(P, INF, [a_motor(ESC[k]["opciones"][x]) for k, x in enumerate(elec)])
        return fin.patrimonio_neto() + P["cuota_viaje"] * fin.cuotas_pagadas

    raros = 0
    for i, e in enumerate(ESC):
        ac = next(j for j, o in enumerate(e["opciones"]) if o["clasificacion"] == "acertada")
        fila = []
        for j, o in enumerate(e["opciones"]):
            if j == ac:
                continue
            ds = []
            for b in bases:
                b1, b2 = list(b), list(b)
                b1[i], b2[i] = ac, j
                ds.append(valor(b2) - valor(b1))
            prom = sum(ds) / len(ds)
            gana = sum(d > 1 for d in ds) / len(ds)
            marca = "  <-- conviene mas que la acertada" if prom > 0 else ""
            raros += bool(marca)
            fila.append(f"{o['clasificacion'][:3]} {prom:+,.0f} (gana en {100 * gana:.0f}%){marca}".replace(",", "."))
        print(f"  Mes {e['mes']}-{e['orden']} ({e['eje_tematico']}): " + " | ".join(fila))
    print(f"\nOpciones que en promedio convienen mas que la acertada: {raros}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 5000)
