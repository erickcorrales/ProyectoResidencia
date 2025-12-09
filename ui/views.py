# ui/views.py
import os, sys
import streamlit as st
import pandas as pd
from calendar import monthrange
import altair as alt

from data.queries import get_top5_sucursales
from services.analytics import preparar_top5

from data.queries import get_top_pizzas

from data.queries import get_pareto_productos
from services.analytics import calcular_pareto_productos
from charts.sales_charts import grafico_pareto_productos


# ===== Ajuste de rutas para imports =====
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(THIS_DIR)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ===== IMPORTS =====

def _debug_toggle():
    return st.sidebar.checkbox("🛠️ Modo debug", value=False, help="Muestra datos y trazas internas")

from charts.sales_charts import (
    chart_monthly_bars, chart_comparison_lines, chart_small_multiples,
    grafico_ranking_sucursales, grafico_ranking_generico
)

from data.queries import (
    get_ventas, get_sucursales, get_monthly_total, get_monthly_sales,
    get_table_range_diag, get_top5_sucursales, get_top_pizzas
)

from services.analytics import (
    calcular_kpis_generales, summary_two_branches, t_test_two_branches
)

from services.transforms import (
    add_month_name, add_period, wide_table_month_branch, fill_missing_months,
    month_pairs_between, fill_missing_months_range
)
from charts.sales_charts import (
    chart_monthly_bars, chart_comparison_lines, chart_small_multiples,
    grafico_ranking_sucursales, grafico_ranking_generico
)

# ===============================================================
# 🔧 UTILIDADES GENERALES
# ===============================================================
def compute_date_range(anio_inicio, anio_fin, months_dict, mes_inicio, mes_fin):
    m_ini = months_dict[mes_inicio]
    m_fin = months_dict[mes_fin]
    if (anio_inicio > anio_fin) or (anio_inicio == anio_fin and m_ini > m_fin):
        st.error("Rango inválido: el inicio debe ser ≤ al fin (año/mes).")
        st.stop()

    fecha_inicio = f"{anio_inicio}-{m_ini:02d}-01"
    dia_fin = monthrange(anio_fin, m_fin)[1]
    fecha_fin = f"{anio_fin}-{m_fin:02d}-{dia_fin:02d}"
    return fecha_inicio, fecha_fin, m_ini, m_fin


# ===============================================================
# 🧮 CACHES
# ===============================================================
@st.cache_data(show_spinner=False)
def _cached_monthly_total(fi, ff, sucs_sel):
    return get_monthly_total(fi, ff, sucs_sel)

@st.cache_data(show_spinner=False)
def _cached_monthly_sales(fi, ff, sucs_sel):
    return get_monthly_sales(fi, ff, sucs_sel)

@st.cache_data(ttl=900, show_spinner=False)
def _load_data():
    ventas = get_ventas()
    sucursales = get_sucursales()[["id_sucursal", "nombre", "ciudad"]]

    df = ventas.merge(sucursales, left_on="sucursal", right_on="id_sucursal", how="left")
    df["fecha_compra"] = pd.to_datetime(df["fecha_compra"])
    df["anio"] = df["fecha_compra"].dt.year
    df["mes"] = df["fecha_compra"].dt.month_name()
    return df

@st.cache_data(ttl=1200, show_spinner=False)
def _sucursales_lookup():
    sucs = get_sucursales()[["id_sucursal", "nombre"]].copy()
    id2name = dict(zip(sucs["id_sucursal"], sucs["nombre"]))
    name2id = dict(zip(sucs["nombre"], sucs["id_sucursal"]))
    return sucs, id2name, name2id

@st.cache_data(ttl=600, show_spinner=False)
def _get_top_pizzas_cached(top_n: int, ids: tuple[int, ...]):
    return get_top_pizzas(top_n=top_n, sucursales_ids=list(ids))

@st.cache_data(ttl=600, show_spinner=False)
def _compute_kpis(df):
    return calcular_kpis_generales(df)

# ===============================================================
# 📊 VISTA KPIs
# ===============================================================
def kpis_view():
    st.title("📊 Indicadores Clave de Rendimiento (KPIs)")
    st.markdown("Explora las métricas principales y rankings de desempeño por sucursal y producto.")

    with st.spinner("Cargando datos y calculando KPIs..."):
        df = _load_data()
        total_ventas, total_ordenes, ticket_promedio = _compute_kpis(df)

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Ventas Totales", f"${total_ventas:,.2f}")
    col2.metric("🧾 Órdenes Totales", f"{total_ordenes:,}")
    col3.metric("🎟️ Ticket Promedio", f"${ticket_promedio:,.2f}")
    
    
    

    
    
    ####
    # ================================
