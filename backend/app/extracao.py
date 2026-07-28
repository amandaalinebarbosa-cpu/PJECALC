"""Extração heurística de dados de sentenças trabalhistas (texto puro).

Retorna uma estrutura que o usuário revisa antes do cálculo.
"""
from __future__ import annotations
import re
from datetime import date
from decimal import Decimal


MESES = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "março": 3, "abril": 4,
    "maio": 5, "junho": 6, "julho": 7, "agosto": 8, "setembro": 9,
    "outubro": 10, "novembro": 11, "dezembro": 12,
}

VERBAS_PADRAO = [
    ("aviso_previo", r"aviso\s+pr[eé]vio(\s+indenizado|\s+proporcional)?"),
    ("decimo_terceiro", r"(13[ºo°]|d[eé]cimo\s+terceiro)\s+sal[aá]rio"),
    ("ferias_vencidas", r"f[eé]rias\s+vencidas"),
    ("ferias_proporcionais", r"f[eé]rias\s+proporcionais"),
    ("terco_ferias", r"1/3\s+(constitucional|de\s+f[eé]rias)"),
    ("saldo_salario", r"saldo\s+de\s+sal[aá]rio"),
    ("fgts", r"FGTS(\s+rescis[oó]rio)?"),
    ("multa_40", r"multa\s+de\s+40\s*%"),
    ("multa_477", r"multa\s+do\s+art\.?\s*477"),
    ("multa_467", r"multa\s+do\s+art\.?\s*467"),
    ("horas_extras", r"horas?\s+extras?"),
    ("adicional_noturno", r"adicional\s+noturno"),
    ("insalubridade", r"(adicional\s+de\s+)?insalubridade"),
    ("periculosidade", r"(adicional\s+de\s+)?periculosidade"),
    ("honorarios", r"honor[aá]rios\s+(advocat[ií]cios|sucumbenciais)"),
]


def _parse_data(s: str) -> str | None:
    s = s.strip().lower()
    m = re.match(r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})", s)
    if m:
        d, mo, y = (int(x) for x in m.groups())
        if y < 100:
            y += 2000 if y < 50 else 1900
        try:
            return date(y, mo, d).isoformat()
        except ValueError:
            return None
    m = re.match(r"(\d{1,2})\s+de\s+([a-zç]+)\s+de\s+(\d{4})", s)
    if m:
        d, mes, y = m.group(1), m.group(2), m.group(3)
        mo = MESES.get(mes)
        if mo:
            try:
                return date(int(y), mo, int(d)).isoformat()
            except ValueError:
                return None
    return None


def _parse_valor(s: str) -> str | None:
    """Converte '1.234,56' ou '1234.56' para string decimal."""
    s = s.strip().replace("R$", "").replace(" ", "")
    if not s:
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return str(Decimal(s))
    except Exception:
        return None


def extrair(texto: str) -> dict:
    t = texto.replace("\xa0", " ")
    tl = t.lower()

    dados: dict = {"campos": {}, "verbas_deferidas": [], "avisos": []}

    for pat in [
        r"admiss[aã]o[:\s]+([0-9/.\-]+|\d{1,2}\s+de\s+[a-zç]+\s+de\s+\d{4})",
        r"admitid[oa]\s+em[:\s]+([0-9/.\-]+|\d{1,2}\s+de\s+[a-zç]+\s+de\s+\d{4})",
        r"contratad[oa]\s+em[:\s]+([0-9/.\-]+|\d{1,2}\s+de\s+[a-zç]+\s+de\s+\d{4})",
    ]:
        m = re.search(pat, tl)
        if m:
            d = _parse_data(m.group(1))
            if d:
                dados["campos"]["admissao"] = d
                break

    for pat in [
        r"demiss[aã]o[:\s]+([0-9/.\-]+|\d{1,2}\s+de\s+[a-zç]+\s+de\s+\d{4})",
        r"dispensa(?:do)?\s+em[:\s]+([0-9/.\-]+|\d{1,2}\s+de\s+[a-zç]+\s+de\s+\d{4})",
        r"rescis[aã]o(?:\s+contratual)?\s+em[:\s]+([0-9/.\-]+|\d{1,2}\s+de\s+[a-zç]+\s+de\s+\d{4})",
    ]:
        m = re.search(pat, tl)
        if m:
            d = _parse_data(m.group(1))
            if d:
                dados["campos"]["demissao"] = d
                break

    m = re.search(r"sal[aá]rio(?:\s+base|\s+mensal)?[:\s]+r?\$?\s*([\d\.,]+)", tl)
    if m:
        v = _parse_valor(m.group(1))
        if v:
            dados["campos"]["salario"] = v

    if re.search(r"justa\s+causa", tl) and not re.search(r"sem\s+justa\s+causa", tl):
        dados["campos"]["motivo"] = "justa_causa"
    elif re.search(r"pedido\s+de\s+demiss[aã]o", tl):
        dados["campos"]["motivo"] = "pedido_demissao"
    elif re.search(r"484[\-\s]?a|acordo", tl):
        dados["campos"]["motivo"] = "acordo_484a"
    else:
        dados["campos"]["motivo"] = "sem_justa_causa"

    for chave, pat in VERBAS_PADRAO:
        if re.search(pat, tl):
            dados["verbas_deferidas"].append(chave)

    for req in ("admissao", "demissao", "salario"):
        if req not in dados["campos"]:
            dados["avisos"].append(f"Campo '{req}' não localizado — preencha manualmente.")

    return dados
