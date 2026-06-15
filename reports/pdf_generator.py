"""Generación del reporte PDF con reportlab y matplotlib."""
from __future__ import annotations

import io
from datetime import date

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image, PageBreak,
)
from reportlab.lib.enums import TA_CENTER

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


def _color_recomendacion(rec: str):
    return {"Comprar": VERDE, "Neutral": AMARILLO, "Evitar": ROJO}.get(rec, colors.grey)


def _emoji_estado(evaluado: bool, cumplido: bool) -> str:
    if not evaluado:
        return "Sin datos"
    return "Cumplido" if cumplido else "No cumplido"


_NOMBRES_INDICADORES = {
    "rsi": "RSI (30-70)",
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
        return "-"
    if tipo == "pct":
        return f"{valor * 100:.{decimales}f}%"
    if tipo == "millones":
        return f"{valor / 1_000_000:,.0f} M"
    return f"{valor:,.{decimales}f}{sufijo}"


# ------------------------------------------------------------------ #
# Gráfica técnica con matplotlib                                      #
# ------------------------------------------------------------------ #
def _grafica_tecnica_png(precios, ticker: str) -> bytes | None:
    try:
        from domain.technical_engine import (
            calcular_rsi, calcular_macd,
            calcular_bollinger, calcular_medias_moviles,
        )

        rsi = calcular_rsi(precios)
        macd_df = calcular_macd(precios)
        bollinger = calcular_bollinger(precios)
        medias = calcular_medias_moviles(precios)

        fig, (ax1, ax2, ax3) = plt.subplots(
            3, 1,
            figsize=(12, 9),
            gridspec_kw={"height_ratios": [3, 1.5, 1]},
            sharex=True,
        )
        fig.patch.set_facecolor("#1a1a2e")
        for ax in (ax1, ax2, ax3):
            ax.set_facecolor("#16213e")
            ax.tick_params(colors="white", labelsize=7)
            ax.yaxis.label.set_color("white")
            for spine in ax.spines.values():
                spine.set_edgecolor("#444")

        fechas = precios.index

        # Panel 1: Precio + Bollinger + Medias
        ax1.plot(fechas, precios["Close"], color="#e0e0e0",
                 linewidth=1, label="Precio")

        if not bollinger.empty:
            ax1.plot(fechas, bollinger["banda_alta"],
                     linewidth=0.8, linestyle="--",
                     label="Bollinger Alta", color="#6464ff")
            ax1.plot(fechas, bollinger["media"],
                     linewidth=0.8, linestyle=":",
                     label="Bollinger Media", color="#4444cc")
            ax1.plot(fechas, bollinger["banda_baja"],
                     linewidth=0.8, linestyle="--",
                     label="Bollinger Baja", color="#6464ff")
            ax1.fill_between(fechas,
                             bollinger["banda_baja"],
                             bollinger["banda_alta"],
                             alpha=0.05, color="#6464ff")

        colores_medias = {
            "sma20": "#ff9800", "sma50": "#2196f3",
            "sma200": "#9c27b0", "ema20": "#ff5722",
        }
        nombres_medias = {
            "sma20": "SMA 20", "sma50": "SMA 50",
            "sma200": "SMA 200", "ema20": "EMA 20",
        }
        if not medias.empty:
            for col, color in colores_medias.items():
                if col in medias.columns:
                    ax1.plot(fechas, medias[col], color=color,
                             linewidth=1, label=nombres_medias[col])

        ax1.set_ylabel("Precio", color="white", fontsize=8)
        ax1.legend(loc="upper left", fontsize=6, facecolor="#1a1a2e",
                   labelcolor="white", framealpha=0.7)
        ax1.set_title(f"{ticker} - Analisis Tecnico",
                      color="white", fontsize=10)

        # Panel 2: MACD
        if not macd_df.empty:
            ax2.plot(fechas, macd_df["macd"], color="#2196f3",
                     linewidth=1, label="MACD")
            ax2.plot(fechas, macd_df["senal"], color="#ff9800",
                     linewidth=1, label="Senal")
            hist = macd_df["histograma"].fillna(0)
            colores_hist = ["#26a69a" if v >= 0 else "#ef5350" for v in hist]
            ax2.bar(fechas, hist, color=colores_hist, alpha=0.6, width=1)
            ax2.axhline(0, color="#666", linewidth=0.5)
            ax2.set_ylabel("MACD", color="white", fontsize=8)
            ax2.legend(loc="upper left", fontsize=6, facecolor="#1a1a2e",
                       labelcolor="white", framealpha=0.7)

        # Panel 3: RSI
        if not rsi.empty:
            ax3.plot(fechas, rsi, color="#9c27b0", linewidth=1, label="RSI")
            ax3.axhline(70, color="#ef5350", linewidth=0.8, linestyle="--")
            ax3.axhline(30, color="#26a69a", linewidth=0.8, linestyle="--")
            ax3.fill_between(fechas, 70, rsi.clip(lower=70),
                             alpha=0.15, color="#ef5350")
            ax3.fill_between(fechas, rsi.clip(upper=30), 30,
                             alpha=0.15, color="#26a69a")
            ax3.set_ylim(0, 100)
            ax3.set_ylabel("RSI", color="white", fontsize=8)

        ax3.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))
        ax3.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
        plt.setp(ax3.xaxis.get_majorticklabels(),
                 rotation=30, ha="right", color="white", fontsize=7)

        plt.tight_layout(pad=1.5)
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150,
                    facecolor=fig.get_facecolor(), bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error generando grafica tecnica: {e}")
        return None


