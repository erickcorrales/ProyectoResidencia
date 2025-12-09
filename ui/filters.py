# ui/filters.py
import calendar
import streamlit as st
from data.queries import get_branches

MONTHS = list(calendar.month_name)[1:]
MONTHS_DICT = {calendar.month_name[i]: i for i in range(1, 13)}


def sidebar_filters():
    st.sidebar.header("📂 Menú")
    vista = "Filtros"
    st.sidebar.header("🔧 Filtros")
    anios = list(range(2020, 2026))
    anio_inicio = st.sidebar.selectbox("Año de inicio", anios, index=0)
    anio_fin    = st.sidebar.selectbox("Año de fin", anios, index=len(anios)-1)
    mes_inicio  = st.sidebar.selectbox("Mes de inicio", MONTHS, index=0)
    mes_fin     = st.sidebar.selectbox("Mes de fin", MONTHS, index=11)

    # === Cargar sucursales ===
    sucs_df = get_branches()

    # Mapas ID <-> Nombre legible
    suc_label_to_id = dict(zip(sucs_df["label"], sucs_df["id_sucursal"]))
    suc_id_to_label = dict(zip(sucs_df["id_sucursal"], sucs_df["label"]))

    # Lista visible de sucursales
    sucs_disp = sucs_df["label"].tolist()

    # Multiselect → devuelve labels
    sucs_sel_labels = st.sidebar.multiselect(
        "Sucursal(es)",
        sucs_disp,
        default=sucs_disp[:2] if sucs_disp else []
    )

    # Convertir labels a IDs
    sucs_sel = [suc_label_to_id[label] for label in sucs_sel_labels]

    st.sidebar.subheader("Opciones del gráfico")
    show_avg = st.sidebar.checkbox("Mostrar línea de promedio", value=True)

    # === EL RETURN CORRECTO ===
    return {
        "vista": vista,
        "anio_inicio": anio_inicio,
        "anio_fin": anio_fin,
        "mes_inicio": mes_inicio,
        "mes_fin": mes_fin,
        "sucs_sel": sucs_sel,   # lista de IDs
        "show_avg": show_avg,
        "months_dict": MONTHS_DICT,
        "suc_id_to_label": suc_id_to_label  # ⬅ ESTE ES EL QUE FALTABA
    }


