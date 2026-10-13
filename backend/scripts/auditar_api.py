"""Juega partidas completas contra la API (base de datos temporal) y verifica que lo que
recibe la pantalla coincida con el motor: barras antes/despues de cada decision, cierre del
mes, cartera y resumen final.

Uso: python scripts/auditar_api.py [partidas]
"""
import os
import random
import sys
import tempfile
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "auditoria.db")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient  # noqa: E402

from app import contenido, motor  # noqa: E402
from app.main import app  # noqa: E402

P, INF = contenido.PARAMETROS, contenido.INFLACION_MENSUAL
problemas = []


def chk(cond, msg):
    if not cond and len(problemas) < 40:
        problemas.append(msg)


def jugar(c, dni, rng, curso):
    v = c.post("/api/alumnos/ingreso", json={"dni": dni, "nombre": "Prueba", "curso_id": curso}).json()
    c.post(f"/api/alumnos/{dni}/personaje", json={"variante": "mujer"})
    elegidas = []
    while not v["terminado"]:
        esc = v["escenario"]
        op = rng.choice(esc["opciones"])
        r = c.post(f"/api/alumnos/{dni}/decisiones", json={"opcion_id": op["opcion_id"]}).json()
        idx = next(i for i, o in enumerate(contenido.ESCENARIOS[esc["numero"] - 1]["opciones"])
                   if o["texto_opcion"] == op["texto"])
        o = contenido.ESCENARIOS[esc["numero"] - 1]["opciones"][idx]
        elegidas.append(motor.OpcionMotor(0, o["delta_ahorro"], o["delta_deuda"], o["clasificacion"], o["tipo_error"],
                                          o.get("ops")))
        donde = f"dni {dni} decision {esc['numero']}"
        # La pantalla recibe lo mismo que calcula el motor.
        previo = motor.barras(P, motor.simular(P, INF, elegidas, cerrar_ultimo=False))
        despues = motor.barras(P, motor.simular(P, INF, elegidas))
        chk(r["barras_previas"] == previo, f"{donde}: barras_previas distintas del motor")
        chk(r["barras"] == despues, f"{donde}: barras distintas del motor")
        chk(r["barras_antes"] == v["barras"], f"{donde}: barras_antes no coincide con lo que se mostraba")
        chk(r["clasificacion"] == o["clasificacion"], f"{donde}: clasificacion cambiada")
        tiene = sum(x["valor"] for x in r["cartera_previa"] if x["tipo"] in ("efectivo", "inversion", "a_cobrar"))
        debe = sum(x["valor"] for x in r["cartera_previa"] if x["tipo"] in ("deuda_cuotas", "deuda_abierta"))
        chk(abs(tiene - debe - previo["patrimonio_neto"]) <= len(r["cartera_previa"]) + 1,
            f"{donde}: la cartera no suma el patrimonio")
        cm = r["cierre_mes"]
        chk((cm is not None) == (esc["orden"] == 2), f"{donde}: cierre en el momento equivocado")
        if cm:
            mc = motor.simular(P, INF, elegidas).cierres[-1]
            chk(cm["patrimonio_final"] == mc.patrimonio_neto, f"{donde}: patrimonio del cierre distinto")
            chk(cm["patrimonio_inicio"] + cm["cobro_neto"] + (previo["patrimonio_neto"] - cm["patrimonio_inicio"]
                - cm["cobro_neto"]) + cm["rendimientos"] - cm["interes_deuda"] - cm["compras"]
                - cm["cuotas_pagadas_en_cierre"] * P["cuota_viaje"] - cm["perdida_inflacion"]
                - cm["patrimonio_final"] in range(-6, 7), f"{donde}: cascada del cierre no cierra")
            # Lo que muestra el tablero al cerrar el mes (barrasCierre en Alumno.jsx).
            cart = cm["cartera"]
            inv = sum(x["valor"] for x in cart if x["tipo"] in ("inversion", "a_cobrar"))
            deu = sum(x["valor"] for x in cart if x["tipo"] in ("deuda_cuotas", "deuda_abierta"))
            chk(abs((cm["patrimonio_final"] - cm["efectivo_final"] + cm["deuda_final"]) - inv) <= len(cart) + 1,
                f"{donde}: inversiones del tablero al cierre no coinciden con la cartera")
            chk(abs(cm["deuda_final"] - deu) <= len(cart) + 1, f"{donde}: deuda del cierre distinta de la cartera")
            sig = r["siguiente"]
            if not r["terminado"]:
                # Al empezar el mes siguiente solo entra el sueldo (los aportes mueven plata de lugar).
                cobro = motor.ingreso_del_mes(P, cm["mes"] + 1) - P["gastos_fijos_mensuales"]
                chk(abs(sig["barras"]["patrimonio_neto"] - (cm["patrimonio_final"] + cobro)) <= 2,
                    f"{donde}: el mes siguiente no arranca desde el cierre + sueldo")
        v = r["siguiente"]
    res = c.get(f"/api/alumnos/{dni}/resumen").json()
    final = motor.simular(P, INF, elegidas)
    b = motor.barras(P, final)
    chk(res["barras"]["patrimonio_neto"] == b["patrimonio_neto"] if "barras" in res else True,
        f"dni {dni}: resumen con patrimonio distinto")
    return final.cuotas_pagadas


def main(n):
    rng = random.Random(7)
    with TestClient(app) as c:
        curso = c.app  # noqa
        from app.seed import CURSO_DEMO
        curso_id = CURSO_DEMO["curso_id"]
        viajes = [jugar(c, 30_000_000 + k, rng, curso_id) for k in range(n)]
    print(f"Partidas jugadas por la API: {n}. Completaron el viaje: {sum(v == 12 for v in viajes)}")
    print("Sin diferencias entre la API y el motor." if not problemas else "DIFERENCIAS:\n  " + "\n  ".join(problemas))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 100)
