"""Capa de datos: UNICA puerta de entrada a Yahoo Finance.

REGLA DE ARQUITECTURA: ningun otro modulo debe importar yfinance ni llamar a
una API externa. Todo pasa por aqui. Asi se puede cambiar la fuente de datos
sin tocar la logica de negocio, y las pruebas pueden simular esta capa.

Estado: ESQUELETO. Funciones aun sin implementar.
"""
from __future__ import annotations

import pandas as pd


def obtener_historico(ticker: str, periodo: str = "1y") -> pd.DataFrame:
    """Devuelve el historico de precios y volumen de un ticker.

    periodo: '1mo', '3mo', '1y', '5y' (ver config.VENTANAS_TEMPORALES).
    Devuelve un DataFrame con columnas normalizadas (Open, High, Low, Close,
    Volume) indexado por fecha. Debe devolver un DataFrame vacio si el ticker
    no existe, nunca lanzar datos inventados.

    >>> PRIMER OBJETIVO DEL PROYECTO: implementar esto y comprobar con un ticker
    de cada mercado (EE.UU., Colombia, Mexico, Brasil) que datos llegan.
    """
    raise NotImplementedError("Pendiente: yfinance.Ticker(ticker).history(period=periodo)")


def obtener_fundamentales(ticker: str) -> dict:
    """Devuelve metricas fundamentales: P/E, EPS, ROE, deuda/capital, margenes, FCF.

    AVISO: la cobertura de fundamentales en Latinoamerica es irregular. Debe
    devolver None en las claves que Yahoo no proporcione. NUNCA inventar valores.
    """
    raise NotImplementedError("Pendiente: yfinance.Ticker(ticker).info / .financials")
