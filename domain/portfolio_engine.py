"""Motor de cartera.
 
ESTADO ACTUAL
-------------
En esta version, la logica de comparacion y ranking de varios tickers vive en la
capa de presentacion (ui/tab_portfolio.py), que llama directamente a los motores
tecnico, fundamental y de scoring para cada activo seleccionado.
 
Este modulo queda reservado para una futura extraccion de esa logica al dominio:
composicion de cartera ponderada (pesos por activo) y metricas de conjunto
(correlacion entre activos, diversificacion y riesgo agregado), de modo que la UI
solo presente y no calcule.
 
Mientras tanto no expone funciones y no debe importarse.
"""