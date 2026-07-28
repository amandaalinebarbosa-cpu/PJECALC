from dataclasses import asdict
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .schemas import RescisaoIn, RescisaoOut
from .calc.rescisao import DadosContrato, calcular_rescisao
from . import sentencas

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


@app.post("/sentencas/upload")
async def upload_sentenca(arquivo: UploadFile = File(...)):
    conteudo = await arquivo.read()
    if not conteudo:
        raise HTTPException(400, "Arquivo vazio")
    texto = sentencas.extrair_texto(arquivo.filename, conteudo)
    return sentencas.salvar(texto, arquivo.filename, conteudo)


@app.post("/sentencas/texto")
def upload_texto(texto: str = Form(...)):
    if not texto.strip():
        raise HTTPException(400, "Texto vazio")
    return sentencas.salvar(texto)


@app.get("/sentencas")
def listar_sentencas():
    return sentencas.listar()


@app.get("/sentencas/{sid}")
def ler_sentenca(sid: str):
    r = sentencas.ler(sid)
    if not r:
        raise HTTPException(404, "Não encontrada")
    return r
