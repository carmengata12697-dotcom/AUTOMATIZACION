"""RAG — Retrieval-Augmented Generation para el asistente del informe.

Implementa el patrón RAG en su versión mínima y honesta:

  1. RECUPERACIÓN (retrieval): de todo lo que se ha calculado, selecciona solo lo
     relevante para la pregunta — los tickers que el usuario menciona y los
     conceptos del glosario que aparecen en su pregunta.
  2. AUMENTACIÓN (augmentation): construye el prompt añadiendo ese contexto
     recuperado.
  3. GENERACIÓN (generation): el LLM (Groq) redacta la respuesta a partir de ese
     contexto.

REGLA DE ORO (grounding): los NÚMEROS salen siempre del contexto calculado por
los motores deterministas; el LLM no los inventa. El glosario solo aporta
definiciones conceptuales (qué es el RSI, el P/E…), nunca datos de la acción.
"""
from __future__ import annotations

import config
from llm import groq_client

# --- Base de conocimiento: definiciones conceptuales de los indicadores ---
# Son textos curados (no datos de mercado). El paso de recuperación añade solo
# los que la pregunta menciona, para que el asistente explique conceptos sin que
# el LLM los improvise de memoria.
_GLOSARIO = [
    {"claves": ["rsi", "fuerza relativa", "sobrecompra", "sobreventa"],
     "texto": "RSI (Índice de Fuerza Relativa): oscilador de 0 a 100. Por debajo "
              "de 30 indica sobreventa y por encima de 70 sobrecompra. El scoring "
              "valora positivamente que esté entre 30 y 70."},
    {"claves": ["macd"],
     "texto": "MACD: diferencia entre dos medias móviles exponenciales del precio. "
              "Se considera alcista cuando la línea MACD supera a su línea de "
              "señal."},
    {"claves": ["bollinger", "banda", "bandas"],
     "texto": "Bandas de Bollinger: una media móvil y dos bandas situadas a ±2 "
              "desviaciones típicas. Que el precio toque la banda baja sugiere que "
              "está relativamente barato a corto plazo."},
    {"claves": ["sma", "media móvil", "medias móviles", "tendencia", "sma200"],
     "texto": "SMA 200: media móvil simple de 200 sesiones; marca la tendencia de "
              "largo plazo. Que el precio esté por encima se interpreta como "
              "tendencia alcista."},
    {"claves": ["pe", "p/e", "per", "precio beneficio"],
     "texto": f"P/E (precio entre beneficio): cuánto se paga por cada unidad de "
              f"beneficio. Cuanto más bajo, más atractivo; el scoring usa el umbral "
              f"P/E < {config.PE_ATRACTIVO}."},
    {"claves": ["roe", "rentabilidad", "recursos propios"],
     "texto": "ROE (rentabilidad sobre recursos propios): beneficio que genera la "
              "empresa con el capital de sus accionistas. Cuanto más alto y "
              "positivo, mejor."},
    {"claves": ["margen", "margen neto"],
     "texto": "Margen neto: porción de los ingresos que queda como beneficio tras "
              "todos los gastos. Un margen mayor indica más eficiencia."},
    {"claves": ["deuda", "apalancamiento", "deuda capital"],
     "texto": "Deuda/Capital: nivel de endeudamiento frente a los recursos "
              "propios. En este proyecto, por debajo de "
              f"{config.DEUDA_CAPITAL_MAX} se considera saludable."},
    {"claves": ["flujo de caja", "caja libre", "fcf", "flujo"],
     "texto": "Flujo de caja libre: efectivo que genera la empresa después de sus "
              "inversiones. Que sea positivo indica solidez financiera."},
    {"claves": ["score", "puntuación", "puntuacion", "recomendación", "recomendacion"],
     "texto": "Score (0-100): porcentaje del peso de los criterios cumplidos sobre "
              f"los que se han podido evaluar. {config.UMBRAL_COMPRAR} o más es "
              f"Comprar, entre {config.UMBRAL_NEUTRAL} y {config.UMBRAL_COMPRAR - 1} "
              "Neutral, y por debajo Evitar."},
]

_SYSTEM = f"""Eres el asistente de un analizador bursátil. Ayudas al usuario a \
entender un informe que YA ha sido calculado por motores deterministas.

PREMISAS (obligatorias, no negociables):
1. Responde ÚNICAMENTE con los datos del CONTEXTO que se te entrega. Si un dato \
no aparece, di con claridad que no está disponible; NO lo inventes ni lo estimes.
2. NO calcules indicadores ni cifras que no estén en el contexto. Puedes comparar \
y relacionar los números que SÍ aparecen.
3. La recomendación (Comprar / Neutral / Evitar) y el score salen del motor de \
scoring, no de ti. Si te piden una recomendación, repite la del contexto; nunca \
emitas una propia distinta.
4. Cuando des una recomendación o consejo de inversión, recuerda el descargo: \
"{config.DESCARGO_RESPONSABILIDAD}"
5. Responde en español, de forma breve, clara y honesta. Si la pregunta no tiene \
que ver con los datos del informe, dilo con amabilidad y reconduce."""


def _fmt(valor, sufijo: str = "", decimales: int = 2) -> str:
    """Formatea un número o devuelve 'sin dato' si es None/NaN."""
    if valor is None:
        return "sin dato"
    try:
        return f"{float(valor):.{decimales}f}{sufijo}"
    except (TypeError, ValueError):
        return str(valor)


