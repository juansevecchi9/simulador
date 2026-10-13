"""Contenido fijo del recorrido: 12 meses x 2 decisiones = 24 escenarios.

Cada opcion define su impacto (delta_ahorro, delta_deuda en pesos), su
clasificacion (acertada / riesgosa / incorrecta), el tipo de error del eje
(None si es acertada) y el mensaje de retroalimentacion, con dos partes: la
consecuencia en la historia del juego y la explicacion de por que una opcion
conviene mas que las otras (sin juzgar). Cada escenario tiene ademas su puesta
en escena: lugar, personaje que lo plantea y objeto ilustrativo. Los montos ya incluyen el costo total de cada decision
(interes pactado, inflacion), expresados en pesos de hoy.

Convencion de deuda: delta_deuda positivo crea deuda abierta (crece con la
tasa de deuda abierta en cada cierre de mes). delta_deuda negativo cancela
deuda existente hasta lo que se deba; lo que no se usa vuelve al efectivo.
"""

EJES = {
    "presupuesto": "Presupuesto",
    "intereses": "Intereses",
    "deuda_credito": "Deuda y crédito",
    "inflacion": "Inflación",
    "riesgo_inversion": "Riesgo e inversión",
    "ahorro": "Ahorro",
}

TIPO_ERROR_POR_EJE = {
    "presupuesto": "gasto_sin_prevision",
    "intereses": "desconocimiento_interes_compuesto",
    "deuda_credito": "sobreendeudamiento",
    "inflacion": "perdida_poder_adquisitivo",
    "riesgo_inversion": "caida_riesgo_alto",
    "ahorro": "consumismo_inmediato",
}

TIPOS_ERROR = {
    "gasto_sin_prevision": "Gasto sin previsión",
    "desconocimiento_interes_compuesto": "Desconocimiento del interés compuesto",
    "sobreendeudamiento": "Sobreendeudamiento",
    "perdida_poder_adquisitivo": "Pérdida de poder adquisitivo por inacción",
    "caida_riesgo_alto": "Caída en propuesta de alto riesgo",
    "consumismo_inmediato": "Consumismo inmediato",
}

# Frase general sobre la importancia de cada eje (resumen final, HU-009).
IMPORTANCIA_EJE = {
    "presupuesto": "Saber organizar ingresos y gastos es la base para tomar cualquier otra decisión financiera.",
    "intereses": "Entender cómo crece un interés con el tiempo cambia las decisiones de pedir o prestar plata.",
    "deuda_credito": "Manejar bien una deuda evita que los intereses se acumulen sin control.",
    "inflacion": "Entender la inflación explica por qué guardar plata sin usarla también tiene un costo.",
    "riesgo_inversion": "Reconocer una inversión riesgosa protege de perder dinero en propuestas poco confiables.",
    "ahorro": "Formar el hábito de ahorrar es la base para afrontar imprevistos y cumplir metas futuras.",
}

# Parametros globales (tabla ParametroGlobal).
PARAMETROS = {
    "costo_total_viaje": 1_200_000,
    "sena_viaje": 120_000,
    "cuota_viaje": 90_000,
    "cantidad_cuotas": 12,
    "efectivo_inicial": 170_000,
    "gastos_fijos_mensuales": 80_000,
    "ingreso_base_mensual": 220_000,
    "tasa_deuda_abierta_mensual": 0.08,
    "suba_dolar_mensual": 0.01,
    # Variaciones de ingreso por mes (suman o restan al ingreso base).
    "ingreso_extra_mes_4": 40_000,
    "ingreso_extra_mes_7": 0,  # lo que te debe Tano entra por la decision del mes 7
    "ingreso_extra_mes_10": -30_000,
}

INFLACION_MENSUAL = {mes: 0.02 for mes in range(1, 13)}

# ---------------------------------------------------------------- narrativa
# Mundo del juego: el alumno trabaja de delivery los fines de semana en la
# Pizzeria Don Tano y junta plata para el viaje de egresados a Bariloche.
# Mes 1 = enero ... mes 12 = diciembre; el viaje es al terminar el mes 12.
TRABAJO = {"nombre": "Pizzería Don Tano", "emoji": "🍕"}
DESTINO = "Bariloche"

PERSONAJES = {
    "tano": {"nombre": "Tano", "rol": "tu jefe en la pizzería"},
    "ruben": {"nombre": "Tío Rubén", "rol": "tu tío"},
    "cami": {"nombre": "Cami", "rol": "tu mejor amiga del curso"},
    "nico": {"nombre": "Nico", "rol": "tu amigo del curso"},
    "sofi": {"nombre": "Sofi", "rol": "de la agencia Egresados Sur"},
    "laura": {"nombre": "Laura", "rol": "asesora del banco"},
    "flor": {"nombre": "Flor", "rol": "tu prima"},
    "carlitos": {"nombre": "Carlitos", "rol": "tu compañero del curso"},
}

LUGARES = {
    "casa": "Tu casa",
    "pizzeria": "Pizzería Don Tano",
    "bicicleteria": "La bicicletería del barrio",
    "agencia": "Agencia Egresados Sur",
    "banco": "El banco",
    "colegio": "El colegio",
    "celular": "En el celular",
    "shopping": "El shopping",
    "parada": "La parada del colectivo",
}

NOTA_INGRESO = {
    4: "Este mes, además del sueldo, te regalaron $40.000 por tu cumpleaños.",
    10: "Este mes hubo menos pedidos en la pizzería y cobraste $30.000 menos.",
}

SEPARADOR_FEEDBACK = "\n\n§\n\n"


# ---- operaciones que puede generar una opcion (ver motor.py) ----
def EF(monto):
    return {"op": "efectivo", "monto": monto}


def DEUDA(monto):
    return {"op": "deuda", "monto": monto}


def INV(nombre, emoji, monto, tasa=0.0, meses=None, liquida=False, tasas=None, moneda="pesos", detalle=""):
    return {"op": "inversion", "nombre": nombre, "emoji": emoji, "monto": monto, "tasa": tasa, "meses": meses,
            "liquida": liquida, "tasas": tasas, "moneda": moneda, "detalle": detalle}


def PRESTAMO(nombre, emoji, cuotas, recibido=0, detalle=""):
    return {"op": "prestamo", "nombre": nombre, "emoji": emoji, "cuotas": cuotas, "recibido": recibido, "detalle": detalle}


def COBRAR(nombre, emoji, pagos, costo=0, detalle=""):
    return {"op": "a_cobrar", "nombre": nombre, "emoji": emoji, "pagos": pagos, "costo": costo, "detalle": detalle}


def COMPRA(nombre, emoji, en_meses, monto):
    return {"op": "compra", "nombre": nombre, "emoji": emoji, "en_meses": en_meses, "monto": monto}


def APORTE(nombre, emoji, monto, tasa):
    return {"op": "aporte", "nombre": nombre, "emoji": emoji, "monto": monto, "tasa": tasa}


