"""Armazenamento simples de sentenças (em disco) e extração de texto."""
from pathlib import Path
from datetime import datetime
from io import BytesIO
import uuid, json

from pypdf import PdfReader
from docx import Document

BASE = Path(__file__).resolve().parent.parent / "storage" / "sentencas"
BASE.mkdir(parents=True, exist_ok=True)


def extrair_texto(nome: str, conteudo: bytes) -> str:
    n = nome.lower()
    if n.endswith(".pdf"):
        reader = PdfReader(BytesIO(conteudo))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    if n.endswith(".docx"):
        doc = Document(BytesIO(conteudo))
        return "\n".join(p.text for p in doc.paragraphs)
    return conteudo.decode("utf-8", errors="ignore")


def salvar(texto: str, nome_original: str | None = None, arquivo_bytes: bytes | None = None) -> dict:
    sid = uuid.uuid4().hex[:12]
    pasta = BASE / sid
    pasta.mkdir()
    (pasta / "texto.txt").write_text(texto, encoding="utf-8")
    if arquivo_bytes and nome_original:
        (pasta / nome_original).write_bytes(arquivo_bytes)
    meta = {
        "id": sid,
        "criado_em": datetime.now().isoformat(timespec="seconds"),
        "nome_original": nome_original,
        "tamanho_texto": len(texto),
    }
    (pasta / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    return meta


def listar() -> list[dict]:
    out = []
    for p in sorted(BASE.iterdir(), reverse=True):
        m = p / "meta.json"
        if m.exists():
            out.append(json.loads(m.read_text(encoding="utf-8")))
    return out


def ler(sid: str) -> dict | None:
    p = BASE / sid
    m = p / "meta.json"
    if not m.exists():
        return None
    data = json.loads(m.read_text(encoding="utf-8"))
    data["texto"] = (p / "texto.txt").read_text(encoding="utf-8")
    return data
