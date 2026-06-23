# Documentación técnica — Analizador Bursátil con IA

> Documentación para desarrolladores del repositorio
> [`carmengata12697-dotcom/AUTOMATIZACION`](https://github.com/carmengata12697-dotcom/AUTOMATIZACION).
> Complementa al `README.md` (visión de usuario) y a `CLAUDE.md` (memoria de decisiones).
> Proyecto académico — Máster en IA Aplicada a las Finanzas.

---

## Índice

1. [Visión general](#1-visión-general)
2. [Arquitectura por capas](#2-arquitectura-por-capas)
3. [Mapa de módulos](#3-mapa-de-módulos)
4. [Flujo de datos extremo a extremo](#4-flujo-de-datos-extremo-a-extremo)
5. [El motor de scoring](#5-el-motor-de-scoring)
6. [La capa LLM (RAG + grounding)](#6-la-capa-llm-rag--grounding)
7. [Configuración](#7-configuración)
8. [Instalación y ejecución](#8-instalación-y-ejecución)
9. [Pruebas](#9-pruebas)
10. [Convenciones y flujo de Git](#10-convenciones-y-flujo-de-git)
11. [Extensión y mantenimiento](#11-extensión-y-mantenimiento)
12. [Marco teórico y referencias](#12-marco-teórico-y-referencias)
13. [Validación empírica del motor de scoring](#13-validación-empírica-del-motor-de-scoring)

---

## 1. Visión general

Aplicación web (Streamlit) que, a partir de uno o varios *tickers*, descarga datos de
Yahoo Finance, calcula indicadores técnicos y fundamentales, los puntúa con un **motor
de scoring determinista**, compara carteras y genera un informe PDF. Encima opera un
**chatbot (LLM)** que explica el informe ya calculado sin inventar cifras.

| Aspecto | Detalle |
|---|---|
| Lenguaje | Python 3 |
| UI | Streamlit |
| Datos de mercado | yfinance (Yahoo Finance) |
| Indicadores técnicos | `ta` |
| Visualización | Plotly (UI) · matplotlib (PDF) |
| Reporte | reportlab |
| LLM | Groq (`llama-3.3-70b-versatile`) |
| Pruebas | pytest · pytest-cov |

**Regla de oro del proyecto:** el LLM nunca calcula ni inventa. La recomendación
(Comprar / Neutral / Evitar) sale **siempre** del `scoring_engine`, nunca del modelo de
lenguaje.

---

## 2. Arquitectura por capas

Dependencias dirigidas: la UI depende del dominio; el dominio no depende de framework ni
de red; el acceso a servicios externos vive tras **una única puerta por servicio**.

```
                         app.py  (orquesta y presenta)
                              │
              ┌───────────────┼───────────────┐
              ▼                               ▼
        ui/  (PRESENTACIÓN)             llm/  (CONVERSACIONAL)
   tab_technical                    groq_client  ← única puerta al LLM
   tab_fundamental                  intent_parser
   tab_recommendation               RAG          ← retrieval + grounding
   tab_portfolio                    report_chat  ← punto de entrada (delega en RAG)
   tab_chat
              │
              ▼
        domain/  (LÓGICA DE NEGOCIO PURA, testeable)
   technical_engine · fundamental_engine
   scoring_engine  ← config.py (pesos/umbrales)
   portfolio_engine (reservado)
              │
              ▼
        data_layer/  (ÚNICA puerta a Yahoo Finance)
   yahoo_client  →  yfinance  →  Yahoo Finance

        reports/pdf_generator   (PDF desde resultados ya calculados)
```

**Reglas de arquitectura (no negociables):**

- Solo `data_layer/yahoo_client.py` importa `yfinance` o llama a una API de mercado.
- Solo `llm/groq_client.py` habla con la API del LLM.
- `domain/` no importa Streamlit, ni red, ni nada de `ui/`. Es lo que se testea.
- `ui/` solo presenta: llama a los motores y renderiza. No contiene lógica de negocio.

---

## 3. Mapa de módulos

| Ruta | Responsabilidad | Notas clave |
|---|---|---|
| `app.py` | Punto de entrada Streamlit; sidebar (tickers, ventana, botón PDF) y 5 pestañas. | Solo orquesta. La generación del PDF se dispara desde el sidebar. |
| `config.py` | Parámetros: mercados, ventanas, `PESOS_SCORING`, umbrales, descargo, `LLM_MODELO`. | Cambiar el comportamiento sin tocar los motores. |
| `data_layer/yahoo_client.py` | `obtener_historico()` y `obtener_fundamentales()`. | Saneo de datos; devuelve estructuras vacías ante fallo; nunca lanza. |
| `domain/technical_engine.py` | RSI, MACD, Bollinger, medias (SMA 20/50/200, EMA 20). | Devuelve series/DataFrames completos para graficar. |
| `domain/fundamental_engine.py` | `procesar_fundamentales()` normaliza ratios. | `deuda_capital` se pasa de escala % a ratio (÷100). |
| `domain/scoring_engine.py` | `calcular_score()`, `clasificar()`. | Núcleo determinista; renormaliza sobre pesos evaluados. |
| `domain/portfolio_engine.py` | Reservado. | Hoy la comparación vive en `ui/tab_portfolio.py`. No importar. |
| `ui/tab_technical.py` | Gráficas de velas + indicadores (Plotly). | Selector de ventana temporal compartido. |
| `ui/tab_fundamental.py` | Tabla de ratios. | — |
| `ui/tab_recommendation.py` | Semáforo, gauge de score y desglose. | — |
| `ui/tab_portfolio.py` | Ranking y comparativa multi-ticker. | Concentra hoy la lógica de comparación. |
| `ui/tab_chat.py` | Pestaña del asistente; construye el contexto y delega en `RAG`. | Contexto cacheado por tupla de tickers. |
| `llm/groq_client.py` | Única puerta al LLM. `disponible()`, `chat()`. | Lee `GROQ_API_KEY` de `.env`; tolerante a fallos. |
| `llm/intent_parser.py` | NL → `{ticker: peso}`. | Fallback por regex si no hay LLM. |
| `llm/RAG.py` | Recuperación + glosario + generación. | Grounding estricto. |
| `llm/report_chat.py` | Punto de entrada del Q&A; reexporta `responder`. | Delega en `RAG`. |
| `reports/pdf_generator.py` | `generar_reporte()`: PDF multi-ticker. | reportlab + matplotlib (`Agg`). |
| `scripts/validar_datos.py` | Validación puntual de la capa de datos. | No es parte de la app. |
| `tests/` | Pruebas unitarias de dominio y LLM. | Datos sintéticos, sin red. |

---

## 4. Flujo de datos extremo a extremo

Ejemplo: una recomendación para un ticker (pestaña Recomendación o Asistente).

```
ticker (str)
  │  data_layer.obtener_historico(ticker, "1y")  ──► DataFrame de precios
  │  data_layer.obtener_fundamentales(ticker)     ──► dict crudo
  ▼
domain.fundamental_engine.procesar_fundamentales(crudo)  ──► dict normalizado
domain.technical_engine.calcular_*(precios)              ──► series/DataFrames
  │  (la UI toma el último valor de cada indicador)
  ▼
domain.scoring_engine.calcular_score(tecnico, fundamental)
  ──► { score, recomendacion, desglose, peso_evaluado, descargo }
  ▼
ui/  renderiza semáforo + gauge + desglose
llm/RAG  (opcional) explica el resultado SIN recalcular
```

Los datos solo fluyen hacia arriba ya calculados. El LLM recibe ese resultado y **solo lo
explica**.

---

## 5. El motor de scoring

`domain/scoring_engine.py` produce un score 0–100 reproducible.

**Criterios y pesos** (`config.PESOS_SCORING`, suman 100):

| Indicador | Categoría | Peso | Se cumple si… |
|---|---|:---:|---|
| `rsi` | Técnico | 10 | `30 < RSI < 70` |
| `macd` | Técnico | 12 | `MACD > señal` |
| `precio_sobre_sma200` | Técnico | 12 | `precio > SMA200` |
| `bollinger_banda_baja` | Técnico | 8 | `precio ≤ banda baja` |
| `pe_vs_sector` | Fundamental | 14 | `0 < P/E < 20` |
| `roe_positivo_creciente` | Fundamental | 14 | `ROE > 0` |
| `deuda_capital` | Fundamental | 12 | `ratio < 1.5` |
| `flujo_caja_libre` | Fundamental | 18 | `FCL > 0` |

**Cálculo:**

```
score = round(peso_cumplido / peso_evaluado * 100, 1)
```

- Solo se suman al denominador los criterios **evaluables** (con dato numérico válido).
- Datos ausentes → se excluyen; **no penalizan**. Se reporta `peso_evaluado`.
- Sin criterios evaluables → `recomendacion = "Datos insuficientes"`, `score = None`.

**Umbrales** (`config`): `≥ 65` Comprar · `40–64` Neutral · `< 40` Evitar.

**Salida (`dict`):** `score`, `recomendacion`, `desglose` (lista por indicador con
`evaluado`/`cumplido`/`peso`/`categoria`), `peso_evaluado`, `descargo`.

> Simplificaciones documentadas: `pe_vs_sector` usa umbral fijo (Yahoo no da mediana
> sectorial fiable) y `roe_positivo_creciente` solo verifica signo positivo (sin histórico
> no se mide crecimiento).

---

## 6. La capa LLM (RAG + grounding)

### Pipeline (`llm/RAG.py`)

1. **Retrieval** — `recuperar(pregunta, contexto)` selecciona los tickers mencionados
   (por símbolo o nombre; si ninguno, todos) y las definiciones del glosario cuyas
   palabras clave aparecen en la pregunta.
2. **Augmentation** — construye el prompt distinguiendo *datos del informe* de
   *definiciones conceptuales*.
3. **Generation** — `groq_client.chat(..., temperatura=0.2)` redacta usando **solo** ese
   contexto.

### Reglas de grounding (system prompt)

- Responder únicamente con datos del contexto; lo ausente se declara como tal.
- No calcular cifras nuevas; sí comparar las existentes.
- La recomendación/score se repite del contexto; nunca se emite una propia.
- Incluir el descargo de `config.DESCARGO_RESPONSABILIDAD`.

### Interpretación de intención (`llm/intent_parser.py`)

`"50% AAPL y el resto entre MSFT y GOOGL"` → `{"AAPL":0.5,"MSFT":0.25,"GOOGL":0.25}`.
"Calcular" = repartir los pesos que el usuario expresa (normalizar a 1). Sin LLM, un
extractor por regex actúa de red de seguridad.

### Tolerancia a fallos

Si falta `GROQ_API_KEY` o la librería `groq`, `groq_client.disponible()` devuelve `False`
y la UI muestra un aviso; **el resto de la app funciona con normalidad**. El chatbot es
opcional.

---

## 7. Configuración

`config.py` (sin secretos):

| Constante | Significado |
|---|---|
| `TICKERS_EJEMPLO` | Ejemplos por mercado (EE.UU., Colombia, México, Brasil). |
| `VENTANAS_TEMPORALES` | `1mo`, `3mo`, `1y`, `5y`. |
| `PESOS_SCORING` | Pesos de los 8 criterios (suman 100). |
| `RSI_MIN`/`RSI_MAX` | `30` / `70`. |
| `PE_ATRACTIVO` | `20`. |
| `ROE_MINIMO` | `0.0`. |
| `DEUDA_CAPITAL_MAX` | `1.5`. |
| `UMBRAL_COMPRAR`/`UMBRAL_NEUTRAL` | `65` / `40`. |
| `DESCARGO_RESPONSABILIDAD` | Texto legal del descargo. |
| `LLM_MODELO` | `llama-3.3-70b-versatile`. |

**Secreto:** `GROQ_API_KEY` va en `.env` (ignorado por git). Ver `.env.example`.

---

## 8. Instalación y ejecución

```bash
# 1. Entorno virtual
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Dependencias
pip install -r requirements.txt

# 3. (Opcional) Chatbot
cp .env.example .env              # Windows: copy .env.example .env
#    Clave gratuita en https://console.groq.com/keys

# 4. Arrancar
streamlit run app.py
```

Cinco pestañas: **Técnico · Fundamental · Recomendación · Cartera · Asistente**.
El Asistente requiere `GROQ_API_KEY`; el resto funciona sin ella.

---

## 9. Pruebas

```bash
python -m pytest                  # toda la suite
python -m pytest --cov=domain     # cobertura sobre los motores
```

| Archivo | Cobertura |
|---|---|
| `tests/test_technical.py` | RSI en rango, SMA de serie constante, orden de Bollinger, columnas MACD, DataFrame vacío. |
| `tests/test_fundamental.py` | Conversión deuda/capital, ROE/margen como fracción, ausentes = `None`, bool ≠ número. |
| `tests/test_scoring.py` | Umbrales, casos extremos (0 y 100), renormalización, estructura del desglose. |
| `tests/test_portfolio.py` | Pesos de cartera suman 1. |
| `tests/test_llm.py` | Normalización de pesos, fallback regex, formato `%`, recuperación RAG por ticker/concepto. |

Objetivo no funcional: **≥ 70 %** sobre `domain/` (superado, ~95 %). Las pruebas usan
datos sintéticos y no tocan la red, incluida la capa RAG.

---

## 10. Convenciones y flujo de Git

- **Ramas:** `main` (estable) ← `develop` (integración) ← `feature/*` (una por
  funcionalidad), fusionadas vía Pull Request.
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/)
  (`feat:`, `fix:`, `chore:`, `test:`, `docs:`), descriptivos y **repartidos por
  integrante** (criterio de evaluación — cada quien commitea su propio trabajo con su
  identidad real).
- **Secretos:** nunca subir `.env` ni claves.

---

## 11. Extensión y mantenimiento

- **Cambiar la fuente de datos:** reescribir solo `data_layer/yahoo_client.py`
  manteniendo las firmas; el dominio no se entera.
- **Cambiar de LLM:** reescribir solo `llm/groq_client.py` y ajustar `config.LLM_MODELO`.
- **Ajustar el scoring:** editar `config.PESOS_SCORING` y los umbrales; no tocar el motor.
- **Activar `portfolio_engine`:** mover la lógica de comparación de `ui/tab_portfolio.py`
  al dominio (composición ponderada y métricas de conjunto) y dejar que la UI solo
  presente.
- **Añadir un indicador al scoring:** añadir su criterio en `scoring_engine._evaluar()`,
  su peso en `config.PESOS_SCORING` y su prueba en `tests/test_scoring.py`.


## 12. Marco teórico y referencias

Cada indicador, ratio y patrón arquitectónico del proyecto se apoya en literatura reconocida. Esta sección resume el fundamento teórico; las referencias completas, en formato **APA 7.ª edición**, están al final.

### Análisis técnico

- **RSI (Índice de Fuerza Relativa).** Oscilador de momento propuesto por Wilder (1978), en escala 0–100, con umbrales de sobrecompra (70) y sobreventa (30). El proyecto considera saludable un RSI entre 30 y 70 y usa el suavizado exponencial de Wilder (periodo 14).
- **MACD.** Indicador de tendencia y momento creado por Appel (2005): diferencia de EMA(12) y EMA(26) con señal EMA(9). El cruce del MACD por encima de su señal indica impulso alcista.
- **Bandas de Bollinger.** Envolventes de volatilidad descritas por Bollinger (2001): SMA(20) ± 2σ. El proyecto usa la banda inferior como señal de precio «barato» a corto plazo.
- **SMA 200.** Referente clásico de tendencia de largo plazo (Murphy, 1999): precio por encima de la SMA 200 ⇒ tendencia primaria alcista.

### Análisis fundamental

La doctrina moderna se remonta a Graham y Dodd (2009) y fue sistematizada para la valoración por Damodaran (2012).

- **P/E.** Múltiplo de valoración más utilizado (Damodaran, 2012); umbral atractivo fijo 0–20 (sustituye a la mediana sectorial, no disponible de forma fiable).
- **ROE.** Rentabilidad sobre recursos propios; se exige ROE > 0 (Graham & Dodd, 2009).
- **Deuda/Capital.** Indicador de apalancamiento; se premian ratios < 1,5.
- **Flujo de caja libre.** Base de la valoración por descuento de flujos (Damodaran, 2012); recibe el mayor peso (18) por su importancia.

### Modelo de scoring multicriterio

El motor aplica una **suma ponderada** (weighted scoring model): cada criterio aporta su peso si se cumple y el resultado se normaliza sobre los criterios evaluables. Frente a un modelo de caja negra, prioriza transparencia y auditabilidad: cada punto del score es trazable hasta un criterio y su umbral.

### IA generativa con grounding (RAG)

El asistente usa **Retrieval-Augmented Generation**, formalizado por Lewis et al. (2020): el LLM responde condicionado a contexto recuperado en lugar de su memoria paramétrica, lo que reduce alucinaciones. Es la garantía de que el modelo razona sobre los números ya calculados sin inventarlos.

### Arquitectura de software

La organización por capas con dependencias dirigidas al dominio sigue la **Clean Architecture** de Martin (2017): la lógica de negocio no depende de frameworks ni de fuentes externas, lo que la hace testeable y estable.

### Referencias (APA 7.ª ed.)

**Análisis técnico y fundamental**

- Appel, G. (2005). *Technical analysis: Power tools for active investors*. FT Prentice Hall.
- Bollinger, J. (2001). *Bollinger on Bollinger Bands*. McGraw-Hill.
- Damodaran, A. (2012). *Investment valuation: Tools and techniques for determining the value of any asset* (3.ª ed.). John Wiley & Sons.
- Graham, B., & Dodd, D. L. (2009). *Security analysis* (6.ª ed.). McGraw-Hill. (Obra original publicada en 1934)
- Murphy, J. J. (1999). *Technical analysis of the financial markets: A comprehensive guide to trading methods and applications*. New York Institute of Finance.
- Wilder, J. W. (1978). *New concepts in technical trading systems*. Trend Research.

**Inteligencia artificial e ingeniería de software**

- Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. En *Advances in Neural Information Processing Systems* (Vol. 33, pp. 9459–9474). Curran Associates. https://proceedings.neurips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html
- Martin, R. C. (2017). *Clean architecture: A craftsman's guide to software structure and design*. Prentice Hall.

**Herramientas y bibliotecas**

- Padroni, D. (2018). *ta: Technical Analysis Library in Python* [Software]. https://github.com/bukosabino/ta
- Streamlit Inc. (2024). *Streamlit documentation*. https://docs.streamlit.io
- yfinance. (2024). *yfinance: Download market data from Yahoo! Finance's API* [Software]. https://github.com/ranaroussi/yfinance

---

## 13. Validación empírica del motor de scoring

Para comprobar que el motor produce resultados coherentes y robustos, se ejecutó sobre datos reales usando el código de dominio del propio proyecto (`domain/scoring_engine.py`) y los pesos de `config.py`, **sin modificación alguna**. El script reproducible es `backtest.py`.

### Metodología

- **Muestra:** AAPL, MSFT y GOOGL (datos técnicos y fundamentales completos).
- **Datos técnicos:** serie diaria de cierres del último año (≈ 264 sesiones, jun-2025 – jun-2026). RSI (Wilder, 14), MACD (12/26/9), SMA 200 y banda inferior de Bollinger (20, 2σ), con las mismas fórmulas de la librería `ta`.
- **Datos fundamentales:** P/E, ROE, deuda/capital y FCL del ejercicio FY2025.
- **Fuente:** Yahoo Finance, obtenidos el 19 de junio de 2026 a través del proveedor financiero de Perplexity.

### Resultados con los pesos base

Los tres valores se evaluaron sobre el 100 % de los criterios (cobertura completa):

| Ticker | Score | Recomendación | Criterios cumplidos (5/8) |
|--------|:-----:|---------------|---------------------------|
| AAPL   | 66,0  | **Comprar**   | RSI, precio>SMA200, ROE>0, deuda/capital, FCL |
| GOOGL  | 66,0  | **Comprar**   | RSI, precio>SMA200, ROE>0, deuda/capital, FCL |
| MSFT   | 54,0  | **Neutral**   | RSI, ROE>0, deuda/capital, FCL |

AAPL y GOOGL alcanzan «Comprar» (66) al cumplir los cinco criterios de mayor peso, incluida la tendencia alcista de largo plazo. MSFT obtiene «Neutral» (54): pese a fundamentales sólidos, su precio cotizaba por debajo de la SMA 200 y su MACD por debajo de la señal en la fecha de corte. El motor no premia a una buena empresa en tramo bajista de corto/medio plazo —comportamiento esperado.

### Análisis de sensibilidad de los pesos

Se recalculó el score bajo cuatro esquemas de ponderación, manteniendo intactos datos y umbrales:

| Esquema de pesos | AAPL | MSFT | GOOGL |
|------------------|------|------|-------|
| Base (proyecto)         | 66,0 · Comprar | 54,0 · Neutral | 66,0 · Comprar |
| Igualitario (12,5 c/u)  | 62,5 · Neutral | 50,0 · Neutral | 62,5 · Neutral |
| Pro-técnico (60/40)     | 60,0 · Neutral | 45,0 · Neutral | 60,0 · Neutral |
| Pro-fundamental (20/80) | 70,0 · Comprar | 65,0 · Comprar | 70,0 · Comprar |

### Conclusiones de la validación

- **Ranking estable.** En los cuatro esquemas, AAPL y GOOGL empatan y se sitúan siempre por encima de MSFT: el orden relativo no depende de los pesos elegidos.
- **Sensibilidad acotada.** Las puntuaciones se mueven en un rango estrecho (AAPL/GOOGL 60–70; MSFT 45–65). Ningún valor cruza de «Comprar» a «Evitar»; los cambios de etiqueta se limitan a la frontera Comprar/Neutral.
- **Coherencia teórica.** El esquema pro-fundamental eleva a las tres empresas (fundamentales sólidos); el pro-técnico las penaliza (señales técnicas débiles en la fecha de corte).
- **Trazabilidad.** Todos los resultados se obtuvieron ejecutando el código de producción sin modificarlo.

*Limitaciones:* muestra reducida (tres valores de un mismo mercado y sector) y un único corte temporal; la cobertura de fundamentales para mercados latinoamericanos en la fuente fue parcial.

---

*Descargo: las recomendaciones son orientativas, generadas automáticamente a partir de
reglas predefinidas. No constituyen asesoría financiera profesional.*
