"""Pestaña de Cartera. Comparación y ranking de los tickers seleccionados."""
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

import config
from data_layer.yahoo_client import obtener_historico, obtener_fundamentales
from domain.technical_engine import (
    calcular_rsi, calcular_macd,
    calcular_bollinger, calcular_medias_moviles,
)
from domain.fundamental_engine import procesar_fundamentales
from domain.scoring_engine import calcular_score


def _ultimos_tecnicos(precios) -> dict:
    if precios.empty:
        return {}

    rsi = calcular_rsi(precios)
    macd_df = calcular_macd(precios)
    bollinger = calcular_bollinger(precios)
    medias = calcular_medias_moviles(precios)

    def ultimo(serie):
        s = serie.dropna()
        return s.iloc[-1] if not s.empty else None

    return {
        "rsi": ultimo(rsi),
        "macd": ultimo(macd_df["macd"]) if not macd_df.empty else None,
        "senal": ultimo(macd_df["senal"]) if not macd_df.empty else None,
        "precio": precios["Close"].dropna().iloc[-1] if not precios.empty else None,
        "sma200": ultimo(medias["sma200"]) if not medias.empty and "sma200" in medias.columns else None,
        "banda_baja": ultimo(bollinger["banda_baja"]) if not bollinger.empty else None,
    }


def _fmt(valor, tipo="num", decimales=2, sufijo=""):
    if valor is None:
        return "—"
    if tipo == "pct":
        return f"{valor * 100:.{decimales}f}%"
    if tipo == "millones":
        return f"{valor / 1_000_000:,.0f} M"
    return f"{valor:,.{decimales}f}{sufijo}"


