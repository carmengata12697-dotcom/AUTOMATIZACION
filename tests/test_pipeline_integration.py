"""Prueba de integración controlada del flujo financiero principal
Valida el pipeline: precios simulados -> indicadores técnicos -> fundamentales procesados -> scoring -> generación de PDF
No depende de Internet ni de Yahoo Finance.
"""

import pandas as pd

from domain.fundamental_engine import procesar_fundamentales
from domain.scoring_engine import calcular_score
from domain.technical_engine import (
    calcular_bollinger,
    calcular_macd,
    calcular_medias_moviles,
    calcular_rsi,
)
from reports.pdf_generator import generar_reporte


def _ultimo(serie):
    """Devuelve el último valor no nulo de una serie"""
    limpia = serie.dropna()
    return limpia.iloc[-1] if not limpia.empty else None


def _precios_simulados():
    """Crea una serie de precios suficiente para indicadores de largo plazo"""
    fechas = pd.date_range("2024-01-01", periods=260, freq="D")

    cierres = [
        100 + indice * 0.12 + ((indice % 7) - 3) * 0.35
        for indice in range(260)
    ]

    precios = pd.DataFrame(
        {
            "Open": [precio - 0.20 for precio in cierres],
            "High": [precio + 0.80 for precio in cierres],
            "Low": [precio - 0.80 for precio in cierres],
            "Close": cierres,
            "Volume": [1_000_000] * len(cierres),
        },
        index=fechas,
    )
    precios.index.name = "Fecha"

    return precios


def test_pipeline_financiero_completo_generar_pdf():
    precios = _precios_simulados()

    rsi = calcular_rsi(precios)
    macd_df = calcular_macd(precios)
    bollinger = calcular_bollinger(precios)
    medias = calcular_medias_moviles(precios)

    tecnico = {
        "rsi": _ultimo(rsi),
        "macd": _ultimo(macd_df["macd"]),
        "senal": _ultimo(macd_df["senal"]),
        "precio": _ultimo(precios["Close"]),
        "sma200": _ultimo(medias["sma200"]),
        "banda_baja": _ultimo(bollinger["banda_baja"]),
    }

    fundamental = procesar_fundamentales(
        {
            "pe": 18.0,
            "eps": 6.2,
            "roe": 0.25,
            "deuda_capital": 80.0,
            "margen_neto": 0.18,
            "flujo_caja_libre": 1_000_000,
        }
    )

    resultado_scoring = calcular_score(tecnico, fundamental)

    datos_pdf = [
        {
            "ticker": "TEST",
            "nombre": "Empresa Simulada",
            "sector": "Tecnología",
            "moneda": "USD",
            "precio_actual": tecnico["precio"],
            "resultado_scoring": resultado_scoring,
            "fundamental": fundamental,
            "precios": precios,
        }
    ]

    pdf_bytes = generar_reporte(datos_pdf)

    assert all(valor is not None for valor in tecnico.values())
    assert resultado_scoring["score"] is not None
    assert resultado_scoring["recomendacion"] in {
        "Comprar",
        "Neutral",
        "Evitar",
    }
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1_000