# ------------------------------------------------------------------ #
# Gráfica de scoring con matplotlib                                   #
# ------------------------------------------------------------------ #
def _grafica_scoring_png(desglose: list) -> bytes | None:
    try:
        tecnico_pts = sum(
            d["peso"] for d in desglose
            if d["evaluado"] and d["cumplido"] and d["categoria"] == "Tecnico"
        )
        tecnico_total = sum(
            d["peso"] for d in desglose
            if d["evaluado"] and d["categoria"] == "Tecnico"
        )
        fund_pts = sum(
            d["peso"] for d in desglose
            if d["evaluado"] and d["cumplido"] and d["categoria"] == "Fundamental"
        )
        fund_total = sum(
            d["peso"] for d in desglose
            if d["evaluado"] and d["categoria"] == "Fundamental"
        )

        fig, ax = plt.subplots(figsize=(7, 3))
        fig.patch.set_facecolor("#1a1a2e")
        ax.set_facecolor("#16213e")
        ax.tick_params(colors="white", labelsize=9)
        for spine in ax.spines.values():
            spine.set_edgecolor("#444")

        x = ["Tecnico", "Fundamental"]
        posibles = [tecnico_total, fund_total]
        obtenidos = [tecnico_pts, fund_pts]

        ax.bar(x, posibles, label="Posibles", width=0.4,
               color=["#2196f3", "#ff9800"], alpha=0.3)
        ax.bar(x, obtenidos, label="Obtenidos", width=0.4,
               color=["#2196f3", "#ff9800"], alpha=0.9)

        ax.set_title("Puntos por categoria", color="white", fontsize=10)
        ax.set_ylabel("Puntos", color="white", fontsize=9)
        ax.legend(facecolor="#1a1a2e", labelcolor="white", fontsize=8)

        for i, (pos, obt) in enumerate(zip(posibles, obtenidos)):
            ax.text(i, obt + 0.5, str(obt), ha="center",
                    color="white", fontsize=9, fontweight="bold")

        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=150,
                    facecolor=fig.get_facecolor(), bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error generando grafica scoring: {e}")
        return None


