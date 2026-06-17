"""Capa LLM (2/2): responde preguntas sobre un informe YA calculado.

REGLA DE ORO (grounding): el LLM recibe los resultados que produjeron los
motores deterministas y SOLO puede explicar o relacionar esos números. Tiene
prohibido inventar datos o emitir recomendaciones por su cuenta.

La implementación es un sistema RAG (Retrieval-Augmented Generation) y vive en
`llm/RAG.py`: recupera los datos relevantes del informe más un glosario de
conceptos, aumenta el prompt y genera la respuesta. Este módulo se mantiene como
el punto de entrada con el nombre acordado en la arquitectura del proyecto y
delega en RAG.
"""
from __future__ import annotations

from llm.RAG import construir_contexto_texto, responder  # noqa: F401  (re-export)

__all__ = ["responder", "construir_contexto_texto"]
