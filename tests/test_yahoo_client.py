import pandas as pd

from data_layer import yahoo_client as yc


class _TickerSimulado:
    """Simula yf.Ticker para probar historial sin hacer llamadas reales"""

    def __init__(self, datos=None, error=None):
        self._datos = datos
        self._error = error

    def history(self, period, auto_adjust):
        if self._error:
            raise self._error
        return self._datos


def _simular_ticker(monkeypatch, datos=None, error=None):
    """Reemplaza yf.Ticker temporalmente por un objeto simulado"""
    monkeypatch.setattr(
        yc.yf,
        "Ticker",
        lambda ticker: _TickerSimulado(datos=datos, error=error),
    )


def test_obtener_historico_conserva_columnas_validas_y_nombra_indice(monkeypatch):
    fechas = pd.date_range("2024-01-01", periods=3, freq="D")

    datos_yahoo = pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0],
            "High": [101.0, 102.0, 103.0],
            "Low": [99.0, 100.0, 101.0],
            "Close": [100.5, 101.5, 102.5],
            "Volume": [1000, 1100, 1200],
            "Dividends": [0.0, 0.0, 0.0],
        },
        index=fechas,
    )

    _simular_ticker(monkeypatch, datos=datos_yahoo)

    resultado = yc.obtener_historico("AAPL", "1y")

    assert list(resultado.columns) == yc._COLUMNAS_PRECIO
    assert len(resultado) == 3
    assert resultado.index.name == "Fecha"
    assert "Dividends" not in resultado.columns


def test_obtener_historico_elimina_filas_sin_cierre(monkeypatch):
    fechas = pd.date_range("2024-01-01", periods=3, freq="D")

    datos_yahoo = pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0],
            "High": [101.0, 102.0, 103.0],
            "Low": [99.0, 100.0, 101.0],
            "Close": [100.5, None, 102.5],
            "Volume": [1000, 1100, 1200],
        },
        index=fechas,
    )

    _simular_ticker(monkeypatch, datos=datos_yahoo)

    resultado = yc.obtener_historico("ECOPETROL.CL", "1y")

    assert len(resultado) == 2
    assert resultado["Close"].isna().sum() == 0


def test_obtener_historico_vacio_devuelve_dataframe_estandar(monkeypatch):
    _simular_ticker(monkeypatch, datos=pd.DataFrame())

    resultado = yc.obtener_historico("TICKER_INEXISTENTE", "1y")

    assert resultado.empty
    assert list(resultado.columns) == yc._COLUMNAS_PRECIO


def test_obtener_historico_si_yahoo_falla_devuelve_dataframe_estandar(monkeypatch):
    _simular_ticker(monkeypatch, error=RuntimeError("Error simulado de Yahoo Finance"))

    resultado = yc.obtener_historico("AAPL", "1y")

    assert resultado.empty
    assert list(resultado.columns) == yc._COLUMNAS_PRECIO


class _TickerFundamentalesSimulado:
    """Simula yf.Ticker para probar .info sin hacer llamadas reales"""

    def __init__(self, info=None, error=None):
        self._info = info
        self._error = error

    @property
    def info(self):
        if self._error:
            raise self._error
        return self._info


def _simular_fundamentales(monkeypatch, info=None, error=None):
    """Reemplaza yf.Ticker temporalmente para pruebas de fundamentales"""
    monkeypatch.setattr(
        yc.yf,
        "Ticker",
        lambda ticker: _TickerFundamentalesSimulado(info=info, error=error),
    )


def test_obtener_fundamentales_mapea_campos_y_metadatos(monkeypatch):
    info_yahoo = {
        "trailingPE": 28.5,
        "trailingEps": 6.2,
        "returnOnEquity": 0.45,
        "debtToEquity": 79.5,
        "profitMargins": 0.25,
        "freeCashflow": 1_000_000,
        "longName": "Apple Inc.",
        "currency": "USD",
        "sector": "Technology",
    }

    _simular_fundamentales(monkeypatch, info=info_yahoo)

    resultado = yc.obtener_fundamentales("AAPL")

    assert resultado["pe"] == 28.5
    assert resultado["eps"] == 6.2
    assert resultado["roe"] == 0.45
    assert resultado["deuda_capital"] == 79.5
    assert resultado["margen_neto"] == 0.25
    assert resultado["flujo_caja_libre"] == 1_000_000
    assert resultado["nombre"] == "Apple Inc."
    assert resultado["moneda"] == "USD"
    assert resultado["sector"] == "Technology"


def test_obtener_fundamentales_usa_shortname_si_no_hay_longname(monkeypatch):
    _simular_fundamentales(
        monkeypatch,
        info={
            "shortName": "Microsoft",
            "currency": "USD",
            "sector": "Technology",
        },
    )

    resultado = yc.obtener_fundamentales("MSFT")

    assert resultado["nombre"] == "Microsoft"
    assert resultado["pe"] is None
    assert resultado["flujo_caja_libre"] is None


def test_obtener_fundamentales_si_yahoo_falla_devuelve_estructura_segura(monkeypatch):
    _simular_fundamentales(
        monkeypatch,
        error=RuntimeError("Error simulado de Yahoo Finance"),
    )

    resultado = yc.obtener_fundamentales("AAPL")

    assert resultado["pe"] is None
    assert resultado["eps"] is None
    assert resultado["roe"] is None
    assert resultado["deuda_capital"] is None
    assert resultado["margen_neto"] is None
    assert resultado["flujo_caja_libre"] is None
    assert resultado["nombre"] is None
    assert resultado["moneda"] is None
    assert resultado["sector"] is None


def test_obtener_fundamentales_con_respuesta_no_diccionario_devuelve_estructura_segura(
    monkeypatch,
):
    _simular_fundamentales(monkeypatch, info=[])

    resultado = yc.obtener_fundamentales("AAPL")

    assert resultado["pe"] is None
    assert resultado["eps"] is None
    assert resultado["roe"] is None
    assert resultado["deuda_capital"] is None
    assert resultado["margen_neto"] is None
    assert resultado["flujo_caja_libre"] is None
    assert resultado["nombre"] is None
    assert resultado["moneda"] is None
    assert resultado["sector"] is None

def test_obtener_historico_con_todos_los_cierres_vacios_devuelve_dataframe_estandar(
    monkeypatch,
):
    fechas = pd.date_range("2024-01-01", periods=2, freq="D")

    datos_yahoo = pd.DataFrame(
        {
            "Open": [100.0, 101.0],
            "High": [101.0, 102.0],
            "Low": [99.0, 100.0],
            "Close": [None, None],
            "Volume": [1000, 1100],
        },
        index=fechas,
    )

    _simular_ticker(monkeypatch, datos=datos_yahoo)

    resultado = yc.obtener_historico("TICKER_SIN_CIERRES", "1y")

    assert resultado.empty
    assert list(resultado.columns) == yc._COLUMNAS_PRECIO