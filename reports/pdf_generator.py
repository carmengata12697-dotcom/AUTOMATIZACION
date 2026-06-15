"""Generación del reporte PDF con reportlab.

Toma los resultados YA calculados (scoring, fundamentales, últimos técnicos)
y arma el PDF. No calcula nada; solo maqueta.
"""
from __future__ import annotations

import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

import config


# ------------------------------------------------------------------ #
# Paleta                                                              #
# ------------------------------------------------------------------ #
VERDE = colors.HexColor("#26a69a")
AMARILLO = colors.HexColor("#ffa726")
ROJO = colors.HexColor("#ef5350")
GRIS_CLARO = colors.HexColor("#f5f5f5")
GRIS_BORDE = colors.HexColor("#dddddd")
AZUL_OSCURO = colors.HexColor("#1a237e")
NEGRO = colors.black


def _color_recomendacion(rec: str):
    return {"Comprar": VERDE, "Neutral": AMARILLO, "Evitar": ROJO}.get(rec, colors.grey)


def _emoji_estado(evaluado: bool, cumplido: bool) -> str:
    if not evaluado:
        return "Sin datos"
    return "Cumplido" if cumplido else "No cumplido"


_NOMBRES_INDICADORES = {
    "rsi": "RSI (30–70)",
    "macd": "MACD alcista",
    "precio_sobre_sma200": "Precio > SMA 200",
    "bollinger_banda_baja": "Precio en banda baja Bollinger",
    "pe_vs_sector": f"P/E < {config.PE_ATRACTIVO}",
    "roe_positivo_creciente": "ROE positivo",
    "deuda_capital": f"Deuda/Capital < {config.DEUDA_CAPITAL_MAX}",
    "flujo_caja_libre": "Flujo de Caja Libre positivo",
}


def _fmt(valor, tipo="num", decimales=2, sufijo=""):
    if valor is None:
        return "—"
    if tipo == "pct":
        return f"{valor * 100:.{decimales}f}%"
    if tipo == "millones":
        return f"{valor / 1_000_000:,.0f} M"
    return f"{valor:,.{decimales}f}{sufijo}"


