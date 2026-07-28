"""Tabelas fiscais oficiais. Valores por competência (AAAA-MM)."""
from decimal import Decimal
from datetime import date

# Salário mínimo nacional por vigência (início)
SALARIO_MINIMO = [
    (date(2024, 1, 1), Decimal("1412.00")),
    (date(2025, 1, 1), Decimal("1518.00")),
]

# INSS empregado — faixas progressivas (a partir de 01/2025)
# (limite_superior, aliquota)
INSS_FAIXAS_2025 = [
    (Decimal("1518.00"), Decimal("0.075")),
    (Decimal("2793.88"), Decimal("0.09")),
    (Decimal("4190.83"), Decimal("0.12")),
    (Decimal("8157.41"), Decimal("0.14")),
]
INSS_TETO_2025 = Decimal("8157.41")

# IRRF mensal — vigência a partir de 05/2025 (faixa isenta ampliada p/ 2 SM via desconto simplificado)
# (limite_superior, aliquota, deducao)
IRRF_FAIXAS_2025 = [
    (Decimal("2428.80"), Decimal("0.00"), Decimal("0.00")),
    (Decimal("2826.65"), Decimal("0.075"), Decimal("182.16")),
    (Decimal("3751.05"), Decimal("0.15"), Decimal("394.16")),
    (Decimal("4664.68"), Decimal("0.225"), Decimal("675.49")),
    (Decimal("999999999"), Decimal("0.275"), Decimal("908.73")),
]
IRRF_DEDUCAO_DEPENDENTE = Decimal("189.59")


def salario_minimo(competencia: date) -> Decimal:
    vigente = SALARIO_MINIMO[0][1]
    for inicio, valor in SALARIO_MINIMO:
        if competencia >= inicio:
            vigente = valor
    return vigente


def calcular_inss(base: Decimal) -> Decimal:
    """INSS progressivo do empregado."""
    if base <= 0:
        return Decimal("0")
    base = min(base, INSS_TETO_2025)
    total = Decimal("0")
    anterior = Decimal("0")
    for limite, aliquota in INSS_FAIXAS_2025:
        if base > limite:
            total += (limite - anterior) * aliquota
            anterior = limite
        else:
            total += (base - anterior) * aliquota
            break
    return total.quantize(Decimal("0.01"))


def calcular_irrf(base: Decimal, dependentes: int = 0) -> Decimal:
    """IRRF sobre base já líquida de INSS e dependentes."""
    base_calc = base - (IRRF_DEDUCAO_DEPENDENTE * dependentes)
    if base_calc <= 0:
        return Decimal("0")
    for limite, aliquota, deducao in IRRF_FAIXAS_2025:
        if base_calc <= limite:
            imposto = base_calc * aliquota - deducao
            return max(imposto, Decimal("0")).quantize(Decimal("0.01"))
    return Decimal("0")
