# ui/views.py
import os, sys
import streamlit as st
import pandas as pd
from calendar import monthrange

from data.queries import get_top_pizzas

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
    get_table_range_diag, get_top_sucursales, get_top_pizzas
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
    """Carga datos base (ventas + sucursales)."""
    ventas = get_ventas()
    sucursales = get_sucursales()
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
# 🏅 RANKING DE PRODUCTOS (PIZZAS)
# ===============================================================
def ranking_pizzas_view():
    st.warning("🟨 DEBUG: Entró a la función ranking_pizzas_view()")
    st.warning("Entró correctamente a ranking_pizzas_view()")
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

    st.write("DEBUG df shape:", df.shape)
    st.write("DEBUG columnas:", df.columns.tolist())
    st.write(df.head())
    if df.empty:
        st.warning("No se encontraron resultados para los filtros seleccionados.")
        return

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


def view_placeholder(title: str):
    """
    Placeholder genérico usado para vistas que aún no están implementadas.
    Permite que app.py las invoque sin errores de importación.
    """
    st.info(f"🚧 Placeholder para '{title}'. Aquí podrás agregar otra vista personalizada.")