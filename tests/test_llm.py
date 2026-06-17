"""Pruebas de la capa LLM (chatbot).

Solo se prueba la parte DETERMINISTA (normalizacion de pesos, fallback por
regex, serializacion del contexto). No se llama a la API de Groq: el objetivo es
verificar la logica propia, no la respuesta del modelo.
"""
from llm.intent_parser import _normalizar, _fallback_regex
from llm.report_chat import construir_contexto_texto


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


def test_construir_contexto_texto_incluye_recomendacion():
    contexto = {"tickers": {"AAPL": {
        "nombre": "Apple Inc.",
        "sector": "Technology",
        "moneda": "USD",
        "precio": 190.5,
        "tecnico": {"rsi": 55.0, "precio": 190.5},
        "fundamental": {"pe": 28.0, "roe": 0.45},
        "scoring": {"score": 72.0, "recomendacion": "Comprar", "peso_evaluado": 90,
                    "desglose": []},
    }}}
    texto = construir_contexto_texto(contexto)
    assert "AAPL" in texto
    assert "Comprar" in texto
    assert "72.0/100" in texto


def test_construir_contexto_texto_sin_tickers():
    assert "ningun ticker" in construir_contexto_texto({"tickers": {}}).lower()
