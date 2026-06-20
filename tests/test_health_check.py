import pandas as pd

from data_layer import yahoo_client as yc


class _TickerSaludSimulado:
    """Simula yf.Ticker para validar disponibilidad sin usar Internet"""

    def __init__(self, datos=None, error=None):
        self._datos = datos
        self._error = error

    def history(self, period, auto_adjust):
        if self._error:
            raise self._error
        return self._datos


def _simular_consulta_salud(monkeypatch, datos=None, error=None):
    """Reemplaza yf.Ticker temporalmente por una respuesta controlada"""
    monkeypatch.setattr(
        yc.yf,
        "Ticker",
        lambda ticker: _TickerSaludSimulado(datos=datos, error=error),
    )


def test_health_check_disponible_informa_ultima_fecha(monkeypatch):
    fechas = pd.to_datetime(["2024-06-13", "2024-06-14"])

    datos_yahoo = pd.DataFrame(
        {
            "Close": [190.0, 191.0],
        },
        index=fechas,
    )

    _simular_consulta_salud(monkeypatch, datos=datos_yahoo)

    resultado = yc.verificar_disponibilidad_yahoo()

    assert resultado["estado"] == "disponible"
    assert resultado["fecha_ultimo_dato"] == "2024-06-14"
    assert resultado["mensaje"] == "Fuente de datos disponible"


def test_health_check_sin_datos_informa_estado_controlado(monkeypatch):
    _simular_consulta_salud(monkeypatch, datos=pd.DataFrame())

    resultado = yc.verificar_disponibilidad_yahoo()

    assert resultado["estado"] == "sin_datos"
    assert resultado["fecha_ultimo_dato"] is None


def test_health_check_error_informa_estado_controlado(monkeypatch):
    _simular_consulta_salud(
        monkeypatch,
        error=RuntimeError("Error simulado de Yahoo Finance"),
    )

    resultado = yc.verificar_disponibilidad_yahoo()

    assert resultado["estado"] == "error"
    assert resultado["fecha_ultimo_dato"] is None