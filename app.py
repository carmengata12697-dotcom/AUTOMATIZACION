"""Punto de entrada de la aplicación Streamlit.

Ejecutar con:  streamlit run app.py
"""
import streamlit as st

from ui import tab_technical, tab_fundamental, tab_recommendation, tab_portfolio

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
    ticker = st.text_input("Ticker", value="AAPL", help="Ej: AAPL, GOOGL, ECOPETROL.CL").strip().upper()

    st.divider()
    st.markdown("**Ejemplos por mercado:**")
    ejemplos = {
        "🇺🇸 EE.UU.": ["AAPL", "GOOGL", "MSFT"],
        "🇨🇴 Colombia": ["ECOPETROL.CL"],
        "🇲🇽 México": ["WALMEX.MX"],
        "🇧🇷 Brasil": ["PETR4.SA"],
    }
    for mercado, tickers in ejemplos.items():
        st.caption(f"{mercado}: {', '.join(tickers)}")

    st.divider()

    # --- Botón descarga PDF ---
    st.markdown("### 📄 Exportar a PDF")
    if st.button("Generar reporte PDF", use_container_width=True):
        with st.spinner("Generando PDF…"):
            try:
                from data_layer.yahoo_client import obtener_historico, obtener_fundamentales
                from domain.technical_engine import calcular_rsi, calcular_macd, calcular_bollinger, calcular_medias_moviles
                from domain.fundamental_engine import procesar_fundamentales
                from domain.scoring_engine import calcular_score
                from reports.pdf_generator import generar_reporte

                precios = obtener_historico(ticker, "1y")
                crudos = obtener_fundamentales(ticker)
                fundamental = procesar_fundamentales(crudos)

                def ultimo(serie):
                    s = serie.dropna()
                    return s.iloc[-1] if not s.empty else None

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

                datos_pdf = {
                    "ticker": ticker,
                    "nombre": fundamental.get("nombre"),
                    "sector": fundamental.get("sector"),
                    "moneda": fundamental.get("moneda"),
                    "precio_actual": tecnico.get("precio"),
                    "resultado_scoring": resultado,
                    "fundamental": fundamental,
                }

                pdf_bytes = generar_reporte(datos_pdf)
                st.download_button(
                    label="⬇️ Descargar PDF",
                    data=pdf_bytes,
                    file_name=f"reporte_{ticker}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Error generando PDF: {e}")

tab1, tab2, tab3, tab4 = st.tabs(
    ["📈 Análisis Técnico", "📊 Análisis Fundamental", "🎯 Recomendación", "💼 Cartera"]
)
with tab1:
    tab_technical.render(ticker)
with tab2:
    tab_fundamental.render(ticker)
with tab3:
    tab_recommendation.render(ticker)
with tab4:
    tab_portfolio.render()

