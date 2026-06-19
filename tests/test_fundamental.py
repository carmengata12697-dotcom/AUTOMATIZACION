"""Pruebas del motor fundamental (normalizacion de ratios)."""
from domain.fundamental_engine import procesar_fundamentales


def test_deuda_capital_se_convierte_a_ratio():
    # Yahoo entrega deuda/capital en escala de porcentaje; debe dividirse entre 100.
    r = procesar_fundamentales({"deuda_capital": 79.5})
    assert r["deuda_capital"] == 79.5 / 100


def test_roe_y_margen_se_conservan_como_fraccion():
    r = procesar_fundamentales({"roe": 0.12, "margen_neto": 0.07})
    assert r["roe"] == 0.12
    assert r["margen_neto"] == 0.07


def test_valores_ausentes_se_conservan_como_none():
    r = procesar_fundamentales({"deuda_capital": None, "pe": None})
    assert r["deuda_capital"] is None
    assert r["pe"] is None


def test_dict_vacio_devuelve_todo_none():
    r = procesar_fundamentales({})
    assert r["pe"] is None and r["roe"] is None and r["deuda_capital"] is None


def test_bool_no_se_trata_como_numero():
    # True es subclase de int; no debe convertirse en ratio.
    r = procesar_fundamentales({"deuda_capital": True})
    assert r["deuda_capital"] is None
