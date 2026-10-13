"""Motor de escenarios y de calculo de consecuencias.

El estado financiero del alumno no se guarda como dato suelto: se recalcula
reproduciendo sus decisiones sobre los parametros globales y la inflacion
mensual. Asi el resultado es siempre consistente con el contenido
parametrizado y con el registro de decisiones.

El sueldo, los gastos fijos, la cuota del viaje y las deudas quedan fijos en
pesos. La inflacion le saca poder de compra a lo que tenes en pesos (tu plata,
tus inversiones y lo que te deben): en cada cierre vale 2% menos.

Cartera: ademas del efectivo, cada decision puede crear posiciones que
evolucionan mes a mes segun sus condiciones:
  - inversion: rinde su tasa mensual, vence a su plazo y vuelve al efectivo;
    las liquidas se pueden rescatar para pagar la cuota del viaje.
  - deuda en cuotas: se paga en los meses pactados (cuotas fijas en pesos).
  - deuda abierta (tarjeta, descubierto): crece con la tasa mensual y se
    cancela sola al cierre con lo que sobra despues de la cuota del viaje.
  - a cobrar: plata que alguien te debe y entra en el mes pactado.
  - compra programada: un gasto comprometido para un mes futuro.
  - aporte mensual: cada mes, al cobrar, se pasa un monto a una inversion.

Ciclo de cada mes:
  1. Cobro: efectivo += ingreso del mes - gastos fijos; se hacen los aportes.
  2. Decision 1 y decision 2: se aplican las operaciones de la opcion elegida.
     Si el efectivo queda negativo, el faltante pasa a deuda (descubierto).
  3. Cierre: rinden las inversiones y vencen las que llegan a plazo; entran
     los cobros; se pagan cuotas de prestamos y compras programadas; la deuda
     abierta suma su interes; se paga la cuota del viaje (y las atrasadas),
     rescatando inversiones liquidas si hace falta; lo que sobra cancela deuda
     abierta; la inflacion achica lo que esta en pesos.
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
DEUDA_ABIERTA = "Tarjeta y descubierto"
RESERVA_CUOTAS = 0  # al cierre, todo lo que sobra despues de la cuota cancela la deuda de tarjeta


@dataclass
class OpcionMotor:
    opcion_id: int
    delta_ahorro: float
    delta_deuda: float
    clasificacion: str
    tipo_error: str | None
    ops: list | None = None

    def operaciones(self) -> list[dict]:
        if self.ops is not None:
            return self.ops
        ops = [{"op": "efectivo", "monto": self.delta_ahorro}]
        if self.delta_deuda:
            ops.append({"op": "deuda", "monto": self.delta_deuda})
        return ops


@dataclass
class Posicion:
    id: int
    tipo: str  # inversion | deuda_cuotas | deuda_abierta | a_cobrar | compra
    nombre: str
    emoji: str = ""
    valor: float = 0.0  # pesos de hoy
    tasa: float = 0.0  # mensual nominal
    tasas: list | None = None  # rendimiento mes a mes (si no es fijo)
    meses: int | None = None  # meses que faltan para vencer (None = sin plazo)
    liquida: bool = False
    moneda: str = "pesos"
    aporte: float = 0.0
    pagos: list = field(default_factory=list)  # [(mes, monto en pesos de hoy, monto nominal)]
    desde: int = 1
    meses_corridos: int = 0
    detalle: str = ""
    paga_con: int | None = None  # deuda en cuotas que se paga con una inversion (id)

    def saldo(self) -> float:
        if self.tipo in ("deuda_cuotas", "a_cobrar", "compra"):
            return sum(p[1] for p in self.pagos)
        return self.valor


@dataclass
class CierreMes:
    mes: int
    cuotas_pagadas_en_cierre: int
    cuota_del_mes_pagada: bool
    cuotas_atrasadas: int
    interes_deuda: float
    perdida_inflacion: float
    efectivo_antes_cuota: float
    efectivo_final: float
    deuda_antes_interes: float
    deuda_final: float
    cuotas_pagadas_total: int
    patrimonio_inicio: float
    cobro_neto: float
    rendimientos: float
    compras: float
    movimientos: list
    cartera: list
    patrimonio_neto: float
    avance_viaje_pct: float
    criterio_financiero_pct: float


@dataclass
class Estado:
    efectivo: float = 0.0
    posiciones: list = field(default_factory=list)
    cuotas_pagadas: int = 0
    cuotas_atrasadas: int = 0
    decisiones: int = 0
    acertadas: int = 0
    riesgosas: int = 0
    incorrectas: int = 0
    mes_actual: int = 1
    orden_actual: int = 1
    terminado: bool = False
    patrimonio_mes_anterior: float = 0.0
    cobro_mes: float = 0.0
    movimientos_mes: list = field(default_factory=list)
    proximo_id: int = 1
    cierres: list = field(default_factory=list)

    # ------------------------------------------------------------ totales
    def de_tipo(self, *tipos) -> list[Posicion]:
        return [p for p in self.posiciones if p.tipo in tipos]

    @property
    def deuda(self) -> float:
        return sum(p.saldo() for p in self.de_tipo("deuda_cuotas", "deuda_abierta"))

    @deuda.setter
    def deuda(self, valor: float) -> None:  # para pruebas y datos iniciales
        for p in self.de_tipo("deuda_abierta"):
            self.posiciones.remove(p)
        if valor:
            self.sumar_deuda_abierta(valor)

    def deuda_abierta(self) -> float:
        return sum(p.valor for p in self.de_tipo("deuda_abierta"))

    def inversiones(self) -> float:
        return sum(p.saldo() for p in self.de_tipo("inversion", "a_cobrar"))

    def patrimonio_neto(self) -> float:
        return self.efectivo + self.inversiones() - self.deuda

    # ------------------------------------------------------------ helpers
    def nueva(self, **kw) -> Posicion:
        p = Posicion(id=self.proximo_id, desde=self.mes_actual, **kw)
        self.proximo_id += 1
        self.posiciones.append(p)
        return p

    def sumar_deuda_abierta(self, monto: float, nombre: str = DEUDA_ABIERTA, tasa: float = 0.08) -> None:
        p = next((x for x in self.de_tipo("deuda_abierta")), None)
        if p is None:
            p = self.nueva(tipo="deuda_abierta", nombre=nombre, emoji="💳", tasa=tasa)
        p.valor += monto

    def cancelar_deuda_abierta(self, monto: float) -> float:
        """Cancela deuda abierta hasta `monto`; devuelve lo cancelado."""
        cancelado = 0.0
        for p in self.de_tipo("deuda_abierta"):
            x = min(p.valor, monto - cancelado)
            p.valor -= x
            cancelado += x
            if p.valor < 0.5:
                self.posiciones.remove(p)
        return cancelado

    def rescatar(self, necesario: float, motivo: str) -> float:
        """Saca plata de inversiones liquidas (primero las que menos rinden)."""
        sacado = 0.0
        for p in sorted(self.de_tipo("inversion"), key=lambda x: x.tasa):
            if not p.liquida or sacado >= necesario:
                continue
            x = min(p.valor, necesario - sacado)
            p.valor -= x
            sacado += x
            self.efectivo += x
            self.movimientos_mes.append(mov(p, "rescate", x, f"Sacaste {pesos_txt(x)} para {motivo}"))
            if p.valor < 0.5 and not p.aporte:
                self.posiciones.remove(p)
        return sacado

    def pagar(self, monto: float, motivo: str, p: Posicion | None = None) -> None:
        if self.efectivo < monto:
            self.rescatar(monto - self.efectivo, motivo)
        if self.efectivo >= monto:
            self.efectivo -= monto
            return
        faltante = monto - self.efectivo
        self.efectivo = 0.0
        self.sumar_deuda_abierta(faltante)
        self.movimientos_mes.append({"posicion": DEUDA_ABIERTA, "emoji": "💳", "tipo": "impago", "monto": round(faltante),
                                     "texto": f"No alcanzó para {motivo}: {pesos_txt(faltante)} pasaron a deuda con la tarjeta"})


def pesos_txt(n: float) -> str:
    v = round(n)
    return ("-$" if v < 0 else "$") + f"{abs(v):,}".replace(",", ".")


def mov(p: Posicion, tipo: str, monto: float, texto: str) -> dict:
    return {"posicion": p.nombre, "emoji": p.emoji, "tipo": tipo, "monto": round(monto), "texto": texto}


def avance_viaje_pct(p: dict, cuotas_pagadas: int) -> float:
    pagado = p["sena_viaje"] + cuotas_pagadas * p["cuota_viaje"]
    return round(100 * pagado / p["costo_total_viaje"], 1)


# Criterio financiero: arranca en 50 y se mueve de a poco con cada decision.
CRITERIO_INICIAL = 50
PUNTOS_CRITERIO = {"acertada": 3, "riesgosa": -1, "incorrecta": -3}


def criterio_pct(estado: Estado) -> float:
    valor = (CRITERIO_INICIAL + PUNTOS_CRITERIO["acertada"] * estado.acertadas
             + PUNTOS_CRITERIO["riesgosa"] * estado.riesgosas + PUNTOS_CRITERIO["incorrecta"] * estado.incorrectas)
    return float(max(0, min(100, valor)))


def ingreso_del_mes(p: dict, mes: int) -> float:
    return p["ingreso_base_mensual"] + p.get(f"ingreso_extra_mes_{mes}", 0)


def _factor(inflacion: dict, desde: int, meses: int) -> float:
    f = 1.0
    for m in range(desde, desde + meses):
        f *= 1 + inflacion.get(m, inflacion.get(12, 0.02))
    return f


def aplicar_opcion(estado: Estado, op: OpcionMotor, inflacion: dict | None = None, p: dict | None = None) -> None:
    inflacion = inflacion or {}
    mes = estado.mes_actual
    vincular = []
    for o in op.operaciones():
        t = o["op"]
        if t == "efectivo":
            estado.efectivo += o["monto"]
        elif t == "deuda":
            if o["monto"] >= 0:
                estado.sumar_deuda_abierta(o["monto"])
            else:
                cancelado = estado.cancelar_deuda_abierta(-o["monto"])
                estado.efectivo += -o["monto"] - cancelado  # lo no usado vuelve
        elif t == "inversion":
            monto = o.get("monto", 0)
            estado.efectivo -= monto
            estado.nueva(tipo="inversion", nombre=o["nombre"], emoji=o.get("emoji", "📈"), valor=monto,
                         tasa=o.get("tasa", 0.0), tasas=list(o["tasas"]) if o.get("tasas") else None,
                         meses=o.get("meses"), liquida=o.get("liquida", False), moneda=o.get("moneda", "pesos"),
                         detalle=o.get("detalle", ""))
        elif t == "aporte":
            pos = estado.nueva(tipo="inversion", nombre=o["nombre"], emoji=o.get("emoji", "🐖"), valor=0.0,
                               tasa=o.get("tasa", 0.0), liquida=True, aporte=o["monto"], detalle=o.get("detalle", ""))
            x = min(o["monto"], max(0.0, estado.efectivo)) if estado.efectivo > 0 else 0.0
            estado.efectivo -= x
            pos.valor += x
        elif t == "prestamo":
            # Las deudas quedan fijas en pesos: la inflacion no las achica (el sueldo tampoco sube).
            estado.efectivo += o.get("recibido", 0)
            pagos = [(mes + k, n, n) for k, n in enumerate(o["cuotas"], start=1)]
            d = estado.nueva(tipo="deuda_cuotas", nombre=o["nombre"], emoji=o.get("emoji", "🤝"), pagos=pagos,
                             detalle=o.get("detalle", ""))
            if o.get("paga_con"):
                vincular.append((d, o["paga_con"]))
        elif t == "a_cobrar":
            pagos = [(mes + k, n / _factor(inflacion, mes, k), n) for k, n in o["pagos"]]
            estado.efectivo -= o.get("costo", 0)
            estado.nueva(tipo="a_cobrar", nombre=o["nombre"], emoji=o.get("emoji", "🧾"), pagos=pagos,
                         detalle=o.get("detalle", ""))
        elif t == "compra":
            k, n = o["en_meses"], o["monto"]
            estado.nueva(tipo="compra", nombre=o["nombre"], emoji=o.get("emoji", "🛒"),
                         pagos=[(mes + k, n, n)], detalle=o.get("detalle", ""))
        elif t == "refinanciar":
            # Tomar un prestamo, cancelar la deuda abierta (mas cara) e invertir lo que sobra.
            # Con solo_deuda se pide solo lo necesario para cancelar la deuda abierta (o nada).
            recibido = o["recibido"]
            cuotas = o["cuotas"]
            if o.get("solo_deuda"):
                tope = min(recibido, round(estado.deuda_abierta()))
                if tope < 1:
                    continue
                cuotas = [round(c * tope / recibido) for c in cuotas]
                recibido = tope
            estado.efectivo += recibido
            pagos = [(mes + k, n, n) for k, n in enumerate(cuotas, start=1)]
            estado.nueva(tipo="deuda_cuotas", nombre=o["nombre"], emoji="🏦", pagos=pagos, detalle=o.get("detalle", ""))
            cancelado = estado.cancelar_deuda_abierta(recibido)
            estado.efectivo -= cancelado
            resto = recibido - cancelado
            if resto > 0:
                estado.efectivo -= resto
                estado.nueva(tipo="inversion", nombre=o["inversion"], emoji="🏦", valor=resto, tasa=o["tasa_inversion"],
                             meses=o.get("meses_inversion", 1), detalle=o.get("detalle_inversion", ""))
    for d, nombre in vincular:
        inv = next((x for x in estado.de_tipo("inversion") if x.nombre == nombre and x.desde == mes), None)
        if inv is not None:
            d.paga_con = inv.id
    if estado.efectivo < 0:  # giro en descubierto
        estado.sumar_deuda_abierta(-estado.efectivo)
        estado.efectivo = 0.0
    estado.decisiones += 1
    if op.clasificacion == "acertada":
        estado.acertadas += 1
    elif op.clasificacion == "riesgosa":
        estado.riesgosas += 1
    else:
        estado.incorrectas += 1


def cerrar_mes(estado: Estado, p: dict, mes: int, inflacion: float) -> CierreMes:
    movs = estado.movimientos_mes
    rendimientos = 0.0
    compras = 0.0

    # 1. Inversiones: rinden y, si llegan a plazo, vuelven al efectivo.
    for inv in list(estado.de_tipo("inversion")):
        if inv.tasas is not None:
            r = inv.tasas[min(inv.meses_corridos, len(inv.tasas) - 1)]
        else:
            r = inv.tasa
        ganancia = inv.valor * r
        inv.valor += ganancia
        inv.meses_corridos += 1
        rendimientos += ganancia
        if abs(ganancia) >= 1:
            pct = f"{round(100 * r, 2):g}".replace(".", ",")
            verbo = ("Subió" if inv.moneda == "dolares" else "Rindió") if ganancia > 0 else "Perdió"
            movs.append(mov(inv, "rinde", ganancia, f"{verbo} {pesos_txt(abs(ganancia))} ({pct}% este mes)"))
        if inv.meses is not None:
            inv.meses -= 1
            if inv.meses <= 0:
                estado.efectivo += inv.valor
                movs.append(mov(inv, "vence", inv.valor, f"Venció: volvieron {pesos_txt(inv.valor)} a tu plata"))
                estado.posiciones.remove(inv)

    # 2. Cobros pactados.
    for c in list(estado.de_tipo("a_cobrar")):
        for pago in [x for x in c.pagos if x[0] == mes]:
            estado.efectivo += pago[1]
            c.pagos.remove(pago)
            movs.append(mov(c, "cobro", pago[1], f"Cobraste {pesos_txt(pago[2])}" + (
                f": con los precios más altos, compran lo que antes {pesos_txt(pago[1])}" if abs(pago[2] - pago[1]) >= 1 else "")))
        if not c.pagos:
            estado.posiciones.remove(c)

    # 3. Cuotas de prestamos y compras programadas.
    for d in list(estado.de_tipo("deuda_cuotas", "compra")):
        for pago in [x for x in d.pagos if x[0] == mes]:
            d.pagos.remove(pago)
            es_compra = d.tipo == "compra"
            inv = next((x for x in estado.de_tipo("inversion") if x.id == d.paga_con), None)
            if inv is not None and inv.valor >= 0.5:
                x = min(inv.valor, pago[1])
                inv.valor -= x
                estado.efectivo += x
                movs.append(mov(inv, "rescate", x, f"Sacaste {pesos_txt(x)} para la cuota de {d.nombre.lower()}"))
                if inv.valor < 0.5:
                    estado.posiciones.remove(inv)
            if es_compra:
                compras += pago[1]
            estado.pagar(pago[1], d.nombre.lower() if es_compra else f"la cuota de {d.nombre.lower()}", d)
            texto = f"Pagaste {pesos_txt(pago[2])}"
            movs.append(mov(d, "compra" if es_compra else "pago", -pago[1], texto))
        if not d.pagos:
            estado.posiciones.remove(d)

    # 4. La deuda abierta suma su interes.
    deuda_antes = estado.deuda
    interes = 0.0
    for d in estado.de_tipo("deuda_abierta"):
        i = d.valor * p["tasa_deuda_abierta_mensual"]
        d.valor += i
        interes += i
        movs.append(mov(d, "interes", -i, f"Sumó {pesos_txt(i)} de interés ({round(100 * p['tasa_deuda_abierta_mensual']):g}%)"))

    # 5. Cuota del viaje (y las atrasadas), rescatando inversiones liquidas si hace falta.
    efectivo_antes = estado.efectivo
    estado.cuotas_atrasadas += 1
    pagadas = 0
    cuota = p["cuota_viaje"]
    if estado.efectivo < cuota * estado.cuotas_atrasadas:
        estado.rescatar(cuota * estado.cuotas_atrasadas - estado.efectivo, "la cuota del viaje")
    while estado.cuotas_atrasadas > 0 and estado.efectivo >= cuota - 0.5:
        estado.efectivo = max(0.0, estado.efectivo - cuota)
        estado.cuotas_pagadas += 1
        estado.cuotas_atrasadas -= 1
        pagadas += 1

    # 6. Lo que sobra despues de la cuota cancela la deuda abierta (tarjeta,
    # descubierto). Si no alcanza, se usan las inversiones que se sacan en el dia:
    # rinden menos de lo que cobra la tarjeta.
    reserva = p["cuota_viaje"] * RESERVA_CUOTAS
    if estado.de_tipo("deuda_abierta"):
        liquido = sum(x.valor for x in estado.de_tipo("inversion") if x.liquida)
        puede = min(estado.deuda_abierta(), estado.efectivo + liquido - reserva)
        falta_efectivo = puede - max(0.0, estado.efectivo - reserva)
        if falta_efectivo >= 1:
            estado.rescatar(falta_efectivo, "cancelar la tarjeta, que cobra más de lo que rinden")
    disponible = estado.efectivo - reserva
    if disponible > 0 and estado.de_tipo("deuda_abierta"):
        cancelado = estado.cancelar_deuda_abierta(disponible)
        estado.efectivo -= cancelado
        if cancelado >= 1:
            queda = estado.deuda_abierta()
            movs.append({"posicion": DEUDA_ABIERTA, "emoji": "💳", "tipo": "pago_deuda", "monto": round(cancelado),
                         "texto": f"Con lo que te sobró después de la cuota pagaste {pesos_txt(cancelado)}"
                         + (" y la cancelaste toda" if queda < 1 else f". Quedan {pesos_txt(queda)}")})
    if estado.deuda_abierta() >= 1:
        queda = estado.deuda_abierta()
        movs.append({"posicion": DEUDA_ABIERTA, "emoji": "⚠️", "tipo": "impago", "monto": -round(queda),
                     "texto": f"No te quedó efectivo para cancelarla: siguen {pesos_txt(queda)} de deuda, que el mes "
                     f"que viene suman {round(100 * p['tasa_deuda_abierta_mensual']):g}% de interés "
                     f"({pesos_txt(queda * p['tasa_deuda_abierta_mensual'])})"})

    # 7. Inflacion: lo que tenes en pesos (plata e inversiones) compra menos. Lo que
    # debes queda fijo en pesos, igual que el sueldo: la inflacion no lo achica.
    f = 1 + inflacion
    pn_antes = estado.patrimonio_neto()
    estado.efectivo /= f
    for x in estado.de_tipo("inversion"):
        x.valor /= f
    perdida = pn_antes - estado.patrimonio_neto()

    cierre = CierreMes(
        mes=mes,
        cuotas_pagadas_en_cierre=pagadas,
        cuota_del_mes_pagada=estado.cuotas_atrasadas == 0,
        cuotas_atrasadas=estado.cuotas_atrasadas,
        interes_deuda=round(interes),
        perdida_inflacion=round(perdida),
        efectivo_antes_cuota=round(efectivo_antes),
        efectivo_final=round(estado.efectivo),
        deuda_antes_interes=round(deuda_antes),
        deuda_final=round(estado.deuda),
        cuotas_pagadas_total=estado.cuotas_pagadas,
        patrimonio_inicio=round(estado.patrimonio_mes_anterior),
        cobro_neto=round(estado.cobro_mes),
        rendimientos=round(rendimientos),
        compras=round(compras),
        movimientos=movs,
        cartera=cartera(estado),
        patrimonio_neto=round(estado.patrimonio_neto()),
        avance_viaje_pct=avance_viaje_pct(p, estado.cuotas_pagadas),
        criterio_financiero_pct=criterio_pct(estado),
    )
    estado.movimientos_mes = []
    estado.cierres.append(cierre)
    return cierre


def _cobrar(estado: Estado, p: dict, mes: int) -> None:
    estado.cobro_mes = ingreso_del_mes(p, mes) - p["gastos_fijos_mensuales"]
    estado.efectivo += estado.cobro_mes
    for inv in estado.de_tipo("inversion"):
        if inv.aporte and inv.desde < mes:
            x = min(inv.aporte, max(0.0, estado.efectivo))
            estado.efectivo -= x
            inv.valor += x
            if x >= 1:
                estado.movimientos_mes.append(mov(inv, "aporte", x, f"Apartaste {pesos_txt(x)} del sueldo"))


def simular(p: dict, inflacion: dict[int, float], opciones_elegidas: list[OpcionMotor],
            cerrar_ultimo: bool = True) -> Estado:
    """Reproduce el recorrido a partir de las opciones elegidas, en orden.
    Con cerrar_ultimo=False se detiene justo despues de la ultima decision (sin cierre)."""
    estado = Estado(efectivo=p["efectivo_inicial"] - p["sena_viaje"])
    pendientes = list(opciones_elegidas)
    for mes in range(1, 13):
        estado.mes_actual, estado.orden_actual = mes, 1
        estado.patrimonio_mes_anterior = estado.patrimonio_neto()
        _cobrar(estado, p, mes)
        for orden in (1, 2):
            estado.orden_actual = orden
            if not pendientes:
                return estado
            aplicar_opcion(estado, pendientes.pop(0), inflacion, p)
            if not pendientes and not cerrar_ultimo:
                return estado
        cerrar_mes(estado, p, mes, inflacion[mes])
    estado.terminado = True
    estado.mes_actual, estado.orden_actual = 12, 2
    return estado


ESTADOS_AVATAR = ("euforico", "contento", "neutral", "preocupado", "triste")


def estado_avatar(estado: Estado) -> str:
    """Expresion del avatar (HU-008), segun tres cosas a la vez: si las cuotas del
    viaje estan al dia, el patrimonio neto y el criterio financiero."""
    patrimonio = estado.patrimonio_neto()
    criterio = criterio_pct(estado)
    atrasadas = estado.cuotas_atrasadas
    if atrasadas >= 2 or patrimonio < -100_000:
        return "triste"
    if atrasadas == 1 or patrimonio < 0:
        return "preocupado"
    if estado.decisiones == 0:
        return "neutral"
    if criterio >= 70 and patrimonio >= 50_000:
        return "euforico"
    if criterio >= 50:
        return "contento"
    return "neutral"


def barras(p: dict, estado: Estado) -> dict:
    liquido = sum(x.valor for x in estado.de_tipo("inversion") if x.liquida)
    return {
        "patrimonio_neto": round(estado.patrimonio_neto()),
        "efectivo": round(estado.efectivo),
        # efectivo + inversiones que se sacan en el dia (con eso se paga la cuota)
        "disponible": round(estado.efectivo + liquido),
        "inversiones": round(estado.inversiones()),
        "deuda": round(estado.deuda),
        "avance_viaje_pct": avance_viaje_pct(p, estado.cuotas_pagadas),
        "criterio_financiero_pct": criterio_pct(estado),
        "cuotas_pagadas": estado.cuotas_pagadas,
        "cuotas_atrasadas": estado.cuotas_atrasadas,
        "acertadas": estado.acertadas,
        "riesgosas": estado.riesgosas,
        "incorrectas": estado.incorrectas,
    }


def _plazo_txt(meses: int) -> str:
    return "vence este mes" if meses <= 1 else f"vence en {meses} meses"


def cartera(estado: Estado) -> list[dict]:
    """Todo lo que el alumno tiene y debe, para mostrarlo siempre en pantalla."""
    mes = estado.mes_actual
    out = [{"id": 0, "tipo": "efectivo", "nombre": "Tu plata", "emoji": "💵", "valor": round(estado.efectivo),
            "detalle": "Efectivo y cuenta: pierde valor con la inflación"}]
    for x in estado.posiciones:
        d = {"id": x.id, "tipo": x.tipo, "nombre": x.nombre, "emoji": x.emoji, "valor": round(x.saldo()),
             "liquida": x.tipo == "inversion" and x.liquida}
        if x.tipo == "inversion":
            partes = []
            if x.tasas is None:
                partes.append(f"{'el dólar sube' if x.moneda == 'dolares' else 'rinde'} {round(100 * x.tasa, 2):g}% por mes".replace(".", ","))
            if x.aporte:
                partes.append(f"le sumás {pesos_txt(x.aporte)} por mes")
            if x.meses is not None:
                partes.append(_plazo_txt(x.meses))
            partes.append("se puede sacar en el día" if x.liquida else "no se puede sacar antes")
            d["detalle"] = x.detalle or "; ".join(partes)
            d["detalle"] = d["detalle"][:1].upper() + d["detalle"][1:]
        elif x.tipo == "deuda_abierta":
            d["detalle"] = f"Crece {round(100 * x.tasa):g}% por mes; al cierre se paga con lo que te sobre"
        else:
            prox = min(x.pagos, key=lambda q: q[0])
            cuando = "este mes" if prox[0] == mes else ("el mes que viene" if prox[0] == mes + 1 else f"en {prox[0] - mes} meses")
            if prox[0] > 12:
                cuando = "después del viaje"
            verbo = {"deuda_cuotas": "Próxima cuota", "a_cobrar": "Cobrás", "compra": "Pagás"}[x.tipo]
            resto = f"; quedan {len(x.pagos)} cuotas" if x.tipo == "deuda_cuotas" and len(x.pagos) > 1 else ""
            fondo = next((i for i in estado.de_tipo("inversion") if i.id == x.paga_con), None)
            if fondo is not None:
                resto += f"; sale de {fondo.nombre.lower()}"
            d["detalle"] = f"{verbo} {pesos_txt(prox[2])} {cuando}{resto}"
        out.append(d)
    return out
