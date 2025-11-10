
# ui/filters.py
import calendar
import streamlit as st
from data.queries import get_branches

MONTHS = list(calendar.month_name)[1:]
MONTHS_DICT = {calendar.month_name[i]: i for i in range(1, 13)}

def sidebar_filters():
    st.sidebar.header("📂 Menú")
    vista = st.sidebar.radio(
    "Selecciona una opción",
    [
        "Filtros",
        "Comparar sucursales",
        "Indicadores Clave (KPIs)",
        "Ranking de Ventas",
        "Ranking de Productos (Pizzas)"
    ],
    index=0
)


    st.sidebar.header("🔧 Filtros")
    anios = list(range(2020, 2026))
    anio_inicio = st.sidebar.selectbox("Año de inicio", anios, index=0)
    anio_fin    = st.sidebar.selectbox("Año de fin", anios, index=len(anios)-1)
    mes_inicio  = st.sidebar.selectbox("Mes de inicio", MONTHS, index=0)
    mes_fin     = st.sidebar.selectbox("Mes de fin", MONTHS, index=11)

    sucs_df = get_branches()

    # Diccionario para mapear nombre legible → id real
    suc_label_to_id = dict(zip(sucs_df["label"], sucs_df["id_sucursal"]))

    # Lista de nombres legibles (para mostrar)
    sucs_disp = sucs_df["label"].tolist()

    # Multiselect visible (muestra nombres, devuelve texto)
    sucs_sel_labels = st.sidebar.multiselect(
        "Sucursal(es)",
        sucs_disp,
        default=sucs_disp[:2] if sucs_disp else []
    )

# Convertir los nombres seleccionados a IDs reales
    sucs_sel = [suc_label_to_id[label] for label in sucs_sel_labels]


    st.sidebar.subheader("Opciones del gráfico")
    show_avg = st.sidebar.checkbox("Mostrar línea de promedio", value=True)

    return {
        "vista": vista,
        "anio_inicio": anio_inicio, "anio_fin": anio_fin,
        "mes_inicio": mes_inicio, "mes_fin": mes_fin,
        "sucs_sel": sucs_sel,
        "show_avg": show_avg,
        "months_dict": MONTHS_DICT
    }
