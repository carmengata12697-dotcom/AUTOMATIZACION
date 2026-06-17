"""Pestaña del Asistente (chatbot). Q&A con RAG sobre el informe ya calculado.

Esta pestaña NO calcula la recomendación: reúne los resultados que ya producen
los motores deterministas (los mismos que usa la pestaña de Recomendación),
construye el contexto y se lo pasa al sistema RAG (llm/RAG.py). El LLM solo
explica; los números salen siempre de los motores.
"""
import streamlit as st

import config
from data_layer.yahoo_client import obtener_historico, obtener_fundamentales
from domain.technical_engine import (
    calcular_rsi, calcular_macd, calcular_bollinger, calcular_medias_moviles,
)
from domain.fundamental_engine import procesar_fundamentales
from domain.scoring_engine import calcular_score
from llm import groq_client, RAG


def _ultimo(serie):
    s = serie.dropna()
    return s.iloc[-1] if not s.empty else None


def _analizar_ticker(ticker: str) -> dict:
    """Ejecuta los motores deterministas para un ticker y devuelve su contexto."""
    precios = obtener_historico(ticker, "1y")
    crudos = obtener_fundamentales(ticker)
    fundamental = procesar_fundamentales(crudos)

    if precios.empty:
        tecnico = {}
    else:
        macd_df = calcular_macd(precios)
        bollinger = calcular_bollinger(precios)
        medias = calcular_medias_moviles(precios)
        tecnico = {
            "rsi": _ultimo(calcular_rsi(precios)),
            "macd": _ultimo(macd_df["macd"]) if not macd_df.empty else None,
            "senal": _ultimo(macd_df["senal"]) if not macd_df.empty else None,
            "precio": precios["Close"].dropna().iloc[-1] if not precios.empty else None,
            "sma200": _ultimo(medias["sma200"]) if not medias.empty and "sma200" in medias.columns else None,
            "banda_baja": _ultimo(bollinger["banda_baja"]) if not bollinger.empty else None,
        }

    resultado = calcular_score(tecnico, fundamental)

    return {
        "nombre": fundamental.get("nombre"),
        "sector": fundamental.get("sector"),
        "moneda": fundamental.get("moneda"),
        "precio": tecnico.get("precio"),
        "tecnico": tecnico,
        "fundamental": fundamental,
        "scoring": resultado,
    }


@st.cache_data(show_spinner=False)
def _construir_contexto(tickers: tuple) -> dict:
    """Construye el contexto de análisis para todos los tickers (cacheado).

    Se cachea por la tupla de tickers para no volver a descargar y recalcular en
    cada turno de la conversación.
    """
    return {"tickers": {t: _analizar_ticker(t) for t in tickers}}


_SUGERENCIAS = [
    "¿Cuál de los tickers tiene mejor recomendación y por qué?",
    "Explica el score de la primera acción criterio a criterio.",
    "¿Qué significa que el RSI esté en ese nivel?",
    "Compara el P/E y el ROE de los tickers seleccionados.",
]


def _procesar(pregunta: str, contexto: dict) -> None:
    """Añade la pregunta al historial, genera la respuesta y la muestra."""
    st.session_state.chat_historial.append({"role": "user", "content": pregunta})
    with st.chat_message("user"):
        st.markdown(pregunta)
    with st.chat_message("assistant"):
        with st.spinner("Pensando…"):
            respuesta = RAG.responder(pregunta, contexto)
        st.markdown(respuesta)
    st.session_state.chat_historial.append({"role": "assistant", "content": respuesta})


def render(tickers: list) -> None:
    st.subheader("💬 Asistente del informe")
    st.caption("Pregunta sobre el análisis ya calculado. El asistente solo explica "
               "los resultados de los motores; no inventa cifras ni da una "
               "recomendación distinta a la del scoring.")

    if not groq_client.disponible():
        st.warning(groq_client.aviso_no_disponible())
        st.info("Para activarlo: crea un archivo `.env` en la raíz con "
                "`GROQ_API_KEY=tu_clave` y reinicia la app.")
        return

    if not tickers:
        st.warning("Introduce al menos un ticker en el panel lateral para que el "
                   "asistente tenga datos sobre los que responder.")
        return

    with st.spinner("Preparando el contexto del informe…"):
        contexto = _construir_contexto(tuple(tickers))

    st.success(f"Asistente listo. Tickers en contexto: {', '.join(tickers)}")

    if "chat_historial" not in st.session_state:
        st.session_state.chat_historial = []

    # Preguntas rápidas como botones: un clic envía la pregunta sin escribir.
    st.markdown("**💡 Preguntas rápidas:**")
    pregunta = None
    columnas = st.columns(2)
    for i, sugerencia in enumerate(_SUGERENCIAS):
        if columnas[i % 2].button(sugerencia, key=f"sug_{i}", use_container_width=True):
            pregunta = sugerencia

    st.divider()

    # Historial de la conversación.
    for mensaje in st.session_state.chat_historial:
        with st.chat_message(mensaje["role"]):
            st.markdown(mensaje["content"])

    # Entrada de texto libre (tiene prioridad si el usuario escribe).
    escrita = st.chat_input("Escribe tu pregunta sobre el análisis…")
    if escrita:
        pregunta = escrita

    if pregunta:
        _procesar(pregunta, contexto)

    if st.session_state.chat_historial:
        if st.button("🗑️ Limpiar conversación"):
            st.session_state.chat_historial = []
            st.rerun()

    st.divider()
    st.caption(f"⚠️ {config.DESCARGO_RESPONSABILIDAD}")
