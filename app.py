"""Punto de entrada de la aplicacion Streamlit.

ESQUELETO: arranca, muestra las pestanas y un mensaje de "en construccion" en
cada una. La logica de calculo vive en los motores (domain/), nunca aqui.

Ejecutar con:  streamlit run app.py
"""
import streamlit as st

from ui import tab_technical, tab_fundamental, tab_recommendation, tab_portfolio

st.set_page_config(page_title="Analizador Bursatil con IA", layout="wide")

st.title("Analizador Bursatil con IA")
st.caption("Esqueleto del proyecto - rama feature/streamlit-base")

ticker = st.sidebar.text_input("Ticker", value="AAPL").strip().upper()

tab1, tab2, tab3, tab4 = st.tabs(
    ["Analisis Tecnico", "Analisis Fundamental", "Recomendacion", "Cartera"]
)
with tab1:
    tab_technical.render(ticker)
with tab2:
    tab_fundamental.render(ticker)
with tab3:
    tab_recommendation.render(ticker)
with tab4:
    tab_portfolio.render()
