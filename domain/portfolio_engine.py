"""Motor de cartera: agrega varios activos en una cartera ponderada.

Sustituye al "comparador" de la propuesta original. Toma los tickers y pesos
que pidio el usuario (estructurados por la capa LLM o por la UI) y calcula las
metricas del CONJUNTO. Aqui esta la sustancia financiera propia del proyecto.
Estado: ESQUELETO.
"""
from __future__ import annotations


def normalizar_pesos(pesos_por_ticker: dict) -> dict:
    """Asegura que los pesos sumen 1.0 (equiponderada si no se especifican)."""
    raise NotImplementedError


def calcular_metricas_cartera(scores_por_ticker: dict, pesos_por_ticker: dict,
                              historicos: dict) -> dict:
    """Metricas a nivel cartera.

    Devuelve un dict con: score_ponderado, matriz de correlacion entre activos,
    medida de diversificacion y riesgo agregado. Todo calculado aqui; el LLM
    solo lo explica despues.
    """
    raise NotImplementedError
