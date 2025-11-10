
# charts/sales_charts.py
import altair as alt
import pandas as pd
from .commons import MONTH_NAME

def chart_monthly_bars(df: pd.DataFrame, title: str, show_avg: bool=True):
    base = alt.Chart(df).encode(
        x=alt.X('mes_nombre:N', sort=MONTH_NAME, title='Mes'),
        y=alt.Y('total_ventas:Q', title='Total de Ventas'),
        tooltip=[
            alt.Tooltip('mes_nombre:N', title='Mes'),
            alt.Tooltip('total_ventas:Q', title='Ventas ($)', format=',.2f')
        ]
    )
    barras = base.mark_bar()
    layers = [barras]

    if show_avg and not df.empty:
        promedio = df["total_ventas"].mean()
        layers += [
            alt.Chart(pd.DataFrame({'y': [promedio]})).mark_rule(strokeDash=[6,3]).encode(y='y:Q'),
            alt.Chart(pd.DataFrame({'y': [promedio]})).mark_text(
                text=f"Promedio: ${promedio:,.2f}", dx=5, dy=-5
            ).encode(y='y:Q')
        ]

    return alt.layer(*layers).properties(width=900, height=420, title=title)

def chart_comparison_lines(df: pd.DataFrame, title: str):
    return (
        alt.Chart(df)
        .mark_line(point=True, strokeWidth=3)
        .encode(
            x=alt.X('periodo:N', sort=None, title='Periodo (Año-Mes)'),
            y=alt.Y('total_ventas:Q', title='Ventas ($)'),
            color=alt.Color('sucursal:N', title='Sucursal'),
            tooltip=[
                alt.Tooltip('sucursal:N', title='Sucursal'),
                alt.Tooltip('anio:O', title='Año'),
                alt.Tooltip('mes_nombre:N', title='Mes'),
                alt.Tooltip('total_ventas:Q', title='Ventas ($)', format=',.2f')
            ]
        )
        .properties(width=1000, height=380, title=title)
    )
    

# [NUEVO] Barras de error (IC95%) por sucursal
def chart_branch_means_ci(df_stats, title: str = "Media mensual con IC 95% por sucursal"):
    """
    df_stats: DataFrame con columnas ['sucursal','mean','li','ls','n'] numéricas.
    Dibuja un punto en la media y una barra vertical (li..ls) como errorbar.
    """
    import altair as alt
    import pandas as pd

    # Asegurar que los valores sean numéricos
    for col in ["mean", "li", "ls", "n"]:
        if col in df_stats.columns:
            df_stats[col] = pd.to_numeric(df_stats[col], errors="coerce")

    base = alt.Chart(df_stats).encode(
        x=alt.X("sucursal:N", title="Sucursal")
    )

    # Barra de error explícita (línea vertical)
    error_rule = base.mark_rule(color="red", strokeWidth=3).encode(
        y="li:Q",
        y2="ls:Q",
        tooltip=[
            alt.Tooltip("sucursal:N", title="Sucursal"),
            alt.Tooltip("mean:Q", title="Media ($)", format=",.2f"),
            alt.Tooltip("li:Q", title="IC95% LI", format=",.2f"),
            alt.Tooltip("ls:Q", title="IC95% LS", format=",.2f"),
            alt.Tooltip("n:Q", title="n"),
        ]
    )

    # Punto de la media
    point = base.mark_point(size=120, color="white", filled=True).encode(
        y="mean:Q"
    )

    return (error_rule + point).properties(
        width=700, height=420, title=title
    )



def chart_small_multiples(df: pd.DataFrame, title: str):
    return (
        alt.Chart(df).mark_bar()
        .encode(
            x=alt.X('periodo:N', sort=None, title='Periodo'),
            y=alt.Y('total_ventas:Q', title='Ventas ($)'),
            color=alt.Color('sucursal:N', legend=None),
            facet=alt.Facet('sucursal:N', columns=1, title=None),
            tooltip=[
                alt.Tooltip('sucursal:N', title='Sucursal'),
                alt.Tooltip('anio:O', title='Año'),
                alt.Tooltip('mes_nombre:N', title='Mes'),
                alt.Tooltip('total_ventas:Q', title='Ventas ($)', format=',.2f')
            ]
        )
        .properties(width=900, height=220, title=title)
    )
    
    
    
import streamlit as st

def grafico_ranking_sucursales(df, top_n=5):
    """Gráfico de ranking de sucursales con formato de miles y tooltip."""
    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X("net:Q", title="Ventas Totales ($)", axis=alt.Axis(format=",.0f")),
            y=alt.Y("nombre:N", sort="-x", title="Sucursal"),
            tooltip=[
                alt.Tooltip("nombre:N", title="Sucursal"),
                alt.Tooltip("net_formateado:N", title="Ventas Totales"),
            ],
            color=alt.Color("net:Q", scale=alt.Scale(scheme="blues"), legend=None)
        )
        .properties(width=700, height=400, title=f"🏆 Top {top_n} Sucursales por Ventas Totales")
    )
    st.altair_chart(chart, use_container_width=True)
  


def grafico_ranking_generico(df, titulo="Ranking"):
    """
    Espera columnas: ['nombre','ventas','cantidad'] y opcionales
    'ventas_formateadas','cantidad_formateada' (si las pasas, se usan en tooltip).
    """
    # Asegurar tipos numéricos
    for c in ("ventas", "cantidad"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    chart = (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
        .encode(
            x=alt.X("ventas:Q", title="Ventas ($)", axis=alt.Axis(format=",.0f")),
            y=alt.Y("nombre:N", sort="-x", title="Elemento"),
            tooltip=[
                alt.Tooltip("nombre:N", title="Nombre"),
                alt.Tooltip("ventas:Q", title="Ventas ($)", format=",.2f"),
                alt.Tooltip("cantidad:Q", title="Cantidad", format=",.0f"),
            ],
            color=alt.Color("nombre:N", legend=None)
        )
        .properties(width=720, height=380, title=titulo)
    )
    st.altair_chart(chart, use_container_width=True)