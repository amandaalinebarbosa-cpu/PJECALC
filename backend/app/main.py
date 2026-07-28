from dataclasses import asdict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .schemas import RescisaoIn, RescisaoOut
from .calc.rescisao import DadosContrato, calcular_rescisao

app = FastAPI(title="PJeCalc Web", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/calc/rescisao", response_model=RescisaoOut)
def calc_rescisao(inp: RescisaoIn):
    dados = DadosContrato(**inp.model_dump())
    res = calcular_rescisao(dados)
    return RescisaoOut(
        verbas=[{"nome": v.nome, "valor": v.valor, "detalhe": v.detalhe} for v in res.verbas],
        inss=res.inss,
        irrf=res.irrf,
        fgts_rescisorio=res.fgts_rescisorio,
        multa_fgts=res.multa_fgts,
        liquido=res.liquido,
    )
