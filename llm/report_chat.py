"""Capa LLM (2/2): responde preguntas sobre un informe YA calculado.

REGLA DE ORO (grounding): el LLM recibe los resultados que produjeron los
motores deterministas y SOLO puede explicar o relacionar esos numeros. Tiene
prohibido inventar datos o emitir recomendaciones por su cuenta. La
recomendacion siempre es la del scoring_engine, acompanada del descargo.
Estado: ESQUELETO.
"""
from __future__ import annotations


def responder(pregunta: str, contexto_analisis: dict) -> str:
    """Responde la pregunta usando UNICAMENTE el contexto de analisis dado."""
    raise NotImplementedError