def render(tickers: list) -> None:
    st.subheader("💼 Comparador de Acciones")

    if not tickers:
        st.warning("Introduce al menos un ticker en el panel lateral.")
        return

    if len(tickers) < 2:
        st.info("Agrega al menos 2 tickers en el panel lateral para comparar.")
        return

    # ---------------------------------------------------------------- #
    # Recolectar datos de todos los tickers                             #
    # ---------------------------------------------------------------- #
    datos = []
    with st.spinner("Calculando scores para todos los tickers…"):
        for ticker in tickers:
            precios = obtener_historico(ticker, "1y")
            crudos = obtener_fundamentales(ticker)
            fundamental = procesar_fundamentales(crudos)
            tecnico = _ultimos_tecnicos(precios)
            resultado = calcular_score(tecnico, fundamental)

            datos.append({
                "ticker": ticker,
                "nombre": fundamental.get("nombre") or ticker,
                "sector": fundamental.get("sector") or "—",
                "moneda": fundamental.get("moneda") or "",
                "precio": tecnico.get("precio"),
                "score": resultado.get("score"),
                "recomendacion": resultado.get("recomendacion", "—"),
                "peso_evaluado": resultado.get("peso_evaluado", 0),
                "desglose": resultado.get("desglose", []),
                "fundamental": fundamental,
                "tecnico": tecnico,
            })

    # Ordenar por score descendente
    datos_ordenados = sorted(
        datos,
        key=lambda x: x["score"] if x["score"] is not None else -1,
        reverse=True,
    )

    # ---------------------------------------------------------------- #
    # Ranking                                                           #
    # ---------------------------------------------------------------- #
    st.markdown("### 🏆 Ranking por score")

    color_map = {
        "Comprar": "#26a69a",
        "Neutral": "#ffa726",
        "Evitar": "#ef5350",
        "Datos insuficientes": "#9e9e9e",
    }
    emoji_map = {
        "Comprar": "🟢",
        "Neutral": "🟡",
        "Evitar": "🔴",
        "Datos insuficientes": "⚫",
    }
    medallas = ["🥇", "🥈", "🥉"]

    cols = st.columns(len(datos_ordenados))
    for i, (col, d) in enumerate(zip(cols, datos_ordenados)):
        color = color_map.get(d["recomendacion"], "#9e9e9e")
        emoji = emoji_map.get(d["recomendacion"], "⚫")
        medalla = medallas[i] if i < len(medallas) else ""
        with col:
            st.markdown(
                f"""
                <div style="background:{color}22; border-left:5px solid {color};
                            padding:1rem; border-radius:8px; text-align:center;">
                    <div style="font-size:2rem;">{medalla}</div>
                    <div style="font-size:1.4rem; font-weight:700;
                                color:{color};">{d['ticker']}</div>
                    <div style="font-size:0.85rem; color:#aaa;
                                margin-bottom:0.4rem;">{d['nombre']}</div>
                    <div style="font-size:1.8rem; font-weight:700;">
                        {d['score'] if d['score'] is not None else '—'}
                    </div>
                    <div style="font-size:0.8rem; color:#aaa;">/ 100</div>
                    <div style="margin-top:0.4rem;">{emoji} {d['recomendacion']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    # ---------------------------------------------------------------- #
    # Gráfica comparativa de scores                                     #
    # ---------------------------------------------------------------- #
    st.markdown("### 📊 Comparativa de scores por categoría")

    tickers_labels = [d["ticker"] for d in datos_ordenados]

    tecnico_pts = []
    fund_pts = []
    tecnico_total = []
    fund_total = []

    for d in datos_ordenados:
        desglose = d["desglose"]
        tecnico_pts.append(sum(
            x["peso"] for x in desglose
            if x["evaluado"] and x["cumplido"] and x["categoria"] == "Tecnico"
        ))
        fund_pts.append(sum(
            x["peso"] for x in desglose
            if x["evaluado"] and x["cumplido"] and x["categoria"] == "Fundamental"
        ))
        tecnico_total.append(sum(
            x["peso"] for x in desglose
            if x["evaluado"] and x["categoria"] == "Tecnico"
        ))
        fund_total.append(sum(
            x["peso"] for x in desglose
            if x["evaluado"] and x["categoria"] == "Fundamental"
        ))

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        name="Técnico obtenido",
        x=tickers_labels,
        y=tecnico_pts,
        marker_color="#2196f3",
    ))
    fig_bar.add_trace(go.Bar(
        name="Fundamental obtenido",
        x=tickers_labels,
        y=fund_pts,
        marker_color="#ff9800",
    ))
    fig_bar.add_trace(go.Bar(
        name="Técnico posible",
        x=tickers_labels,
        y=tecnico_total,
        marker_color="rgba(33,150,243,0.25)",
    ))
    fig_bar.add_trace(go.Bar(
        name="Fundamental posible",
        x=tickers_labels,
        y=fund_total,
        marker_color="rgba(255,152,0,0.25)",
    ))
    fig_bar.update_layout(
        barmode="group",
        height=350,
        template="plotly_dark",
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1),
    )
    st.plotly_chart(fig_bar, use_container_width=True, key="comparativa_scores")

    st.divider()

    # ---------------------------------------------------------------- #
    # Tabla comparativa de indicadores técnicos                        #
    # ---------------------------------------------------------------- #
    st.markdown("### 📈 Comparativa de indicadores técnicos")

    filas_tecnico = []
    for d in datos_ordenados:
        t = d["tecnico"]
        moneda = d["moneda"]
        filas_tecnico.append({
            "Ticker": d["ticker"],
            "Precio": _fmt(t.get("precio"), decimales=2, sufijo=f" {moneda}"),
            "RSI": _fmt(t.get("rsi"), decimales=1),
            "MACD": _fmt(t.get("macd"), decimales=4),
            "SMA 200": _fmt(t.get("sma200"), decimales=2),
            "Banda Baja Bollinger": _fmt(t.get("banda_baja"), decimales=2),
        })
    df_tecnico = pd.DataFrame(filas_tecnico).set_index("Ticker")
    st.dataframe(df_tecnico, use_container_width=True)

    st.divider()

    # ---------------------------------------------------------------- #
    # Tabla comparativa de indicadores fundamentales                   #
    # ---------------------------------------------------------------- #
    st.markdown("### 💰 Comparativa de indicadores fundamentales")

    filas_fund = []
    for d in datos_ordenados:
        f = d["fundamental"]
        moneda = d["moneda"]
        filas_fund.append({
            "Ticker": d["ticker"],
            "Sector": d["sector"],
            "P/E": _fmt(f.get("pe"), decimales=2),
            "EPS": _fmt(f.get("eps"), decimales=2),
            "ROE": _fmt(f.get("roe"), tipo="pct"),
            "Margen Neto": _fmt(f.get("margen_neto"), tipo="pct"),
            "Deuda/Capital": _fmt(f.get("deuda_capital"), decimales=2),
            "FCL": _fmt(f.get("flujo_caja_libre"), tipo="millones",
                        sufijo=f" {moneda}"),
        })
    df_fund = pd.DataFrame(filas_fund).set_index("Ticker")
    st.dataframe(df_fund, use_container_width=True)

    st.divider()

    # ---------------------------------------------------------------- #
    # Desglose detallado por indicador                                 #
    # ---------------------------------------------------------------- #
    st.markdown("### 🔍 Desglose detallado por indicador")

    _NOMBRES = {
        "rsi": "RSI (30-70)",
        "macd": "MACD alcista",
        "precio_sobre_sma200": "Precio > SMA 200",
        "bollinger_banda_baja": "Precio en banda baja Bollinger",
        "pe_vs_sector": f"P/E < {config.PE_ATRACTIVO}",
        "roe_positivo_creciente": "ROE positivo",
        "deuda_capital": f"Deuda/Capital < {config.DEUDA_CAPITAL_MAX}",
        "flujo_caja_libre": "Flujo de Caja Libre positivo",
    }

    filas_desglose = []
    for indicador in _NOMBRES.keys():
        fila = {"Indicador": _NOMBRES[indicador]}
        for d in datos_ordenados:
            item = next(
                (x for x in d["desglose"] if x["indicador"] == indicador),
                None,
            )
            if item is None:
                fila[d["ticker"]] = "—"
            elif not item["evaluado"]:
                fila[d["ticker"]] = "⚫ Sin datos"
            elif item["cumplido"]:
                fila[d["ticker"]] = "✅ Cumplido"
            else:
                fila[d["ticker"]] = "❌ No cumplido"
        filas_desglose.append(fila)

    df_desglose = pd.DataFrame(filas_desglose).set_index("Indicador")
    st.dataframe(df_desglose, use_container_width=True)

    st.info(f"⚠️ {config.DESCARGO_RESPONSABILIDAD}")