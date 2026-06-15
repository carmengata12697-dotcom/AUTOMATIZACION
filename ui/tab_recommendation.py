"""Pestaña de Recomendación. Semáforo + score + desglose por indicador."""
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

import config
from data_layer.yahoo_client import obtener_historico, obtener_fundamentales
from domain.technical_engine import calcular_rsi, calcular_macd, calcular_bollinger, calcular_medias_moviles
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

    precio_actual = precios["Close"].dropna().iloc[-1] if not precios.empty else None

    return {
        "rsi": ultimo(rsi),
        "macd": ultimo(macd_df["macd"]) if not macd_df.empty else None,
        "senal": ultimo(macd_df["senal"]) if not macd_df.empty else None,
        "precio": precio_actual,
        "sma200": ultimo(medias["sma200"]) if not medias.empty and "sma200" in medias.columns else None,
        "banda_baja": ultimo(bollinger["banda_baja"]) if not bollinger.empty else None,
    }


_EMOJIS = {"rsi": "📉", "macd": "📊", "precio_sobre_sma200": "📈",
           "bollinger_banda_baja": "〰️", "pe_vs_sector": "💰",
           "roe_positivo_creciente": "📋", "deuda_capital": "🏦",
           "flujo_caja_libre": "💵"}

_NOMBRES = {
    "rsi": "RSI (30–70)",
    "macd": "MACD alcista",
    "precio_sobre_sma200": "Precio > SMA 200",
    "bollinger_banda_baja": "Precio en banda baja Bollinger",
    "pe_vs_sector": f"P/E < {config.PE_ATRACTIVO}",
    "roe_positivo_creciente": "ROE positivo",
    "deuda_capital": f"Deuda/Capital < {config.DEUDA_CAPITAL_MAX}",
    "flujo_caja_libre": "Flujo de Caja Libre positivo",
}


def _render_ticker(ticker: str) -> None:
    """Renderiza la recomendación completa para un ticker."""
    with st.spinner(f"Calculando score para {ticker}…"):
        precios = obtener_historico(ticker, "1y")
        crudos = obtener_fundamentales(ticker)
        fundamental = procesar_fundamentales(crudos)
        tecnico = _ultimos_tecnicos(precios)
        resultado = calcular_score(tecnico, fundamental)

    score = resultado.get("score")
    recomendacion = resultado.get("recomendacion", "—")
    desglose = resultado.get("desglose", [])
    peso_evaluado = resultado.get("peso_evaluado", 0)

    color_map = {"Comprar": "#26a69a", "Neutral": "#ffa726", "Evitar": "#ef5350",
                 "Datos insuficientes": "#9e9e9e"}
    emoji_map = {"Comprar": "🟢", "Neutral": "🟡", "Evitar": "🔴", "Datos insuficientes": "⚫"}
    color = color_map.get(recomendacion, "#9e9e9e")
    emoji = emoji_map.get(recomendacion, "⚫")

    st.markdown(
        f"""
        <div style="background:{color}22; border-left:6px solid {color};
                    padding:1.2rem 1.5rem; border-radius:8px; margin-bottom:1rem;">
            <span style="font-size:2.5rem;">{emoji}</span>
            <span style="font-size:2rem; font-weight:700; margin-left:0.5rem;
                         color:{color};">{recomendacion}</span>
            {"<br><span style='font-size:1.1rem;'>Score: <strong>" + str(score) + " / 100</strong></span>" if score is not None else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if score is not None:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "Score total"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": color},
                "steps": [
                    {"range": [0, 40], "color": "rgba(239,83,80,0.13)"},
                    {"range": [40, 65], "color": "rgba(255,167,38,0.13)"},
                    {"range": [65, 100], "color": "rgba(38,166,154,0.13)"},
                ],
                "threshold": {
                    "line": {"color": color, "width": 4},
                    "thickness": 0.75,
                    "value": score,
                },
            },
        ))
        fig_gauge.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20),
                                template="plotly_dark")
        st.plotly_chart(fig_gauge, use_container_width=True, key=f"gauge_{ticker}")

        st.caption(f"Peso evaluado: {peso_evaluado:.0f} / 100 puntos "
                   f"({100 - peso_evaluado:.0f} puntos sin datos disponibles)")

    st.divider()

    st.markdown("#### Desglose por indicador")
    if desglose:
        filas = []
        for d in desglose:
            nombre = _NOMBRES.get(d["indicador"], d["indicador"])
            emoji_ind = _EMOJIS.get(d["indicador"], "")
            if not d["evaluado"]:
                estado = "⚫ Sin datos"
            elif d["cumplido"]:
                estado = "✅ Cumplido"
            else:
                estado = "❌ No cumplido"
            filas.append({
                "": emoji_ind,
                "Indicador": nombre,
                "Categoría": d["categoria"],
                "Peso": f"{d['peso']}%",
                "Estado": estado,
            })
        df = pd.DataFrame(filas)
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()

    if desglose:
        tecnico_pts = sum(d["peso"] for d in desglose if d["evaluado"] and d["cumplido"] and d["categoria"] == "Tecnico")
        tecnico_total = sum(d["peso"] for d in desglose if d["evaluado"] and d["categoria"] == "Tecnico")
        fund_pts = sum(d["peso"] for d in desglose if d["evaluado"] and d["cumplido"] and d["categoria"] == "Fundamental")
        fund_total = sum(d["peso"] for d in desglose if d["evaluado"] and d["categoria"] == "Fundamental")

        fig_bar = go.Figure(data=[
            go.Bar(name="Obtenidos", x=["Técnico", "Fundamental"],
                   y=[tecnico_pts, fund_pts],
                   marker_color=["#2196f3", "#ff9800"]),
            go.Bar(name="Posibles", x=["Técnico", "Fundamental"],
                   y=[tecnico_total, fund_total],
                   marker_color=["rgba(33,150,243,0.27)", "rgba(255,152,0,0.27)"]),
        ])
        fig_bar.update_layout(
            barmode="overlay", height=280, title="Puntos por categoría",
            template="plotly_dark", margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig_bar, use_container_width=True, key=f"bar_{ticker}")

    st.info(f"⚠️ {resultado.get('descargo', config.DESCARGO_RESPONSABILIDAD)}")


def render(tickers: list) -> None:
    st.subheader("🎯 Recomendación")

    if not tickers:
        st.warning("Introduce al menos un ticker en el panel lateral.")
        return

    if len(tickers) == 1:
        _render_ticker(tickers[0])
    else:
        tabs = st.tabs([f"🎯 {t}" for t in tickers])
        for tab, ticker in zip(tabs, tickers):
            with tab:
                _render_ticker(ticker)