"""Cliente del LLM: UNICA puerta de entrada a Groq.

Igual que data_layer es la unica capa que habla con Yahoo Finance, este modulo
es el unico que habla con la API del LLM (Groq). El resto de la capa llm/
(intent_parser, report_chat) construye los mensajes y delega aqui el envio.

La clave NO va en el codigo: se lee de la variable de entorno GROQ_API_KEY,
que se carga desde un archivo .env (ignorado por git). Nunca se sube al repo.

Groq ofrece modelos open-source gratuitos (con limites de uso). Por defecto se
usa 'llama-3.3-70b-versatile'; se puede cambiar en config.LLM_MODELO.
"""
from __future__ import annotations

import os

try:  # carga .env si python-dotenv esta instalado (recomendado en requirements)
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import config

# Mensaje unico que se muestra cuando el LLM no esta disponible, para no romper
# la app si falta la clave o la libreria.
_AVISO_SIN_LLM = (
    "El asistente no esta disponible: falta la clave de Groq (GROQ_API_KEY en el "
    "archivo .env) o la libreria 'groq'. El resto de la aplicacion funciona con "
    "normalidad; el analisis y la recomendacion no dependen del chatbot."
)


def disponible() -> bool:
    """True si hay clave configurada y la libreria 'groq' se puede importar."""
    if not os.getenv("GROQ_API_KEY"):
        return False
    try:
        import groq  # noqa: F401
    except Exception:
        return False
    return True


def aviso_no_disponible() -> str:
    """Texto explicativo para mostrar en la UI cuando el LLM no esta listo."""
    return _AVISO_SIN_LLM


def _cliente():
    """Crea el cliente de Groq leyendo la clave del entorno."""
    from groq import Groq
    return Groq(api_key=os.getenv("GROQ_API_KEY"))


def chat(mensajes: list[dict], temperatura: float = 0.2,
         modelo: str | None = None, json_mode: bool = False) -> str:
    """Envia una conversacion al LLM y devuelve el texto de la respuesta.

    Parametros
    ----------
    mensajes : lista de dicts {"role": "system"|"user"|"assistant", "content": ...}
    temperatura : 0 = determinista, valores altos = mas creativo. Baja a proposito:
                  queremos respuestas fieles al contexto, no imaginativas.
    modelo : id del modelo de Groq; por defecto config.LLM_MODELO.
    json_mode : si True, pide a Groq que la respuesta sea JSON valido.

    Si el LLM no esta disponible o la llamada falla, devuelve un mensaje de aviso
    en texto claro (nunca lanza excepcion hacia la UI).
    """
    if not disponible():
        return _AVISO_SIN_LLM

    modelo = modelo or config.LLM_MODELO
    kwargs = {
        "model": modelo,
        "messages": mensajes,
        "temperature": temperatura,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    try:
        respuesta = _cliente().chat.completions.create(**kwargs)
        return (respuesta.choices[0].message.content or "").strip()
    except Exception as e:  # red, limite de uso, modelo retirado, etc.
        return f"No se pudo obtener respuesta del asistente ({type(e).__name__}: {e})."
