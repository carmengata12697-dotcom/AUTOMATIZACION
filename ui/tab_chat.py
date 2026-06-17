"""Pestana del Asistente (chatbot). Q&A con grounding sobre el informe calculado.

Esta pestana NO calcula la recomendacion: reune los resultados que ya producen
los motores deterministas (los mismos que usa la pestana de Recomendacion),
construye el contexto y se lo pasa a llm.report_chat. El LLM solo explica.
"""
import streamlit as st

import config
from data_layer.yahoo_client import obtener_historico, obtener_fundamentales
from domain.technical_engine import (
    calcular_rsi, calcular_macd, calcular_bollinger, calcular_medias_moviles,
)
from domain.fundamental_engine import procesar_fundamentales
from domain.scoring_engine import calcular_score
from llm import groq_client, report_chat


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
    """Construye el contexto de analisis para todos los tickers (cacheado).

    Se cachea por la tupla de tickers para no volver a descargar y recalcular en
    cada turno de la conversacion.
    """
    return {"tickers": {t: _analizar_ticker(t) for t in tickers}}


_SUGERENCIAS = [
    "¿Cual de los tickers tiene mejor recomendacion y por que?",
    "Explica el score de la primera accion criterio a criterio.",
    "¿Que significa que el RSI este en ese nivel?",
    "Compara el P/E y el ROE de los tickers seleccionados.",
]


def render(tickers: list) -> None:
    st.subheader("💬 Asistente del informe")
    st.caption("Pregunta sobre el analisis ya calculado. El asistente solo explica "
               "los resultados de los motores; no inventa cifras ni da una "
               "recomendacion distinta a la del scoring.")

    if not groq_client.disponible():
        st.warning(groq_client.aviso_no_disponible())
        st.info("Para activarlo: crea un archivo `.env` en la raiz con "
                "`GROQ_API_KEY=tu_clave` y reinicia la app.")
        return

    if not tickers:
        st.warning("Introduce al menos un ticker en el panel lateral para que el "
                   "asistente tenga datos sobre los que responder.")
        return

    with st.spinner("Preparando el contexto del informe…"):
        contexto = _construir_contexto(tuple(tickers))

    st.success(f"Asistente listo. Tickers en contexto: {', '.join(tickers)}")

    # Historial de conversacion por sesion.
    if "chat_historial" not in st.session_state:
        st.session_state.chat_historial = []

    with st.expander("💡 Ejemplos de preguntas"):
        for s in _SUGERENCIAS:
            st.markdown(f"- {s}")

    for mensaje in st.session_state.chat_historial:
        with st.chat_message(mensaje["role"]):
            st.markdown(mensaje["content"])

    pregunta = st.chat_input("Escribe tu pregunta sobre el analisis…")
    if pregunta:
        st.session_state.chat_historial.append({"role": "user", "content": pregunta})
        with st.chat_message("user"):
            st.markdown(pregunta)

        with st.chat_message("assistant"):
            with st.spinner("Pensando…"):
                respuesta = report_chat.responder(pregunta, contexto)
            st.markdown(respuesta)

        st.session_state.chat_historial.append(
            {"role": "assistant", "content": respuesta}
        )

    if st.session_state.chat_historial:
        if st.button("🗑️ Limpiar conversacion"):
            st.session_state.chat_historial = []
            st.rerun()

    st.divider()
    st.caption(f"⚠️ {config.DESCARGO_RESPONSABILIDAD}")
