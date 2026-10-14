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
        out.append(motor.OpcionMotor(0, o["delta_ahorro"], o["delta_deuda"], o["clasificacion"], o["tipo_error"],
                                     o.get("ops")))
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
    assert incorrecta.patrimonio_neto() < prudente.patrimonio_neto() / 4
    assert motor.avance_viaje_pct(P, incorrecta.cuotas_pagadas) < 100
    assert motor.criterio_pct(incorrecta) == 0


def _estado(efectivo=0.0, deuda=0.0, **kw):
    e = motor.Estado(efectivo=efectivo, **kw)
    e.deuda = deuda
    return e


def test_cierre_paga_cuota_interes_cancela_deuda_con_lo_que_sobra_e_inflacion():
    e = _estado(200_000, 10_000)
    c = motor.cerrar_mes(e, P, 1, 0.02)
    assert c.cuotas_pagadas_en_cierre == 1 and c.cuota_del_mes_pagada
    assert c.interes_deuda == 800  # 8% de 10.000
    # 200.000 - 90.000 de cuota - 10.800 de deuda cancelada (queda la reserva de una cuota)
    assert e.deuda == 0 and round(e.efectivo) == round((200_000 - 90_000 - 10_800) / 1.02)


def test_deuda_se_cancela_con_todo_lo_que_sobra_y_avisa_lo_que_queda():
    e = _estado(150_000, 100_000)
    c = motor.cerrar_mes(e, P, 1, 0.0)
    # 100.000 + 8% = 108.000; 150.000 - 90.000 de cuota = 60.000 que cancelan deuda
    assert round(e.deuda) == 48_000 and round(e.efectivo) == 0
    assert any(m["tipo"] == "impago" and "$48.000" in m["texto"] for m in c.movimientos)


def test_cuota_impaga_queda_atrasada_y_se_paga_despues():
    e = _estado(50_000)
    c1 = motor.cerrar_mes(e, P, 1, 0.0)
    assert not c1.cuota_del_mes_pagada and c1.cuotas_atrasadas == 1
    e.efectivo += 200_000
    c2 = motor.cerrar_mes(e, P, 2, 0.0)
    assert c2.cuotas_pagadas_en_cierre == 2 and c2.cuota_del_mes_pagada


def test_cancelar_deuda_no_paga_de_mas():
    e = _estado(200_000, 30_000)
    motor.aplicar_opcion(e, motor.OpcionMotor(0, -98_000, -100_000, "acertada", None))
    assert e.deuda == 0 and e.efectivo == 200_000 - 98_000 + 70_000


def test_descubierto_pasa_a_deuda():
    e = _estado(10_000)
    motor.aplicar_opcion(e, motor.OpcionMotor(0, -30_000, 0, "riesgosa", "x"))
    assert e.efectivo == 0 and e.deuda == 20_000


def test_inversion_rinde_mes_a_mes_y_vuelve_al_vencer():
    e = _estado(100_000)
    op = motor.OpcionMotor(0, 0, 0, "acertada", None,
                           [{"op": "inversion", "nombre": "PF", "monto": 40_000, "tasa": 0.03, "meses": 2}])
    motor.aplicar_opcion(e, op, INF)
    assert e.efectivo == 60_000 and e.inversiones() == 40_000 and e.patrimonio_neto() == 100_000
    sin_inflacion = {m: 0.0 for m in range(1, 13)}
    e.efectivo += 200_000
    motor.cerrar_mes(e, P, 1, 0.0)
    assert round(e.inversiones()) == 41_200  # rindio un mes, todavia no vence
    motor.cerrar_mes(e, P, 2, 0.0)
    assert e.inversiones() == 0  # vencio: volvio al efectivo
    assert sin_inflacion


def test_prestamo_en_cuotas_se_paga_en_sus_meses():
    e = _estado(0)
    op = motor.OpcionMotor(0, 0, 0, "riesgosa", "x",
                           [{"op": "prestamo", "nombre": "Rubén", "recibido": 50_000, "cuotas": [27_000, 27_000]}])
    motor.aplicar_opcion(e, op, {m: 0.0 for m in range(1, 13)})
    assert e.efectivo == 50_000 and e.deuda == 54_000
    e.efectivo += 300_000
    motor.cerrar_mes(e, P, 1, 0.0)
    assert e.deuda == 54_000  # la primera cuota es el mes que viene
    e.mes_actual = 2
    motor.cerrar_mes(e, P, 2, 0.0)
    assert e.deuda == 27_000


