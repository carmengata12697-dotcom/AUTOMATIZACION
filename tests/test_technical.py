"""Pruebas del motor tecnico (datos sinteticos, sin red)."""
import numpy as np
import pandas as pd
 
from domain import technical_engine as te
 
 
def _precios(valores):
    fechas = pd.date_range("2024-01-01", periods=len(valores), freq="D")
    serie = pd.Series(valores, index=fechas, dtype="float64")
    return pd.DataFrame({"Open": serie, "High": serie + 1, "Low": serie - 1,
                         "Close": serie, "Volume": 1000})
 
 
def test_rsi_en_rango_0_100():
    np.random.seed(1)
    df = _precios(100 + np.cumsum(np.random.normal(0, 1, 200)))
    rsi = te.calcular_rsi(df).dropna()
    assert len(rsi) > 0
    assert rsi.between(0, 100).all()
 
 
def test_sma20_de_serie_constante_es_la_constante():
    df = _precios([100.0] * 40)
    sma20 = te.calcular_medias_moviles(df)["sma20"].dropna()
    assert np.allclose(sma20.values, 100.0)
 
 
def test_bollinger_ordenadas():
    np.random.seed(2)
    df = _precios(100 + np.cumsum(np.random.normal(0, 1, 100)))
    bb = te.calcular_bollinger(df).dropna()
    assert (bb["banda_baja"] <= bb["media"]).all()
    assert (bb["media"] <= bb["banda_alta"]).all()
 
 
def test_macd_tiene_sus_columnas():
    np.random.seed(3)
    df = _precios(100 + np.cumsum(np.random.normal(0, 1, 100)))
    macd = te.calcular_macd(df)
    assert list(macd.columns) == ["macd", "senal", "histograma"]
 
 
def test_dataframe_vacio_no_rompe():
    vacio = pd.DataFrame()
    assert te.calcular_rsi(vacio).empty
    assert te.calcular_macd(vacio).empty
    assert te.calcular_bollinger(vacio).empty
    assert te.calcular_medias_moviles(vacio).empty