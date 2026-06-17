"""Pruebas de la capa LLM (chatbot con RAG).

Solo se prueba la parte DETERMINISTA (normalización de pesos, fallback por regex,
serialización del contexto, formato de porcentajes y recuperación RAG). No se
llama a la API de Groq: el objetivo es verificar la lógica propia, no la
respuesta del modelo.
"""
from llm.intent_parser import _normalizar, _fallback_regex
from llm.RAG import construir_contexto_texto, recuperar, _pct


_CONTEXTO = {"tickers": {
    "AAPL": {
        "nombre": "Apple Inc.", "sector": "Technology", "moneda": "USD",
        "precio": 190.5,
        "tecnico": {"rsi": 55.0, "precio": 190.5},
        "fundamental": {"pe": 28.0, "roe": 0.45, "margen_neto": 0.25},
        "scoring": {"score": 72.0, "recomendacion": "Comprar", "peso_evaluado": 90,
                    "desglose": []},
    },
    "MSFT": {
        "nombre": "Microsoft Corp.", "sector": "Technology", "moneda": "USD",
        "precio": 410.0,
        "tecnico": {"rsi": 60.0, "precio": 410.0},
        "fundamental": {"pe": 33.0, "roe": 0.40, "margen_neto": 0.36},
        "scoring": {"score": 58.0, "recomendacion": "Neutral", "peso_evaluado": 88,
                    "desglose": []},
    },
}}


def test_normalizar_pesos_suman_uno():
    pesos = _normalizar({"AAPL": 0.5, "MSFT": 0.25, "GOOGL": 0.25})
    assert abs(sum(pesos.values()) - 1.0) < 1e-6
    assert pesos["AAPL"] == 0.5


def test_normalizar_reescala_si_no_suman_uno():
    pesos = _normalizar({"AAPL": 2, "MSFT": 2})  # suman 4 -> 0.5 y 0.5
    assert pesos == {"AAPL": 0.5, "MSFT": 0.5}


def test_normalizar_ignora_pesos_invalidos():
    pesos = _normalizar({"AAPL": "x", "MSFT": -1, "GOOGL": 1})
    assert pesos == {"GOOGL": 1.0}


def test_normalizar_vacio():
    assert _normalizar({}) == {}


def test_fallback_regex_detecta_tickers_y_equipondera():
    pesos = _fallback_regex("quiero AAPL y MSFT")
    assert set(pesos) == {"AAPL", "MSFT"}
    assert pesos["AAPL"] == 0.5


def test_fallback_regex_reconoce_sufijos_de_mercado():
    pesos = _fallback_regex("invertir en PETR4.SA")
    assert "PETR4.SA" in pesos


def test_pct_formatea_fraccion_como_porcentaje():
    assert _pct(0.45) == "45.0%"
    assert _pct(None) == "sin dato"


def test_construir_contexto_texto_incluye_recomendacion_y_porcentaje():
    texto = construir_contexto_texto(_CONTEXTO)
    assert "AAPL" in texto
    assert "Comprar" in texto
    assert "72.0/100" in texto
    assert "45.0%" in texto  # ROE en formato porcentaje


def test_construir_contexto_texto_sin_tickers():
    assert "ningún ticker" in construir_contexto_texto({"tickers": {}}).lower()


def test_recuperar_filtra_por_ticker_mencionado():
    texto = recuperar("¿cómo está MSFT?", _CONTEXTO)
    assert "MSFT" in texto
    assert "AAPL" not in texto  # solo se recupera el ticker preguntado


def test_recuperar_incluye_concepto_del_glosario():
    texto = recuperar("¿qué significa el RSI de AAPL?", _CONTEXTO)
    assert "CONCEPTOS RELEVANTES" in texto
    assert "Fuerza Relativa" in texto


def test_recuperar_sin_ticker_devuelve_todos():
    texto = recuperar("compara las dos acciones", _CONTEXTO)
    assert "AAPL" in texto and "MSFT" in texto
