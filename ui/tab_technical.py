"""Pestaña de Análisis Técnico.

Solo presenta; no calcula. Llama a los motores de dominio y a yahoo_client,
y renderiza los resultados con Plotly.
"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import config
from data_layer.yahoo_client import obtener_historico
from domain.technical_engine import (
    calcular_rsi,
    calcular_macd,
    calcular_bollinger,
    calcular_medias_moviles,
)


def _render_ticker(ticker: str, periodo: str) -> None:
    """Renderiza el análisis técnico completo para un ticker."""
    with st.spinner(f"Descargando datos de {ticker}…"):
        precios = obtener_historico(ticker, periodo)

    if precios.empty:
        st.error(f"No se encontraron datos para **{ticker}**. Comprueba el ticker.")
        return

    rsi = calcular_rsi(precios)
    macd_df = calcular_macd(precios)
    bollinger = calcular_bollinger(precios)
    medias = calcular_medias_moviles(precios)

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.55, 0.25, 0.20],
        vertical_spacing=0.04,
        subplot_titles=(
            f"{ticker} — Precio y Bollinger",
            "MACD",
            "RSI",
        ),
    )

    # Velas
    fig.add_trace(
        go.Candlestick(
            x=precios.index,
            open=precios["Open"],
            high=precios["High"],
            low=precios["Low"],
            close=precios["Close"],
            name="Precio",
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350",
        ),
        row=1, col=1,
    )

    # Bandas de Bollinger
    if not bollinger.empty:
        fig.add_trace(go.Scatter(
            x=bollinger.index, y=bollinger["banda_alta"],
            name="Bollinger Alta", line=dict(color="rgba(100,100,255,0.4)", width=1),
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=bollinger.index, y=bollinger["media"],
            name="Bollinger Media", line=dict(color="rgba(100,100,255,0.7)", width=1, dash="dot"),
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=bollinger.index, y=bollinger["banda_baja"],
            name="Bollinger Baja", line=dict(color="rgba(100,100,255,0.4)", width=1),
            fill="tonexty", fillcolor="rgba(100,100,255,0.05)",
        ), row=1, col=1)

    # Medias móviles
    colores_medias = {"sma20": "#ff9800", "sma50": "#2196f3", "sma200": "#9c27b0", "ema20": "#ff5722"}
    nombres_medias = {"sma20": "SMA 20", "sma50": "SMA 50", "sma200": "SMA 200", "ema20": "EMA 20"}
    if not medias.empty:
        for col, color in colores_medias.items():
            if col in medias.columns:
                fig.add_trace(go.Scatter(
                    x=medias.index, y=medias[col],
                    name=nombres_medias[col],
                    line=dict(color=color, width=1.5),
                ), row=1, col=1)

    # MACD
    if not macd_df.empty:
        fig.add_trace(go.Scatter(
            x=macd_df.index, y=macd_df["macd"],
            name="MACD", line=dict(color="#2196f3", width=1.5),
        ), row=2, col=1)
        fig.add_trace(go.Scatter(
            x=macd_df.index, y=macd_df["senal"],
            name="Señal", line=dict(color="#ff9800", width=1.5),
        ), row=2, col=1)
        colores_hist = ["#26a69a" if v >= 0 else "#ef5350" for v in macd_df["histograma"].fillna(0)]
        fig.add_trace(go.Bar(
            x=macd_df.index, y=macd_df["histograma"],
            name="Histograma", marker_color=colores_hist, opacity=0.6,
        ), row=2, col=1)

    # RSI
    if not rsi.empty:
        fig.add_trace(go.Scatter(
            x=rsi.index, y=rsi,
            name="RSI", line=dict(color="#9c27b0", width=1.5),
        ), row=3, col=1)
        fig.add_hrect(y0=70, y1=100, row=3, col=1,
                      fillcolor="rgba(239,83,80,0.1)", line_width=0)
        fig.add_hrect(y0=0, y1=30, row=3, col=1,
                      fillcolor="rgba(38,166,154,0.1)", line_width=0)
        fig.add_hline(y=70, row=3, col=1, line=dict(color="#ef5350", width=1, dash="dash"))
        fig.add_hline(y=30, row=3, col=1, line=dict(color="#26a69a", width=1, dash="dash"))

    fig.update_layout(
        height=750,
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=20, t=60, b=20),
        template="plotly_dark",
    )
    fig.update_yaxes(title_text="Precio", row=1, col=1)
    fig.update_yaxes(title_text="MACD", row=2, col=1)
    fig.update_yaxes(title_text="RSI", range=[0, 100], row=3, col=1)

    st.plotly_chart(fig, use_container_width=True)

    # Resumen de últimos valores
    st.markdown("#### Últimos valores")
    col1, col2, col3, col4 = st.columns(4)
    ultimo_close = precios["Close"].iloc[-1]
    col1.metric("Último cierre", f"{ultimo_close:.2f}")

    if not rsi.empty and not rsi.dropna().empty:
        v = rsi.dropna().iloc[-1]
        estado = "🔴 Sobrecomprado" if v > 70 else ("🟢 Sobrevendido" if v < 30 else "⚪ Neutro")
        col2.metric("RSI", f"{v:.1f}", estado)

    if not macd_df.empty and not macd_df["macd"].dropna().empty:
        m = macd_df["macd"].dropna().iloc[-1]
        s = macd_df["senal"].dropna().iloc[-1]
        col3.metric("MACD", f"{m:.4f}", f"Señal: {s:.4f}")

    if not medias.empty and "sma200" in medias.columns:
        sma200 = medias["sma200"].dropna()
        if not sma200.empty:
            v200 = sma200.iloc[-1]
            diff = (ultimo_close - v200) / v200 * 100
            col4.metric("SMA 200", f"{v200:.2f}", f"{diff:+.1f}%")


def render(tickers: list) -> None:
    st.subheader("📈 Análisis Técnico")

    if not tickers:
        st.warning("Introduce al menos un ticker en el panel lateral.")
        return

    # Selector de ventana temporal (compartido para todos)
    ventana_label = st.selectbox(
        "Ventana temporal",
        list(config.VENTANAS_TEMPORALES.keys()),
        index=2,
        key="ventana_tecnico",
    )
    periodo = config.VENTANAS_TEMPORALES[ventana_label]

    # Si hay más de un ticker, mostrar pestañas internas
    if len(tickers) == 1:
        _render_ticker(tickers[0], periodo)
    else:
        tabs = st.tabs([f"📊 {t}" for t in tickers])
        for tab, ticker in zip(tabs, tickers):
            with tab:
                _render_ticker(ticker, periodo)