# Analizador Bursátil con IA

Aplicación web que analiza acciones cotizadas, compone carteras y emite una
recomendación mediante un motor de *scoring* determinista, con un asistente
conversacional (LLM) que **explica** los resultados sin inventarlos.

> Estado: **esqueleto** (rama `feature/streamlit-base`). La estructura y una app
> mínima ejecutable están montadas; los motores de cálculo aún no.

## Cómo ejecutar

```bash
# 1. Crear y activar un entorno virtual
python -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Arrancar la app
streamlit run app.py
```

Debería abrirse el navegador con las cuatro pestañas mostrando "En construcción".
Si llegas hasta aquí, el armazón funciona.

## Estructura

```
.
├── app.py                  # Punto de entrada Streamlit (solo presenta)
├── config.py               # Parámetros: mercados, ventanas, PESOS del scoring
├── data_layer/             # ÚNICA puerta a Yahoo Finance
│   └── yahoo_client.py
├── domain/                 # Lógica de negocio (sin API, fácil de testear)
│   ├── technical_engine.py     # RSI, MACD, Bollinger, medias móviles
│   ├── fundamental_engine.py   # Ratios financieros
│   ├── scoring_engine.py       # Núcleo determinista de la recomendación
│   └── portfolio_engine.py     # Cartera + métricas del conjunto
├── ui/                     # Pestañas de Streamlit (sin cálculo)
├── reports/                # Generación del PDF
├── llm/                    # Chatbot: parseo de intención + Q&A con grounding
├── tests/                  # pytest (objetivo: 70% sobre domain/)
└── requirements.txt
```

## Regla de oro del proyecto

El LLM **nunca calcula ni inventa**. Solo traduce la petición del usuario a datos
estructurados y explica resultados que ya produjeron los motores deterministas.
La recomendación de compra sale siempre del `scoring_engine`, acompañada del
descargo de responsabilidad. (Detalle completo en `CLAUDE.md`.)

## Orden de construcción

1. `data_layer/yahoo_client.py` — y validar qué datos llegan para tickers de
   EE.UU. y Latinoamérica.
2. Motores de dominio: técnico, fundamental, scoring.
3. `portfolio_engine`.
4. Pestañas de la UI.
5. Reporte PDF.
6. Capa LLM (la última).

Las pruebas y la documentación acompañan cada paso, no van al final.

## Ramas

- `main`: estable.
- `develop`: integración.
- `feature/*`: una por funcionalidad/integrante (ej. `feature/streamlit-base`,
  `feature/technical-engine`).

Commits con [Conventional Commits](https://www.conventionalcommits.org/)
(`feat:`, `fix:`, `docs:`, `test:`), descriptivos y repartidos entre integrantes.
