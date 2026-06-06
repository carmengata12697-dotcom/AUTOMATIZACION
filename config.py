"""Configuración central del proyecto.

Aquí viven los parámetros que NO son lógica de negocio: mercados de ejemplo,
ventanas temporales y los PESOS del motor de scoring (tomados de la propuesta).
Centralizarlos aquí permite ajustarlos sin tocar los motores y facilita las
pruebas.
"""

# Tickers de ejemplo por mercado. La app acepta cualquier ticker válido en Yahoo.
TICKERS_EJEMPLO = {
    "EE.UU.": ["AAPL", "GOOGL", "MSFT"],
    "Colombia": ["ECOPETROL.CL"],
    "Mexico": ["WALMEX.MX"],
    "Brasil": ["PETR4.SA"],
}

# Ventanas temporales para el analisis tecnico (etiqueta -> periodo yfinance)
VENTANAS_TEMPORALES = {
    "1 mes": "1mo",
    "3 meses": "3mo",
    "1 ano": "1y",
    "5 anos": "5y",
}

# Pesos del motor de scoring (suman 100). Fuente: propuesta del proyecto.
# El motor de scoring (domain/scoring_engine.py) consume este diccionario.
PESOS_SCORING = {
    "rsi": 10,
    "macd": 12,
    "precio_sobre_sma200": 12,
    "bollinger_banda_baja": 8,
    "pe_vs_sector": 14,
    "roe_positivo_creciente": 14,
    "deuda_capital": 12,
    "flujo_caja_libre": 18,
}

# Umbrales de recomendacion (sobre 100)
UMBRAL_COMPRAR = 65   # >= 65  -> Comprar
UMBRAL_NEUTRAL = 40   # 40-64  -> Neutral ; < 40 -> Evitar

DESCARGO_RESPONSABILIDAD = (
    "Esta recomendacion es orientativa y se genera de forma automatica a partir "
    "de reglas predefinidas. No constituye asesoria financiera profesional."
)
