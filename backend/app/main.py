from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from .schemas import RescisaoIn, RescisaoOut
from .calc.rescisao import DadosContrato, calcular_rescisao
from . import sentencas, extracao, exportar

app = FastAPI(title="PJeCalc Web", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


def _executar(inp: RescisaoIn) -> RescisaoOut:
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


@app.post("/calc/rescisao", response_model=RescisaoOut)
def calc_rescisao(inp: RescisaoIn):
    return _executar(inp)


@app.post("/calc/rescisao/pdf")
def calc_rescisao_pdf(inp: RescisaoIn):
    out = _executar(inp)
    pdf = exportar.pdf_memoria(inp.model_dump(mode="json"), out.model_dump(mode="json"))
    return Response(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="memoria-calculo.pdf"'},
    )


@app.post("/calc/rescisao/estruturado")
def calc_rescisao_json(inp: RescisaoIn):
    out = _executar(inp)
    blob = exportar.json_estruturado(inp.model_dump(mode="json"), out.model_dump(mode="json"))
    return Response(
        blob,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="calculo.pjcweb"'},
    )


@app.post("/sentencas/upload")
async def upload_sentenca(arquivo: UploadFile = File(...)):
    conteudo = await arquivo.read()
    if not conteudo:
        raise HTTPException(400, "Arquivo vazio")
    texto = sentencas.extrair_texto(arquivo.filename, conteudo)
    meta = sentencas.salvar(texto, arquivo.filename, conteudo)
    meta["extracao"] = extracao.extrair(texto)
    return meta


@app.post("/sentencas/texto")
def upload_texto(texto: str = Form(...)):
    if not texto.strip():
        raise HTTPException(400, "Texto vazio")
    meta = sentencas.salvar(texto)
    meta["extracao"] = extracao.extrair(texto)
    return meta


@app.get("/sentencas")
def listar_sentencas():
    return sentencas.listar()


@app.get("/sentencas/{sid}")
def ler_sentenca(sid: str):
    r = sentencas.ler(sid)
    if not r:
        raise HTTPException(404, "Não encontrada")
    r["extracao"] = extracao.extrair(r["texto"])
    return r
