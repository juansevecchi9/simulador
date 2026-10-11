"""Contenido fijo del recorrido: 12 meses x 2 decisiones = 24 escenarios.

Cada opcion define su impacto (delta_ahorro, delta_deuda en pesos), su
clasificacion (acertada / riesgosa / incorrecta), el tipo de error del eje
(None si es acertada) y el mensaje de retroalimentacion, que explica el
mecanismo sin juzgar. Los montos ya incluyen el costo total de cada decision
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

NOTA_INGRESO = {
    4: "Este mes recibiste $40.000 extra de regalo de cumpleaños.",
    7: "Este mes cobraste $60.000 extra por la changa de vacaciones de invierno.",
    10: "Este mes trabajaste menos horas y cobraste $30.000 menos.",
}


def _op(texto, da, dd, clasif, eje, mensaje):
    return {
        "texto_opcion": texto,
        "delta_ahorro": da,
        "delta_deuda": dd,
        "clasificacion": clasif,
        "tipo_error": None if clasif == "acertada" else TIPO_ERROR_POR_EJE[eje],
        "mensaje_feedback": mensaje,
    }


A, R, I = "acertada", "riesgosa", "incorrecta"


def _esc(mes, orden, eje, texto, opciones):
    return {
        "mes": mes,
        "orden": orden,
        "eje_tematico": eje,
        "texto_situacion": texto,
        "opciones": [_op(o[0], o[1], o[2], o[3], eje, o[4]) for o in opciones],
    }


ESCENARIOS = [
    # ------------------------------------------------------------- MES 1
    _esc(1, 1, "presupuesto",
         "Cobraste $220.000 y ya pagaste $80.000 de gastos fijos, así que te quedan $140.000 para el mes. "
         "La cuota del viaje es de $90.000. Te armaste tres presupuestos posibles. ¿Con cuál te quedás?",
         [
             ("Cuota $90.000, gastos del mes $30.000 y reserva para imprevistos $20.000.", -30_000, 0, A,
              "Tu presupuesto suma exactamente $140.000 y te deja $20.000 de reserva. Cuando todos los gastos "
              "entran en lo que cobrás y además queda un colchón, un imprevisto no te obliga a endeudarte."),
             ("Cuota $90.000 y gastos del mes $50.000, sin reserva para imprevistos.", -45_000, 20_000, R,
              "El presupuesto sumaba bien, pero no dejaba margen. A mitad de mes apareció un gasto imprevisto de "
              "$20.000 y lo pagaste con la tarjeta: esa deuda genera intereses mientras no la canceles. Sin "
              "reserva, cada imprevisto termina en deuda."),
             ("Cuota $90.000, gastos del mes $45.000 y reserva $15.000.", -60_000, 20_000, I,
              "Ese presupuesto sumaba $150.000, pero tenías $140.000: faltaban $10.000 desde el principio. "
              "Además, el imprevisto de $20.000 terminó en la tarjeta. Sumar cada línea antes de decidir evita "
              "que un presupuesto que parece ordenado no cierre."),
         ]),
    _esc(1, 2, "deuda_credito",
         "Necesitás zapatillas para la changa, porque trabajás muchas horas de pie. Cuestan $40.000. "
         "Recordá que los precios suben un 2% por mes. ¿Cómo las pagás?",
         [
             ("En 2 cuotas de $20.200, con un interés del 1% mensual (en total, $40.400).", -39_200, 0, A,
              "Pagaste $40.400 en dos cuotas, pero como los precios suben 2% por mes, esa plata vale cada mes "
              "un poco menos: en pesos de hoy las cuotas te costaron unos $39.200. Cuando el interés de las "
              "cuotas (1%) es menor que la inflación (2%), financiar puede salir más barato que pagar contado."),
             ("Contado, con 1% de descuento: $39.600.", -39_600, 0, R,
              "Pagaste $39.600 hoy. Parecía lo más barato, pero las 2 cuotas al 1% valían, en pesos de hoy, "
              "unos $39.200. Con inflación del 2%, un descuento chico por pagar contado puede no compensar lo "
              "que pierden de valor las cuotas."),
             ("3 cuotas sin interés de $13.334, más un costo de gestión de $6.000 al inicio.", -44_400, 0, I,
              "Las cuotas no tenían interés, pero el costo de gestión de $6.000 llevó el total a unos $46.000. "
              "Aun descontando la inflación, te costaron unos $44.400. Un cargo fijo puede ser un interés "
              "escondido: conviene comparar siempre el total que se termina pagando."),
         ]),
    # ------------------------------------------------------------- MES 2
    _esc(2, 1, "intereses",
         "Se rompió la bici que usás para ir a la changa y el arreglo sale $50.000. Si no la arreglás, no "
         "podés trabajar. Tenés tres maneras de pagarlo:",
         [
             ("Pagarlo con tus ahorros, aunque eso te deje con menos colchón por unos meses.", -50_000, 0, A,
              "Usaste $50.000 de tus ahorros y no pagaste ningún interés. Si tenés la plata, usarla para un "
              "gasto necesario suele ser más barato que pedir prestado."),
             ("Pedirle prestado a un conocido, que te cobra un 5% de interés por cada mes. Como se lo devolvés "
              "en 2 meses, el interés se calcula siempre sobre los $50.000 originales.", -55_000, 0, R,
              "Con interés simple, cada mes se paga el 5% de $50.000, o sea $2.500. En 2 meses son $5.000 de "
              "interés: devolviste $55.000. Pedir prestado teniendo ahorros hace que el mismo arreglo te cueste "
              "más."),
             ("Usar una app de préstamos que promete ¡primer mes con 0% de interés!, aunque te cobra $15.000 "
              "por otorgarte el préstamo y lo tenés que devolver en un mes.", 0, 65_000, I,
              "El 0% de interés escondía un cargo de $15.000: sobre $50.000 es un 30% en un solo mes. Y como el "
              "préstamo quedó como deuda abierta, si no se cancela sigue generando intereses mes a mes."),
         ]),
    _esc(2, 2, "inflacion",
         "Tenés guardados $90.000 para la cuota del viaje del mes que viene. Los precios suben un 2% por mes "
         "y el dólar, un 1% por mes. ¿Qué hacés con esa plata hasta entonces?",
         [
             ("Adelantar la cuota: la agencia te hace un 7% de descuento si la pagás ahora.", 6_300, 0, A,
              "El 7% de descuento sobre $90.000 son $6.300 que te quedan en el bolsillo. Pagar por adelantado "
              "algo que igual ibas a pagar, con un descuento mayor que la inflación, protege tu plata."),
             ("Ponerlos en un plazo fijo que paga 1,5% mensual hasta el mes que viene.", 1_350, 0, R,
              "Ganaste $1.350 de interés, pero en ese mismo mes los precios subieron 2%. Un plazo fijo que paga "
              "menos que la inflación hace crecer los pesos, pero no lo que podés comprar con ellos."),
             ("Comprar dólares para cuidarlos de la inflación y venderlos el mes que viene para pagar la cuota.",
              -5_000, 0, I,
              "Al comprar y vender dólares se pierde la diferencia entre el precio de compra y el de venta, y "
              "además el dólar subió solo 1% mientras los precios subieron 2%. Como la cuota se paga en pesos, "
              "pasar a dólares por un mes hizo que perdieras unos $5.000."),
         ]),
    # ------------------------------------------------------------- MES 3
    _esc(3, 1, "presupuesto",
         "Armando el presupuesto del mes, tenés que decidir qué hacer con los imprevistos.",
         [
             ("Separar $20.000 como fondo de imprevistos, aunque eso recorte salidas.", -20_000, 0, A,
              "Gastaste menos en salidas y armaste un fondo de $20.000. Un fondo de imprevistos hace que un "
              "gasto inesperado salga de tu plata y no de una deuda."),
             ("No separar nada: si pasa algo, lo ves en el momento.", -45_000, 0, R,
              "Sin un fondo, el gasto del mes se fue agrandando y terminaste gastando $45.000. Cuando no hay "
              "una parte separada, todo lo disponible parece gastable."),
             ("Usar el límite de la tarjeta como fondo de imprevistos y disponer de todo el efectivo.",
              -70_000, 25_000, I,
              "Gastaste $70.000 del efectivo y el imprevisto de $25.000 fue a la tarjeta. El límite de la "
              "tarjeta no es un fondo: es deuda, y genera intereses cada mes que no la cancelás."),
         ]),
    _esc(3, 2, "riesgo_inversion",
         "Un influencer que seguís muestra capturas: su grupo de inversión pagó 12% por semana durante los "
         "últimos 3 meses. El mínimo para entrar es $30.000, y dos compañeros de tu curso ya entraron y "
         "cobraron.",
         [
             ("No entrar.", 0, 0, A,
              "No pusiste plata. Un 12% semanal sería más de 50% por mes: ninguna inversión real paga eso de "
              "forma sostenida. Qué pasó después: a las 5 semanas el grupo dejó de pagar y el influencer borró "
              "la cuenta. Los primeros cobraban con la plata de los que entraban después."),
             ("Entrar con el mínimo, $30.000.", -30_000, 0, R,
              "Perdiste los $30.000. Qué pasó después: a las 5 semanas el grupo dejó de pagar y el influencer "
              "borró la cuenta. Los primeros cobraban con la plata de los que entraban después, por eso al "
              "principio parecía funcionar."),
             ("Entrar con $60.000 para aprovechar.", -60_000, 0, I,
              "Perdiste los $60.000. Qué pasó después: a las 5 semanas el grupo dejó de pagar y el influencer "
              "borró la cuenta. Que otros hayan cobrado al principio es justamente cómo funcionan estos "
              "esquemas: pagan con la plata de los que entran después."),
         ]),
    # ------------------------------------------------------------- MES 4
    _esc(4, 1, "intereses",
         "Te regalaron $40.000 para tu cumpleaños y querés que rindan hasta fin de año. Tenés tres "
         "propuestas:",
         [
             ("Un plazo fijo a 30 días, que vas renovando, al 3,5% mensual.", 5_000, 0, A,
              "Un 3,5% mensual le gana a la inflación del 2%: tu plata crece más rápido que los precios. Para "
              "comparar tasas hay que llevarlas siempre a la misma unidad (mensual o anual)."),
             ("Una cuenta de una fintech que paga ¡30% anual!", 2_000, 0, R,
              "Un 30% anual equivale a 2,5% por mes: parece un número más grande, pero rinde menos que el plazo "
              "fijo al 3,5% mensual. Las tasas anuales y mensuales no se comparan directo."),
             ("Prestárselos a tu tío, que te devuelve $44.000 dentro de 6 meses.", -10_000, 0, I,
              "Recibís $4.000 más, un 10% en 6 meses: menos de 1,7% por mes. Mientras tanto los precios suben "
              "2% por mes, así que cuando te los devuelva vas a poder comprar menos que hoy."),
         ]),
    _esc(4, 2, "ahorro",
         "Te sobraron $40.000 y querés que tu plata trabaje para vos. Eso es invertir: poner la plata en algo "
         "que, con el tiempo, te devuelva más. En cada inversión hay que mirar tres cosas: cuánto rinde, qué "
         "riesgo tiene de perder valor y qué tan rápido podés recuperar la plata si la necesitás. Ojo: el mes "
         "que viene tenés que pagar la cuota.",
         [
             ("Un fondo común money market: tu plata se junta con la de otras personas y se presta a bancos por "
              "muy poco tiempo. Rinde poco, alrededor de 1,8% mensual, pero la podés sacar el mismo día.",
              2_000, 0, A,
              "El fondo rinde poco, pero casi no tiene riesgo y podés sacar la plata cuando la necesitás. Si "
              "tenés que pagar una cuota pronto, lo más importante es que la plata esté disponible."),
             ("Un plazo fijo a 180 días que paga más, 2,5% mensual, pero la plata no se puede sacar hasta "
              "dentro de 6 meses.", -10_000, 0, R,
              "Rendía más, pero la plata quedó inmovilizada y para la cuota tuviste que cubrirte de otra forma, "
              "con un costo de unos $10.000. Una inversión que no podés sacar a tiempo no sirve para plata que "
              "vas a necesitar pronto."),
             ("Acciones de una empresa conocida: comprás una parte chiquita de la empresa. Si a la empresa le va "
              "bien su precio sube, si le va mal baja, y puede moverse mucho de un mes al otro.",
              -25_000, 0, I,
              "Qué pasó después: justo cuando necesitabas la plata para la cuota, la acción había bajado y "
              "tuviste que venderla perdiendo. Las acciones pueden subir o bajar mucho en poco tiempo, por eso "
              "no conviene usar plata que vas a necesitar pronto."),
         ]),
    # ------------------------------------------------------------- MES 5
    _esc(5, 1, "deuda_credito",
         "Se rompió la notebook que usás para el colegio. El arreglo cuesta $48.000.",
         [
             ("Pagarlo con tus ahorros.", -48_000, 0, A,
              "Pagaste $48.000 y no generaste deuda ni intereses."),
             ("Pagarlo con la tarjeta en 3 cuotas con interés.", -52_000, 0, R,
              "Las 3 cuotas con interés hicieron que el arreglo te costara unos $52.000, $4.000 más que "
              "pagándolo con tus ahorros."),
             ("Aceptar un préstamo preaprobado de tu billetera virtual: te depositan $110.000 al toque, pagás el "
              "arreglo y te queda plata extra.", 62_000, 110_000, I,
              "Tu efectivo subió $62.000, pero ahora debés $110.000 y esa deuda crece cada mes con los "
              "intereses. Que el efectivo suba no significa que tengas más: tu patrimonio bajó."),
         ]),
    _esc(5, 2, "riesgo_inversion",
         "La agencia avisa que este mes hay que pagar $50.000 de excursiones del viaje y te faltan $20.000 "
         "para llegar.",
         [
             ("Usar tus ahorros y recortar gastos del mes.", -50_000, 0, A,
              "Pagaste las excursiones con tu plata y recortando gastos, sin arriesgar nada."),
             ("Poner $20.000 en una billetera virtual que paga 1% diario, para juntar lo que falta.",
              -70_000, 0, R,
              "Qué pasó después: la billetera congeló los retiros y recuperaste solo una parte. Ninguna "
              "inversión seria paga 1% por día: sería más de 35% por mes. Cuando un rendimiento es tan alto, "
              "el riesgo de perder la plata también lo es."),
             ("Apostar $20.000 a que Argentina le gana a Bolivia, que paga 1,15 si gana.", -90_000, 0, I,
              "Qué pasó después: empataron 1 a 1 y perdiste la apuesta. Aun si Argentina ganaba, con una "
              "cuota de 1,15 sobre $20.000 solo te ganabas $3.000. Una apuesta no es una forma de financiar "
              "un gasto: se puede perder todo."),
         ]),
    # ------------------------------------------------------------- MES 6
    _esc(6, 1, "inflacion",
         "Anuncian que el mes que viene aumenta el transporte.",
         [
             ("Cargar ahora en la SUBE lo que vas a usar el mes que viene.", 8_000, 0, A,
              "Pagaste a precio de hoy algo que igual ibas a usar: te ahorraste el aumento."),
             ("No hacer nada y cargar a medida que lo necesites.", 0, 0, R,
              "Vas a pagar el transporte con el aumento. Cuando sabés que un precio va a subir, adelantar la "
              "compra de lo que igual vas a usar protege tu plata."),
             ("Comprar de todo antes de que suba, aunque algunas cosas no las uses.", -50_000, 0, I,
              "Adelantar compras protege de la inflación solo si son cosas que igual ibas a usar. Comprar de "
              "más es gastar plata que no recuperás."),
         ]),
    _esc(6, 2, "ahorro",
         "Querés empezar a ahorrar todos los meses.",
         [
             ("Programar que, el día que cobrás, un 10% se pase solo a un fondo que rinde.", 3_000, 0, A,
              "Ahorrar apenas cobrás, antes de gastar, hace que el ahorro no dependa de que sobre plata. Y en "
              "un fondo que rinde, no pierde valor con la inflación."),
             ("Guardar efectivo en una alcancía: así no lo ves y no lo gastás.", 0, 0, R,
              "Ahorrar es un buen hábito, pero el efectivo guardado pierde 2% de valor cada mes con la "
              "inflación. La misma plata en un fondo que rinde mantendría su valor."),
             ("Ahorrar lo que te sobre a fin de mes.", -30_000, 0, I,
              "A fin de mes casi nunca sobra: los gastos chicos ocupan todo el lugar disponible y este mes se "
              "fueron $30.000. Si el ahorro es lo último, suele no haber ahorro."),
         ]),
    # ------------------------------------------------------------- MES 7
    _esc(7, 1, "presupuesto",
         "En las vacaciones de invierno tu jefe te ofrece tres propuestas de trabajo:",
         [
             ("40 horas a $1.000 la hora, con pago seguro.", 40_000, 0, A,
              "Cobraste $40.000 seguros. Como la cuota del viaje es un gasto fijo, conviene que el ingreso que "
              "la paga también sea seguro: un ingreso variable puede no alcanzar justo el mes que lo necesitás."),
             ("Cobrar a comisión: el 10% de lo que vendas. El año pasado alguien sacó $80.000 y otros sacaron "
              "$20.000.", 15_000, 0, R,
              "Qué pasó después: vendiste poco y cobraste $15.000. Un ingreso a comisión puede ser mayor, pero "
              "no es seguro, y la cuota fija no espera."),
             ("Hacer un curso de $30.000, que pagás con la tarjeta, para certificarte y cobrar el doble por "
              "hora en el verano.", 0, 30_000, I,
              "El curso puede servir, pero el ingreso extra llega recién después del viaje y ahora tenés "
              "$30.000 de deuda en la tarjeta que genera intereses. Gastar hoy un ingreso futuro que todavía no "
              "cobraste deja al presupuesto sin margen."),
         ]),
    _esc(7, 2, "inflacion",
         "Tu jefe te debe $60.000 por las horas extra. Te ofrece tres formas de pagarte:",
         [
             ("Pagarte en 2 meses, ajustando lo que te debe por inflación más 1% cada mes.", 1_200, 0, A,
              "Cada mes tu plata creció 3% (2% de inflación más 1%): cobrás unos $63.650. Descontada la "
              "inflación, ganaste poder de compra."),
             ("Pagarte ahora, y lo ponés en un plazo fijo al 1,5% mensual.", -600, 0, R,
              "El 1,5% parece más que el 1% de la otra opción, pero ese 1% se sumaba a la inflación. El plazo "
              "fijo al 1,5% rinde menos que los precios, que suben 2%: perdiste un poco de poder de compra."),
             ("Pagarte en 3 cuotas fijas de $20.300, que en total suman $60.900.", -1_500, 0, I,
              "Cobrás $60.900, más que los $60.000, pero en cuotas fijas que pierden valor con la inflación: "
              "en pesos de hoy equivalen a unos $58.500. Cuotas sin ajuste pierden valor cada mes."),
         ]),
    # ------------------------------------------------------------- MES 8
    _esc(8, 1, "intereses",
         "Querés una consola usada que cuesta $100.000 y no tenés toda la plata. ¿Cómo la conseguís?",
         [
             ("Juntar la plata durante 3 meses y comprarla después.", -106_000, 0, A,
              "Por la inflación, en 3 meses la consola sube a unos $106.000, pero no pagás ningún interés. "
              "Esperar es lo más barato cuando no hay apuro."),
             ("Préstamo de un familiar, al 4% mensual simple, a 6 meses.", -124_000, 0, R,
              "Con interés simple, cada mes pagás el 4% de $100.000: $4.000. En 6 meses son $24.000 de "
              "interés, y la consola te cuesta $124.000."),
             ("Préstamo de una app: ¡solo 3,5% mensual!, capitalizable, a 12 meses.", -151_000, 0, I,
              "Capitalizable significa que cada mes el interés se suma a lo que debés, y el mes siguiente "
              "también genera interés: es interés compuesto. En 12 meses, $100.000 al 3,5% llegan a unos "
              "$151.000. Una tasa más baja puede salir más cara si el plazo es más largo y el interés es "
              "compuesto."),
         ]),
    _esc(8, 2, "deuda_credito",
         "Llegó el resumen de la tarjeta: gastaste $60.000. El pago mínimo es de $6.000 y la tarjeta cobra un "
         "8% mensual sobre lo que no pagues.",
         [
             ("Pagar el total.", -60_000, 0, A,
              "Pagaste los $60.000 y no quedó saldo que genere intereses."),
             ("Pagar el mínimo.", -6_000, 54_000, R,
              "Pagaste el mínimo, así que el saldo de $54.000 siguió generando intereses: cada mes se suma un 8% "
              "y van a seguir acumulándose mientras la deuda no se cancele por completo."),
             ("No pagar este mes.", 0, 60_000, I,
              "Los $60.000 quedaron como deuda y crecen 8% cada mes. Si no se paga, la deuda crece sola, sin "
              "que vuelvas a usar la tarjeta."),
         ]),
    # ------------------------------------------------------------- MES 9
    _esc(9, 1, "presupuesto",
         "Te entraron $40.000 extra y tenés tres deudas de $40.000 cada una. Solo te alcanza para cancelar "
         "una:",
         [
             ("La tarjeta, que cobra 8% mensual.", 3_000, 0, A,
              "Cancelaste la deuda más cara. Cuando la plata no alcanza para todas, conviene pagar primero la "
              "que cobra más interés: cada mes te ahorrás ese 8%."),
             ("Las cuotas del celular, al 3% mensual.", 1_000, 0, R,
              "Te ahorraste el 3% mensual del celular, pero la tarjeta siguió cobrando 8%. Pagar la deuda más "
              "barata primero deja crecer la más cara."),
             ("El préstamo de tu tío, que no te cobra interés pero te lo recuerda cada vez que lo ves.",
              0, 0, I,
              "Cancelaste la única deuda que no te costaba nada, mientras la tarjeta (8%) y el celular (3%) "
              "siguieron sumando intereses. Ordenar las deudas por su tasa ayuda a decidir cuál pagar primero."),
         ]),
    _esc(9, 2, "ahorro",
         "Tenés $30.000 ahorrados que quizás necesites pronto para las cuotas.",
         [
             ("Una cuenta remunerada al 24% anual, que suma intereses todos los días, y la plata se saca "
              "cuando quieras.", 600, 0, A,
              "Rinde lo mismo que el plazo fijo, pero podés sacar la plata cuando la necesitás. A igual "
              "rendimiento, conviene la opción con más liquidez."),
             ("Un plazo fijo a 30 días al 24% anual.", 600, 0, R,
              "Rinde lo mismo que la cuenta remunerada, pero la plata queda inmovilizada 30 días. Si la "
              "necesitás antes para una cuota, no la podés usar."),
             ("Un compañero te los pide para revender zapatillas y te devuelve $36.000 en un mes: un 20%. Dice "
              "que ya le funcionó con otros dos.", -30_000, 0, I,
              "Qué pasó después: las zapatillas no se vendieron y tu compañero nunca te devolvió la plata. Además, "
              "aunque saliera bien, tu plata queda atada a que él venda, justo cuando tenés cuotas fijas para "
              "pagar. Un 20% en un mes es una promesa muy alta para plata que necesitás pronto."),
         ]),
    # ------------------------------------------------------------- MES 10
    _esc(10, 1, "intereses",
         "Tenés $50.000 que vas a usar dentro de 6 meses, después del viaje. Recordá que los precios suben 2% "
         "por mes y el dólar sube 1% por mes.",
         [
             ("Una cuenta que paga 2,5% mensual y suma cada mes los intereses al capital, que el mes "
              "siguiente también generan interés.", 2_000, 0, A,
              "Con interés compuesto llegás a unos $57.990 en 6 meses: los intereses de cada mes también "
              "generan intereses. Es la opción que más crece."),
             ("Un plazo fijo a 6 meses, al 2,5% mensual simple.", 1_000, 0, R,
              "Con interés simple, el 2,5% se calcula siempre sobre los $50.000: llegás a $57.500. A la misma "
              "tasa, el interés compuesto rinde más porque los intereses también generan intereses."),
             ("Comprar dólares y venderlos dentro de 6 meses.", -3_000, 0, I,
              "El dólar sube 1% por mes: en 6 meses tus $50.000 se convierten en unos $53.000. Pero los "
              "precios suben 2% por mes, así que podés comprar menos que hoy."),
         ]),
    _esc(10, 2, "riesgo_inversion",
         "Un amigo te recomienda una criptomoneda nueva que está explotando: subió 300% en un mes.",
         [
             ("No invertir.", 0, 0, A,
              "No pusiste plata. Qué pasó con la cripto: subió 40% en dos semanas más y después cayó 85% "
              "cuando sus creadores vendieron todo."),
             ("Poner un poco de tus ahorros, $20.000.", 20_000, 0, R,
              "Esta vez te salió bien: vendiste a tiempo y ganaste $20.000. Qué pasó con la cripto: subió 40% "
              "en dos semanas más y después cayó 85% cuando sus creadores vendieron todo. Que haya salido "
              "bien no la hace una decisión menos riesgosa."),
             ("Poner una parte importante de tus ahorros, $80.000.", -80_000, 0, I,
              "Qué pasó con la cripto: subió 40% en dos semanas más y después cayó 85% cuando sus creadores "
              "vendieron todo, y perdiste $80.000. Una suba muy rápida no garantiza que siga subiendo."),
         ]),
    # ------------------------------------------------------------- MES 11
    _esc(11, 1, "deuda_credito",
         "Tu banco te ofrece un préstamo de $100.000 a una tasa promocional del 1,5% mensual.",
         [
             ("Tomarlo y ponerlo en un plazo fijo al 2,5% mensual. Si tenés deuda de tarjeta, usarlo primero "
              "para cancelarla, porque cobra 8%.", -98_000, -100_000, A,
              "Una deuda conviene cuando lo que te rinde es mayor que lo que te cuesta y no tiene riesgo: "
              "pagás 1,5% y ganás 2,5%. Y si tenías deuda de tarjeta al 8%, la cambiaste por una del 1,5%."),
             ("Tomarlo y ponerlo en una plataforma cripto que paga 6% mensual.", -20_000, 0, R,
              "Qué pasó después: la plataforma frenó los retiros y recuperaste solo el 80%, pero el préstamo "
              "lo tenés que devolver completo. Tomar deuda para invertir en algo riesgoso multiplica la "
              "pérdida."),
             ("Tomarlo y ponerlo en un plazo fijo al 18% anual, para no tenerlo quieto.", -2_000, 0, I,
              "Un 18% anual es 1,5% por mes: exactamente lo mismo que te cobra el préstamo, así que no ganaste "
              "nada, y con la inflación del 2% perdiste poder de compra. Para comparar tasas hay que llevarlas "
              "a la misma unidad."),
         ]),
    _esc(11, 2, "ahorro",
         "Tenés ahorros para después del viaje y querés invertirlos.",
         [
             ("Repartir la plata: una parte en un fondo money market, que la presta por muy poco tiempo, rinde "
              "poco y se saca cuando quieras; y otra parte en un fondo de bonos, que presta la plata al Estado o "
              "a empresas por más tiempo a cambio de un interés mayor.", 4_000, 0, A,
              "Repartir la plata entre inversiones distintas se llama diversificar: si a una le va mal, no "
              "perdés todo. Combinaste algo líquido con algo que rinde un poco más."),
             ("Ponerla toda en una sola acción que subió mucho este año.", -40_000, 0, R,
              "Qué pasó después: la acción corrigió y bajó. Que algo haya subido mucho no significa que siga "
              "subiendo, y tener todo en un solo lugar hace que una caída te afecte de lleno."),
             ("Pagar $65.000 por un curso de inversiones que garantiza ganar 20% mensual.", -65_000, 0, I,
              "Nadie puede garantizar un 20% mensual: sería multiplicar la plata casi 9 veces en un año. Las "
              "promesas de ganancia garantizada y muy alta son una señal de alerta."),
         ]),
    # ------------------------------------------------------------- MES 12
    _esc(12, 1, "inflacion",
         "Necesitás una campera para el viaje que cuesta $50.000. Recordá que los precios suben 2% por mes.",
         [
             ("Contado, con 5% de descuento: $47.500.", -47_500, 0, A,
              "Pagaste $47.500. El 5% de descuento es más de lo que la inflación le saca de valor a unas pocas "
              "cuotas, así que esta vez el contado conviene. Las cuotas convienen cuando el descuento por "
              "pagar contado es chico frente a la inflación."),
             ("2 cuotas sin interés de $25.000.", -48_500, 0, R,
              "Por la inflación, las 2 cuotas de $25.000 valen en pesos de hoy unos $48.500: más que pagar "
              "contado con el 5% de descuento."),
             ("3 cuotas de $17.000.", -49_000, 0, I,
              "Las 3 cuotas suman $51.000: tienen un interés escondido. Aun con la inflación, equivalen a "
              "unos $49.000 de hoy, más que las otras dos opciones."),
         ]),
    _esc(12, 2, "riesgo_inversion",
         "Tu prima te invita a Comunidad Libertad Financiera: pagás $25.000 de inscripción y cobrás $10.000 "
         "por cada amigo que sumes. Ella recuperó lo suyo en 2 semanas.",
         [
             ("No sumarte.", 0, 0, A,
              "No pusiste plata. Qué pasó después: a los dos meses no se sumaba nadie nuevo y nadie más cobró. "
              "Cuando la única forma de ganar es sumar a otros, se trata de un esquema piramidal."),
             ("Sumarte con la inscripción básica.", -25_000, 0, R,
              "Qué pasó después: a los dos meses no se sumaba nadie nuevo y nadie más cobró, y perdiste los "
              "$25.000. Cuando la única forma de ganar es sumar a otros, se trata de un esquema piramidal."),
             ("Sumarte con el plan premium de $90.000, que paga el doble por cada amigo.", -90_000, 0, I,
              "Qué pasó después: a los dos meses no se sumaba nadie nuevo y nadie más cobró, y perdiste los "
              "$90.000. Los que entran tarde pierden su plata, porque solo cobran los primeros."),
         ]),
]
