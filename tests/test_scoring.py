"""Pruebas del motor de scoring."""
from domain.scoring_engine import calcular_score, clasificar
 
TODOS_TECNICOS_OK = {"rsi": 50, "macd": 2, "senal": 1, "precio": 100, "sma200": 90, "banda_baja": 101}
TODOS_FUND_OK = {"pe": 10, "roe": 0.2, "deuda_capital": 0.5, "flujo_caja_libre": 1000}
 
 
def test_clasificar_umbrales():
    assert clasificar(80) == "Comprar"
    assert clasificar(65) == "Comprar"
    assert clasificar(64.9) == "Neutral"
    assert clasificar(40) == "Neutral"
    assert clasificar(39.9) == "Evitar"
 
 
def test_todos_los_criterios_cumplidos_da_100():
    r = calcular_score(TODOS_TECNICOS_OK, TODOS_FUND_OK)
    assert r["score"] == 100
    assert r["recomendacion"] == "Comprar"
    assert r["peso_evaluado"] == 100
 
 
def test_ningun_criterio_cumplido_da_0():
    tecnico = {"rsi": 80, "macd": 1, "senal": 2, "precio": 80, "sma200": 90, "banda_baja": 70}
    fund = {"pe": 30, "roe": -0.1, "deuda_capital": 2.0, "flujo_caja_libre": -100}
    r = calcular_score(tecnico, fund)
    assert r["score"] == 0
    assert r["recomendacion"] == "Evitar"
 
 
def test_renormaliza_cuando_faltan_fundamentales():
    # Solo tecnicos evaluables (peso 42); falla el MACD (12), cumplen rsi(10)+sma200(12)+bollinger(8)=30.
    tecnico = {"rsi": 50, "macd": 1, "senal": 2, "precio": 100, "sma200": 90, "banda_baja": 101}
    r = calcular_score(tecnico, {})
    assert r["peso_evaluado"] == 42
    assert r["score"] == round(30 / 42 * 100, 1)
 
 
def test_sin_datos_devuelve_insuficiente():
    r = calcular_score({}, {})
    assert r["score"] is None
    assert r["recomendacion"] == "Datos insuficientes"
 
 
def test_estructura_del_desglose():
    r = calcular_score(TODOS_TECNICOS_OK, TODOS_FUND_OK)
    assert len(r["desglose"]) == 8
    for item in r["desglose"]:
        assert {"indicador", "categoria", "peso", "evaluado", "cumplido"} <= item.keys()
    assert "descargo" in r