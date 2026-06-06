"""Generacion del reporte PDF con reportlab.

Toma los resultados YA calculados (scoring, graficas, metricas) y arma el PDF.
No calcula nada; solo maqueta. Estado: ESQUELETO.
"""
from __future__ import annotations


def generar_reporte(datos_analisis: dict) -> bytes:
    """Devuelve el PDF en bytes para que Streamlit lo ofrezca como descarga.

    El PDF debe incluir el descargo de responsabilidad (config.DESCARGO_RESPONSABILIDAD).
    """
    raise NotImplementedError
