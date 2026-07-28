from decimal import Decimal
from datetime import date
from typing import Literal
from pydantic import BaseModel, Field


class RescisaoIn(BaseModel):
    admissao: date
    demissao: date
    salario: Decimal = Field(gt=0)
    motivo: Literal["sem_justa_causa", "pedido_demissao", "justa_causa", "acordo_484a"]
    aviso_cumprido: bool = False
    ferias_vencidas: bool = False
    dependentes: int = 0
    saldo_fgts_depositado: Decimal = Decimal("0")


class VerbaOut(BaseModel):
    nome: str
    valor: Decimal
    detalhe: str = ""


class RescisaoOut(BaseModel):
    verbas: list[VerbaOut]
    inss: Decimal
    irrf: Decimal
    fgts_rescisorio: Decimal
    multa_fgts: Decimal
    liquido: Decimal
