"""Pestana de Analisis Fundamental. Solo presenta; no calcula."""
import streamlit as st


def render(ticker: str) -> None:
    st.subheader("Analisis Fundamental")
    st.info("En construccion. Aqui ira la tabla de ratios (P/E, EPS, ROE, "
            "deuda/capital, margen neto, flujo de caja).")
