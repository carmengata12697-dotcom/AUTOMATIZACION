"""Capa LLM (1/2): traduce lenguaje natural a una cartera estructurada.

Ejemplo: "quiero 50% en AAPL y el resto a partes iguales entre MSFT y GOOGL"
  -> {"AAPL": 0.5, "MSFT": 0.25, "GOOGL": 0.25}

REGLA DE ORO: el LLM SOLO interpreta la intencion y devuelve datos
estructurados. NO calcula indicadores, NO da recomendaciones, NO inventa cifras.
Aqui "calcular" se limita a repartir los pesos que el propio usuario expresa
(normalizar para que sumen 1); ningun dato de mercado sale del LLM.
"""
from __future__ import annotations

import json
import re

from llm import groq_client

_SYSTEM = """Eres un parser que convierte la peticion de un usuario sobre una \
cartera de acciones en JSON. Reglas estrictas:
- Devuelve UNICAMENTE un objeto JSON con la forma {"pesos": {"TICKER": numero}}.
- Las claves son los simbolos bursatiles (tickers) en MAYUSCULAS tal y como los \
escribe el usuario (p. ej. AAPL, MSFT, ECOPETROL.CL, PETR4.SA).
- Los numeros son la proporcion de cada ticker entre 0 y 1; deben sumar 1.
- "a partes iguales", "el resto repartido", etc. implican repartir lo restante \
por igual entre los tickers sin porcentaje explicito.
- Si el usuario no da porcentajes, reparte por igual entre todos los tickers.
- No inventes tickers que el usuario no haya mencionado. No anadas explicaciones."""


def _normalizar(pesos: dict) -> dict:
    """Limpia y reescala los pesos para que sumen 1.0 (equipondera si no hay datos)."""
    limpios = {}
    for ticker, peso in (pesos or {}).items():
        if not isinstance(ticker, str):
            continue
        clave = ticker.strip().upper()
        try:
            valor = float(peso)
        except (TypeError, ValueError):
            valor = 0.0
        if clave and valor > 0:
            limpios[clave] = limpios.get(clave, 0.0) + valor

    if not limpios:
        return {}

    total = sum(limpios.values())
    if total <= 0:
        # Sin pesos utiles: equiponderar entre los tickers detectados.
        n = len(limpios)
        return {t: round(1 / n, 4) for t in limpios}
    return {t: round(v / total, 4) for t, v in limpios.items()}


def _fallback_regex(texto: str) -> dict:
    """Extrae tickers con un patron simple si el LLM no esta disponible.

    Reconoce simbolos en mayusculas (con sufijos tipo .CL, .MX, .SA) y, si los hay,
    los reparte por igual. No interpreta porcentajes: es una red de seguridad
    minima para que la app siga siendo usable sin LLM.
    """
    # Tickers en mayusculas, admitiendo un digito (PETR4) y sufijo de mercado (.SA).
    candidatos = re.findall(r"\b[A-Z]{1,6}[0-9]?(?:\.[A-Z]{1,3})?\b", texto or "")
    descartar = {"EL", "LA", "Y", "EN", "DE", "A", "RSI", "MACD", "PE", "ROE", "PDF"}
    tickers = [c for c in candidatos if c not in descartar]
    if not tickers:
        return {}
    n = len(tickers)
    return {t: round(1 / n, 4) for t in dict.fromkeys(tickers)}


def parsear_intencion(texto_usuario: str) -> dict:
    """Devuelve {ticker: peso} a partir de la peticion en lenguaje natural.

    Los pesos estan normalizados (suman 1.0). Devuelve {} si no se reconoce
    ningun ticker. Nunca lanza excepcion: ante cualquier fallo recurre a un
    extractor por expresiones regulares.
    """
    if not (texto_usuario or "").strip():
        return {}

    if not groq_client.disponible():
        return _fallback_regex(texto_usuario)

    respuesta = groq_client.chat(
        mensajes=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": texto_usuario},
        ],
        temperatura=0.0,
        json_mode=True,
    )

    try:
        datos = json.loads(respuesta)
        pesos = datos.get("pesos", datos)  # tolera que devuelva el dict directo
        normalizados = _normalizar(pesos if isinstance(pesos, dict) else {})
        return normalizados or _fallback_regex(texto_usuario)
    except (json.JSONDecodeError, AttributeError, TypeError):
        return _fallback_regex(texto_usuario)
