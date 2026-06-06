"""Pestana de Recomendacion. Muestra el resultado del motor de scoring."""
import streamlit as st


def render(ticker: str) -> None:
    st.subheader("Recomendacion")
    st.info("En construccion. Aqui ira el semaforo (Comprar/Neutral/Evitar), "
            "el score sobre 100 y el desglose por indicador.")
