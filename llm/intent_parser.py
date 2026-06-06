"""Capa LLM (1/2): traduce lenguaje natural a una cartera estructurada.

Ejemplo: "quiero 50% en AAPL y el resto a partes iguales entre MSFT y GOOGL"
  -> {"AAPL": 0.5, "MSFT": 0.25, "GOOGL": 0.25}

REGLA DE ORO: el LLM SOLO interpreta la intencion y devuelve datos
estructurados. NO calcula indicadores, NO da recomendaciones, NO inventa cifras.
Estado: ESQUELETO.
"""
from __future__ import annotations


def parsear_intencion(texto_usuario: str) -> dict:
    """Devuelve {ticker: peso} a partir de la peticion en lenguaje natural."""
    raise NotImplementedError