# 📈 CRECIMIENTO ANUAL (YoY)
# ================================
    from services.analytics import calcular_crecimiento_anual
    from charts.sales_charts import chart_crecimiento_anual

    st.markdown("## 📈 Crecimiento Anual (YoY)")

    df_yoy = calcular_crecimiento_anual(df)

    st.dataframe(
        df_yoy[["anio", "ventas_formato", "crecimiento_formato"]]
            .rename(columns={
                "anio": "Año",
                "ventas_formato": "Ventas Totales",
                "crecimiento_formato": "Crecimiento"
            }),
        use_container_width=True
    )

    st.altair_chart(chart_crecimiento_anual(df_yoy), use_container_width=True)


    st.markdown("---")
    st.subheader("🏆 Top 5 Sucursales por Ventas Totales")

    ranking = (
        df.groupby("nombre", as_index=False)["net"]
        .sum()
        .sort_values(by="net", ascending=False)
        .head(5)
    )
    ranking["net"] = ranking["net"].round(2)
    ranking["net_formateado"] = ranking["net"].apply(lambda x: f"${x:,.2f}")

    st.dataframe(
        ranking[["nombre", "net_formateado"]].rename(columns={"nombre": "Sucursal", "net_formateado": "Ventas Totales"}),
        use_container_width=True
    )

    grafico_ranking_sucursales(ranking)
    st.caption(f"📊 Datos procesados: {len(df):,} filas, {df['nombre'].nunique()} sucursales totales.")
    
    
    


    
    
    
    # ===============================================================
#  Gráfico Pareto de Ventas por Sucursal
# ===============================================================
    st.markdown("## 📈 Análisis Pareto de Ventas por Sucursal")

    df_pareto = (
        df.groupby("nombre", as_index=False)["net"]
        .sum()
        .sort_values(by="net", ascending=False)
    )

    df_pareto["ventas"] = df_pareto["net"]
    df_pareto["ventas_acum"] = df_pareto["ventas"].cumsum()
    df_pareto["porcentaje_acum"] = df_pareto["ventas_acum"] / df_pareto["ventas"].sum()
    
    

    # 🔹 Gráfico de barras (ventas por sucursal)
    bars = alt.Chart(df_pareto).mark_bar(color="#4CC9F0").encode(
        x=alt.X("nombre:N", sort=df_pareto["nombre"].tolist(), title="Sucursal"),
        y=alt.Y("ventas:Q", title="Ventas ($)"),
        tooltip=[
            alt.Tooltip("nombre:N", title="Sucursal"),
            alt.Tooltip("ventas:Q", title="Ventas ($)", format=","),
            alt.Tooltip("porcentaje_acum:Q", title="% Acumulado", format=".2%")
        ]
    )

    # 🔸 Línea acumulada (% Pareto)
    line = alt.Chart(df_pareto).mark_line(point=True, color="#FF6D00", strokeWidth=3).encode(
        x=alt.X("nombre:N", sort=df_pareto["nombre"].tolist()),
        y=alt.Y("porcentaje_acum:Q", title="% Acumulado", axis=alt.Axis(format="%")),
    )

    pareto_chart = alt.layer(bars, line).resolve_scale(
        y="independent"  # eje independiente para line y bars
    ).properties(
        width=900,
        height=450,
        title="Pareto de Ventas por Sucursal"
    )
    
    

    st.altair_chart(pareto_chart, use_container_width=True)


    
    
    
        # =======================================================
    #  PARTICIPACIÓN POR SUCURSAL (%)
    # =======================================================
    st.markdown("---")
    st.subheader("🏙️ Participación por Sucursal en las Ventas Totales")

    # Agrupación por sucursal y ciudad
    participacion = (
        df.groupby(["nombre", "ciudad"])
        .agg(
            ventas_totales=("net", "sum"),
            total_ordenes=("order_id", "nunique"),
        )
        .reset_index()
    )

    # Ticket promedio
    participacion["ticket_promedio"] = (
        participacion["ventas_totales"] / participacion["total_ordenes"]
    )

    # Porcentaje sobre total global
    total_global = participacion["ventas_totales"].sum()
    participacion["porcentaje"] = (
        participacion["ventas_totales"] / total_global * 100
    )

    # Tabla formateada
    participacion_fmt = participacion.assign(
        ventas_totales=lambda x: x["ventas_totales"].apply(lambda v: f"${v:,.2f}"),
        total_ordenes=lambda x: x["total_ordenes"].apply(lambda v: f"{v:,}"),
        ticket_promedio=lambda x: x["ticket_promedio"].apply(lambda v: f"${v:,.2f}"),
        porcentaje=lambda x: x["porcentaje"].apply(lambda v: f"{v:.2f}%")
    )

    st.dataframe(
        participacion_fmt,
        use_container_width=True
    )


    # Gráfico donut
    from charts.sales_charts import chart_participacion_sucursales
    chart_participacion_sucursales(participacion)

    
    
    
    
    

