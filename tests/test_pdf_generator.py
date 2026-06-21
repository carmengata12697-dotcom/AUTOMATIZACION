import pandas as pd

from reports.pdf_generator import generar_reporte


def _desglose_base():
    """Retorna un desglose mínimo compatible con el motor de scoring"""
    return [
        {
            "indicador": "rsi",
            "categoria": "Tecnico",
            "peso": 10,
            "evaluado": True,
            "cumplido": True,
        },
        {
            "indicador": "macd",
            "categoria": "Tecnico",
            "peso": 12,
            "evaluado": True,
            "cumplido": False,
        },
        {
            "indicador": "pe_vs_sector",
            "categoria": "Fundamental",
            "peso": 14,
            "evaluado": True,
            "cumplido": True,
        },
        {
            "indicador": "flujo_caja_libre",
            "categoria": "Fundamental",
            "peso": 18,
            "evaluado": True,
            "cumplido": True,
        },
    ]


def _ticker_pdf(
    ticker="AAPL",
    nombre="Apple Inc.",
    recomendacion="Comprar",
    score=66.0,
    precios=None,
):
    """Construye una entrada simulada con el formato esperado por el PDF"""
    return {
        "ticker": ticker,
        "nombre": nombre,
        "sector": "Technology",
        "moneda": "USD",
        "precio_actual": 190.50,
        "resultado_scoring": {
            "score": score,
            "recomendacion": recomendacion,
            "peso_evaluado": 100,
            "desglose": _desglose_base(),
        },
        "fundamental": {
            "pe": 28.5,
            "eps": 6.2,
            "roe": 0.45,
            "margen_neto": 0.25,
            "deuda_capital": 0.80,
            "flujo_caja_libre": 1_000_000,
        },
        "precios": precios if precios is not None else pd.DataFrame(),
    }


def test_generar_reporte_devuelve_pdf_valido_para_un_ticker():
    datos = [_ticker_pdf()]

    pdf_bytes = generar_reporte(datos)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1_000


def test_generar_reporte_soporta_varios_tickers_y_datos_incompletos():
    datos = [
        _ticker_pdf("AAPL", "Apple Inc.", "Comprar", 66.0),
        {
            "ticker": "TICKER_SIN_DATOS",
            "nombre": None,
            "sector": None,
            "moneda": None,
            "precio_actual": None,
            "resultado_scoring": {
                "score": None,
                "recomendacion": "Datos insuficientes",
                "peso_evaluado": 0,
                "desglose": [],
            },
            "fundamental": {},
            "precios": pd.DataFrame(),
        },
    ]

    pdf_bytes = generar_reporte(datos)

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1_000


def test_generar_reporte_con_precios_crea_grafica_tecnica():
    fechas = pd.date_range("2024-01-01", periods=60, freq="D")
    cierres = [100 + i * 0.5 for i in range(60)]

    precios = pd.DataFrame(
        {
            "Open": cierres,
            "High": [precio + 1 for precio in cierres],
            "Low": [precio - 1 for precio in cierres],
            "Close": cierres,
            "Volume": [1_000] * 60,
        },
        index=fechas,
    )
    precios.index.name = "Fecha"

    pdf_bytes = generar_reporte([_ticker_pdf(precios=precios)])

    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1_000