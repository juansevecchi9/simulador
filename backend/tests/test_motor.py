import os
import random
from collections import Counter

os.environ["DATABASE_URL"] = "sqlite:///./test_simulador.db"

import pytest
from fastapi.testclient import TestClient

from app import contenido, motor

P = contenido.PARAMETROS
INF = contenido.INFLACION_MENSUAL


def _ops(elegir):
    out = []
    for esc in contenido.ESCENARIOS:
        idx = elegir(esc)
        o = esc["opciones"][idx]
        out.append(motor.OpcionMotor(0, o["delta_ahorro"], o["delta_deuda"], o["clasificacion"], o["tipo_error"]))
    return out


def _por_clasif(clasif):
    return lambda esc: next(i for i, o in enumerate(esc["opciones"]) if o["clasificacion"] == clasif)


# ------------------------------------------------------------ secuencia y contenido (HU-001)

def test_secuencia_cada_eje_cuatro_veces_y_sin_repetir_en_el_mes():
    conteo = Counter(e for par in motor.SECUENCIA_EJES.values() for e in par)
    assert set(conteo) == set(contenido.EJES) and all(v == 4 for v in conteo.values())
    assert all(a != b for a, b in motor.SECUENCIA_EJES.values())


def test_contenido_respeta_la_secuencia():
    assert len(contenido.ESCENARIOS) == 24
    for esc in contenido.ESCENARIOS:
        assert motor.SECUENCIA_EJES[esc["mes"]][esc["orden"] - 1] == esc["eje_tematico"]


def test_cada_escenario_tiene_3_o_4_opciones_con_una_acertada_y_errores_del_eje():
    for esc in contenido.ESCENARIOS:
        ops = esc["opciones"]
        assert 3 <= len(ops) <= 4
        assert any(o["clasificacion"] == "acertada" for o in ops)
        for o in ops:
            if o["clasificacion"] == "acertada":
                assert o["tipo_error"] is None
            else:
                assert o["tipo_error"] == contenido.TIPO_ERROR_POR_EJE[esc["eje_tematico"]]


def test_apariciones_del_mismo_eje_tienen_valores_distintos():
    por_eje = {}
    for esc in contenido.ESCENARIOS:
        firma = tuple((o["delta_ahorro"], o["delta_deuda"]) for o in esc["opciones"])
        por_eje.setdefault(esc["eje_tematico"], []).append(firma)
    for eje, firmas in por_eje.items():
        assert len(set(firmas)) == 4, eje


def test_mensajes_sin_juicios_de_valor():
    prohibidas = ["hiciste mal", "deberías", "error tuyo", "mal hecho"]
    for esc in contenido.ESCENARIOS:
        for o in esc["opciones"]:
            assert not any(p in o["mensaje_feedback"].lower() for p in prohibidas)


# ------------------------------------------------------------ calculo (HU-002, HU-004)

def test_perfiles_de_jugador():
    prudente = motor.simular(P, INF, _ops(_por_clasif("acertada")))
    incorrecta = motor.simular(P, INF, _ops(lambda e: max(i for i, o in enumerate(e["opciones"])
                                                          if o["clasificacion"] == "incorrecta")))
    assert prudente.terminado and motor.avance_viaje_pct(P, prudente.cuotas_pagadas) == 100
    assert prudente.deuda == 0 and prudente.patrimonio_neto() > 200_000
    assert motor.criterio_pct(prudente) == 100
    assert incorrecta.patrimonio_neto() < -300_000
    assert motor.avance_viaje_pct(P, incorrecta.cuotas_pagadas) < 100
    assert motor.criterio_pct(incorrecta) == 0


def test_cierre_aplica_interes_e_inflacion():
    e = motor.Estado(efectivo=200_000, deuda=10_000)
    c = motor.cerrar_mes(e, P, 1, 0.02)
    assert c.cuotas_pagadas_en_cierre == 1 and c.cuota_del_mes_pagada
    assert round(e.deuda) == 10_800
    assert round(e.efectivo) == round((200_000 - 90_000) * 0.98)


def test_cuota_impaga_queda_atrasada_y_se_paga_despues():
    e = motor.Estado(efectivo=50_000)
    c1 = motor.cerrar_mes(e, P, 1, 0.0)
    assert not c1.cuota_del_mes_pagada and c1.cuotas_atrasadas == 1
    e.efectivo += 200_000
    c2 = motor.cerrar_mes(e, P, 2, 0.0)
    assert c2.cuotas_pagadas_en_cierre == 2 and c2.cuota_del_mes_pagada


