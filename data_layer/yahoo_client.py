"""Capa de datos: UNICA puerta de entrada a Yahoo Finance.
 
REGLA DE ARQUITECTURA: ningun otro modulo debe importar yfinance ni llamar a
una API externa. Todo pasa por aqui. Asi se puede cambiar la fuente de datos
sin tocar la logica de negocio, y las pruebas pueden simular esta capa.
"""
from __future__ import annotations
 
import pandas as pd
import yfinance as yf
 
# Columnas de precio que normalizamos y exponemos al resto del proyecto.
_COLUMNAS_PRECIO = ["Open", "High", "Low", "Close", "Volume"]
 
 
def obtener_historico(ticker: str, periodo: str = "1y") -> pd.DataFrame:
    """Devuelve el historico de precios y volumen de un ticker.
 
    periodo: '1mo', '3mo', '1y', '5y' (ver config.VENTANAS_TEMPORALES).
    Devuelve un DataFrame con columnas Open, High, Low, Close, Volume indexado
    por fecha. Descarta las filas sin cierre (algunos mercados, como la
    cotizacion colombiana, traen el ultimo dia vacio), de modo que el ultimo
    cierre siempre sea un valor real. Si el ticker no existe o falla la
    descarga, devuelve un DataFrame vacio (nunca lanza excepcion ni inventa
    datos).
    """
    try:
        datos = yf.Ticker(ticker).history(period=periodo, auto_adjust=True)
    except Exception:
        return pd.DataFrame(columns=_COLUMNAS_PRECIO)
 
    if datos is None or datos.empty:
        return pd.DataFrame(columns=_COLUMNAS_PRECIO)
 
    columnas = [c for c in _COLUMNAS_PRECIO if c in datos.columns]
    datos = datos[columnas].copy()
 
    # Eliminar dias sin cierre (huecos de datos), p. ej. el ultimo dia de
    # algunas cotizaciones latinoamericanas que llega vacio.
    if "Close" in datos.columns:
        datos = datos.dropna(subset=["Close"])
 
    if datos.empty:
        return pd.DataFrame(columns=_COLUMNAS_PRECIO)
 
    datos.index.name = "Fecha"
    return datos
 
def verificar_disponibilidad_yahoo(ticker_referencia: str = "AAPL") -> dict:
    """Verifica si Yahoo Finance responde y reporta la fecha del último dato
    No interpreta si el mercado está abierto o cerrado. Un dato del último día
    hábil sigue representando una fuente disponible, incluso en fines de semana
    o fuera del horario de negociación
    """
    try:
        datos = yf.Ticker(ticker_referencia).history(
            period="5d",
            auto_adjust=True,
        )
    except Exception:
        return {
            "estado": "error",
            "fecha_ultimo_dato": None,
            "mensaje": "No fue posible consultar Yahoo Finance",
        }

    if datos is None or datos.empty or "Close" not in datos.columns:
        return {
            "estado": "sin_datos",
            "fecha_ultimo_dato": None,
            "mensaje": "No se recibieron datos desde Yahoo Finance",
        }

    datos_validos = datos.dropna(subset=["Close"])

    if datos_validos.empty:
        return {
            "estado": "sin_datos",
            "fecha_ultimo_dato": None,
            "mensaje": "No se recibieron datos desde Yahoo Finance",
        }

    fecha_ultimo_dato = pd.Timestamp(datos_validos.index[-1]).date().isoformat()

    return {
        "estado": "disponible",
        "fecha_ultimo_dato": fecha_ultimo_dato,
        "mensaje": "Fuente de datos disponible",
    }

# Mapa: clave limpia del proyecto -> clave cruda en yfinance .info
_MAPA_FUNDAMENTALES = {
    "pe": "trailingPE",
    "eps": "trailingEps",
    "roe": "returnOnEquity",
    "deuda_capital": "debtToEquity",
    "margen_neto": "profitMargins",
    "flujo_caja_libre": "freeCashflow",
}
 
 
def obtener_fundamentales(ticker: str) -> dict:
    """Devuelve metricas fundamentales en un diccionario limpio.
 
    Claves: pe, eps, roe, deuda_capital, margen_neto, flujo_caja_libre, mas
    nombre, moneda y sector como contexto. Cada valor puede ser un numero/cadena
    o None si Yahoo no lo proporciona. NUNCA inventa valores.
 
    Nota de escalas (importante para el motor de scoring):
      - roe y margen_neto vienen como fraccion (0.27 = 27%).
      - deuda_capital viene en escala de porcentaje (79.5 equivale a un ratio
        0.795); para el criterio "deuda/capital < 1.5" hay que dividir entre 100.
      - flujo_caja_libre va en la moneda de reporte de la empresa, que puede no
        coincidir con la moneda del precio; el scoring solo mira su signo.
    """
    base = {clave: None for clave in _MAPA_FUNDAMENTALES}
    base.update({"nombre": None, "moneda": None, "sector": None})
 
    try:
        info = yf.Ticker(ticker).info
    except Exception:
        return base
 
    if not isinstance(info, dict) or not info:
        return base
 
    for clave_limpia, clave_yahoo in _MAPA_FUNDAMENTALES.items():
        base[clave_limpia] = info.get(clave_yahoo)
 
    base["nombre"] = info.get("longName") or info.get("shortName")
    base["moneda"] = info.get("currency")
    base["sector"] = info.get("sector")
    return base