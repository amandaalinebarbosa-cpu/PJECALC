"""Cálculo de verbas rescisórias trabalhistas básicas.

Referência: CLT arts. 477-487, Lei 8.036/90 (FGTS), Lei 12.506/11 (aviso proporcional).
"""
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from dateutil.relativedelta import relativedelta

from .tabelas import calcular_inss, calcular_irrf

Q = Decimal("0.01")


def _q(v: Decimal) -> Decimal:
    return v.quantize(Q, rounding=ROUND_HALF_UP)


@dataclass
class DadosContrato:
    admissao: date
    demissao: date
    salario: Decimal
    motivo: str  # 'sem_justa_causa' | 'pedido_demissao' | 'justa_causa' | 'acordo_484a'
    aviso_cumprido: bool = False
    ferias_vencidas: bool = False  # há período aquisitivo vencido não gozado
    dependentes: int = 0
    saldo_fgts_depositado: Decimal = Decimal("0")


@dataclass
class Verba:
    nome: str
    valor: Decimal
    detalhe: str = ""


@dataclass
class ResultadoRescisao:
    verbas: list[Verba] = field(default_factory=list)
    inss: Decimal = Decimal("0")
    irrf: Decimal = Decimal("0")
    fgts_rescisorio: Decimal = Decimal("0")
    multa_fgts: Decimal = Decimal("0")
    liquido: Decimal = Decimal("0")

    def add(self, nome: str, valor: Decimal, detalhe: str = ""):
        self.verbas.append(Verba(nome, _q(valor), detalhe))


def _dias_aviso_proporcional(anos_completos: int) -> int:
    """Lei 12.506/11: 30 dias + 3 por ano completo, máximo 90."""
    return min(30 + 3 * anos_completos, 90)


def _projecao_aviso(dados: DadosContrato) -> tuple[date, int]:
    """Se o aviso é indenizado, projeta a data de saída para efeito de 13º/férias.
    Retorna (data_projetada, dias_aviso)."""
    if dados.motivo in ("sem_justa_causa", "acordo_484a") and not dados.aviso_cumprido:
        anos = relativedelta(dados.demissao, dados.admissao).years
        dias = _dias_aviso_proporcional(anos)
        return dados.demissao + relativedelta(days=dias), dias
    return dados.demissao, 0


def calcular_rescisao(dados: DadosContrato) -> ResultadoRescisao:
    res = ResultadoRescisao()
    salario = dados.salario
    data_saida, dias_aviso = _projecao_aviso(dados)

    # 1) Saldo de salário — dias trabalhados no mês da demissão
    dias_trab = dados.demissao.day
    saldo = salario / Decimal(30) * dias_trab
    res.add("Saldo de salário", saldo, f"{dias_trab}/30 dias")

    # 2) Aviso prévio indenizado
    if dias_aviso > 0:
        valor_aviso = salario / Decimal(30) * dias_aviso
        res.add("Aviso prévio indenizado", valor_aviso, f"{dias_aviso} dias")
        if dados.motivo == "acordo_484a":
            # art. 484-A CLT: aviso pela metade se indenizado
            res.verbas[-1].valor = _q(valor_aviso / 2)
            res.verbas[-1].detalhe += " (50% - art. 484-A)"

    # 3) 13º salário proporcional (meses trabalhados no ano da saída, >=15 dias conta mês)
    ref = data_saida
    meses_13 = ref.month
    # ajuste: se admissão foi no ano corrente, contar a partir dela
    if dados.admissao.year == ref.year:
        meses_13 = ref.month - dados.admissao.month + 1
        if dados.admissao.day > 15:
            meses_13 -= 1
    meses_13 = max(0, min(12, meses_13))
    if dados.motivo != "justa_causa":
        valor_13 = salario / Decimal(12) * meses_13
        res.add("13º salário proporcional", valor_13, f"{meses_13}/12 avos")

    # 4) Férias vencidas (se houver) + 1/3
    if dados.ferias_vencidas and dados.motivo != "justa_causa":
        res.add("Férias vencidas", salario, "período aquisitivo integral")
        res.add("1/3 constitucional s/ férias vencidas", salario / 3)

    # 5) Férias proporcionais + 1/3
    # meses do período aquisitivo em curso (>=15 dias conta mês)
    aq_inicio = dados.admissao
    while aq_inicio + relativedelta(years=1) <= data_saida:
        aq_inicio += relativedelta(years=1)
    delta = relativedelta(data_saida, aq_inicio)
    meses_ferias = delta.years * 12 + delta.months
    if delta.days >= 15:
        meses_ferias += 1
    meses_ferias = max(0, min(12, meses_ferias))
    if dados.motivo != "justa_causa" and meses_ferias > 0:
        valor_fp = salario / Decimal(12) * meses_ferias
        res.add("Férias proporcionais", valor_fp, f"{meses_ferias}/12 avos")
        res.add("1/3 constitucional s/ férias proporcionais", valor_fp / 3)

    # 6) FGTS do mês + 13º + aviso (8% sobre bases tributáveis)
    base_fgts = saldo + (salario / Decimal(12) * meses_13 if dados.motivo != "justa_causa" else Decimal(0))
    if dias_aviso > 0:
        base_fgts += salario / Decimal(30) * dias_aviso
    fgts_mes = base_fgts * Decimal("0.08")
    res.fgts_rescisorio = _q(fgts_mes)

    # 7) Multa 40% (ou 20% no acordo 484-A) sobre saldo total do FGTS
    saldo_total_fgts = dados.saldo_fgts_depositado + fgts_mes
    if dados.motivo == "sem_justa_causa":
        res.multa_fgts = _q(saldo_total_fgts * Decimal("0.4"))
    elif dados.motivo == "acordo_484a":
        res.multa_fgts = _q(saldo_total_fgts * Decimal("0.2"))

    # 8) INSS sobre saldo + 13º (aviso indenizado NÃO integra base — Súmula 688/STF e TST)
    base_inss = saldo
    if meses_13 > 0 and dados.motivo != "justa_causa":
        base_inss_13 = salario / Decimal(12) * meses_13
        res.inss = calcular_inss(saldo) + calcular_inss(base_inss_13)
    else:
        res.inss = calcular_inss(saldo)

    # 9) IRRF sobre saldo (aviso indenizado e férias indenizadas isentos)
    res.irrf = calcular_irrf(saldo - calcular_inss(saldo), dados.dependentes)

    bruto = sum((v.valor for v in res.verbas), Decimal(0))
    res.liquido = _q(bruto - res.inss - res.irrf + res.multa_fgts + res.fgts_rescisorio)
    return res
