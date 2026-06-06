"""Pruebas del motor de scoring."""
from domain.scoring_engine import clasificar


def test_clasificar_umbrales():
    assert clasificar(80) == "Comprar"
    assert clasificar(50) == "Neutral"
    assert clasificar(10) == "Evitar"