def test_si_falta_para_la_cuota_se_sacan_inversiones_liquidas_y_no_las_trabadas():
    e = _estado(150_000)
    ops = [{"op": "inversion", "nombre": "Fondo", "monto": 50_000, "tasa": 0.0, "liquida": True},
           {"op": "inversion", "nombre": "PF 180", "monto": 40_000, "tasa": 0.0, "meses": 6}]
    motor.aplicar_opcion(e, motor.OpcionMotor(0, 0, 0, "acertada", None, ops), INF)
    assert e.efectivo == 60_000
    c = motor.cerrar_mes(e, P, 1, 0.0)
    assert c.cuota_del_mes_pagada and e.efectivo == 0
    assert {x.nombre: round(x.valor) for x in e.posiciones} == {"Fondo": 20_000, "PF 180": 40_000}


def test_aporte_mensual_se_separa_al_cobrar():
    nada = motor.OpcionMotor(0, 0, 0, "acertada", None, [])
    aporte = motor.OpcionMotor(0, 0, 0, "acertada", None,
                               [{"op": "aporte", "nombre": "Fondo", "monto": 22_000, "tasa": 0.02}])
    e = motor.simular(P, INF, [nada] * 11 + [aporte] + [nada] * 2)  # aporte en el mes 6; despues el mes 7
    fondo = next(x for x in e.posiciones if x.nombre == "Fondo")
    # 22.000 en el mes 6 (2% de interes y 2% de inflacion se compensan) + 22.000 al cobrar en los meses 7 y 8
    assert round(fondo.valor) == 66_000


def test_criterio_arranca_en_50_y_se_mueve_de_a_poco():
    e = motor.Estado(efectivo=1e9)
    assert motor.criterio_pct(e) == 50
    for c in ["acertada", "riesgosa", "acertada", "incorrecta"]:
        motor.aplicar_opcion(e, motor.OpcionMotor(0, 0, 0, c, None))
    assert motor.criterio_pct(e) == round(50 + 50 / 24 * (1 - 1 / 3 + 1 - 1), 1)
    for _ in range(30):
        motor.aplicar_opcion(e, motor.OpcionMotor(0, 0, 0, "incorrecta", None))
    assert motor.criterio_pct(e) == 0


def test_avatar_cinco_expresiones():
    e = _estado(0, 150_000)
    assert motor.estado_avatar(e) == "triste"
    e = _estado(0, 5_000)
    assert motor.estado_avatar(e) == "preocupado"
    e = motor.Estado(efectivo=100_000)
    assert motor.estado_avatar(e) == "neutral"  # todavia no decidio
    e.decisiones, e.acertadas = 19, 19
    assert motor.estado_avatar(e) == "euforico"
    e.acertadas, e.riesgosas = 2, 17
    assert motor.estado_avatar(e) == "neutral"


def test_perfil_que_completa_el_viaje_con_buen_criterio_festeja():
    elegir = iter(range(24))
    ops = _ops(lambda esc: _por_clasif("acertada")(esc) if next(elegir) % 5 else _por_clasif("riesgosa")(esc))
    e = motor.simular(P, INF, ops)
    assert motor.avance_viaje_pct(P, e.cuotas_pagadas) == 100 and motor.estado_avatar(e) == "euforico"


def test_feedback_tiene_consecuencia_y_explicacion():
    for esc in contenido.ESCENARIOS:
        for o in esc["opciones"]:
            consecuencia, sep, explicacion = o["mensaje_feedback"].partition(contenido.SEPARADOR_FEEDBACK)
            assert sep and consecuencia.strip() and len(explicacion) > 120


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
    assert client.post("/api/alumnos/40111222/personaje", json={"variante": "hack"}).status_code == 422
    client.post("/api/alumnos/40111222/personaje", json={"variante": "mujer.1.2.3.4.5.6"})
    assert "{nombre}" not in r["escenario"]["texto_situacion"] and "Ana" in r["escenario"]["texto_situacion"]
    rng = random.Random(3)
    for paso in range(24):
        est = client.get("/api/alumnos/40111222/estado").json()
        assert est["escenario"]["mes"] == paso // 2 + 1
        op = rng.choice(est["escenario"]["opciones"])["opcion_id"]
        res = client.post("/api/alumnos/40111222/decisiones", json={"opcion_id": op, "tiempo_resolucion": 20}).json()
        assert res["consecuencia"] and res["explicacion"] and res["siguiente"] and (res["cierre_mes"] is not None) == (paso % 2 == 1)
    assert res["terminado"]
    # reingreso con el mismo DNI continua donde lo dejo y conserva el personaje
    r2 = client.post("/api/alumnos/ingreso", json={"dni": 40111222, "nombre": "Ana", "curso_id": 1001}).json()
    assert r2["terminado"] and r2["estudiante"]["variante_personaje"] == "mujer.1.2.3.4.5.6"
    assert client.post("/api/alumnos/40111222/personaje", json={"variante": "varon"}).json()["estudiante"][
        "variante_personaje"] == "mujer.1.2.3.4.5.6"
    hist = client.get("/api/alumnos/40111222/historial").json()
    assert len(hist) == 24 and all(h["elegida_id"] in [o["opcion_id"] for o in h["opciones"]] for h in hist)
    resumen = client.get("/api/alumnos/40111222/resumen").json()
    assert sum(f["acertadas"] + f["riesgosas"] + f["incorrectas"] for f in resumen["por_eje"]) == 24
    assert resumen["puntos_fuertes"] and all(f["importancia"] for f in resumen["puntos_fuertes"])

    cur = client.post("/api/docente/ingreso", json={"codigo_acceso": "doce2026"}).json()
    g = client.get(f"/api/docente/cursos/{cur['curso_id']}/general", params={"codigo": "DOCE2026"}).json()
    assert g["cantidad_alumnos"] == 1 and g["estados"] == {"completo": 1}
    ejes = client.get(f"/api/docente/cursos/1001/ejes", params={"codigo": "DOCE2026"}).json()
    assert len(ejes) == 6 and ejes[0]["acertadas_pct"] <= ejes[-1]["acertadas_pct"]
    det = client.get(f"/api/docente/cursos/1001/ejes/ahorro", params={"codigo": "DOCE2026"}).json()
    assert len(det["escenas"]) == 4
    al = client.get(f"/api/docente/cursos/1001/alumnos/40111222", params={"codigo": "DOCE2026"}).json()
    assert len(al["trayectoria"]) == 12 and al["finalizacion_pct"] == 100


