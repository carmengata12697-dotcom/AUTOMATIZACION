"""Pruebas del analisis de sensibilidad de los pesos del motor de scoring.

Autor: Carlos Achiquez (GitHub: Carlos1310823).

Complementan a test_scoring.py: alli se prueba el comportamiento con los pesos
por defecto; aqui se ejercita el parametro `pesos` de calcular_score() y se
comprueba que el RANKING entre valores es estable ante distintas ponderaciones
(robustez del modelo multicriterio).
"""
from domain.scoring_engine import calcular_score

# Tres valores filtrados (fotografia real FY2025) usados en la validacion empirica.
TECNICOS = {
    "AAPL":  {"rsi": 56.2, "macd": 2.31, "senal": 1.87, "precio": 201.0, "sma200": 192.4, "banda_baja": 188.7},
    "MSFT":  {"rsi": 61.4, "macd": 5.12, "senal": 5.40, "precio": 470.4, "sma200": 472.1, "banda_baja": 451.2},
    "GOOGL": {"rsi": 54.8, "macd": 1.95, "senal": 1.50, "precio": 178.2, "sma200": 170.6, "banda_baja": 165.3},
}
FUNDAMENTALES = {
    "AAPL":  {"pe": 34.244,  "roe": 1.71422,  "deuda_capital": 1.17053, "flujo_caja_libre": 98_767_000_000},
    "MSFT":  {"pe": 36.467,  "roe": 0.332808, "deuda_capital": 0.167664, "flujo_caja_libre": 71_611_000_000},
    "GOOGL": {"pe": 29.0018, "roe": 0.357048, "deuda_capital": 0.142779, "flujo_caja_libre": 73_266_000_000},
}

PESOS_IGUALITARIO = {
    "rsi": 12.5, "macd": 12.5, "precio_sobre_sma200": 12.5, "bollinger_banda_baja": 12.5,
    "pe_vs_sector": 12.5, "roe_positivo_creciente": 12.5, "deuda_capital": 12.5, "flujo_caja_libre": 12.5,
}
PESOS_PRO_TECNICO = {
    "rsi": 15, "macd": 15, "precio_sobre_sma200": 15, "bollinger_banda_baja": 15,
    "pe_vs_sector": 10, "roe_positivo_creciente": 10, "deuda_capital": 10, "flujo_caja_libre": 10,
}
PESOS_PRO_FUNDAMENTAL = {
    "rsi": 5, "macd": 5, "precio_sobre_sma200": 5, "bollinger_banda_baja": 5,
    "pe_vs_sector": 20, "roe_positivo_creciente": 20, "deuda_capital": 20, "flujo_caja_libre": 20,
}


def _score(tk, pesos=None):
    return calcular_score(TECNICOS[tk], FUNDAMENTALES[tk], pesos)["score"]


def _ranking(pesos=None):
    return sorted(TECNICOS, key=lambda tk: _score(tk, pesos), reverse=True)


def test_pesos_personalizados_cambian_el_score():
    """Pasar pesos distintos a los de config debe alterar el score numerico."""
    base = _score("MSFT")
    pro_fund = _score("MSFT", PESOS_PRO_FUNDAMENTAL)
    assert base != pro_fund


def test_ranking_estable_ante_distintas_ponderaciones():
    """El orden AAPL/GOOGL por encima de MSFT se mantiene en todos los escenarios."""
    escenarios = [None, PESOS_IGUALITARIO, PESOS_PRO_TECNICO, PESOS_PRO_FUNDAMENTAL]
    rankings = [_ranking(p) for p in escenarios]
    # MSFT siempre es el ultimo (el de menor score) en los cuatro escenarios.
    for r in rankings:
        assert r[-1] == "MSFT"


def test_pesos_igualitarios_dan_score_valido():
    """Con pesos iguales el score sigue en el rango 0-100 para los tres valores."""
    for tk in TECNICOS:
        s = _score(tk, PESOS_IGUALITARIO)
        assert s is not None
        assert 0 <= s <= 100


def test_escenario_pro_fundamental_favorece_a_msft():
    """Al dar mas peso a lo fundamental, MSFT sube de Neutral a un score mayor."""
    base = _score("MSFT")
    pro_fund = _score("MSFT", PESOS_PRO_FUNDAMENTAL)
    assert pro_fund > base
