"""Exportação da memória de cálculo em PDF e em JSON estruturado (.pjcweb)."""
from __future__ import annotations
from io import BytesIO
from datetime import datetime
from decimal import Decimal
import json

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)


def _brl(v) -> str:
    d = Decimal(str(v)).quantize(Decimal("0.01"))
    s = f"{d:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def pdf_memoria(entrada: dict, resultado: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        title="Memória de Cálculo — PJeCalc Web",
    )
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>Memória de Cálculo — Verbas Rescisórias</b>", styles["Title"]))
    story.append(Paragraph(
        f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        styles["Normal"],
    ))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("<b>Dados do contrato</b>", styles["Heading2"]))
    rot = {
        "admissao": "Admissão", "demissao": "Demissão", "salario": "Salário",
        "motivo": "Motivo", "aviso_cumprido": "Aviso cumprido",
        "ferias_vencidas": "Férias vencidas", "dependentes": "Dependentes",
        "saldo_fgts_depositado": "Saldo FGTS depositado",
    }
    linhas = [[rot.get(k, k), str(v)] for k, v in entrada.items()]
    t = Table(linhas, colWidths=[6 * cm, 9 * cm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f2f2f2")),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("<b>Verbas apuradas</b>", styles["Heading2"]))
    linhas = [["Verba", "Detalhe", "Valor (R$)"]]
    for v in resultado["verbas"]:
        linhas.append([v["nome"], v.get("detalhe", ""), _brl(v["valor"])])
    linhas.append(["FGTS rescisório (8%)", "", _brl(resultado["fgts_rescisorio"])])
    linhas.append(["Multa FGTS", "", _brl(resultado["multa_fgts"])])
    linhas.append(["(-) INSS", "", "-" + _brl(resultado["inss"])])
    linhas.append(["(-) IRRF", "", "-" + _brl(resultado["irrf"])])
    linhas.append(["LÍQUIDO", "", _brl(resultado["liquido"])])

    t = Table(linhas, colWidths=[6 * cm, 6 * cm, 4 * cm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0e6f0")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#d5e8d4")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (2, 1), (2, -1), "RIGHT"),
    ]))
    story.append(t)

    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph(
        "<i>Documento gerado por PJeCalc Web. Confira os parâmetros antes de "
        "protocolar. Índices de atualização monetária e juros não incluídos "
        "nesta versão.</i>",
        styles["Italic"],
    ))

    doc.build(story)
    return buf.getvalue()


def json_estruturado(entrada: dict, resultado: dict) -> bytes:
    """Formato .pjcweb — abre em qualquer editor; contém tudo para
    reimportar no PJeCalc Web ou para reproduzir manualmente no PJe-Calc oficial."""
    doc = {
        "formato": "pjcweb/1",
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "entrada": entrada,
        "resultado": resultado,
    }
    return json.dumps(doc, ensure_ascii=False, indent=2, default=str).encode("utf-8")
