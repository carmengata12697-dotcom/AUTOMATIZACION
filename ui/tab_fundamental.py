"""Pestaña de Análisis Fundamental. Solo presenta; no calcula."""
import pandas as pd
import streamlit as st

from data_layer.yahoo_client import obtener_fundamentales
from domain.fundamental_engine import procesar_fundamentales


def _fmt(valor, tipo="num", decimales=2, sufijo=""):
    """Formatea un valor o devuelve '—' si es None."""
    if valor is None:
        return "—"
    if tipo == "pct":
        return f"{valor * 100:.{decimales}f}%"
    if tipo == "millones":
        return f"{valor / 1_000_000:,.0f} M"
    return f"{valor:,.{decimales}f}{sufijo}"


def _render_ticker(ticker: str) -> None:
    """Renderiza el análisis fundamental completo para un ticker."""
    with st.spinner(f"Descargando fundamentales de {ticker}…"):
        crudos = obtener_fundamentales(ticker)
        datos = procesar_fundamentales(crudos)

    nombre = datos.get("nombre") or ticker
    moneda = datos.get("moneda") or ""
    sector = datos.get("sector") or "—"
    fcf = datos.get("flujo_caja_libre")

    st.markdown(f"### {nombre}")
    st.caption(f"Sector: **{sector}** | Moneda de reporte: **{moneda}**")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Valoración")
        st.metric("P/E Ratio (TTM)", _fmt(datos.get("pe"), decimales=1))
        st.metric("EPS (TTM)", _fmt(datos.get("eps"), decimales=2, sufijo=f" {moneda}"))

    with col2:
        st.markdown("#### Rentabilidad")
        st.metric("ROE", _fmt(datos.get("roe"), tipo="pct"))
        st.metric("Margen Neto", _fmt(datos.get("margen_neto"), tipo="pct"))

    st.divider()

    col3, col4 = st.columns(2)
    with col3:
        st.markdown("#### Salud Financiera")
        deuda = datos.get("deuda_capital")
        deuda_str = _fmt(deuda, decimales=2) if deuda is not None else "—"
        delta_deuda = "✅ OK (< 1.5)" if deuda is not None and deuda < 1.5 else ("⚠️ Alto (≥ 1.5)" if deuda is not None else None)
        st.metric("Deuda / Capital", deuda_str, delta_deuda)

    with col4:
        st.markdown("#### Flujo de Caja")
        fcf_str = _fmt(fcf, tipo="millones", sufijo=f" {moneda}") if fcf is not None else "—"
        delta_fcf = "✅ Positivo" if fcf is not None and fcf > 0 else ("🔴 Negativo" if fcf is not None else None)
        st.metric("Flujo de Caja Libre", fcf_str, delta_fcf)

    st.divider()

    st.markdown("#### Resumen de métricas")
    filas = {
        "P/E Ratio (TTM)": _fmt(datos.get("pe"), decimales=2),
        "EPS (TTM)": _fmt(datos.get("eps"), decimales=2),
        "ROE": _fmt(datos.get("roe"), tipo="pct"),
        "Margen Neto": _fmt(datos.get("margen_neto"), tipo="pct"),
        "Deuda / Capital": _fmt(datos.get("deuda_capital"), decimales=2),
        "Flujo de Caja Libre": _fmt(fcf, tipo="millones", sufijo=f" {moneda}") if fcf is not None else "—",
        "Sector": sector,
        "Moneda": moneda,
    }
    df_tabla = pd.DataFrame(filas.items(), columns=["Métrica", "Valor"])
    st.dataframe(df_tabla, use_container_width=True, hide_index=True)


def render(tickers: list) -> None:
    st.subheader("📊 Análisis Fundamental")

    if not tickers:
        st.warning("Introduce al menos un ticker en el panel lateral.")
        return

    if len(tickers) == 1:
        _render_ticker(tickers[0])
    else:
        tabs = st.tabs([f"📊 {t}" for t in tickers])
        for tab, ticker in zip(tabs, tickers):
            with tab:
                _render_ticker(ticker)