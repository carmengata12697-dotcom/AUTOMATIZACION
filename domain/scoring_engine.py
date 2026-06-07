"""Motor de scoring: NUCLEO DETERMINISTA de la recomendacion.

Aplica los pesos de config.PESOS_SCORING a los resultados de los motores
tecnico y fundamental y produce un score 0-100 con su recomendacion.

IMPORTANTE: la recomendacion (Comprar / Neutral / Evitar) SALE DE AQUI, nunca
del LLM. El LLM solo explica este resultado. Ver CLAUDE.md (regla de oro).
Estado: ESQUELETO.
"""
from __future__ import annotations

import config


def calcular_score(tecnico: dict, fundamental: dict,
                   pesos: dict = config.PESOS_SCORING) -> dict:
    """Combina senales tecnicas y fundamentales en un score ponderado.

    Devuelve un dict con:
      - score: float 0-100
      - recomendacion: 'Comprar' | 'Neutral' | 'Evitar'
      - desglose: contribucion de cada indicador (para justificar y mostrar)
    """
    raise NotImplementedError


def clasificar(score: float) -> str:
    """Traduce un score numerico a etiqueta segun los umbrales de config."""
    if score >= config.UMBRAL_COMPRAR:
        return "Comprar"
    if score >= config.UMBRAL_NEUTRAL:
        return "Neutral"
    return "Evitar"
