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
    "ingreso_extra_mes_7": 60_000,
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
    7: "Este mes cobraste $60.000 extra: Tano te pagó medio aguinaldo.",
    10: "Este mes hubo menos pedidos en la pizzería y cobraste $30.000 menos.",
}

SEPARADOR_FEEDBACK = "\n\n§\n\n"


def _op(texto, da, dd, clasif, eje, consecuencia, explicacion):
    return {
        "texto_opcion": texto,
        "delta_ahorro": da,
        "delta_deuda": dd,
        "clasificacion": clasif,
        "tipo_error": None if clasif == "acertada" else TIPO_ERROR_POR_EJE[eje],
        # Feedback = consecuencia en la historia + explicacion de las tres opciones.
        "mensaje_feedback": consecuencia + SEPARADOR_FEEDBACK + explicacion,
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
        "opciones": [_op(o[0], o[1], o[2], o[3], eje, o[4], explicacion) for o in opciones],
    }


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
         "de la bici. Las que te sirven cuestan $50.000. Acordate de que los precios suben 2% por mes. "
         "¿Cómo las pagás?",
         [
             ("💳 En 2 cuotas sin interés de $25.000, una este mes y otra el que viene.", -48_500, 0, A,
              "Estrenaste zapatillas y la segunda cuota la pagás con plata que ya vale un poco menos: en pesos de "
              "hoy te costaron unos $48.500."),
             ("💵 De contado, con 2% de descuento: pagás $49.000 en el momento.", -49_000, 0, R,
              "Estrenaste zapatillas pagando $49.000, unos $500 más de lo que te costaban, en pesos de hoy, las "
              "2 cuotas sin interés."),
             ("🧾 En 3 cuotas de $18.000, así cada pago te queda más liviano.", -52_000, 0, I,
              "Estrenaste zapatillas, pero pagás $54.000 en total. Aun con la inflación, te costaron unos $3.500 "
              "más que en 2 cuotas sin interés."),
         ],
         "Con precios que suben 2% por mes, cada cuota fija vale un poco menos cuando la pagás. Las 2 cuotas "
         "sin interés equivalen a unos $48.500 de hoy: menos que los $49.000 del contado con 2% de descuento. "
         "Las 3 cuotas de $18.000 suman $54.000, o sea que tienen $4.000 de interés escondido, y la inflación no "
         "llega a compensarlo: equivalen a unos $52.000 de hoy. Para comparar formas de pago hay que mirar el "
         "total y cuánto valen esas cuotas con la inflación."),
    # ------------------------------------------------------------- MES 2 (febrero)
    _esc(2, 1, "intereses", "bicicleteria", "tano", "🚲",
         "{nombre}, se rompió la bici con la que hacés el delivery y el arreglo sale $50.000. Tano te avisa que "
         "sin bici no podés trabajar el fin de semana. Tenés tres maneras de pagarlo:",
         [
             ("🐷 Usar tus ahorros, aunque te quede menos colchón por unos meses.", -50_000, 0, A,
              "La bici quedó como nueva y volviste a repartir ese mismo fin de semana, sin deberle nada a nadie."),
             ("🤝 Pedirle prestado al tío Rubén, que te cobra 5% por mes sobre los $50.000, y devolverle todo "
              "en 2 meses.", -55_000, 0, R,
              "Volviste a repartir, pero le devolvés $55.000 al tío Rubén: $5.000 más de lo que costó el "
              "arreglo."),
             ("📱 Usar la app PrestaYa, que te da el primer mes sin interés aunque te cobra $15.000 por darte "
              "el préstamo.", 0, 65_000, I,
              "Volviste a repartir, pero le debés $65.000 a PrestaYa. Esa deuda queda abierta y crece 8% cada "
              "mes hasta que la canceles."),
         ],
         "Con tus ahorros el arreglo cuesta $50.000 y no pagás intereses. Con el tío Rubén, el 5% de $50.000 son "
         "$2.500 por mes: en 2 meses, $5.000 de interés. Con PrestaYa, el primer mes sin interés esconde un "
         "cargo de $15.000, que sobre $50.000 es un 30% de golpe, y si no la cancelás la deuda sigue creciendo. "
         "Si tenés la plata, usarla para un gasto necesario suele ser más barato que pedir prestado."),
    _esc(2, 2, "inflacion", "agencia", "sofi", "✈️",
         "Tenés guardados $90.000 para la cuota de Bariloche del mes que viene. Los precios suben 2% por mes y "
         "el dólar, 1% por mes. Pasás por la agencia Egresados Sur y Sofi te cuenta las opciones. ¿Qué hacés "
         "con esa plata hasta entonces?",
         [
             ("✈️ Adelantar la cuota ahora, porque la agencia te hace un 5% de descuento si la pagás antes.",
              4_500, 0, A,
              "Pagaste la cuota por adelantado y te quedaron $4.500 a favor para el viaje."),
             ("🏦 Ponerlos en un plazo fijo que paga 1,5% por mes y sacarlos justo para la cuota.", 1_350, 0, R,
              "Ganaste $1.350 de interés, pero en el mismo mes los precios subieron 2%: tenés más pesos, aunque "
              "alcanzan para un poco menos."),
             ("💵 Comprar dólares para cuidarlos y venderlos el mes que viene para pagar la cuota.", -5_000, 0, I,
              "Cuando vendiste los dólares para pagar la cuota, entre la diferencia de compra y venta y la "
              "inflación perdiste unos $5.000."),
         ],
         "Adelantar la cuota con 5% de descuento te ahorra $4.500, más de lo que la inflación le saca a esa "
         "plata en un mes. El plazo fijo al 1,5% te da $1.350, pero los precios suben 2%: tenés más pesos y "
         "podés comprar menos. Con los dólares perdés la diferencia entre el precio de compra y el de venta, y "
         "además el dólar sube 1% mientras los precios suben 2%; como la cuota se paga en pesos, no te protege."),
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
    _esc(3, 2, "riesgo_inversion", "celular", "nico", "📈",
         "Nico te muestra en el celular las capturas de @maxi.inversor: su grupo de inversión pagó 12% por "
         "semana durante los últimos 3 meses. El mínimo para entrar es $30.000 y dos compañeros del curso ya "
         "entraron y cobraron. Nico dice que con eso se pagan medio viaje.",
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
         "Un 12% por semana es más de 50% por mes: ninguna inversión real paga eso de forma sostenida. Que "
         "algunos cobren al principio es justamente cómo funcionan estos esquemas: pagan a los primeros con la "
         "plata de los que entran después. Por eso no entrar era la única opción sin pérdida; entrar con poco o "
         "con mucho solo cambia cuánto se pierde."),
    # ------------------------------------------------------------- MES 4 (abril)
    _esc(4, 1, "intereses", "casa", "ruben", "🎂",
         "¡Feliz cumpleaños, {nombre}! Te regalaron $40.000 y querés que rindan hasta el viaje. Tenés tres "
         "propuestas:",
         [
             ("🏦 Un plazo fijo a 30 días al 3% por mes, que vas renovando cada vez que vence.", 4_000, 0, A,
              "Tus $40.000 crecen más rápido que los precios: cuando llegue el viaje te van a alcanzar para más "
              "cosas que hoy."),
             ("📲 Una cuenta en la billetera Rayo, que paga 30% anual y se puede sacar cuando quieras.",
              2_000, 0, R,
              "Tu plata crece 2,5% por mes, apenas por encima de la inflación: rinde, aunque menos que el plazo "
              "fijo al 3% mensual."),
             ("🤝 Prestárselos al tío Rubén, que te devuelve $44.000 dentro de 6 meses.", -1_000, 0, I,
              "Cuando el tío Rubén te devuelva los $44.000, con los precios 2% más altos cada mes, vas a poder "
              "comprar menos que con $40.000 hoy."),
         ],
         "Para comparar, hay que llevar todas las tasas a la misma unidad. El plazo fijo paga 3% por mes. El 30% "
         "anual de la billetera parece más, pero dividido por 12 es 2,5% por mes. Lo del tío Rubén son $4.000 en "
         "6 meses, un 10%: menos de 1,7% por mes, por debajo de la inflación del 2%. El plazo fijo es el único "
         "que le gana a la inflación con margen."),
    _esc(4, 2, "ahorro", "banco", "laura", "🏦",
         "{nombre}, te sobraron $40.000 y Laura, la asesora del banco, te explica qué es invertir: poner la plata "
         "en algo que, con el tiempo, te devuelva más. Hay que mirar tres cosas: cuánto rinde, qué riesgo tiene "
         "de perder valor y qué tan rápido podés recuperar la plata. Ojo: el mes que viene pagás otra cuota del "
         "viaje.",
         [
             ("💧 Un fondo money market: tu plata se junta con la de otras personas y se presta a bancos por muy "
              "poco tiempo. Rinde alrededor de 2% por mes y la sacás el mismo día.", 2_000, 0, A,
              "Tu plata rindió y, cuando llegó la cuota del viaje, la sacaste en el día."),
             ("🔒 Un plazo fijo a 180 días que paga más, 3% por mes, aunque la plata no se puede sacar hasta "
              "dentro de 6 meses.", -10_000, 0, R,
              "La plata quedó trabada 6 meses. Para pagar la cuota le pediste un adelanto a Tano, que te "
              "descontó $10.000 del sueldo."),
             ("📊 Acciones de una empresa conocida: comprás una parte chiquita de la empresa, y su precio sube "
              "si le va bien y baja si le va mal.", -25_000, 0, I,
              "Justo cuando necesitabas la plata para la cuota, la acción había bajado y vendiste perdiendo "
              "$25.000."),
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
             ("🐷 Con tus ahorros, aunque te quede menos margen este mes.", -50_000, 0, A,
              "La notebook volvió a andar y no le debés nada a nadie."),
             ("💳 Con la tarjeta, en 3 cuotas de $18.000.", -52_000, 0, R,
              "La notebook volvió a andar, pero el arreglo te terminó costando unos $2.000 más en pesos de hoy."),
             ("📲 Con el préstamo preaprobado de la billetera Rayo: te depositan $120.000 al instante, pagás el "
              "arreglo y te queda plata extra.", 70_000, 120_000, I,
              "Tu efectivo subió $70.000, pero ahora debés $120.000 y el primer mes ya suma $9.600 de "
              "intereses. Esa deuda compite directo con las cuotas del viaje."),
         ],
         "Con tus ahorros pagás $50.000 y no quedás debiendo. Las 3 cuotas de $18.000 suman $54.000: aun con la "
         "inflación, el arreglo te cuesta más. El préstamo preaprobado te hace sentir con más plata, pero debés "
         "$120.000 que crecen 8% por mes: pagás intereses también por los $70.000 que no necesitabas."),
    _esc(5, 2, "riesgo_inversion", "agencia", "sofi", "🏔️",
         "Sofi, de Egresados Sur, avisa que este mes hay que pagar $50.000 de excursiones del viaje: el cerro "
         "Catedral y la navegación por el lago. Te faltan $20.000 para llegar.",
         [
             ("✂️ Usar tus ahorros y recortar gastos del mes hasta completar.", -50_000, 0, A,
              "Pagaste las excursiones: ya tenés asegurados el cerro Catedral y la navegación por el lago."),
             ("📲 Poner $20.000 en una billetera virtual que paga 1% por día para juntar lo que falta.",
              -60_000, 0, R,
              "Qué pasó después: la billetera congeló los retiros y recuperaste solo la mitad. Igual tuviste "
              "que pagar las excursiones, así que perdiste $10.000."),
             ("⚽ Apostar $20.000 a que Argentina le gana a Bolivia, que paga 1,15 si gana.", -70_000, 0, I,
              "Qué pasó después: empataron 1 a 1 y perdiste los $20.000. Igual tuviste que pagar las "
              "excursiones, así que esa plata salió de lo que tenías para el viaje."),
         ],
         "Ninguna inversión seria paga 1% por día: sería más de 35% por mes, y un rendimiento así viene con un "
         "riesgo enorme de perder la plata. La apuesta tampoco sirve para juntar plata: si Argentina ganaba, con "
         "1,15 sobre $20.000 ganabas apenas $3.000, y si no ganaba perdías todo. Recortar gastos es más lento, "
         "pero es la única opción en la que la plata está segura."),
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
             ("🔁 Programar que, el día que Tano te paga, el 10% se pase solo a un fondo que rinde.", 3_000, 0, A,
              "Cada mes, sin pensarlo, una parte de tu sueldo va a la plata para Bariloche, y además rinde."),
             ("🐖 Guardar billetes en una alcancía, así no los ves y no los gastás.", 0, 0, R,
              "Tu alcancía se va llenando, pero los billetes valen cada mes un poco menos."),
             ("📆 Ahorrar lo que te sobre a fin de mes, cuando ya sepas cuánto gastaste.", -30_000, 0, I,
              "A fin de mes no sobró nada: entre salidas y gastos chicos se fueron $30.000."),
         ],
         "Ahorrar apenas cobrás, antes de gastar, hace que el ahorro no dependa de que sobre plata; y en un fondo "
         "que rinde, no pierde valor. La alcancía también ayuda a no gastar, pero el efectivo guardado pierde 2% "
         "de valor por mes. Ahorrar lo que sobra suele fallar: los gastos chicos ocupan todo el lugar disponible."),
    # ------------------------------------------------------------- MES 7 (julio)
    _esc(7, 1, "presupuesto", "pizzeria", "tano", "⏱️",
         "Llegaron las vacaciones de invierno y Tano te ofrece trabajar más en la pizzería. Te da tres "
         "propuestas:",
         [
             ("⏱️ 40 horas extra a $1.000 la hora, con pago seguro a fin de mes.", 40_000, 0, A,
              "Cobraste $40.000 seguros: casi la mitad de la próxima cuota del viaje."),
             ("📈 Cobrar el 10% de lo que vendas por teléfono: el año pasado un chico sacó $80.000 y otro "
              "$20.000.", 20_000, 0, R,
              "Qué pasó después: hubo pocos pedidos y cobraste $20.000, la mitad de lo que te daban las horas "
              "seguras."),
             ("🎓 Hacer un curso de cocina de $30.000, pagándolo con tarjeta, para que en el verano Tano te "
              "pague el doble por hora.", 0, 30_000, I,
              "Hiciste el curso, pero el aumento llega recién en el verano, después del viaje. Mientras tanto, "
              "debés $30.000 en la tarjeta."),
         ],
         "La cuota del viaje es un gasto fijo, así que conviene que el ingreso que la paga también sea seguro. A "
         "comisión podés ganar más o mucho menos, y no sabés cuánto hasta fin de mes. El curso puede servir, pero "
         "el aumento llega después del viaje y hoy te deja $30.000 de deuda que crece 8% por mes."),
    _esc(7, 2, "inflacion", "pizzeria", "tano", "🧾",
         "Tano te debe $60.000 por las horas extra y te ofrece tres formas de pagarte:",
         [
             ("📊 En 2 meses, ajustando lo que te debe por la inflación más un 1% por mes.", 1_000, 0, A,
              "Cobrás un poco más tarde, pero con más poder de compra que hoy."),
             ("🏦 Todo ahora, y vos lo ponés en un plazo fijo al 1,5% por mes.", -500, 0, R,
              "Cobraste en el momento, pero el plazo fijo rindió menos que la inflación y perdiste un poco de "
              "poder de compra."),
             ("🗓️ En 3 cuotas fijas de $20.500, que en total suman $61.500.", -1_000, 0, I,
              "Cobrás $61.500, pero cada cuota llega con precios más altos: en pesos de hoy es menos de lo que te "
              "debía."),
         ],
         "Con el ajuste por inflación más 1%, tu plata crece 3% por mes y le gana a los precios. El plazo fijo "
         "al 1,5% parece más que ese 1%, pero el 1% se suma a la inflación y el 1,5% no: rinde menos que el 2% "
         "que suben los precios. Las 3 cuotas fijas suman $61.500, pero no se ajustan, y con la inflación "
         "equivalen a unos $59.000 de hoy."),
    # ------------------------------------------------------------- MES 8 (agosto)
    _esc(8, 1, "intereses", "shopping", "nico", "📷",
         "{nombre}, querés llevar al viaje una cámara GoPro usada para filmar todo. Cuesta $100.000 y no tenés "
         "toda la plata. ¿Cómo la conseguís?",
         [
             ("⏳ Juntar la plata durante 3 meses y comprarla antes del viaje.", -106_000, 0, A,
              "La compraste un poco más cara por la inflación, pero sin pagar intereses: va a filmar todo "
              "Bariloche."),
             ("🤝 Pedirle prestado al tío Rubén, al 4% por mes simple, y devolverle en 6 meses.", -124_000, 0, R,
              "Tenés la cámara, pero le devolvés al tío Rubén $124.000: $24.000 de intereses."),
             ("📱 Sacar un préstamo en PrestaYa al 3,5% por mes capitalizable, a 12 meses.", -151_000, 0, I,
              "Tenés la cámara, pero vas a pagar unos $151.000: el interés de cada mes se sumó a la deuda y "
              "también generó interés."),
         ],
         "Si esperás 3 meses, por la inflación la cámara sube a unos $106.000, pero no pagás intereses. Con el "
         "tío Rubén, el interés simple es 4% de $100.000 cada mes: $4.000 por 6 meses, $24.000. Con PrestaYa, "
         "capitalizable significa que cada mes el interés se suma a lo que debés y el mes siguiente también "
         "genera interés: es interés compuesto, y en 12 meses llegás a unos $151.000. Una tasa más baja puede "
         "salir más cara si el plazo es más largo y el interés es compuesto."),
    _esc(8, 2, "deuda_credito", "celular", None, "💳",
         "Llegó el resumen de la tarjeta: gastaste $60.000 en ropa para el viaje. El pago mínimo es de $6.000 y "
         "la tarjeta cobra 8% por mes sobre lo que no pagues.",
         [
             ("💵 Pagar el total del resumen.", -60_000, 0, A,
              "Pagaste los $60.000 y la tarjeta quedó en cero."),
             ("➖ Pagar el mínimo de $6.000 y el resto más adelante.", -6_000, 54_000, R,
              "Pagaste $6.000. Los $54.000 restantes siguen como deuda: el mes que viene van a ser $58.320, y "
              "así cada mes, aunque no vuelvas a usar la tarjeta."),
             ("⏭️ No pagar este mes y ponerte al día cuando cobres el próximo sueldo.", 0, 60_000, I,
              "Los $60.000 quedaron como deuda: el mes que viene van a ser $64.800, y siguen creciendo 8% por "
              "mes."),
         ],
         "Pagar el total cancela la deuda y no genera intereses. El pago mínimo evita recargos, pero lo que no "
         "pagaste queda como deuda y crece 8% por mes. Si no pagás nada, crece toda la deuda. La deuda de la "
         "tarjeta crece sola, aunque no vuelvas a usarla."),
    # ------------------------------------------------------------- MES 9 (septiembre)
    _esc(9, 1, "presupuesto", "casa", "ruben", "🧮",
         "{nombre}, te entraron $40.000 extra de propinas y tenés tres deudas de $40.000 cada una. Solo te "
         "alcanza para cancelar una:",
         [
             ("💳 La tarjeta, que cobra 8% por mes.", 3_000, 0, A,
              "Cancelaste la tarjeta y cada mes te ahorrás $3.200 de intereses: plata que queda para el viaje."),
             ("📱 Las cuotas del celular, que cobran 3% por mes.", 1_000, 0, R,
              "Te ahorrás $1.200 por mes del celular, pero la tarjeta sigue sumando $3.200 de intereses por mes."),
             ("🤝 Lo que le debés al tío Rubén, que no te cobra interés pero te lo recuerda en cada asado.",
              0, 0, I,
              "El tío Rubén quedó contento, pero la tarjeta y el celular siguen sumando $4.400 de intereses por "
              "mes."),
         ],
         "Cuando la plata no alcanza para todas las deudas, conviene cancelar primero la que cobra más interés. "
         "La tarjeta cobra 8%: $3.200 por mes sobre $40.000. El celular cobra 3%: $1.200 por mes. El tío Rubén "
         "no cobra interés, así que esa deuda no crece mientras esperás."),
    _esc(9, 2, "ahorro", "celular", "nico", "👟",
         "Tenés $30.000 ahorrados que quizás necesites pronto para alguna cuota del viaje. ¿Dónde los ponés?",
         [
             ("💧 En una cuenta remunerada al 24% anual, que suma intereses todos los días y te deja sacar la "
              "plata cuando quieras.", 600, 0, A,
              "Tu plata rinde y está disponible si una cuota se complica."),
             ("🔒 En un plazo fijo a 30 días al 24% anual.", 600, 0, R,
              "Rinde lo mismo, pero si la necesitás antes de los 30 días no la podés usar."),
             ("👟 Prestárselos a Nico para revender zapatillas: te devuelve $36.000 en un mes, un 20%, y dice "
              "que ya le funcionó con otros dos.", -30_000, 0, I,
              "Qué pasó después: las zapatillas no se vendieron y Nico no te pudo devolver la plata. Perdiste "
              "$30.000, un tercio de una cuota."),
         ],
         "La cuenta remunerada y el plazo fijo rinden lo mismo, 24% anual, unos $600 por mes; pero de la cuenta "
         "sacás la plata cuando quieras y en el plazo fijo queda trabada 30 días. A igual rendimiento, conviene "
         "la opción con más liquidez. Lo de Nico promete un 20% en un mes, depende de que él venda y, si sale "
         "mal, perdés todo, justo cuando tenés cuotas fijas que pagar."),
    # ------------------------------------------------------------- MES 10 (octubre)
    _esc(10, 1, "intereses", "banco", "laura", "🎓",
         "{nombre}, tus abuelos te dieron $50.000 para el primer mes de la facultad, dentro de 6 meses, cuando "
         "vuelvas del viaje. Los precios suben 2% por mes y el dólar sube 1% por mes. Laura, del banco, te "
         "muestra tres opciones:",
         [
             ("🔁 Una cuenta que paga 2,5% por mes y suma los intereses al capital, así el mes siguiente también "
              "generan interés.", 2_000, 0, A,
              "Llegás a unos $57.990: los intereses de cada mes también generaron intereses."),
             ("🏦 Un plazo fijo a 6 meses al 2,5% por mes simple.", 1_000, 0, R,
              "Llegás a $57.500: unos $490 menos que con interés compuesto."),
             ("💵 Comprar dólares y venderlos dentro de 6 meses.", -3_000, 0, I,
              "Tus $50.000 se convierten en unos $53.000 al vender los dólares, pero con los precios 2% más "
              "altos cada mes, alcanzan para menos que hoy."),
         ],
         "Las dos primeras pagan la misma tasa, 2,5% por mes. Con interés simple se calcula siempre sobre los "
         "$50.000 y llegás a $57.500. Con interés compuesto, los intereses de cada mes también generan "
         "intereses y llegás a unos $57.990. Los dólares suben 1% por mes, menos que los precios, que suben 2%: "
         "en 6 meses tenés más pesos, pero podés comprar menos."),
    _esc(10, 2, "riesgo_inversion", "celular", "nico", "🚀",
         "Nico te muestra $ROCKET, una criptomoneda nueva que subió 300% en un mes. Dice que si entrás ahora, "
         "te pagás el viaje entero.",
         [
             ("🙅 No invertir, aunque Nico insista en que es la oportunidad del año.", 0, 0, A,
              "Qué pasó con $ROCKET: subió 40% dos semanas más y después cayó 85% cuando sus creadores vendieron "
              "todo. Tu plata del viaje quedó a salvo."),
             ("🪙 Poner solo un poco de tus ahorros, $20.000, para no arriesgar demasiado.", 20_000, 0, R,
              "Esta vez te salió bien: vendiste a tiempo y ganaste $20.000. Qué pasó con $ROCKET: subió 40% dos "
              "semanas más y después cayó 85% cuando sus creadores vendieron todo. Si vendías una semana "
              "después, perdías casi todo."),
             ("💰 Poner una parte importante de tus ahorros, $80.000, ya que viene subiendo fuerte.",
              -80_000, 0, I,
              "Qué pasó con $ROCKET: subió 40% dos semanas más y después cayó 85% cuando sus creadores vendieron "
              "todo. Perdiste $80.000, casi una cuota entera del viaje."),
         ],
         "Una suba de 300% en un mes no dice nada de lo que va a pasar después: monedas nuevas como esta pueden "
         "caer casi a cero cuando sus creadores venden. Poner poco limita la pérdida, pero sigue siendo apostar "
         "plata del viaje; poner mucho expone una parte grande de tus ahorros. Que a alguien le haya salido bien "
         "no hace que la decisión sea menos riesgosa."),
    # ------------------------------------------------------------- MES 11 (noviembre)
    _esc(11, 1, "deuda_credito", "banco", "laura", "🏦",
         "Falta un mes para el viaje. Laura, del banco, te ofrece un préstamo de $100.000 a una tasa promocional "
         "del 1,5% por mes. ¿Qué hacés?",
         [
             ("🔄 Tomarlo y, si tenés deuda de tarjeta, cancelarla primero, porque cobra 8%; lo que sobre, a un "
              "plazo fijo al 2,5% por mes.", -98_000, -100_000, A,
              "Si tenías deuda de tarjeta al 8%, la cambiaste por una del 1,5%; y lo que sobró rinde más de lo "
              "que cuesta."),
             ("🪙 Tomarlo y ponerlo en una plataforma cripto que paga 6% por mes.", -20_000, 0, R,
              "Qué pasó después: la plataforma frenó los retiros y recuperaste solo el 80%, pero al banco le "
              "devolvés los $100.000 completos."),
             ("🏦 Tomarlo y ponerlo en un plazo fijo al 18% anual, para no tenerlo quieto.", -2_000, 0, I,
              "Un 18% anual es 1,5% por mes: lo mismo que te cobra el préstamo. No ganaste nada y, con la "
              "inflación, perdiste poder de compra."),
         ],
         "Una deuda conviene si reemplaza una deuda más cara o si lo que te rinde es más de lo que te cuesta, "
         "sin riesgo. El préstamo al 1,5% sirve para cancelar la tarjeta, que cobra 8%, y lo que sobra en un "
         "plazo fijo al 2,5% te deja ganancia. Ponerlo en una plataforma que promete 6% suma riesgo con plata "
         "prestada. Y el plazo fijo al 18% anual es 1,5% por mes: exactamente lo que cuesta el préstamo."),
    _esc(11, 2, "ahorro", "banco", "laura", "🧺",
         "Tenés ahorros para cuando vuelvas del viaje y querés invertirlos. ¿Qué hacés?",
         [
             ("🧺 Repartir la plata: una parte en un fondo money market, que se saca cuando quieras, y otra en "
              "un fondo de bonos, que presta al Estado o a empresas por más tiempo a cambio de un interés "
              "mayor.", 4_000, 0, A,
              "Repartiste la plata: si a una inversión le va mal, la otra la compensa."),
             ("📈 Ponerla toda en una sola acción que subió mucho este año.", -40_000, 0, R,
              "Qué pasó después: la acción bajó y, como tenías todo ahí, perdiste $40.000."),
             ("🎓 Pagar $65.000 por un curso de inversiones que garantiza ganar 20% por mes.", -65_000, 0, I,
              "Pagaste $65.000 por el curso y nunca viste ese 20% mensual."),
         ],
         "Repartir la plata entre inversiones distintas se llama diversificar: si a una le va mal, no perdés "
         "todo. Poner todo en una sola acción hace que una caída te afecte de lleno, y que haya subido mucho no "
         "significa que siga subiendo. Nadie puede garantizar un 20% por mes: sería multiplicar la plata casi 9 "
         "veces en un año."),
    # ------------------------------------------------------------- MES 12 (diciembre)
    _esc(12, 1, "inflacion", "shopping", "cami", "🧥",
         "¡Último mes antes de Bariloche! Necesitás una campera de nieve que cuesta $50.000. Recordá que los "
         "precios suben 2% por mes. ¿Cómo la pagás?",
         [
             ("💵 De contado, con 5% de descuento: pagás $47.500.", -47_500, 0, A,
              "Pagaste $47.500 y ya tenés la campera lista para la nieve."),
             ("💳 En 2 cuotas sin interés de $25.000.", -48_500, 0, R,
              "Tenés la campera, pero las 2 cuotas valen, en pesos de hoy, unos $48.500: $1.000 más que el "
              "contado con descuento."),
             ("🧾 En 3 cuotas de $17.000.", -49_000, 0, I,
              "Tenés la campera, pero las 3 cuotas suman $51.000 y, aun con la inflación, equivalen a unos "
              "$49.000 de hoy."),
         ],
         "Esta vez el descuento por pagar contado es grande: 5% es más de lo que la inflación le saca de valor a "
         "dos cuotas. Las 2 cuotas sin interés equivalen a unos $48.500 de hoy, y las 3 cuotas de $17.000 suman "
         "$51.000, con interés escondido, y equivalen a unos $49.000. Las cuotas convienen cuando el descuento "
         "por contado es chico frente a la inflación; cuando el descuento es grande, conviene el contado."),
    _esc(12, 2, "riesgo_inversion", "casa", "flor", "🔺",
         "Tu prima Flor te invita a Comunidad Libertad Financiera: pagás $25.000 de inscripción y cobrás $10.000 "
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