def _deltas(ops):
    """Efecto inmediato de las operaciones en el efectivo y en la deuda abierta."""
    da = dd = 0
    for o in ops:
        t = o["op"]
        if t == "efectivo":
            da += o["monto"]
        elif t == "deuda":
            dd += o["monto"]
        elif t == "inversion":
            da -= o["monto"]
        elif t == "prestamo":
            da += o["recibido"]
        elif t == "a_cobrar":
            da -= o["costo"]
        elif t == "aporte":
            da -= o["monto"]
        elif t == "refinanciar":
            dd -= o["recibido"]
    return da, dd


def _op(texto, da, dd, clasif, eje, consecuencia, explicacion, ops=None):
    if ops is not None:
        da, dd = _deltas(ops)
    return {
        "texto_opcion": texto,
        "delta_ahorro": da,
        "delta_deuda": dd,
        "clasificacion": clasif,
        "tipo_error": None if clasif == "acertada" else TIPO_ERROR_POR_EJE[eje],
        # Feedback = consecuencia en la historia + explicacion de las tres opciones.
        "mensaje_feedback": consecuencia + SEPARADOR_FEEDBACK + explicacion,
        # Como evoluciona la decision mes a mes (None = efecto inmediato con los deltas).
        "ops": ops,
    }


A, R, I = "acertada", "riesgosa", "incorrecta"


def _esc(mes, orden, eje, lugar, personaje, objeto, texto, opciones, explicacion):
    return {
        "mes": mes,
        "orden": orden,
        "eje_tematico": eje,
        "texto_situacion": texto,
        "lugar": lugar,
        "personaje": personaje,
        "objeto": objeto,
        "opciones": [_op(o[0], o[1], o[2], o[3], eje, o[4], explicacion, o[5] if len(o) > 5 else None) for o in opciones],
    }


# Interes simple del 2,5% sobre $50.000 expresado como rendimiento de cada mes.
SIMPLE_2_5 = [round(1250 / (50_000 + 1250 * k), 6) for k in range(6)]

