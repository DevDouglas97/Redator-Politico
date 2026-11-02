"""Funções de apresentação e exportação dos relatórios em PDF."""

import re
from typing import Any
from xml.sax.saxutils import escape

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _tabela_frequencias(titulo: str, frequencias: pd.Series, limite: int) -> list[Any]:
    """Monta uma seção tabular para uma série de contagens."""
    estilos = getSampleStyleSheet()
    linhas = [[Paragraph("<b>Nome</b>", estilos["BodyText"]), Paragraph("<b>Registros</b>", estilos["BodyText"])]]
    linhas.extend(
        [
            [Paragraph(escape(str(nome)), estilos["BodyText"]), str(int(qtd))]
            for nome, qtd in frequencias.head(limite).items()
        ]
    )
    tabela = Table(linhas, colWidths=[5.8 * inch, 1.0 * inch], repeatRows=1, hAlign="LEFT")
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#24476B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EEF3F8")]),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#C9D2DC")),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return [Paragraph(escape(titulo), estilos["Heading2"]), Spacer(1, 4), tabela, Spacer(1, 14)]


def salvar_pdf_analise(df: pd.DataFrame, caminho_pdf: str) -> None:
    """Gera o relatório estatístico em PDF com título e tabelas legíveis."""
    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle(
        "TituloRelatorio",
        parent=estilos["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#24476B"),
    )
    documento = SimpleDocTemplate(
        caminho_pdf,
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )
    conteudo: list[Any] = [
        Paragraph("Análise de Proposições Parlamentares — RS", titulo),
        Spacer(1, 8),
        Paragraph(f"Total de proposições: <b>{len(df)}</b>", estilos["BodyText"]),
        Spacer(1, 16),
    ]
    conteudo += _tabela_frequencias("Deputados com mais registros", df["Deputado(a)"].value_counts(), 5)
    conteudo += _tabela_frequencias("Partidos com maior volume", df["Partido"].value_counts(), 8)
    conteudo += _tabela_frequencias("Status mais frequentes", df["Último Status"].fillna("N/A").value_counts(), 5)
    documento.build(conteudo)


def _converter_negrito(texto: str) -> str:
    """Escapa o texto e converte negritos Markdown para a marcação do ReportLab."""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escape(texto))


def salvar_pdf_boletim(texto_markdown: str, caminho_pdf: str) -> None:
    """Gera o PDF mantendo títulos, negritos e recuo dos detalhes do boletim."""
    estilos = getSampleStyleSheet()
    estilos.add(
        ParagraphStyle(
            "TituloBoletim", parent=estilos["Title"], textColor=colors.HexColor("#24476B"), spaceAfter=12
        )
    )
    estilos.add(ParagraphStyle("ItemBoletim", parent=estilos["BodyText"], leftIndent=12, spaceBefore=5, spaceAfter=4))
    estilos.add(ParagraphStyle("DetalheBoletim", parent=estilos["BodyText"], leftIndent=30, spaceAfter=4))
    documento = SimpleDocTemplate(
        caminho_pdf,
        pagesize=letter,
        rightMargin=0.7 * inch,
        leftMargin=0.7 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
    )
    conteudo: list[Any] = []
    for linha in texto_markdown.splitlines():
        limpa = linha.strip()
        if not limpa:
            conteudo.append(Spacer(1, 5))
        elif limpa.startswith("# "):
            conteudo.append(Paragraph(escape(limpa[2:]), estilos["TituloBoletim"]))
        elif linha.startswith("  * "):
            conteudo.append(Paragraph("• " + _converter_negrito(limpa[2:]), estilos["DetalheBoletim"]))
        elif limpa.startswith("* "):
            conteudo.append(Paragraph(_converter_negrito(limpa[2:]), estilos["ItemBoletim"]))
        else:
            conteudo.append(Paragraph(_converter_negrito(limpa), estilos["BodyText"]))
    documento.build(conteudo)
