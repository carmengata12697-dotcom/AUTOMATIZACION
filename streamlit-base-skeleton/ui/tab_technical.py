"""Pestana de Analisis Tecnico. Solo presenta; no calcula."""
import streamlit as st


def render(ticker: str) -> None:
    st.subheader("Analisis Tecnico")
    st.info("En construccion. Aqui iran las graficas de precio con RSI, MACD, "
            "Bollinger y medias moviles para el ticker: " + (ticker or "-"))