# ===============================================================
#  RANKING DE PRODUCTOS (PIZZAS)
# ===============================================================
def ranking_pizzas_view():
   # st.warning(" DEBUG: Entró a la función ranking_pizzas_view()")
   # st.warning("Entró correctamente a ranking_pizzas_view()")
    st.subheader("🍕 Ranking de Productos (Pizzas)")

    top_n = st.number_input("📈 Mostrar Top N productos", min_value=1, max_value=50, value=5, step=1)
    sucs_df, id2name, name2id = _sucursales_lookup()
    opciones_sucs = sucs_df["nombre"].tolist()

    sucs_sel_names = st.multiselect(
        "🏙️ Filtrar por sucursal (opcional)",
        options=opciones_sucs,
        help="Si lo dejas vacío, mostrará el ranking general de todas las sucursales."
    )
    sucs_sel_ids = tuple(name2id[n] for n in sucs_sel_names)

    with st.spinner("Consultando base de datos..."):
        df = _get_top_pizzas_cached(int(top_n), sucs_sel_ids)

    

    df["ventas_formateadas"] = df["ventas"].apply(lambda x: f"${x:,.2f}")
    df["cantidad_formateada"] = df["cantidad"].apply(lambda x: f"{x:,.0f}")

    st.markdown("### 🔢 Resultados")
    st.dataframe(
        df[["nombre", "cantidad_formateada", "ventas_formateadas"]]
          .rename(columns={"nombre": "Producto", "cantidad_formateada": "Cantidad", "ventas_formateadas": "Ventas ($)"}),
        use_container_width=True
    )

    st.markdown("### 📊 Visualización")
    titulo = f"Top {top_n} pizzas más vendidas" + ("" if not sucs_sel_names else f" — filtro: {', '.join(sucs_sel_names)}")
    grafico_ranking_generico(df, titulo=titulo)
    
    
    
            # ===============================================================
#  PARETO DE PRODUCTOS (PIZZAS)
# ===============================================================
    st.markdown("---")
    st.header("🍕 Análisis Pareto de Ventas por Producto")

    with st.spinner("Generando Pareto de productos..."):
        df_prod = get_pareto_productos()

        # 🔥 FORZAR ORDEN ANTES DEL CÁLCULO
        df_prod = df_prod.sort_values(by="ventas", ascending=False).reset_index(drop=True)

        df_prod = calcular_pareto_productos(df_prod)

    st.caption(f"🔎 Datos procesados: {len(df_prod):,} productos analizados.")

    tabla_pareto = df_prod.copy()

    tabla_pareto["ventas"] = tabla_pareto["ventas"].apply(lambda x: f"${x:,.2f}")
    tabla_pareto["ventas_acum"] = tabla_pareto["ventas_acum"].apply(lambda x: f"${x:,.2f}")
    tabla_pareto["porcentaje_acum"] = tabla_pareto["porcentaje_acum"].apply(lambda x: f"{x*100:.2f}%")

    st.dataframe(
        tabla_pareto[["producto", "ventas", "ventas_acum", "porcentaje_acum"]],
        use_container_width=True
)
    
    

    chart_prod = grafico_pareto_productos(df_prod)
    st.altair_chart(chart_prod, use_container_width=True)




    


def view_placeholder(title: str):
    """
    Placeholder genérico usado para vistas que aún no están implementadas.
    Permite que app.py las invoque sin errores de importación.
    """
    st.info(f"🚧 Placeholder para '{title}'. Aquí podrás agregar otra vista personalizada.")
    
    
    
