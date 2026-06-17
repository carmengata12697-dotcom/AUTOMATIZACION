# CLAUDE.md — Contexto del proyecto para Claude Code

Este archivo es la memoria del proyecto. Si retomas el trabajo desde Claude Code
(u otra sesión), lee esto primero y respétalo.

## Qué es el proyecto

Aplicación web (Streamlit) que, a partir de uno o varios tickers, descarga datos
de Yahoo Finance, calcula indicadores técnicos y fundamentales, los puntúa con un
motor de *scoring* determinista, compone carteras ponderadas y permite descargar
un informe en PDF. Encima hay un chatbot (LLM) que ayuda a componer la cartera y
responde preguntas sobre el informe ya calculado.

## Arquitectura por capas

- **`data_layer/`** — ÚNICA capa que habla con Yahoo Finance (yfinance). Ningún
  otro módulo importa yfinance ni llama a APIs externas.
- **`domain/`** — lógica de negocio pura (técnico, fundamental, scoring, cartera).
  Sin dependencias de framework. Es lo que se testea.
- **`ui/`** — Streamlit. Solo presenta; no calcula nada.
- **`reports/`** — genera el PDF a partir de resultados ya calculados.
- **`llm/`** — capa conversacional.

## REGLA DE ORO (no negociable)

El LLM **nunca calcula ni inventa**:

1. `llm/intent_parser.py` traduce lenguaje natural a `{ticker: peso}`. Nada más.
2. El Q&A es un sistema **RAG** (`llm/RAG.py`): recupera del informe ya calculado
   solo lo relevante a la pregunta (tickers + glosario de conceptos), aumenta el
   prompt y genera la respuesta. Usa **únicamente** esos resultados; tiene
   prohibido generar cifras o juicios que no estén en el contexto (*grounding*).
   `llm/report_chat.py` se mantiene como punto de entrada y delega en `RAG.py`.
3. La recomendación Comprar/Neutral/Evitar **sale del `scoring_engine`**, nunca
   del LLM. Siempre acompañada del descargo de `config.DESCARGO_RESPONSABILIDAD`.

Si en algún momento dudas entre "que el LLM razone" y "que el LLM invente": puede
razonar y relacionar números dados, no puede producir los números.

## Orden de construcción

1. `data_layer/yahoo_client.py` (+ verificar cobertura de tickers LatAm).
2. `domain/technical_engine.py`, `fundamental_engine.py`, `scoring_engine.py`.
3. `domain/portfolio_engine.py` (sustituye al "comparador" de la propuesta).
4. `ui/` (pestañas).
5. `reports/pdf_generator.py`.
6. `llm/` (última fase).

Pruebas (`pytest`, objetivo 70% sobre `domain/`) y documentación en paralelo.

## Decisiones tomadas (no revertir sin acuerdo del grupo)

- **Streamlit, no Flask.** El repo tenía un arranque en Flask (`routes.py`,
  `models.py`, `configuración.py`...). Se descarta. Esos archivos se eliminarán
  en un commit aparte y documentado cuando todo el grupo lo sepa; no borrarlos
  en silencio.
- **`ta` en vez de `pandas-ta`** para indicadores técnicos: `pandas-ta` ha dado
  problemas de compatibilidad con pandas/numpy recientes. Si se prefiere volver a
  `pandas-ta`, validar antes que instala y corre.
- **Nombres de archivo en inglés y sin acentos** (`app.py`, `config.py`,
  `data_layer/`...). Evita problemas de codificación entre sistemas (Windows /
  Linux / macOS) que provocan los nombres con tildes.
- Los **pesos del scoring** viven en `config.PESOS_SCORING`, no incrustados en el
  código del motor.
- **Groq como proveedor del LLM** (modelos open-source gratuitos, p. ej.
  `llama-3.3-70b-versatile`) en lugar de Anthropic: cuota gratuita suficiente para
  el proyecto. Toda la comunicación con la API pasa por `llm/groq_client.py`
  (única puerta al LLM, igual que `data_layer` lo es a Yahoo). El modelo se
  configura en `config.LLM_MODELO`.

## Convenciones

- Ramas: `main` (estable) ← `develop` (integración) ← `feature/*`.
- Commits: Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`),
  descriptivos, frecuentes y repartidos por integrante (es criterio de
  evaluación).
- La API key del LLM va en `.env` (ya ignorado por git). Nunca subirla.

## Aviso sobre el equipo

Proyecto en grupo. La participación individual se evalúa por el historial de
commits, así que cada integrante debe commitear su propio trabajo.