def test_cancelar_deuda_no_paga_de_mas():
    e = motor.Estado(efectivo=200_000, deuda=30_000)
    motor.aplicar_opcion(e, motor.OpcionMotor(0, -98_000, -100_000, "acertada", None))
    assert e.deuda == 0 and e.efectivo == 200_000 - 98_000 + 70_000


def test_descubierto_pasa_a_deuda():
    e = motor.Estado(efectivo=10_000)
    motor.aplicar_opcion(e, motor.OpcionMotor(0, -30_000, 0, "riesgosa", "x"))
    assert e.efectivo == 0 and e.deuda == 20_000


def test_criterio_es_promedio_corrido():
    e = motor.Estado(efectivo=1e9)
    for c in ["acertada", "riesgosa", "acertada", "incorrecta"]:
        motor.aplicar_opcion(e, motor.OpcionMotor(0, 0, 0, c, None))
    assert motor.criterio_pct(e) == 50


def test_avatar():
    e = motor.Estado(efectivo=0, deuda=5_000)
    assert motor.estado_avatar(e) == "alerta"
    e = motor.Estado(efectivo=100_000, patrimonio_mes_anterior=50_000)
    assert motor.estado_avatar(e) == "tranquilo"
    e = motor.Estado(efectivo=100_000, patrimonio_mes_anterior=120_000)
    assert motor.estado_avatar(e) == "neutral"


# ------------------------------------------------------------ API de punta a punta

@pytest.fixture(scope="module")
def client():
    if os.path.exists("test_simulador.db"):
        os.remove("test_simulador.db")
    from app.main import app
    with TestClient(app) as c:
        yield c
    os.remove("test_simulador.db")


def test_ingreso_validaciones(client):
    assert client.post("/api/alumnos/ingreso", json={"dni": 1, "nombre": "", "curso_id": 1001}).status_code == 422
    assert client.post("/api/alumnos/ingreso", json={"dni": 1, "nombre": "Ana", "curso_id": 9}).status_code == 404
    assert client.post("/api/docente/ingreso", json={"codigo_acceso": "MAL"}).status_code == 401


def test_recorrido_completo_y_panel(client):
    r = client.post("/api/alumnos/ingreso", json={"dni": 40111222, "nombre": "Ana", "curso_id": 1001}).json()
    assert r["escenario"]["mes"] == 1 and r["barras"]["avance_viaje_pct"] == 10.0
    assert all("clasificacion" not in o for o in r["escenario"]["opciones"])
    client.post("/api/alumnos/40111222/personaje", json={"variante": "mujer"})
    rng = random.Random(3)
    for paso in range(24):
        est = client.get("/api/alumnos/40111222/estado").json()
        assert est["escenario"]["mes"] == paso // 2 + 1
        op = rng.choice(est["escenario"]["opciones"])["opcion_id"]
        res = client.post("/api/alumnos/40111222/decisiones", json={"opcion_id": op, "tiempo_resolucion": 20}).json()
        assert res["mensaje"] and (res["cierre_mes"] is not None) == (paso % 2 == 1)
    assert res["terminado"]
    # reingreso con el mismo DNI continua donde lo dejo y conserva el personaje
    r2 = client.post("/api/alumnos/ingreso", json={"dni": 40111222, "nombre": "Ana", "curso_id": 1001}).json()
    assert r2["terminado"] and r2["estudiante"]["variante_personaje"] == "mujer"
    resumen = client.get("/api/alumnos/40111222/resumen").json()
    assert sum(f["acertadas"] + f["riesgosas"] + f["incorrectas"] for f in resumen["por_eje"]) == 24
    assert resumen["punto_fuerte"]["importancia"] and resumen["punto_debil"]["importancia"]

    cur = client.post("/api/docente/ingreso", json={"codigo_acceso": "doce2026"}).json()
    g = client.get(f"/api/docente/cursos/{cur['curso_id']}/general", params={"codigo": "DOCE2026"}).json()
    assert g["cantidad_alumnos"] == 1 and g["estados"] == {"completo": 1}
    ejes = client.get(f"/api/docente/cursos/1001/ejes", params={"codigo": "DOCE2026"}).json()
    assert len(ejes) == 6 and ejes[0]["acertadas_pct"] <= ejes[-1]["acertadas_pct"]
    det = client.get(f"/api/docente/cursos/1001/ejes/ahorro", params={"codigo": "DOCE2026"}).json()
    assert len(det["escenas"]) == 4
    al = client.get(f"/api/docente/cursos/1001/alumnos/40111222", params={"codigo": "DOCE2026"}).json()
    assert len(al["trayectoria"]) == 12 and al["finalizacion_pct"] == 100