ESCENARIOS = [
    # ------------------------------------------------------------- MES 1 (enero)
    _esc(1, 1, "presupuesto", "casa", "cami", "📋",
         "{nombre}, cobraste tu primer sueldo en la Pizzería Don Tano: $220.000. Ya pagaste $80.000 de gastos "
         "fijos, así que te quedan $140.000 para el mes. A fin de mes vence la primera cuota del viaje a "
         "Bariloche, de $90.000. Cami te ayudó a armar tres presupuestos. ¿Con cuál te quedás?",
         [
             ("📋 Cuota $90.000, salidas y gustos $30.000 y reserva para imprevistos $20.000.", -30_000, 0, A,
              "Cerraste el mes con la cuota de Bariloche cubierta y $20.000 de reserva guardados para lo que "
              "surja."),
             ("📝 Cuota $90.000 y salidas y gustos $50.000, ya que con eso llegás justo a fin de mes.",
              -50_000, 20_000, R,
              "A mitad de mes se te pinchó la rueda de la bici del delivery y el arreglo costó $20.000. Como no "
              "tenías reserva, lo pagaste con la tarjeta: esa deuda crece 8% por mes hasta que la canceles."),
             ("🗒️ Cuota $90.000, salidas y gustos $40.000 y reserva para imprevistos $20.000.",
              -60_000, 20_000, I,
              "Este presupuesto sumaba $150.000, pero tenías $140.000: desde el primer día faltaban $10.000. "
              "Encima se te pinchó la rueda de la bici y los $20.000 del arreglo fueron a la tarjeta, que crece "
              "8% por mes."),
         ],
         "El primer presupuesto suma exactamente $140.000 y deja un colchón. El segundo también suma bien, "
         "pero no deja margen, así que cualquier imprevisto termina en deuda. El tercero parece ordenado porque "
         "tiene reserva, pero suma $150.000: más de lo que tenés. Antes de elegir un presupuesto conviene sumar "
         "cada línea, comprobar que entre en lo que cobrás y dejar algo para imprevistos."),
    _esc(1, 2, "deuda_credito", "shopping", "tano", "👟",
         "Tano te avisa que para hacer delivery necesitás zapatillas cómodas, porque pasás muchas horas arriba "
         "de la bici. Las que te sirven cuestan $50.000. Acordate de que los precios suben 2% todos los meses. "
         "¿Cómo las pagás?",
         [
             ("💳 En 2 cuotas sin interés de $25.000, la primera el mes que viene.", 0, 0, A,
              "Estrenaste zapatillas y vas a pagar las cuotas con plata que, para entonces, vale un poco menos: "
              "en pesos de hoy te cuestan $48.539.",
              [PRESTAMO("Cuotas de las zapatillas", "👟", [25_000, 25_000])]),
             ("💵 De contado, con 2% de descuento: pagás $49.000 en el momento.", 0, 0, R,
              "Estrenaste zapatillas pagando $49.000: $461 más de lo que te costaban, en pesos de hoy, las 2 "
              "cuotas sin interés.",
              [EF(-49_000)]),
             ("🧾 En 3 cuotas de $18.000, la primera el mes que viene, así cada pago te queda más liviano.",
              0, 0, I,
              "Estrenaste zapatillas, pero pagás $54.000 en total. Aun con la inflación, en pesos de hoy te "
              "cuestan $51.910: $3.371 más que en 2 cuotas sin interés.",
              [PRESTAMO("Cuotas de las zapatillas", "👟", [18_000, 18_000, 18_000])]),
         ],
         "Los precios suben 2% todos los meses y se acumula: lo que hoy cuesta $100, el mes que viene cuesta $102 "
         "y al siguiente $104,04. Por eso una cuota fija vale menos cuanto más tarde la pagás. La cuota de $25.000 "
         "del mes que viene equivale hoy a $25.000 ÷ 1,02 = $24.510, y la de dentro de dos meses a $25.000 ÷ "
         "(1,02 × 1,02) = $24.029: en total, $48.539, menos que los $49.000 del contado. Las 3 cuotas de $18.000 "
         "suman $54.000 ($4.000 de interés escondido) y equivalen a $17.647 + $17.301 + $16.962 = $51.910: la "
         "inflación no alcanza a compensar ese interés."),
    # ------------------------------------------------------------- MES 2 (febrero)
    _esc(2, 1, "intereses", "bicicleteria", "tano", "🚲",
         "{nombre}, se rompió la bici con la que hacés el delivery y el arreglo sale $50.000. Tano te avisa que "
         "sin bici no podés trabajar el fin de semana. Tenés tres maneras de pagarlo:",
         [
             ("🐷 Usar tus ahorros, aunque te quede menos colchón por unos meses.", 0, 0, A,
              "La bici quedó como nueva y volviste a repartir ese mismo fin de semana, sin deberle nada a nadie.",
              [EF(-50_000)]),
             ("🤝 Pedirle prestado al tío Rubén, que te cobra 10% de interés, y devolverle todo en 1 mes.",
              0, 0, R,
              "Volviste a repartir, pero el mes que viene le devolvés $55.000 al tío Rubén: $5.000 más de lo que "
              "costó el arreglo.",
              [EF(-50_000), PRESTAMO("Préstamo del tío Rubén", "🤝", [55_000], recibido=50_000)]),
             ("📱 Usar la app PrestaYa, que te da el primer mes sin interés aunque te cobra $15.000 por darte "
              "el préstamo.", 0, 0, I,
              "Volviste a repartir, pero el mes que viene le tenés que devolver $65.000 a PrestaYa: $15.000 más "
              "de lo que costó el arreglo.",
              [EF(-50_000), PRESTAMO("Préstamo de PrestaYa", "📱", [65_000], recibido=50_000)]),
         ],
         "Con tus ahorros el arreglo cuesta $50.000 y no pagás intereses. Con el tío Rubén, el 10% de $50.000 "
         "son $5.000: le devolvés $55.000 en un mes. Con PrestaYa, el primer mes sin interés esconde un cargo de "
         "$15.000, que sobre $50.000 es un 30% de golpe: le devolvés $65.000. Si tenés la plata, usarla para un "
         "gasto necesario suele ser más barato que pedir prestado."),
    _esc(2, 2, "inflacion", "agencia", "sofi", "✈️",
         "Tenés guardados $90.000 para la cuota de Bariloche, que se paga a fin de mes. Los precios suben 2% por "
         "mes y el dólar, 1% por mes. Pasás por la agencia Egresados Sur y Sofi te cuenta las opciones. ¿Qué "
         "hacés con esa plata hasta entonces?",
         [
             ("✈️ Adelantar la cuota ahora, porque la agencia te hace un 5% de descuento si la pagás antes.",
              0, 0, A,
              "Pagaste $85.500 en vez de $90.000: te quedaron $4.500 a favor para el viaje.",
              [EF(4_500)]),
             ("🏦 Ponerlos en un plazo fijo que paga 1,5% por mes y sacarlos justo para la cuota.", 0, 0, R,
              "El plazo fijo te devolvió $91.350: ganaste $1.350, menos que los $4.500 que te ahorraba el "
              "descuento.",
              [INV("Plazo fijo para la cuota", "🏦", 90_000, tasa=0.015, meses=1)]),
             ("💵 Comprar dólares para cuidarte de la inflación y venderlos el mes que viene para pagar la cuota.",
              0, 0, I,
              "Al comprar y vender perdiste la diferencia de precio ($2.700) y el dólar subió solo 1%: volvieron "
              "$88.173, menos de lo que tenías.",
              [EF(-2_700), INV("Dólares para la cuota", "💵", 87_300, tasa=0.01, meses=1, moneda="dolares")]),
         ],
         "Adelantar la cuota con 5% de descuento te ahorra $90.000 × 5% = $4.500. El plazo fijo al 1,5% te da "
         "$90.000 × 1,5% = $1.350: algo, pero mucho menos, y además rinde menos que el 2% que suben los precios. "
         "Con los dólares perdés la diferencia entre el precio de compra y el de venta (3%: quedan $87.300) y el "
         "dólar sube 1%: $87.300 × 1,01 = $88.173. Como la cuota se paga en pesos, pasar a dólares por un mes te "
         "deja con menos plata."),
    # ------------------------------------------------------------- MES 3 (marzo)
    _esc(3, 1, "presupuesto", "colegio", "cami", "🎉",
         "{nombre}, empezaron las clases y Cami está organizando las salidas del curso para juntar plata para "
         "la fiesta de egresados. Mientras armás el presupuesto del mes, tenés que decidir qué hacer con los "
         "imprevistos.",
         [
             ("🛟 Separar $20.000 como fondo de imprevistos, aunque eso recorte algunas salidas.", -20_000, 0, A,
              "Saliste un poco menos y armaste un fondo de $20.000. Cuando se rompió el cargador del celular, lo "
              "pagaste de ahí sin tocar la plata de la cuota."),
             ("🤷 No separar nada y, si pasa algo, resolverlo en el momento con lo que tengas.", -40_000, 0, R,
              "Sin una parte separada, las salidas se fueron agrandando y gastaste $40.000. Llegás a fin de mes "
              "más justo para la cuota del viaje."),
             ("💳 Usar el límite de la tarjeta como fondo de imprevistos y disponer de todo el efectivo.",
              -70_000, 20_000, I,
              "Gastaste $70.000 del efectivo y, cuando se rompió el cargador y surgieron otros gastos, $20.000 "
              "fueron a la tarjeta. Esa deuda crece 8% por mes y compite con la plata del viaje."),
         ],
         "Un fondo de imprevistos separado hace que un gasto inesperado salga de tu plata y no de una deuda. Si "
         "no separás nada, todo lo disponible parece gastable y el gasto se agranda. Y el límite de la tarjeta "
         "no es un fondo: lo que usás es deuda, y crece 8% por mes si no la cancelás."),
    _esc(3, 2, "riesgo_inversion", "celular", "nico", "insta",
         "Nico te muestra en el celular el Instagram de @maxi.inversor: su grupo de inversión pagó 12% por "
         "semana, en pesos, durante los últimos 3 meses. El mínimo para entrar es $30.000 y dos compañeros del "
         "curso ya entraron y cobraron. Nico dice que con eso se pagan medio viaje.",
         [
             ("🙅 No entrar, aunque tus compañeros ya hayan cobrado.", 0, 0, A,
              "Qué pasó después: a las 5 semanas el grupo dejó de pagar y @maxi.inversor borró la cuenta. Tu "
              "plata del viaje quedó intacta."),
             ("🪙 Entrar con el mínimo de $30.000 para probar cómo funciona.", -30_000, 0, R,
              "Qué pasó después: a las 5 semanas el grupo dejó de pagar y @maxi.inversor borró la cuenta. "
              "Perdiste $30.000: un tercio de una cuota del viaje."),
             ("💰 Entrar con $60.000, ya que los que entraron antes cobraron sin problema.", -60_000, 0, I,
              "Qué pasó después: a las 5 semanas el grupo dejó de pagar y @maxi.inversor borró la cuenta. "
              "Perdiste $60.000: dos tercios de una cuota del viaje."),
         ],
         "Un 12% por semana es más de 50% por mes, en pesos o en cualquier moneda: ninguna inversión real paga "
         "eso de forma sostenida. Que algunos cobren al principio es justamente cómo funcionan estos esquemas: "
         "pagan a los primeros con la plata de los que entran después. Por eso no entrar era la única opción sin "
         "pérdida; entrar con poco o con mucho solo cambia cuánto se pierde."),
    # ------------------------------------------------------------- MES 4 (abril)
    _esc(4, 1, "intereses", "casa", "ruben", "🎂",
         "¡Feliz cumpleaños, {nombre}! Te regalaron $40.000 y querés que rindan hasta el viaje. Todas las "
         "propuestas son en pesos:",
         [
             ("🏦 Un plazo fijo a 30 días al 3% por mes, que vas renovando cada vez que vence.", 0, 0, A,
              "Tus $40.000 crecen 3% por mes, más rápido que los precios: cuando llegue el viaje te van a "
              "alcanzar para más cosas que hoy.",
              [INV("Plazo fijo de cumpleaños", "🏦", 40_000, tasa=0.03, meses=9, liquida=True,
                   detalle="Rinde 3% por mes; se renueva cada 30 días hasta el viaje")]),
             ("📲 Una cuenta en la billetera Rayo, que paga 30% anual en pesos y se puede sacar cuando quieras.",
              0, 0, R,
              "Tu plata crece 2,5% por mes, apenas por encima de la inflación: rinde, aunque menos que el plazo "
              "fijo al 3% mensual.",
              [INV("Cuenta en Rayo", "📲", 40_000, tasa=0.025, liquida=True)]),
             ("🤝 Prestárselos al tío Rubén, que el mes que viene te devuelve $40.400.", 0, 0, I,
              "El tío Rubén te devuelve $40.400, pero en ese mes los precios suben 2%: para comprar lo mismo que "
              "hoy con $40.000 vas a necesitar $40.800.",
              [COBRAR("Lo que te debe el tío Rubén", "🤝", [(1, 40_400)], costo=40_000)]),
         ],
         "Para comparar, hay que llevar todas las tasas a la misma unidad. El plazo fijo paga 3% por mes. El 30% "
         "anual de la billetera parece más, pero dividido por 12 es 2,5% por mes. Lo del tío Rubén son $400 en un "
         "mes: un 1%. Como los precios suben 2% por mes, en un mes $40.000 tienen que llegar a $40.800 solo para "
         "comprar lo mismo: el plazo fijo llega a $41.200 (ganás), Rayo a $41.000 (ganás poco) y el tío Rubén a "
         "$40.400 (perdés)."),
    _esc(4, 2, "ahorro", "banco", "laura", "🏦",
         "{nombre}, te sobraron $40.000 y Laura, la asesora del banco, te explica qué es invertir: poner la plata "
         "en algo que, con el tiempo, te devuelva más. Hay que mirar tres cosas: cuánto rinde, qué riesgo tiene "
         "de perder valor y qué tan rápido podés recuperar la plata. Ojo: todos los meses pagás una cuota del "
         "viaje.",
         [
             ("💧 Un fondo money market: tu plata se junta con la de otras personas y se presta a bancos por muy "
              "poco tiempo. Rinde alrededor de 2% por mes y la sacás el mismo día.", 0, 0, A,
              "Tu plata rinde lo mismo que suben los precios y, si una cuota se complica, la sacás en el día.",
              [INV("Fondo money market", "💧", 40_000, tasa=0.02, liquida=True)]),
             ("🗓️ Un plazo fijo a 180 días que paga más, 3% por mes, aunque la plata no se puede sacar hasta "
              "dentro de 6 meses.", 0, 0, R,
              "Rinde más, pero la plata queda trabada 6 meses: si te falta para una cuota, no la vas a poder usar.",
              [INV("Plazo fijo a 180 días", "🗓️", 40_000, tasa=0.03, meses=6)]),
             ("📊 Acciones de una empresa conocida: comprás una parte chiquita de la empresa, y su precio sube "
              "si le va bien y baja si le va mal.", 0, 0, I,
              "Qué pasó después: la acción bajó justo cuando necesitabas la plata para la cuota y vendiste: "
              "volvieron $15.000 de los $40.000. Perdiste $25.000.",
              [EF(-25_000)]),
         ],
         "El fondo money market rinde poco, casi no tiene riesgo y la plata se saca el mismo día. El plazo fijo "
         "a 180 días rinde más, pero la plata queda inmovilizada justo cuando tenés cuotas que pagar. Las "
         "acciones pueden subir o bajar mucho de un mes al otro. Para plata que vas a necesitar pronto, lo más "
         "importante es que esté disponible y no pierda valor."),
    # ------------------------------------------------------------- MES 5 (mayo)
    _esc(5, 1, "deuda_credito", "colegio", "cami", "💻",
         "Se rompió la notebook que usás para el colegio y para organizar el viaje con Cami. El arreglo cuesta "
         "$50.000. ¿Cómo lo pagás?",
         [
             ("🐷 Con tus ahorros, aunque te quede menos margen este mes.", 0, 0, A,
              "La notebook volvió a andar y no le debés nada a nadie.",
              [EF(-50_000)]),
             ("💳 Con la tarjeta, en 3 cuotas de $18.000, la primera el mes que viene.", 0, 0, R,
              "La notebook volvió a andar, pero vas a pagar $54.000: en pesos de hoy, $51.910.",
              [PRESTAMO("Cuotas del arreglo de la notebook", "💳", [18_000, 18_000, 18_000])]),
             ("📲 Con el préstamo preaprobado de la billetera Rayo: te depositan $120.000 al instante, pagás el "
              "arreglo y te queda plata extra. Lo devolvés en 6 cuotas de $25.000.", 0, 0, I,
              "Tu plata subió $70.000, pero ahora debés 6 cuotas de $25.000: $150.000 por $120.000. Esas cuotas "
              "compiten todos los meses con la del viaje.",
              [EF(-50_000), PRESTAMO("Préstamo preaprobado de Rayo", "📲", [25_000] * 6, recibido=120_000)]),
         ],
         "Con tus ahorros pagás $50.000 y no quedás debiendo. Las 3 cuotas de $18.000 suman $54.000: aun "
         "descontando la inflación ($17.647 + $17.301 + $16.962 = $51.910 de hoy), el arreglo te cuesta más. El "
         "préstamo preaprobado te hace sentir con más plata, pero devolvés $150.000 por $120.000: pagás intereses "
         "también por los $70.000 que no necesitabas."),
    _esc(5, 2, "riesgo_inversion", "agencia", "sofi", "🏔️",
         "Sofi, de Egresados Sur, avisa que este mes hay que pagar $50.000 de excursiones del viaje: el cerro "
         "Catedral y la navegación por el lago. Revisás tus cuentas y solo tenés $30.000 libres, porque el resto "
         "ya está separado para la cuota. No te alcanza: te faltan $20.000. ¿De dónde los sacás?",
         [
             ("✂️ Recortar salidas y gastos del mes hasta juntar los $20.000 que faltan.", 0, 0, A,
              "Saliste menos, pero juntaste lo que faltaba y pagaste las excursiones: ya tenés asegurados el "
              "cerro Catedral y la navegación por el lago.",
              [EF(-50_000)]),
             ("📲 Poner tus $30.000 en una billetera virtual que paga 1% por día, para que crezcan hasta la fecha "
              "de pago.", 0, 0, R,
              "Qué pasó después: la billetera congeló los retiros y recuperaste solo la mitad, "
              "$15.000. Igual tuviste que pagar las excursiones, así que perdiste $15.000 de la plata del viaje.",
              [EF(-65_000)]),
             ("⚽ Apostar tus $30.000 a que Argentina le gana a Bolivia, que paga 1,70: si gana, cobrás $51.000 y "
              "te sobra.", 0, 0, I,
              "Qué pasó después: empataron 1 a 1 y perdiste los $30.000. Igual tuviste que pagar las "
              "excursiones, así que esa plata salió de lo que tenías para el viaje.",
              [EF(-80_000)]),
         ],
         "Ninguna inversión seria paga 1% por día: sería más de 35% por mes, y un rendimiento así viene con un "
         "riesgo enorme de perder la plata. Además, aunque fuera real, en un mes tus $30.000 llegarían a unos "
         "$40.000: igual no alcanzaba. La apuesta parecía resolverlo todo, pero si Argentina no ganaba perdías "
         "lo que tenías, y los resultados de un partido no se pueden asegurar. Recortar gastos es más lento, pero "
         "es la única opción en la que tu plata no corre riesgo."),
    # ------------------------------------------------------------- MES 6 (junio)
    _esc(6, 1, "inflacion", "parada", None, "🚌",
         "Anuncian que el mes que viene el colectivo aumenta 20%. Lo usás para ir al colegio y a la pizzería los "
         "días de lluvia, y gastás unos $40.000 por mes.",
         [
             ("🚌 Cargar ahora en la SUBE lo que vas a usar el mes que viene.", 8_000, 0, A,
              "Te ahorraste $8.000 del aumento: casi una décima parte de una cuota del viaje."),
             ("⏳ Seguir cargando a medida que lo necesites, como siempre.", 0, 0, R,
              "Pagaste el colectivo con el aumento: $8.000 más que si hubieras cargado antes."),
             ("🛍️ Aprovechar y comprar también ropa y otras cosas antes de que suban, aunque algunas no las "
              "necesites todavía.", -50_000, 0, I,
              "Compraste cosas que no usaste y se fueron $50.000: más de la mitad de una cuota del viaje."),
         ],
         "Si gastás $40.000 por mes en colectivo y aumenta 20%, cargar ahora te ahorra $8.000. Cargar a medida "
         "que lo necesitás no te hace perder plata, pero pagás el aumento. Comprar de más antes de un aumento "
         "solo conviene con cosas que igual ibas a usar: si no, gastás plata que no recuperás."),
    _esc(6, 2, "ahorro", "pizzeria", "tano", "🐖",
         "{nombre}, ya vas por la mitad del año y querés llegar a Bariloche con plata para gastar allá. Decidís "
         "empezar a ahorrar todos los meses. ¿Cómo lo hacés?",
         [
             ("🔁 Programar que, el día que Tano te paga, el 10% se pase solo a un fondo que paga intereses en "
              "pesos, cerca de 2% por mes.", 0, 0, A,
              "Desde ahora, cada mes $22.000 de tu sueldo van solos al fondo para Bariloche, y los intereses "
              "compensan lo que suben los precios.",
              [APORTE("Fondo para gastar en Bariloche", "🔁", 22_000, 0.02)]),
             ("🐖 Guardar el 10% del sueldo en billetes en una alcancía, así no los ves y no los gastás.", 0, 0, R,
              "Cada mes $22.000 van a la alcancía. Se va llenando, pero los billetes valen cada mes un poco menos.",
              [APORTE("Alcancía para Bariloche", "🐖", 22_000, 0.0)]),
             ("📆 Ahorrar lo que te sobre a fin de mes, cuando ya sepas cuánto gastaste.", 0, 0, I,
              "A fin de mes no sobró nada: entre salidas y gastos chicos se fueron $30.000.",
              [EF(-30_000)]),
         ],
         "Ahorrar apenas cobrás, antes de gastar, hace que el ahorro no dependa de que sobre plata; y si el fondo "
         "paga cerca de 2% por mes, tu plata acompaña a los precios y no pierde valor. La alcancía también ayuda "
         "a no gastar, pero los billetes pierden 2% de valor por mes: $22.000 guardados 6 meses compran lo que "
         "hoy $22.000 ÷ 1,02⁶ = $19.535. Ahorrar lo que sobra suele fallar: los gastos chicos ocupan todo el "
         "lugar disponible."),
    # ------------------------------------------------------------- MES 7 (julio)
    _esc(7, 1, "presupuesto", "pizzeria", "tano", "⏱️",
         "Llegaron las vacaciones de invierno y Tano te ofrece trabajar 40 horas más. Te da tres propuestas:",
         [
             ("⏱️ 40 horas extra en la pizzería a $1.000 la hora, que te paga a fin de mes.", 0, 0, A,
              "Cobraste $40.000 a fin de mes: casi la mitad de la próxima cuota del viaje.",
              [EF(40_000)]),
             ("📈 Cobrar el 10% de lo que vendas por teléfono: el año pasado un chico sacó $80.000 y otro "
              "$20.000.", 0, 0, R,
              "Qué pasó después: hubo pocos pedidos y cobraste $20.000, la mitad de lo que te daban las horas "
              "seguras.",
              [EF(20_000)]),
             ("🎂 40 horas en el catering de un casamiento que organiza Tano, también a $1.000 la hora, pero que "
              "te paga en marzo del año que viene, cuando cobre el evento.", 0, 0, I,
              "Trabajaste las 40 horas, pero los $40.000 llegan en marzo, después del viaje: no te sirven para "
              "ninguna cuota, y para entonces, con los precios más altos, van a comprar menos.",
              [COBRAR("Lo que te paga Tano por el catering", "🎂", [(8, 40_000)])]),
         ],
         "La cuota del viaje es un gasto fijo de todos los meses, así que conviene que la plata que la paga llegue "
         "a tiempo y sea segura. Las horas en la pizzería pagan $40.000 a fin de mes. A comisión podés ganar más o "
         "mucho menos, y no sabés cuánto hasta fin de mes. El catering paga lo mismo, pero en marzo: después del "
         "viaje, y con 8 meses de precios subiendo, $40.000 ÷ 1,02⁸ = $34.140 de hoy."),
    _esc(7, 2, "inflacion", "pizzeria", "tano", "🧾",
         "Tano te debe $60.000 por las horas extra del mes pasado y te ofrece tres formas de pagarte. Pensá cuánto "
         "vas a tener dentro de 3 meses:",
         [
             ("📊 Pagarte dentro de 3 meses, ajustando lo que te debe por la inflación más un 1% por mes.", 0, 0, A,
              "En 3 meses Tano te paga $65.564: le gana a los precios y a las otras dos opciones.",
              [COBRAR("Lo que te debe Tano (ajustado)", "📊", [(3, 65_564)])]),
             ("🏦 Pagarte todo ahora, y vos lo ponés 3 meses en un plazo fijo al 1,5% por mes.", 0, 0, R,
              "En 3 meses el plazo fijo te devuelve $62.741: más que los $61.500 de la tercera opción, pero menos "
              "que con el ajuste por inflación.",
              [EF(60_000), INV("Plazo fijo con la plata de Tano", "🏦", 60_000, tasa=0.015, meses=3)]),
             ("🗓️ Pagarte $61.500 juntos dentro de 3 meses.", 0, 0, I,
              "En 3 meses cobrás $61.500: más pesos que hoy, pero con los precios 6,12% más altos alcanzan para "
              "menos que $60.000 hoy.",
              [COBRAR("Lo que te debe Tano", "🗓️", [(3, 61_500)])]),
         ],
         "En 3 meses los precios suben 2% cada mes y se acumula: 1,02 × 1,02 × 1,02 = 1,0612, o sea 6,12%. Para "
         "comprar lo mismo que hoy con $60.000 vas a necesitar $63.672. Con el ajuste por inflación más 1% tu "
         "plata crece 3% cada mes: $60.000 × 1,03 × 1,03 × 1,03 = $65.564 (le gana a los precios). El plazo fijo "
         "al 1,5%: $60.000 × 1,015 × 1,015 × 1,015 = $62.741, más que los $61.500 de la tercera opción, pero menos "
         "que los $63.672 que necesitás. En pesos de hoy: $61.783, $59.122 y $57.953."),
    # ------------------------------------------------------------- MES 8 (agosto)
    _esc(8, 1, "intereses", "shopping", "nico", "📷",
         "{nombre}, querés llevar al viaje una cámara GoPro usada para filmar todo. Cuesta $100.000 y no tenés "
         "toda la plata. ¿Cómo la conseguís?",
         [
             ("⏳ Juntar la plata durante 2 meses y comprarla después, aunque para entonces cueste más.", 0, 0, A,
              "En 2 meses la cámara va a costar $104.040, pero no pagás intereses: va a filmar todo Bariloche.",
              [COMPRA("Cámara GoPro", "📷", 2, 104_040)]),
             ("🤝 Pedirle prestado al tío Rubén, que te cobra 4% por mes, en 2 cuotas de $54.000.", 0, 0, R,
              "Tenés la cámara ya, pero le devolvés al tío Rubén $108.000: $8.000 de intereses.",
              [EF(-100_000), PRESTAMO("Préstamo del tío Rubén", "🤝", [54_000, 54_000], recibido=100_000)]),
             ("📱 Sacar un préstamo en PrestaYa: 2 cuotas de solo $56.000.", 0, 0, I,
              "Tenés la cámara ya, pero pagás $112.000: $12.000 de intereses, un 6% por mes.",
              [EF(-100_000), PRESTAMO("Préstamo de PrestaYa", "📱", [56_000, 56_000], recibido=100_000)]),
         ],
         "Si esperás 2 meses, la cámara sube con los precios, 2% cada mes y acumulado: $100.000 × 1,02 × 1,02 = "
         "$104.040. Pero tu sueldo y tu plata se miden con esos mismos precios y no pagás intereses: en pesos de "
         "hoy sigue costando $100.000. Con el tío Rubén, el 4% de $100.000 son $4.000 por mes: en 2 cuotas de "
         "$54.000 pagás $108.000. PrestaYa no dice la tasa, pero 2 cuotas de $56.000 son $112.000: $12.000 de "
         "interés, un 6% por mes. Hacer la cuenta del total es la forma de comparar préstamos."),
    _esc(8, 2, "deuda_credito", "celular", None, "💳",
         "Llegó el resumen de la tarjeta: gastaste $60.000 en ropa para el viaje. El pago mínimo es de $6.000 y "
         "la tarjeta cobra 8% por mes sobre lo que no pagues.",
         [
             ("💵 Pagar el total del resumen.", -60_000, 0, A,
              "Pagaste los $60.000 y la tarjeta quedó en cero."),
             ("➖ Pagar el mínimo de $6.000 y el resto más adelante.", -6_000, 54_000, R,
              "Pagaste $6.000. Los $54.000 restantes siguen como deuda: al cierre suman 8% y pasan a $58.320, "
              "aunque no vuelvas a usar la tarjeta. Se van a ir pagando con lo que te sobre cada mes."),
             ("⏭️ No pagar este mes y ponerte al día cuando cobres el próximo sueldo.", 0, 60_000, I,
              "Los $60.000 quedaron como deuda: al cierre suman 8% y pasan a $64.800, y siguen creciendo hasta "
              "que te sobre plata para cancelarlos."),
         ],
         "Pagar el total cancela la deuda y no genera intereses. El pago mínimo evita recargos, pero lo que no "
         "pagaste queda como deuda y crece 8% por mes. Si no pagás nada, crece toda la deuda. La deuda de la "
         "tarjeta crece sola, aunque no vuelvas a usarla."),
    # ------------------------------------------------------------- MES 9 (septiembre)
    _esc(9, 1, "presupuesto", "colegio", "cami", "🧮",
         "Cami te pide un consejo: le entraron $40.000 de propinas y tiene tres deudas de $40.000 cada una. Solo "
         "le alcanza para cancelar una. ¿Qué le recomendás?",
         [
             ("💳 Que cancele la tarjeta, que cobra 8% por mes.", 0, 0, A,
              "Cami canceló la tarjeta y cada mes se ahorra $3.200 de intereses: plata que le queda para el viaje."),
             ("📱 Que cancele las cuotas del celular, que cobran 3% por mes.", 0, 0, R,
              "Cami se ahorra $1.200 por mes del celular, pero la tarjeta le sigue sumando $3.200 de intereses "
              "por mes."),
             ("🤝 Que le devuelva a su tío, que no le cobra interés pero se lo recuerda en cada asado.", 0, 0, I,
              "El tío de Cami quedó contento, pero la tarjeta y el celular le siguen sumando $4.400 de intereses "
              "por mes."),
         ],
         "Cuando la plata no alcanza para todas las deudas, conviene cancelar primero la que cobra más interés. "
         "La tarjeta cobra 8%: $3.200 por mes sobre $40.000. El celular cobra 3%: $1.200 por mes. El tío no cobra "
         "interés, así que esa deuda no crece mientras se espera. Es lo mismo que hace el juego con tus deudas: "
         "lo que te sobra al cierre cancela primero la tarjeta."),
    _esc(9, 2, "ahorro", "colegio", "carlitos", "👟",
         "Tenés $30.000 ahorrados que quizás necesites pronto si alguna cuota del viaje se complica. ¿Dónde los "
         "invertís?",
         [
             ("💧 En una cuenta remunerada al 24% anual, que suma intereses todos los días y te deja sacar la "
              "plata cuando quieras.", 0, 0, A,
              "Tu plata rinde y está disponible si una cuota se complica.",
              [INV("Cuenta remunerada", "💧", 30_000, tasa=0.02, liquida=True)]),
             ("🏦 En un plazo fijo a 30 días al 25% anual, que paga un poco más.", 0, 0, R,
              "Rinde apenas $25 más por mes, pero la plata queda trabada: si la necesitás antes de que venza, no "
              "la podés usar.",
              [INV("Plazo fijo a 30 días", "🏦", 30_000, tasa=0.0208, meses=2)]),
             ("👟 Prestárselos a Carlitos para revender zapatillas: te devuelve $36.000 en un mes, un 20%, y dice "
              "que ya le funcionó con otros dos.", 0, 0, I,
              "Qué pasó después: las zapatillas no se vendieron y Carlitos no te pudo devolver la plata. Perdiste "
              "$30.000, un tercio de una cuota.",
              [EF(-30_000)]),
         ],
         "El plazo fijo paga 25% anual y la cuenta 24%: sobre $30.000 son $625 contra $600 por mes, apenas $25 de "
         "diferencia. A cambio, en el plazo fijo la plata queda trabada, y esta plata es para cubrir una cuota si "
         "hace falta: por eso conviene la cuenta, que se saca cuando quieras. Lo de Carlitos promete un 20% en un "
         "mes, depende de que él venda y, si sale mal, perdés todo."),
    # ------------------------------------------------------------- MES 10 (octubre)
    _esc(10, 1, "intereses", "agencia", "sofi", "📸",
         "{nombre}, Sofi te ofrece reservar el álbum de fotos y el video del viaje a precio congelado: $57.800, "
         "que se pagan dentro de 6 meses, cuando vuelvas de Bariloche. Separaste $50.000 de tus ahorros para eso. "
         "Los precios suben 2% por mes y el dólar 1% por mes. ¿Dónde invertís los $50.000 para llegar?",
         [
             ("🔁 En una cuenta que paga 2,5% por mes y suma los intereses al capital, así el mes siguiente "
              "también generan interés.", 0, 0, A,
              "En 6 meses llegás a $57.985: alcanza para el álbum y el video, y te sobran $185.",
              [INV("Inversión para el álbum (interés compuesto)", "🔁", 50_000, tasa=0.025, meses=6),
               COMPRA("Álbum y video del viaje", "📸", 6, 57_800)]),
             ("🏦 En un plazo fijo a 6 meses al 2,5% por mes simple.", 0, 0, R,
              "En 6 meses llegás a $57.500: te faltan $300 para el álbum y el video, que vas a tener que poner de "
              "tu plata.",
              [INV("Plazo fijo para el álbum (interés simple)", "🏦", 50_000, meses=6,
                   tasas=SIMPLE_2_5, detalle="Suma $1.250 por mes (2,5% de $50.000); vence en 6 meses"),
               COMPRA("Álbum y video del viaje", "📸", 6, 57_800)]),
             ("💵 Comprar dólares y venderlos dentro de 6 meses.", 0, 0, I,
              "En 6 meses, al vender los dólares tenés $53.076: te faltan $4.724 para el álbum y el video.",
              [INV("Dólares para el álbum", "💵", 50_000, tasa=0.01, meses=6, moneda="dolares"),
               COMPRA("Álbum y video del viaje", "📸", 6, 57_800)]),
         ],
         "Las dos primeras pagan la misma tasa, 2,5% por mes. Con interés simple se calcula siempre sobre los "
         "$50.000: $1.250 por mes, $7.500 en 6 meses, y llegás a $57.500. Con interés compuesto, los intereses de "
         "cada mes también generan intereses: $50.000 × 1,025 seis veces = $57.985. Los dólares suben 1% por mes: "
         "$50.000 × 1,01 seis veces = $53.076. A la misma tasa, el interés compuesto siempre rinde más que el "
         "simple."),
    _esc(10, 2, "riesgo_inversion", "celular", "nico", "🚀",
         "Nico te muestra $ROCKET, una criptomoneda nueva que subió 300% en un mes. Dice que si entrás ahora, "
         "te pagás el viaje entero.",
         [
             ("🙅 No invertir, aunque Nico insista en que es la oportunidad del año.", 0, 0, A,
              "Qué pasó con $ROCKET: primero subió 40% y después cayó 85% cuando sus creadores vendieron "
              "todo. Tu plata del viaje quedó a salvo."),
             ("🪙 Poner solo un poco de tus ahorros, $20.000, para no arriesgar demasiado.", 0, 0, R,
              "Esta vez te salió bien: se duplicó, vendiste a tiempo y ganaste $20.000. Pero después $ROCKET "
              "cayó 85%: si esperabas un poco más, perdías casi todo.",
              [EF(20_000)]),
             ("💰 Poner una parte importante de tus ahorros, $80.000, ya que viene subiendo fuerte.", 0, 0, I,
              "Qué pasó con $ROCKET: primero subió 40% y te entusiasmaste; después cayó 85% cuando sus "
              "creadores vendieron todo. De tus $80.000 volvieron $16.800: perdiste $63.200.",
              [EF(-63_200)]),
         ],
         "Una suba de 300% en un mes no dice nada de lo que va a pasar después: monedas nuevas como esta pueden "
         "caer casi a cero cuando sus creadores venden. Poner poco limita la pérdida, pero sigue siendo apostar "
         "plata del viaje; poner mucho expone una parte grande de tus ahorros. Que a alguien le haya salido bien "
         "no hace que la decisión sea menos riesgosa."),
    # ------------------------------------------------------------- MES 11 (noviembre)
    _esc(11, 1, "deuda_credito", "banco", "laura", "🏦",
         "Falta un mes para el viaje. Laura, del banco, te ofrece un préstamo de $100.000 a una tasa promocional "
         "del 1,5% por mes, que devolvés el mes que viene: $101.500. ¿Qué hacés?",
         [
             ("🔄 Tomarlo y, si tenés deuda de tarjeta, cancelarla primero, porque cobra 8%; lo que sobre, a un "
              "plazo fijo al 2,5% por mes.", 0, 0, A,
              "Si tenías deuda de tarjeta al 8%, la cambiaste por una del 1,5%; y lo que sobró rinde más de lo "
              "que cuesta.",
              [{"op": "refinanciar", "nombre": "Préstamo del banco", "recibido": 100_000, "cuotas": [101_500],
                "inversion": "Plazo fijo con el préstamo", "tasa_inversion": 0.025, "meses_inversion": 1}]),
             ("🙅 No tomarlo: pedir prestado siempre sale más caro que no deber nada.", 0, 0, R,
              "No perdiste nada, pero si tenías deuda de tarjeta, siguió creciendo al 8% por mes cuando podías "
              "pasarla al 1,5%.", []),
             ("🪙 Tomarlo y ponerlo en una plataforma cripto que paga 6% por mes.", 0, 0, R,
              "Qué pasó después: la plataforma frenó los retiros y recuperaste solo el 80%, pero al banco le "
              "devolvés los $101.500 completos.",
              [PRESTAMO("Préstamo del banco", "🏦", [101_500], recibido=100_000), EF(-20_000)]),
             ("🏦 Tomarlo y ponerlo en un plazo fijo al 18% anual, para no tenerlo quieto.", 0, 0, I,
              "Un 18% anual es 1,5% por mes: lo mismo que te cobra el préstamo. No ganaste nada y, con la "
              "inflación, perdiste poder de compra.",
              [PRESTAMO("Préstamo del banco", "🏦", [101_500], recibido=100_000),
               INV("Plazo fijo al 18% anual", "🏦", 100_000, tasa=0.015, meses=1)]),
         ],
         "Una deuda conviene si reemplaza una deuda más cara o si lo que te rinde es más de lo que te cuesta, "
         "sin riesgo. Este préstamo cobra 1,5% por mes: sirve para cancelar la tarjeta, que cobra 8%, y lo que "
         "sobra en un plazo fijo al 2,5% te deja ganancia. No tomarlo no te hace perder plata, pero deja pasar "
         "esa diferencia. Ponerlo en una plataforma que promete 6% suma riesgo con plata prestada. Y el plazo "
         "fijo al 18% anual es 18 ÷ 12 = 1,5% por mes: exactamente lo que cuesta el préstamo."),
    _esc(11, 2, "ahorro", "banco", "laura", "🧺",
         "Tenés $50.000 ahorrados para cuando vuelvas del viaje y querés invertirlos. ¿Qué hacés?",
         [
             ("🧺 Repartirlos: la mitad en un fondo que sacás en el día y la mitad en un fondo de bonos que rinde "
              "algo más.", 0, 0, A,
              "Repartiste la plata: si a una inversión le va mal, la otra la compensa.",
              [INV("Fondo money market", "💧", 25_000, tasa=0.02, liquida=True),
               INV("Fondo de bonos", "🧺", 25_000, tasa=0.025, liquida=True)]),
             ("📈 Ponerlos todos en acciones de una empresa que subió 80% este año y viene creciendo fuerte.",
              0, 0, R,
              "Qué pasó después: la acción bajó 40% y, como tenías todo ahí, perdiste $20.000.",
              [EF(-20_000)]),
             ("🎓 Pagar $65.000 por un curso de inversiones que garantiza ganar 20% por mes en pesos.", 0, 0, I,
              "Pagaste $65.000 por el curso y nunca viste ese 20% mensual.",
              [EF(-65_000)]),
         ],
         "Repartir la plata entre inversiones distintas se llama diversificar: si a una le va mal, no perdés "
         "todo. Un fondo de bonos presta la plata al Estado o a empresas por más tiempo, a cambio de un interés "
         "un poco mayor. Poner todo en una sola acción hace que una caída te afecte de lleno, y que haya subido "
         "mucho no significa que siga subiendo. Nadie puede garantizar un 20% por mes en pesos: sería multiplicar "
         "la plata casi 9 veces en un año (1,2 multiplicado 12 veces)."),
    # ------------------------------------------------------------- MES 12 (diciembre)
    _esc(12, 1, "inflacion", "shopping", "cami", "🧥",
         "¡Último mes antes de Bariloche! Necesitás una campera de nieve que cuesta $50.000. Recordá que los "
         "precios suben 2% todos los meses. ¿Cómo la pagás?",
         [
             ("💵 De contado, con 5% de descuento: pagás $47.500.", 0, 0, A,
              "Pagaste $47.500 y ya tenés la campera lista para la nieve.",
              [EF(-47_500)]),
             ("💳 En 2 cuotas sin interés de $25.000, la primera el mes que viene.", 0, 0, R,
              "Tenés la campera, pero las 2 cuotas valen, en pesos de hoy, $48.539: $1.039 más que el contado "
              "con descuento.",
              [PRESTAMO("Cuotas de la campera", "🧥", [25_000, 25_000])]),
             ("🧾 En 3 cuotas de $17.000, la primera el mes que viene.", 0, 0, I,
              "Tenés la campera, pero las 3 cuotas suman $51.000 y, aun con la inflación, en pesos de hoy "
              "valen $49.026.",
              [PRESTAMO("Cuotas de la campera", "🧥", [17_000, 17_000, 17_000])]),
         ],
         "Esta vez el descuento por pagar contado es grande. Las 2 cuotas sin interés, con los precios subiendo "
         "2% por mes y acumulado, equivalen a $25.000 ÷ 1,02 + $25.000 ÷ (1,02 × 1,02) = $48.539 de hoy. Las 3 "
         "cuotas de $17.000 suman $51.000, con interés escondido, y equivalen a $49.026. El contado con 5% de "
         "descuento cuesta $47.500. Las cuotas convienen cuando el descuento por contado es chico frente a la "
         "inflación; cuando el descuento es grande, conviene el contado."),
    _esc(12, 2, "riesgo_inversion", "casa", "flor", "🔺",
         "Tu prima Flor te invita al Club Despegue Financiero: pagás $25.000 de inscripción y cobrás $10.000 "
         "por cada amigo que sumes. Ella recuperó lo suyo en 2 semanas y te dice que con eso tenés plata para "
         "gastar en Bariloche.",
         [
             ("🙅 No sumarte, aunque Flor ya haya recuperado lo suyo.", 0, 0, A,
              "Qué pasó después: a los dos meses no se sumaba nadie nuevo y nadie más cobró. Tu plata para "
              "Bariloche quedó intacta."),
             ("🪙 Sumarte con la inscripción básica de $25.000.", -25_000, 0, R,
              "Qué pasó después: a los dos meses no se sumaba nadie nuevo y nadie más cobró. Perdiste $25.000 "
              "de la plata para gastar en el viaje."),
             ("💎 Sumarte con el plan premium de $90.000, que paga el doble por cada amigo.", -90_000, 0, I,
              "Qué pasó después: a los dos meses no se sumaba nadie nuevo y nadie más cobró. Perdiste $90.000: "
              "una cuota entera del viaje."),
         ],
         "Cuando la única forma de ganar es sumar a otros, se trata de un esquema piramidal: los primeros cobran "
         "con la plata de los que entran después, y cuando deja de entrar gente, los últimos pierden todo. Por "
         "eso no sumarse era la única opción sin pérdida; el plan premium solo agranda lo que se pierde."),
]


def presentacion(esc_mes: int, esc_orden: int) -> dict:
    """Datos de puesta en escena (lugar, personaje, objeto) de un escenario."""
    for e in ESCENARIOS:
        if e["mes"] == esc_mes and e["orden"] == esc_orden:
            return {"lugar": e["lugar"], "personaje": e["personaje"], "objeto": e["objeto"]}
    return {"lugar": "casa", "personaje": None, "objeto": None}
