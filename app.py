"""Punto de entrada de la aplicación Streamlit.

Ejecutar con:  streamlit run app.py
"""
import streamlit as st

from ui import tab_technical, tab_fundamental, tab_recommendation, tab_portfolio, tab_chat

st.set_page_config(
    page_title="Analizador Bursátil con IA",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Analizador Bursátil con IA")
st.caption("Análisis técnico, fundamental y recomendación automatizada")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Configuración")

    st.markdown("**Selecciona hasta 3 tickers:**")
    ticker1 = st.text_input("Ticker 1", value="AAPL", help="Ej: AAPL").strip().upper()
    ticker2 = st.text_input("Ticker 2", value="", help="Ej: GOOGL (opcional)").strip().upper()
    ticker3 = st.text_input("Ticker 3", value="", help="Ej: MSFT (opcional)").strip().upper()

    tickers = [t for t in [ticker1, ticker2, ticker3] if t]

    st.divider()
    st.markdown("**Ejemplos por mercado:**")
    ejemplos = {
        "🇺🇸 EE.UU.": ["AAPL", "GOOGL", "MSFT"],
        "🇨🇴 Colombia": ["ECOPETROL.CL"],
        "🇲🇽 México": ["WALMEX.MX"],
        "🇧🇷 Brasil": ["PETR4.SA"],
    }
    for mercado, tks in ejemplos.items():
        st.caption(f"{mercado}: {', '.join(tks)}")

    st.divider()

    # --- Botón descarga PDF ---
    st.markdown("### 📄 Exportar a PDF")
    st.caption("Genera un reporte con todos los tickers seleccionados.")

    if st.button("Generar reporte PDF", use_container_width=True) and tickers:
        with st.spinner("Generando PDF…"):
            try:
                from data_layer.yahoo_client import obtener_historico, obtener_fundamentales
                from domain.technical_engine import (
                    calcular_rsi, calcular_macd,
                    calcular_bollinger, calcular_medias_moviles,
                )
                from domain.fundamental_engine import procesar_fundamentales
                from domain.scoring_engine import calcular_score
                from reports.pdf_generator import generar_reporte

                def ultimo(serie):
                    s = serie.dropna()
                    return s.iloc[-1] if not s.empty else None

                datos_tickers = []
                for ticker_pdf in tickers:
                    precios = obtener_historico(ticker_pdf, "1y")
                    crudos = obtener_fundamentales(ticker_pdf)
                    fundamental = procesar_fundamentales(crudos)

                    rsi = calcular_rsi(precios)
                    macd_df = calcular_macd(precios)
                    bollinger = calcular_bollinger(precios)
                    medias = calcular_medias_moviles(precios)

                    tecnico = {
                        "rsi": ultimo(rsi),
                        "macd": ultimo(macd_df["macd"]) if not macd_df.empty else None,
                        "senal": ultimo(macd_df["senal"]) if not macd_df.empty else None,
                        "precio": precios["Close"].dropna().iloc[-1] if not precios.empty else None,
                        "sma200": ultimo(medias["sma200"]) if not medias.empty and "sma200" in medias.columns else None,
                        "banda_baja": ultimo(bollinger["banda_baja"]) if not bollinger.empty else None,
                    }

                    resultado = calcular_score(tecnico, fundamental)

                    datos_tickers.append({
                        "ticker": ticker_pdf,
                        "nombre": fundamental.get("nombre"),
                        "sector": fundamental.get("sector"),
                        "moneda": fundamental.get("moneda"),
                        "precio_actual": tecnico.get("precio"),
                        "resultado_scoring": resultado,
                        "fundamental": fundamental,
                        "precios": precios,
                    })

                pdf_bytes = generar_reporte(datos_tickers)
                st.download_button(
                    label="⬇️ Descargar PDF",
                    data=pdf_bytes,
                    file_name=f"reporte_{'_'.join(tickers)}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Error generando PDF: {e}")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📈 Análisis Técnico", "📊 Análisis Fundamental", "🎯 Recomendación",
     "💼 Cartera", "💬 Asistente"]
)
with tab1:
    tab_technical.render(tickers)
with tab2:
    tab_fundamental.render(tickers)
with tab3:
    tab_recommendation.render(tickers)
with tab4:
    tab_portfolio.render(tickers)
with tab5:
    tab_chat.render(tickers)