# ------------------------------------------------------------------ #
# Sección de un ticker dentro del PDF                                 #
# ------------------------------------------------------------------ #
def _seccion_ticker(datos: dict, estilos: dict) -> list:
    """Genera la lista de elementos reportlab para un ticker."""
    ticker = datos.get("ticker", "-")
    nombre = datos.get("nombre") or ticker
    sector = datos.get("sector") or "-"
    moneda = datos.get("moneda") or ""
    precio_actual = datos.get("precio_actual")
    resultado = datos.get("resultado_scoring", {})
    fundamental = datos.get("fundamental", {})
    precios = datos.get("precios")

    score = resultado.get("score")
    recomendacion = resultado.get("recomendacion", "-")
    desglose = resultado.get("desglose", [])

    elementos = []

    # Encabezado del ticker
    elementos.append(Paragraph(
        f"{nombre} ({ticker})",
        estilos["titulo_ticker"],
    ))
    elementos.append(Paragraph(
        f"Sector: {sector} | Fecha: {date.today().strftime('%d/%m/%Y')}",
        estilos["subtitulo"],
    ))
    elementos.append(HRFlowable(width="100%", thickness=1,
                                color=AZUL_OSCURO, spaceAfter=10))

    # Resumen ejecutivo
    elementos.append(Paragraph("Resumen ejecutivo", estilos["seccion"]))
    score_str = f"{score} / 100" if score is not None else "Sin datos"
    precio_str = (
        _fmt(precio_actual, decimales=2, sufijo=f" {moneda}")
        if precio_actual else "-"
    )
    resumen_data = [
        ["Ticker", ticker],
        ["Nombre", nombre],
        ["Precio actual", precio_str],
        ["Score", score_str],
        ["Recomendacion", recomendacion],
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
    elementos.append(tabla_resumen)
    elementos.append(Spacer(1, 0.4 * cm))

    # Gráfica técnica
    elementos.append(Paragraph("Analisis Tecnico", estilos["seccion"]))
    if precios is not None and not precios.empty:
        png_tecnico = _grafica_tecnica_png(precios, ticker)
        if png_tecnico:
            elementos.append(Image(io.BytesIO(png_tecnico),
                                   width=16 * cm, height=12 * cm))
            elementos.append(Spacer(1, 0.3 * cm))
        else:
            elementos.append(Paragraph(
                "No fue posible generar la grafica tecnica.",
                estilos["normal"]))
    else:
        elementos.append(Paragraph(
            "No hay datos de precios disponibles.", estilos["normal"]))

    # Análisis fundamental
    elementos.append(Paragraph("Analisis Fundamental", estilos["seccion"]))
    fund_data = [
        ["Metrica", "Valor"],
        ["P/E Ratio (TTM)", _fmt(fundamental.get("pe"), decimales=2)],
        ["EPS (TTM)", _fmt(fundamental.get("eps"), decimales=2)],
        ["ROE", _fmt(fundamental.get("roe"), tipo="pct")],
        ["Margen Neto", _fmt(fundamental.get("margen_neto"), tipo="pct")],
        ["Deuda / Capital", _fmt(fundamental.get("deuda_capital"), decimales=2)],
        ["Flujo de Caja Libre", _fmt(
            fundamental.get("flujo_caja_libre"), tipo="millones",
            sufijo=f" {moneda}",
        )],
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
    elementos.append(tabla_fund)

    # Desglose del scoring
    elementos.append(Paragraph("Desglose del Scoring", estilos["seccion"]))
    if desglose:
        scoring_data = [["Indicador", "Categoria", "Peso", "Estado"]]
        for d in desglose:
            nombre_ind = _NOMBRES_INDICADORES.get(d["indicador"], d["indicador"])
            estado = _emoji_estado(d["evaluado"], d["cumplido"])
            scoring_data.append([
                nombre_ind,
                d["categoria"],
                f"{d['peso']}%",
                estado,
            ])
        tabla_scoring = Table(scoring_data,
                              colWidths=[7.5 * cm, 3.5 * cm, 2 * cm, 3 * cm])
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
        elementos.append(tabla_scoring)

        # Gráfica de barras scoring
        png_scoring = _grafica_scoring_png(desglose)
        if png_scoring:
            elementos.append(Spacer(1, 0.4 * cm))
            elementos.append(Image(io.BytesIO(png_scoring),
                                   width=12 * cm, height=5 * cm))

    peso_eval = resultado.get("peso_evaluado", 0)
    elementos.append(Spacer(1, 0.3 * cm))
    elementos.append(Paragraph(
        f"Peso evaluado: {peso_eval:.0f} / 100 puntos "
        f"({100 - peso_eval:.0f} puntos sin datos disponibles).",
        ParagraphStyle("pequeno", parent=estilos["normal"],
                       fontSize=9, textColor=colors.grey),
    ))

    return elementos


# ------------------------------------------------------------------ #
# Función principal                                                   #
# ------------------------------------------------------------------ #
def generar_reporte(datos_lista: list) -> bytes:
    """Recibe una lista de dicts (uno por ticker) y genera el PDF completo."""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    estilos_base = getSampleStyleSheet()

    estilos = {
        "titulo_portada": ParagraphStyle(
            "TituloPortada", parent=estilos_base["Title"],
            fontSize=24, textColor=AZUL_OSCURO, spaceAfter=6,
        ),
        "titulo_ticker": ParagraphStyle(
            "TituloTicker", parent=estilos_base["Heading1"],
            fontSize=18, textColor=AZUL_OSCURO, spaceBefore=6, spaceAfter=4,
        ),
        "subtitulo": ParagraphStyle(
            "Subtitulo", parent=estilos_base["Normal"],
            fontSize=11, textColor=colors.grey, spaceAfter=2,
        ),
        "seccion": ParagraphStyle(
            "Seccion", parent=estilos_base["Heading2"],
            fontSize=13, textColor=AZUL_OSCURO, spaceBefore=14, spaceAfter=6,
        ),
        "normal": estilos_base["Normal"],
        "pie": ParagraphStyle(
            "Pie", parent=estilos_base["Normal"],
            fontSize=8, textColor=colors.grey,
            alignment=TA_CENTER, spaceBefore=12,
        ),
    }

    historia = []

    # ---------------------------------------------------------------- #
    # PORTADA GENERAL                                                   #
    # ---------------------------------------------------------------- #
    historia.append(Spacer(1, 1 * cm))
    historia.append(Paragraph("Reporte de Analisis Bursatil", estilos["titulo_portada"]))
    historia.append(Paragraph(
        f"Fecha: {date.today().strftime('%d/%m/%Y')}",
        estilos["subtitulo"],
    ))

    tickers_str = " | ".join(
        d.get("ticker", "-") for d in datos_lista
    )
    historia.append(Paragraph(f"Acciones analizadas: {tickers_str}", estilos["subtitulo"]))
    historia.append(HRFlowable(width="100%", thickness=2,
                                color=AZUL_OSCURO, spaceAfter=16))

    # Tabla resumen comparativa
    historia.append(Paragraph("Resumen comparativo", estilos["seccion"]))
    comp_data = [["Ticker", "Nombre", "Precio", "Score", "Recomendacion"]]
    for d in datos_lista:
        resultado = d.get("resultado_scoring", {})
        moneda = d.get("moneda") or ""
        comp_data.append([
            d.get("ticker", "-"),
            d.get("nombre") or d.get("ticker", "-"),
            _fmt(d.get("precio_actual"), decimales=2, sufijo=f" {moneda}"),
            f"{resultado.get('score', '-')} / 100" if resultado.get("score") else "-",
            resultado.get("recomendacion", "-"),
        ])

    tabla_comp = Table(comp_data, colWidths=[2.5 * cm, 5 * cm, 3 * cm, 2.5 * cm, 3 * cm])
    estilo_comp = [
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_OSCURO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, GRIS_BORDE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (3, 0), (3, -1), "CENTER"),
        ("ALIGN", (4, 0), (4, -1), "CENTER"),
    ]
    for i, d in enumerate(datos_lista, start=1):
        rec = d.get("resultado_scoring", {}).get("recomendacion", "-")
        estilo_comp.append(
            ("TEXTCOLOR", (4, i), (4, i), _color_recomendacion(rec))
        )
        estilo_comp.append(
            ("FONTNAME", (4, i), (4, i), "Helvetica-Bold")
        )
    tabla_comp.setStyle(TableStyle(estilo_comp))
    historia.append(tabla_comp)
    historia.append(Spacer(1, 0.5 * cm))

    # ---------------------------------------------------------------- #
    # SECCIÓN POR TICKER (una página nueva por cada uno)               #
    # ---------------------------------------------------------------- #
    for i, datos in enumerate(datos_lista):
        historia.append(PageBreak())
        historia.extend(_seccion_ticker(datos, estilos))

    # ---------------------------------------------------------------- #
    # DESCARGO DE RESPONSABILIDAD                                       #
    # ---------------------------------------------------------------- #
    historia.append(Spacer(1, 1 * cm))
    historia.append(HRFlowable(width="100%", thickness=1, color=GRIS_BORDE))
    historia.append(Paragraph(config.DESCARGO_RESPONSABILIDAD, estilos["pie"]))

    doc.build(historia)
    buffer.seek(0)
    return buffer.read()