def _pct(valor, decimales: int = 1) -> str:
    """Formatea una fracción (0.45) como porcentaje ('45.0%'). 'sin dato' si falta."""
    if valor is None:
        return "sin dato"
    try:
        return f"{float(valor) * 100:.{decimales}f}%"
    except (TypeError, ValueError):
        return str(valor)


def _serializar_ticker(ticker: str, datos: dict) -> str:
    """Convierte el análisis de un ticker en un bloque de texto compacto."""
    tec = datos.get("tecnico") or {}
    fun = datos.get("fundamental") or {}
    sco = datos.get("scoring") or {}

    lineas = [f"### {ticker} — {datos.get('nombre') or 'N/D'}"]
    if datos.get("sector"):
        lineas.append(f"Sector: {datos['sector']} | Moneda: {datos.get('moneda') or 'N/D'}")
    lineas.append(f"Precio actual: {_fmt(datos.get('precio') or tec.get('precio'))}")

    lineas.append(
        "Técnico -> "
        f"RSI: {_fmt(tec.get('rsi'))}, "
        f"MACD: {_fmt(tec.get('macd'), decimales=3)} (señal {_fmt(tec.get('senal'), decimales=3)}), "
        f"SMA200: {_fmt(tec.get('sma200'))}, "
        f"Banda baja Bollinger: {_fmt(tec.get('banda_baja'))}"
    )
    lineas.append(
        "Fundamental -> "
        f"P/E: {_fmt(fun.get('pe'))}, "
        f"EPS: {_fmt(fun.get('eps'))}, "
        f"ROE: {_pct(fun.get('roe'))}, "
        f"Margen neto: {_pct(fun.get('margen_neto'))}, "
        f"Deuda/Capital: {_fmt(fun.get('deuda_capital'), decimales=3)}, "
        f"Flujo caja libre: {_fmt(fun.get('flujo_caja_libre'), decimales=0)}"
    )

    score = sco.get("score")
    lineas.append(
        f"Scoring -> Recomendación: {sco.get('recomendacion', 'N/D')}, "
        f"Score: {('%.1f/100' % score) if score is not None else 'N/D'}, "
        f"Peso evaluado: {_fmt(sco.get('peso_evaluado'), decimales=0)}/100"
    )

    desglose = sco.get("desglose") or []
    if desglose:
        partes = []
        for d in desglose:
            if not d.get("evaluado"):
                estado = "sin dato"
            else:
                estado = "cumplido" if d.get("cumplido") else "no cumplido"
            partes.append(f"{d.get('indicador')} ({d.get('peso')}%): {estado}")
        lineas.append("Desglose -> " + "; ".join(partes))

    return "\n".join(lineas)


def construir_contexto_texto(contexto_analisis: dict) -> str:
    """Serializa TODO el análisis a texto plano (sin filtrar). Útil en pruebas."""
    tickers = (contexto_analisis or {}).get("tickers") or {}
    if not tickers:
        return "No hay ningún ticker analizado todavía."
    bloques = [_serializar_ticker(t, d) for t, d in tickers.items()]
    return "\n\n".join(bloques)


def recuperar(pregunta: str, contexto_analisis: dict) -> str:
    """Paso de RECUPERACIÓN: selecciona lo relevante para la pregunta.

    - Tickers: incluye los que la pregunta menciona (por símbolo o nombre); si no
      menciona ninguno, incluye todos.
    - Glosario: incluye solo los conceptos cuyas palabras clave aparezcan en la
      pregunta.
    Devuelve el bloque de contexto ya aumentado, listo para el prompt.
    """
    q = (pregunta or "").lower()
    tickers = (contexto_analisis or {}).get("tickers") or {}

    if not tickers:
        return "No hay ningún ticker analizado todavía."

    # Recuperar tickers relevantes (los nombrados; si ninguno, todos).
    relevantes = {}
    for ticker, datos in tickers.items():
        nombre = (datos.get("nombre") or "").lower()
        if ticker.lower() in q or (nombre and nombre.split()[0] in q):
            relevantes[ticker] = datos
    if not relevantes:
        relevantes = tickers

    bloques_tickers = [_serializar_ticker(t, d) for t, d in relevantes.items()]

    # Recuperar conceptos del glosario mencionados en la pregunta.
    conceptos = [g["texto"] for g in _GLOSARIO
                 if any(clave in q for clave in g["claves"])]

    partes = ["DATOS DEL INFORME (recuperados):", "\n\n".join(bloques_tickers)]
    if conceptos:
        partes.append("\nCONCEPTOS RELEVANTES (solo definiciones, no datos de la "
                      "acción):\n- " + "\n- ".join(conceptos))
    return "\n".join(partes)


def responder(pregunta: str, contexto_analisis: dict) -> str:
    """Pipeline RAG completo: recupera, aumenta el prompt y genera la respuesta.

    Usa ÚNICAMENTE el contexto recuperado del análisis ya calculado. Si el LLM no
    está disponible, devuelve un aviso claro (la app no depende del chatbot).
    """
    if not (pregunta or "").strip():
        return "Escribe una pregunta sobre el análisis y te respondo."

    if not groq_client.disponible():
        return groq_client.aviso_no_disponible()

    contexto_recuperado = recuperar(pregunta, contexto_analisis)
    contenido_usuario = (
        f"{contexto_recuperado}\n\n"
        f"PREGUNTA DEL USUARIO:\n{pregunta}"
    )

    return groq_client.chat(
        mensajes=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": contenido_usuario},
        ],
        temperatura=0.2,
    )