def test_cuotas_que_salen_de_un_fondo():
    """Las cuotas vinculadas a un fondo se pagan sacando de ese fondo, no del sueldo."""
    e = motor.Estado(efectivo=0)
    e.mes_actual = 6
    op = motor.OpcionMotor(1, 0, 0, "acertada", None, [
        {"op": "efectivo", "monto": 50_000},
        {"op": "prestamo", "nombre": "Cuotas", "emoji": "🥾", "cuotas": [25_000, 25_000], "recibido": 0,
         "paga_con": "Fondo"},
        {"op": "inversion", "nombre": "Fondo", "emoji": "💧", "monto": 50_000, "tasa": 0.03, "liquida": True}])
    motor.aplicar_opcion(e, op)
    e.efectivo = 200_000
    motor.cerrar_mes(e, P, 6, 0.0)
    motor.cerrar_mes(e, P, 7, 0.0)
    fondo = e.de_tipo("inversion")[0]
    assert round(fondo.valor) == round(50_000 * 1.03 * 1.03 - 25_000)


def test_refinanciar_solo_la_deuda():
    """Sin deuda de tarjeta no se toma el prestamo; con deuda, solo lo necesario."""
    op = motor.OpcionMotor(1, 0, 0, "acertada", None, [
        {"op": "refinanciar", "nombre": "Préstamo", "recibido": 100_000, "cuotas": [101_500], "solo_deuda": True,
         "inversion": "Plazo", "tasa_inversion": 0.025}])
    e = motor.Estado(efectivo=10_000)
    motor.aplicar_opcion(e, op)
    assert e.posiciones == [] and e.efectivo == 10_000
    e = motor.Estado(efectivo=10_000)
    e.deuda = 40_000
    motor.aplicar_opcion(e, op)
    assert e.deuda_abierta() == 0
    assert e.de_tipo("deuda_cuotas")[0].pagos[0][2] == 40_600
    assert e.de_tipo("inversion") == [] and e.efectivo == 10_000


def test_prestamo_para_invertir_que_vence_junto():
    """Préstamo y plazo fijo en pesos que vencen juntos: la inflación no cambia la cuenta,
    solo le saca valor a la ganancia."""
    e = motor.Estado(efectivo=0)
    e.mes_actual = 11
    op = motor.OpcionMotor(1, 0, 0, "acertada", None, [
        {"op": "prestamo", "nombre": "Préstamo", "emoji": "🏦", "cuotas": [1_500, 101_500], "recibido": 100_000,
         "desde": 0, "paga_con": "Plazo"},
        {"op": "inversion", "nombre": "Plazo", "emoji": "🏦", "monto": 100_000, "tasa": 0.025, "meses": 2}])
    motor.aplicar_opcion(e, op)
    e.efectivo = 1_500  # para el interés del primer mes
    motor.cerrar_mes(e, P, 11, 0.02)
    motor.cerrar_mes(e, P, 12, 0.02)
    assert e.deuda == 0 and e.de_tipo("inversion") == []
    # $105.063 − $101.500 = $3.563 (más los $1.500 que pusiste) → gana $2.063, que pierden algo con la inflación
    assert 3_450 < e.efectivo < 3_563