# ===============================================================
#  COMPARAR SUCURSALES 
# ===============================================================
from services.analytics import get_branch_comparison_data
from charts.sales_charts import chart_comparison_lines


def view_comparar_sucursales(fecha_inicio, fecha_fin, sucursales, map_sucursales):

    st.subheader("🏙️ Comparar Sucursales")

    # Validación mínima
    if len(sucursales) < 2:
        st.warning("⚠️ Debes seleccionar al menos **2 sucursales** para comparar.")
        return

    st.write("🔍 Rango seleccionado:", fecha_inicio, "→", fecha_fin)

    # Carga de datos
    with st.spinner("Cargando datos comparativos..."):
        df = get_branch_comparison_data(fecha_inicio, fecha_fin, sucursales)

    if df.empty:
        st.error("No hay datos para las sucursales y rango seleccionados.")
        return

    # Mapear IDs  Nombres legibles
    df["sucursal_nombre"] = df["sucursal"].map(map_sucursales)

    # ====== Asegurar columnas necesarias ======
    # Crear columna periodo si no existe
    if "periodo" not in df.columns:
        df["periodo"] = df["anio"].astype(str) + "-" + df["mes"].astype(str).str.zfill(2)

    # Crear nombre del mes si no existe
    if "mes_nombre" not in df.columns:
        import calendar
        df["mes_nombre"] = df["mes"].apply(lambda x: calendar.month_name[int(x)])

    # ======================================================
    #  TABLA RESUMEN
    # ======================================================
    st.markdown("### 📋 Resumen comparativo por sucursal")

    # Construir tabla resumen
    resumen = (
        df.groupby("sucursal_nombre", as_index=False)["total_ventas"]
        .sum()
        .rename(columns={
            "sucursal_nombre": "Sucursal",
            "total_ventas": "Ventas Totales"
        })
    )

    resumen["Ventas Totales"] = resumen["Ventas Totales"].round(2)

    # Mostrar tabla resumen normal
    st.dataframe(resumen, use_container_width=True)

    # ======================================================
    #  COMPARACIÓN DIRECTA (solo si hay 2 sucursales)
    # ======================================================
    from services.analytics import comparar_dos_sucursales

    if len(resumen) == 2:
        st.subheader("🔍 Comparación directa entre sucursales")

        # Usar la tabla resumen (NO el df completo)
        tabla_comparacion = comparar_dos_sucursales(resumen)

        st.dataframe(tabla_comparacion, hide_index=True)
    else:
        st.info("Selecciona exactamente 2 sucursales para mostrar la comparación.")
    

    # ======================================================
    #  GRÁFICO DE TENDENCIA
    # ======================================================
    st.markdown("### 📉 Tendencia de ventas mensuales")

    chart = (
        alt.Chart(df)
        .mark_line(point=True, strokeWidth=3)
        .encode(
            x=alt.X('periodo:N', sort=None, title='Periodo (Año-Mes)'),
            y=alt.Y('total_ventas:Q', title='Ventas ($)'),
            color=alt.Color('sucursal_nombre:N', title='Sucursal'),
            tooltip=[
                alt.Tooltip('sucursal_nombre:N', title='Sucursal'),
                alt.Tooltip('anio:O', title='Año'),
                alt.Tooltip('mes_nombre:N', title='Mes'),
                alt.Tooltip('total_ventas:Q', title='Ventas ($)', format=',.2f')
            ]
        )
        .properties(
            width=1000,
            height=420,
            title="Comparación de Ventas por Sucursal"
        )
    )

    st.altair_chart(chart, use_container_width=True)

    # ======================================================
    st.markdown("---")
    st.caption(f"Datos procesados: {len(df):,} registros.")
    
    
    
def vista_top5():
    st.subheader("🏆 Top 5 Sucursales por Ventas Totales")

    df = get_top5_sucursales()
    df = preparar_top5(df)

    tabla = df[[
        "sucursal", 
        "ciudad",
        "ventas_totales_fmt",
        "total_ordenes_fmt",
        "ticket_promedio_fmt"
    ]]

    tabla.columns = [
        "Sucursal",
        "Ciudad",
        "Ventas Totales",
        "Total Órdenes",
        "Ticket Promedio"
    ]

    st.dataframe(tabla, use_container_width=True)
    
    
    from charts.sales_charts import chart_top5

    st.markdown("###  Gráfico Top 5 por Ventas")
    grafico = chart_top5(df)
    st.altair_chart(grafico, use_container_width=True)
    
    
