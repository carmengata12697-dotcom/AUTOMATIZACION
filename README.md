# Analizador Bursátil con IA

Aplicación web que analiza acciones cotizadas, compara varias a la vez y emite
una recomendación mediante un motor de *scoring* determinista, con un asistente
conversacional (LLM) que **explica** los resultados sin inventarlos.

Proyecto académico — Máster en IA Aplicada a las Finanzas.

## Qué hace

- **Análisis técnico**: RSI, MACD, Bandas de Bollinger y medias móviles, con gráficas interactivas.
- **Análisis fundamental**: P/E, EPS, ROE, deuda/capital, margen neto y flujo de caja libre.
- **Recomendación**: score de 0 a 100 con semáforo (Comprar / Neutral / Evitar) y desglose por indicador, mediante un motor de reglas con pesos transparentes.
- **Cartera**: comparación y ranking de varios tickers a la vez.
- **Reporte PDF**: informe descargable con gráficas, tablas y el desglose del scoring.
- **Asistente (chatbot)**: responde preguntas sobre el informe ya calculado, sin inventar cifras.

Soporta tickers de EE.UU. y Latinoamérica (p. ej. `AAPL`, `ECOPETROL.CL`, `WALMEX.MX`, `PETR4.SA`).

## Cómo ejecutar

```bash
# 1. Entorno virtual
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Dependencias
pip install -r requirements.txt

# 3. (Opcional) Chatbot: copia la plantilla y pon tu clave de Groq
cp .env.example .env              # Windows: copy .env.example .env
#    Clave gratuita en https://console.groq.com/keys

# 4. Arrancar
streamlit run app.py
```

Se abre el navegador con cinco pestañas: Técnico, Fundamental, Recomendación,
Cartera y Asistente. El Asistente necesita la clave de Groq en `.env`; el resto
de la app funciona sin ella.

## Pruebas

```bash
python -m pytest                    # toda la suite
python -m pytest --cov=domain       # con cobertura sobre los motores
```

Los motores de dominio (técnico, fundamental, scoring) tienen pruebas unitarias
con datos sintéticos; cobertura aproximada del 95 % sobre `domain/`.

## Arquitectura

Separada por capas; la lógica de cálculo no vive en la interfaz.

```
.
├── app.py                  # Entrada Streamlit (solo presenta)
├── config.py               # Mercados, ventanas y PESOS/umbrales del scoring
├── data_layer/             # ÚNICA puerta a Yahoo Finance
│   └── yahoo_client.py
├── domain/                 # Lógica de negocio (sin API, testeable)
│   ├── technical_engine.py
│   ├── fundamental_engine.py
│   ├── scoring_engine.py
│   └── portfolio_engine.py     # reservado (la comparación vive hoy en la UI)
├── ui/                     # Pestañas de Streamlit
│   ├── tab_technical.py · tab_fundamental.py · tab_recommendation.py
│   ├── tab_portfolio.py
│   └── tab_chat.py
├── llm/                    # Chatbot: cliente Groq, RAG, intención y Q&A
├── reports/
│   └── pdf_generator.py
├── scripts/
│   └── validar_datos.py
├── tests/
└── requirements.txt
```

## Regla de oro

El LLM **nunca calcula ni inventa**. Solo traduce la petición del usuario a datos
estructurados y explica los resultados que ya produjeron los motores
deterministas. La recomendación (Comprar / Neutral / Evitar) sale siempre del
`scoring_engine`, acompañada del descargo: *esta recomendación es orientativa y
no constituye asesoría financiera profesional*. (Detalle completo en `CLAUDE.md`.)

## Flujo de trabajo en GitHub

- `main`: rama estable e integrada.
- `feature/*`: una rama por funcionalidad, fusionada a `main` mediante Pull Request.
- Commits con [Conventional Commits](https://www.conventionalcommits.org/)
  (`feat:`, `fix:`, `chore:`, `test:`, `docs:`), descriptivos y repartidos entre los integrantes.

## Tecnologías

Python · Streamlit · yfinance · ta · Plotly · reportlab · Groq · pytest