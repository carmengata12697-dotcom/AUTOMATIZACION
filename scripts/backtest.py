"""Validacion empirica del motor de scoring (backtesting + analisis de sensibilidad).

Autor: Carlos Achiquez (GitHub: Carlos1310823).

Este script ejercita el MOTOR DE SCORING REAL del proyecto
(domain/scoring_engine.py) con los PESOS REALES (config.PESOS_SCORING) sobre un
conjunto de valores reales, y comprueba la ROBUSTEZ del ranking ante distintas
ponderaciones (analisis de sensibilidad de los pesos).

Objetivo academico: aportar evidencia empirica de que la recomendacion del
motor es estable y no depende de un ajuste fino arbitrario de los pesos.

Uso (desde la raiz del repositorio):
    python scripts/backtest.py

Los fundamentales y los indicadores tecnicos incluidos son una FOTOGRAFIA real
(FY2025, datos de mercado obtenidos de Yahoo Finance el 19/06/2026) para que el
script sea reproducible sin depender de la red. Para una corrida en vivo,
sustituye el bloque DATOS por las salidas de technical_engine y
fundamental_engine.
"""
from __future__ import annotations

import json
import os
import sys

# Permite ejecutar el script tanto desde la raiz como desde scripts/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import config
from domain import scoring_engine

# --------------------------------------------------------------------------
# DATOS: fotografia real (FY2025). Tecnicos = ultimos valores de la serie;
# fundamentales = del proveedor. Reemplazables por datos en vivo.
# --------------------------------------------------------------------------
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

# --------------------------------------------------------------------------
# ESCENARIOS de ponderacion para el analisis de sensibilidad.
# --------------------------------------------------------------------------
ESCENARIOS = {
    "Base (proyecto)": config.PESOS_SCORING,
    "Igualitario (12,5 c/u)": {k: 12.5 for k in config.PESOS_SCORING},
    "Pro-tecnico (60/40)": {
        "rsi": 15, "macd": 15, "precio_sobre_sma200": 15, "bollinger_banda_baja": 15,
        "pe_vs_sector": 10, "roe_positivo_creciente": 10, "deuda_capital": 10, "flujo_caja_libre": 10,
    },
    "Pro-fundamental (20/80)": {
        "rsi": 5, "macd": 5, "precio_sobre_sma200": 5, "bollinger_banda_baja": 5,
        "pe_vs_sector": 20, "roe_positivo_creciente": 20, "deuda_capital": 20, "flujo_caja_libre": 20,
    },
}

TICKERS = list(TECNICOS.keys())


def resultados_base() -> dict:
    """Calcula el score con los pesos base para cada ticker."""
    salida = {}
    for tk in TICKERS:
        r = scoring_engine.calcular_score(TECNICOS[tk], FUNDAMENTALES[tk])
        cumplidos = [c["indicador"] for c in r["desglose"] if c["cumplido"]]
        salida[tk] = {
            "score": r["score"],
            "recomendacion": r["recomendacion"],
            "peso_evaluado": r["peso_evaluado"],
            "criterios_cumplidos": cumplidos,
        }
    return salida


def analisis_sensibilidad() -> dict:
    """Recalcula el score de cada ticker bajo cada escenario de pesos."""
    tabla = {}
    for nombre, pesos in ESCENARIOS.items():
        tabla[nombre] = {}
        for tk in TICKERS:
            r = scoring_engine.calcular_score(TECNICOS[tk], FUNDAMENTALES[tk], pesos)
            tabla[nombre][tk] = {"score": r["score"], "recomendacion": r["recomendacion"]}
    return tabla


def ranking(fila: dict) -> list:
    """Orden de tickers por score descendente (para comprobar estabilidad)."""
    return sorted(fila, key=lambda tk: fila[tk]["score"], reverse=True)


def main() -> None:
    base = resultados_base()
    sens = analisis_sensibilidad()

    print("=" * 72)
    print("VALIDACION EMPIRICA - PESOS BASE (config.PESOS_SCORING)")
    print("=" * 72)
    for tk, d in base.items():
        print(f"{tk:>6}:  score={d['score']:>5}  ->  {d['recomendacion']:<8}"
              f"  (peso evaluado={d['peso_evaluado']}/100)")
        print(f"         criterios cumplidos: {d['criterios_cumplidos']}")

    print("\n" + "=" * 72)
    print("ANALISIS DE SENSIBILIDAD DE LOS PESOS")
    print("=" * 72)
    print(f"{'Escenario':<26}" + "".join(f"{tk:>14}" for tk in TICKERS))
    rankings = []
    for nombre, fila in sens.items():
        celdas = "".join(f"{str(fila[tk]['score']) + ' ' + fila[tk]['recomendacion'][:3]:>14}" for tk in TICKERS)
        print(f"{nombre:<26}{celdas}")
        rankings.append(ranking(fila))

    estable = all(r == rankings[0] for r in rankings)
    print("\n" + "-" * 72)
    print(f"Ranking en el escenario base: {' > '.join(rankings[0])}")
    print(f"Ranking ESTABLE en los {len(rankings)} escenarios: "
          f"{'SI' if estable else 'NO'}")
    print("-" * 72)

    salida = {"base": base, "sensibilidad": sens,
              "ranking_estable": estable, "ranking_base": rankings[0]}
    destino = os.path.join(os.path.dirname(__file__), "backtest_resultados.json")
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(salida, f, indent=2, ensure_ascii=False)
    print(f"\nResultados guardados en: {destino}")


if __name__ == "__main__":
    main()
