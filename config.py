"""Configuracion central del proyecto.
 
Aqui viven los parametros que NO son logica de negocio: mercados de ejemplo,
ventanas temporales, los PESOS del motor de scoring y sus UMBRALES.
Centralizarlos aqui permite ajustarlos sin tocar los motores.
"""
 
TICKERS_EJEMPLO = {
    "EE.UU.": ["AAPL", "GOOGL", "MSFT"],
    "Colombia": ["ECOPETROL.CL"],
    "Mexico": ["WALMEX.MX"],
    "Brasil": ["PETR4.SA"],
}
 
VENTANAS_TEMPORALES = {
    "1 mes": "1mo",
    "3 meses": "3mo",
    "1 ano": "1y",
    "5 anos": "5y",
}
 
# Pesos del motor de scoring (suman 100). Fuente: propuesta del proyecto.
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
 
# --- Umbrales de cada criterio del scoring ---
RSI_MIN = 30          # RSI por encima de este valor (no sobrevendido extremo)
RSI_MAX = 70          # ...y por debajo de este (no sobrecomprado)
PE_ATRACTIVO = 20     # P/E por debajo => atractivo. Sustituye a la mediana
                      # sectorial, que Yahoo no proporciona de forma fiable.
ROE_MINIMO = 0.0      # ROE por encima de 0 => rentabilidad positiva
DEUDA_CAPITAL_MAX = 1.5  # ratio deuda/capital por debajo => salud financiera
 
# Umbrales de recomendacion (sobre 100)
UMBRAL_COMPRAR = 65   # >= 65  -> Comprar
UMBRAL_NEUTRAL = 40   # 40-64  -> Neutral ; < 40 -> Evitar
 
DESCARGO_RESPONSABILIDAD = (
    "Esta recomendacion es orientativa y se genera de forma automatica a partir "
    "de reglas predefinidas. No constituye asesoria financiera profesional."
)

# --- Capa LLM (chatbot) ---
# Cerebro del chatbot: Groq (modelos open-source gratuitos, con limites de uso).
# La clave NO va aqui: se lee de GROQ_API_KEY (archivo .env, ignorado por git).
# Modelo por defecto: Llama 3.3 70B (buena calidad, gratuito en Groq). Alternativa
# mas rapida: "llama-3.1-8b-instant".
LLM_MODELO = "llama-3.3-70b-versatile"