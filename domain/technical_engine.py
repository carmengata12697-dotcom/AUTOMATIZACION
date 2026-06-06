"""Motor tecnico: calcula indicadores sobre el historico de precios.

Recibe el DataFrame que devuelve data_layer.obtener_historico. No llama a
ninguna API. Logica de negocio pura -> facil de testear.
Estado: ESQUELETO.
"""
from __future__ import annotations

import pandas as pd


def calcular_rsi(precios: pd.DataFrame, ventana: int = 14) -> pd.Series:
    """Indice de Fuerza Relativa (RSI)."""
    raise NotImplementedError


def calcular_macd(precios: pd.DataFrame) -> pd.DataFrame:
    """MACD: linea MACD, linea de senal e histograma."""
    raise NotImplementedError


def calcular_bollinger(precios: pd.DataFrame, ventana: int = 20) -> pd.DataFrame:
    """Bandas de Bollinger (media + bandas superior e inferior)."""
    raise NotImplementedError


def calcular_medias_moviles(precios: pd.DataFrame) -> pd.DataFrame:
    """Medias moviles SMA/EMA (incluida SMA 200 para tendencia de largo plazo)."""
    raise NotImplementedError
