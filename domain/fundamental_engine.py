"""Motor fundamental: organiza e interpreta las metricas financieras.

Recibe el dict que devuelve data_layer.obtener_fundamentales y lo convierte en
una estructura limpia para el scoring y la UI. No inventa valores ausentes:
los deja como None y marca que no estan disponibles.
Estado: ESQUELETO.
"""
from __future__ import annotations


def procesar_fundamentales(crudos: dict) -> dict:
    """Normaliza los ratios fundamentales y senala los no disponibles.

    Devuelve un dict con claves: pe, eps, roe, deuda_capital, margen_neto,
    flujo_caja_libre. Cada valor puede ser un numero o None.
    """
    raise NotImplementedError
