"""Capa LLM (2/2): responde preguntas sobre un informe YA calculado.

REGLA DE ORO (grounding): el LLM recibe los resultados que produjeron los
motores deterministas y SOLO puede explicar o relacionar esos numeros. Tiene
prohibido inventar datos o emitir recomendaciones por su cuenta. La
recomendacion siempre es la del scoring_engine, acompanada del descargo.

Este modulo no descarga ni calcula nada: recibe un `contexto_analisis` ya
construido por el codigo determinista (la UI), lo serializa a texto legible y
se lo pasa al LLM junto con las reglas de comportamiento.
"""
from __future__ import annotations

import config
from llm import groq_client

_SYSTEM = f"""Eres el asistente de un analizador bursatil. Ayudas al usuario a \
entender un informe que YA ha sido calculado por motores deterministas.

PREMISAS (obligatorias, no negociables):
1. Responde UNICAMENTE con los datos del CONTEXTO que se te entrega. Si un dato \
no aparece en el contexto, di claramente que no esta disponible; NO lo inventes \
ni lo estimes.
2. NO calcules indicadores nuevos ni cifras que no esten en el contexto. Puedes \
comparar y relacionar los numeros que SI aparecen.
3. La recomendacion (Comprar / Neutral / Evitar) y el score salen del motor de \
scoring, no de ti. Si te piden una recomendacion, repite la del contexto; nunca \
emitas una propia distinta.
4. Cuando des una recomendacion o consejo de inversion, recuerda el descargo: \
"{config.DESCARGO_RESPONSABILIDAD}"
5. Responde en espanol, de forma breve, clara y honesta. Si la pregunta no tiene \
que ver con los datos del informe, dilo con amabilidad y reconduce."""


def _fmt(valor, sufijo: str = "", decimales: int = 2) -> str:
    """Formatea un numero o devuelve 'sin dato' si es None/NaN."""
    if valor is None:
        return "sin dato"
    try:
        return f"{float(valor):.{decimales}f}{sufijo}"
    except (TypeError, ValueError):
        return str(valor)


def _serializar_ticker(ticker: str, datos: dict) -> str:
    """Convierte el analisis de un ticker en un bloque de texto compacto."""
    tec = datos.get("tecnico") or {}
    fun = datos.get("fundamental") or {}
    sco = datos.get("scoring") or {}

    lineas = [f"### {ticker} — {datos.get('nombre') or 'N/D'}"]
    if datos.get("sector"):
        lineas.append(f"Sector: {datos['sector']} | Moneda: {datos.get('moneda') or 'N/D'}")
    lineas.append(f"Precio actual: {_fmt(datos.get('precio') or tec.get('precio'))}")

    lineas.append(
        "Tecnico -> "
        f"RSI: {_fmt(tec.get('rsi'))}, "
        f"MACD: {_fmt(tec.get('macd'), decimales=3)} (senal {_fmt(tec.get('senal'), decimales=3)}), "
        f"SMA200: {_fmt(tec.get('sma200'))}, "
        f"Banda baja Bollinger: {_fmt(tec.get('banda_baja'))}"
    )
    lineas.append(
        "Fundamental -> "
        f"P/E: {_fmt(fun.get('pe'))}, "
        f"EPS: {_fmt(fun.get('eps'))}, "
        f"ROE: {_fmt(fun.get('roe'), decimales=3)}, "
        f"Margen neto: {_fmt(fun.get('margen_neto'), decimales=3)}, "
        f"Deuda/Capital: {_fmt(fun.get('deuda_capital'), decimales=3)}, "
        f"Flujo caja libre: {_fmt(fun.get('flujo_caja_libre'), decimales=0)}"
    )

    score = sco.get("score")
    lineas.append(
        f"Scoring -> Recomendacion: {sco.get('recomendacion', 'N/D')}, "
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
    """Serializa el dict de analisis a texto plano para el LLM (tambien util en tests)."""
    tickers = (contexto_analisis or {}).get("tickers") or {}
    if not tickers:
        return "No hay ningun ticker analizado todavia."
    bloques = [_serializar_ticker(t, d) for t, d in tickers.items()]
    return "\n\n".join(bloques)


def responder(pregunta: str, contexto_analisis: dict) -> str:
    """Responde la pregunta usando UNICAMENTE el contexto de analisis dado.

    `contexto_analisis` tiene la forma:
        {"tickers": {"AAPL": {"nombre", "sector", "moneda", "precio",
                              "tecnico": {...}, "fundamental": {...},
                              "scoring": {...}}, ...}}

    Devuelve la respuesta en texto. Si el LLM no esta disponible, devuelve un
    aviso claro (la app no depende del chatbot para funcionar).
    """
    if not (pregunta or "").strip():
        return "Escribe una pregunta sobre el analisis y te respondo."

    if not groq_client.disponible():
        return groq_client.aviso_no_disponible()

    contexto_texto = construir_contexto_texto(contexto_analisis)
    contenido_usuario = (
        f"CONTEXTO DEL INFORME (datos ya calculados):\n{contexto_texto}\n\n"
        f"PREGUNTA DEL USUARIO:\n{pregunta}"
    )

    return groq_client.chat(
        mensajes=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": contenido_usuario},
        ],
        temperatura=0.2,
    )