# ------------------------------------------------------------------ #
# Función principal                                                   #
# ------------------------------------------------------------------ #
def generar_reporte(datos_analisis: dict) -> bytes:
    """Devuelve el PDF en bytes para que Streamlit lo ofrezca como descarga.

    datos_analisis debe contener:
      - ticker (str)
      - nombre (str | None)
      - sector (str | None)
      - moneda (str | None)
      - precio_actual (float | None)
      - resultado_scoring (dict): salida de scoring_engine.calcular_score
      - fundamental (dict): salida de fundamental_engine.procesar_fundamentales
    """
    ticker = datos_analisis.get("ticker", "—")
    nombre = datos_analisis.get("nombre") or ticker
    sector = datos_analisis.get("sector") or "—"
    moneda = datos_analisis.get("moneda") or ""
    precio_actual = datos_analisis.get("precio_actual")
    resultado = datos_analisis.get("resultado_scoring", {})
    fundamental = datos_analisis.get("fundamental", {})

    score = resultado.get("score")
    recomendacion = resultado.get("recomendacion", "—")
    desglose = resultado.get("desglose", [])
    descargo = resultado.get("descargo", config.DESCARGO_RESPONSABILIDAD)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    estilos = getSampleStyleSheet()
    estilo_titulo = ParagraphStyle(
        "Titulo", parent=estilos["Title"],
        fontSize=22, textColor=AZUL_OSCURO, spaceAfter=4,
    )
    estilo_subtitulo = ParagraphStyle(
        "Subtitulo", parent=estilos["Normal"],
        fontSize=12, textColor=colors.grey, spaceAfter=2,
    )
    estilo_seccion = ParagraphStyle(
        "Seccion", parent=estilos["Heading2"],
        fontSize=13, textColor=AZUL_OSCURO, spaceBefore=14, spaceAfter=6,
    )
    estilo_normal = estilos["Normal"]
    estilo_pie = ParagraphStyle(
        "Pie", parent=estilos["Normal"],
        fontSize=8, textColor=colors.grey, alignment=TA_CENTER, spaceBefore=12,
    )
    estilo_rec = ParagraphStyle(
        "Rec", parent=estilos["Normal"],
        fontSize=26, textColor=_color_recomendacion(recomendacion),
        alignment=TA_CENTER, spaceAfter=4,
    )

    historia = []

    # ---------------------------------------------------------------- #
    # PORTADA                                                           #
    # ---------------------------------------------------------------- #
    historia.append(Spacer(1, 0.5 * cm))
    historia.append(Paragraph(f"Reporte de Análisis Bursátil", estilo_titulo))
    historia.append(Paragraph(f"{nombre} ({ticker})", estilo_subtitulo))
    historia.append(Paragraph(f"Sector: {sector} | Fecha: {date.today().strftime('%d/%m/%Y')}", estilo_subtitulo))
    historia.append(HRFlowable(width="100%", thickness=2, color=AZUL_OSCURO, spaceAfter=16))

    # ---------------------------------------------------------------- #
    # RESUMEN EJECUTIVO                                                 #
    # ---------------------------------------------------------------- #
    historia.append(Paragraph("Resumen ejecutivo", estilo_seccion))

    score_str = f"{score} / 100" if score is not None else "Sin datos suficientes"
    precio_str = _fmt(precio_actual, decimales=2, sufijo=f" {moneda}") if precio_actual else "—"

    resumen_data = [
        ["Ticker", ticker],
        ["Nombre", nombre],
        ["Precio actual", precio_str],
        ["Score", score_str],
        ["Recomendación", recomendacion],
    ]
    tabla_resumen = Table(resumen_data, colWidths=[5 * cm, 11 * cm])
    tabla_resumen.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), GRIS_CLARO),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, GRIS_BORDE),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, GRIS_CLARO]),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("TEXTCOLOR", (1, 4), (1, 4), _color_recomendacion(recomendacion)),
        ("FONTNAME", (1, 4), (1, 4), "Helvetica-Bold"),
        ("FONTSIZE", (1, 4), (1, 4), 13),
    ]))
    historia.append(tabla_resumen)
    historia.append(Spacer(1, 0.4 * cm))

    # ---------------------------------------------------------------- #
    # ANÁLISIS FUNDAMENTAL                                              #
    # ---------------------------------------------------------------- #
    historia.append(Paragraph("Análisis Fundamental", estilo_seccion))
    fund_data = [
        ["Métrica", "Valor"],
        ["P/E Ratio (TTM)", _fmt(fundamental.get("pe"), decimales=2)],
        ["EPS (TTM)", _fmt(fundamental.get("eps"), decimales=2)],
        ["ROE", _fmt(fundamental.get("roe"), tipo="pct")],
        ["Margen Neto", _fmt(fundamental.get("margen_neto"), tipo="pct")],
        ["Deuda / Capital", _fmt(fundamental.get("deuda_capital"), decimales=2)],
        ["Flujo de Caja Libre", _fmt(fundamental.get("flujo_caja_libre"), tipo="millones",
                                     sufijo=f" {moneda}")],
    ]
    tabla_fund = Table(fund_data, colWidths=[8 * cm, 8 * cm])
    tabla_fund.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_OSCURO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, GRIS_BORDE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
    ]))
    historia.append(tabla_fund)

    # ---------------------------------------------------------------- #
    # DESGLOSE DEL SCORING                                             #
    # ---------------------------------------------------------------- #
    historia.append(Paragraph("Desglose del Scoring", estilo_seccion))

    if desglose:
        scoring_data = [["Indicador", "Categoría", "Peso", "Estado"]]
        for d in desglose:
            nombre_ind = _NOMBRES_INDICADORES.get(d["indicador"], d["indicador"])
            estado = _emoji_estado(d["evaluado"], d["cumplido"])
            scoring_data.append([
                nombre_ind,
                d["categoria"],
                f"{d['peso']}%",
                estado,
            ])

        col_widths = [7.5 * cm, 3.5 * cm, 2 * cm, 3 * cm]
        tabla_scoring = Table(scoring_data, colWidths=col_widths)

        # Colores condicionales por estado
        estilo_tabla = [
            ("BACKGROUND", (0, 0), (-1, 0), AZUL_OSCURO),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, GRIS_BORDE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
            ("PADDING", (0, 0), (-1, -1), 6),
            ("ALIGN", (2, 0), (2, -1), "CENTER"),
            ("ALIGN", (3, 0), (3, -1), "CENTER"),
        ]
        for i, d in enumerate(desglose, start=1):
            if not d["evaluado"]:
                estilo_tabla.append(("TEXTCOLOR", (3, i), (3, i), colors.grey))
            elif d["cumplido"]:
                estilo_tabla.append(("TEXTCOLOR", (3, i), (3, i), VERDE))
                estilo_tabla.append(("FONTNAME", (3, i), (3, i), "Helvetica-Bold"))
            else:
                estilo_tabla.append(("TEXTCOLOR", (3, i), (3, i), ROJO))

        tabla_scoring.setStyle(TableStyle(estilo_tabla))
        historia.append(tabla_scoring)

    peso_eval = resultado.get("peso_evaluado", 0)
    historia.append(Spacer(1, 0.3 * cm))
    historia.append(Paragraph(
        f"Peso evaluado: {peso_eval:.0f} / 100 puntos "
        f"({100 - peso_eval:.0f} puntos sin datos disponibles).",
        ParagraphStyle("pequeño", parent=estilo_normal, fontSize=9, textColor=colors.grey),
    ))

    # ---------------------------------------------------------------- #
    # DESCARGO DE RESPONSABILIDAD                                       #
    # ---------------------------------------------------------------- #
    historia.append(Spacer(1, 0.8 * cm))
    historia.append(HRFlowable(width="100%", thickness=1, color=GRIS_BORDE))
    historia.append(Paragraph(descargo, estilo_pie))

    doc.build(historia)
    buffer.seek(0)
    return buffer.read()

