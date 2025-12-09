
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

## top sucursales anterior, talvez se peude eliminar
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


def chart_top5(df):
    return (
        alt.Chart(df)
        .mark_bar(cornerRadius=4)
        .encode(
            x=alt.X("ventas_totales:Q", title="Ventas Totales ($)"),
            y=alt.Y("sucursal:N", sort="-x", title="Sucursal"),
            tooltip=[
                alt.Tooltip("sucursal:N", title="Sucursal"),
                alt.Tooltip("ciudad:N", title="Ciudad"),
                alt.Tooltip("ventas_totales:Q", title="Ventas Totales", format="$.2f"),
                alt.Tooltip("total_ordenes:Q", title="Total Órdenes", format=","),
                alt.Tooltip("ticket_promedio:Q", title="Ticket Promedio", format="$.2f")
            ]
        )
        .properties(
            height=300,
            width="container"
        )
        .configure_mark(opacity=0.9)
    )


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
    
    
    
def chart_participacion_sucursales(df):
    df = df.copy()
    df["label"] = df["nombre"] + " (" + df["ciudad"] + ")"
    
    chart = (
        alt.Chart(df)
        .mark_arc(innerRadius=80)
        .encode(
            theta=alt.Theta("ventas_totales:Q", title="Ventas"),
            color=alt.Color("label:N", title="Sucursal"),
            tooltip=[
                alt.Tooltip("nombre:N", title="Sucursal"),
                alt.Tooltip("ciudad:N", title="Ciudad"),
                alt.Tooltip("ventas_totales:Q", title="Ventas ($)", format=",.2f"),
                alt.Tooltip("porcentaje:Q", title="Participación (%)", format=",.2f"),
            ]
        )
        .properties(title="Participación de Ventas por Sucursal", width=600, height=500)
    )

    st.altair_chart(chart, use_container_width=True)




def chart_crecimiento_anual(df):
    """
    Gráfico de línea para crecimiento anual YoY.
    df debe tener columnas: anio, ventas, crecimiento
    """
    chart = (
        alt.Chart(df)
        .mark_line(point=True, strokeWidth=3)
        .encode(
            x=alt.X("anio:O", title="Año"),
            y=alt.Y("ventas:Q", title="Ventas ($)", axis=alt.Axis(format=",.0f")),
            tooltip=[
                alt.Tooltip("anio:O", title="Año"),
                alt.Tooltip("ventas:Q", title="Ventas Totales", format=",.2f"),
                alt.Tooltip("crecimiento:Q", title="Crecimiento (%)", format=".2f")
            ]
        )
        .properties(
            width=800,
            height=350,
            title="Crecimiento Anual de Ventas (YoY)"
        )
    )
    return chart




def chart_pareto(df):
    """
    Gráfico Pareto 80/20.
    df debe tener columnas: nombre, ventas, porcentaje_acum
    """
    base = alt.Chart(df).encode(
        x=alt.X("nombre:N", sort=df["nombre"].tolist(), title="Producto"),
    )

    barras = base.mark_bar(color="#4c72b0").encode(
        y=alt.Y("ventas:Q", title="Ventas ($)", axis=alt.Axis(format=",.0f")),
        tooltip=[
            alt.Tooltip("nombre:N", title="Producto"),
            alt.Tooltip("ventas:Q", title="Ventas", format=",.2f"),
            alt.Tooltip("porcentaje_acum:Q", title="% Acumulado", format=".2f")
        ]
    )

    linea = base.mark_line(color="red", point=True).encode(
        y=alt.Y("porcentaje_acum:Q", title="Porcentaje acumulado (%)"),
    )

    return (barras + linea).properties(width=900, height=400, title="Análisis de Pareto 80/20")




import altair as alt


def grafico_pareto_productos(df):
    import altair as alt

    # Asegurar que el dataframe viene ordenado
    df = df.sort_values(by="ventas", ascending=False).reset_index(drop=True)

    # === Gráfico de barras ===
    bars = (
        alt.Chart(df)
        .mark_bar(color="#4CC9F0")
        .encode(
            x=alt.X("producto:N", sort=df["producto"].tolist(), title="Producto"),
            y=alt.Y("ventas:Q", title="Ventas ($)"),
            tooltip=[
                alt.Tooltip("producto:N", title="Producto"),
                alt.Tooltip("ventas:Q", title="Ventas ($)", format=",.2f"),
                alt.Tooltip("porcentaje_acum:Q", title="% Acumulado", format=".2%")
            ],
        )
    )

    # === Línea Pareto (PORCENTAJE ACUMULADO) ===
    line = (
        alt.Chart(df)
        .mark_line(point=True, color="#FF6D00", strokeWidth=3)
        .encode(
            x=alt.X("producto:N", sort=df["producto"].tolist()),
            y=alt.Y("porcentaje_acum:Q",
                    axis=alt.Axis(format="%", title="% Acumulado")),
        )
    )

    chart = (
        alt.layer(bars, line)
        .resolve_scale(y="independent")
        .properties(width=1100, height=450, title="Pareto de Ventas por Producto")
    )

    return chart
