

import os, sys
ROOT = os.path.dirname(os.path.abspath(__file__))        # C:\Users\ASUS\Desktop\ResidenciasStreamlit
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
# ------------------------------------------------------
    
import streamlit as st
from data.config import PAGE_TITLE, PAGE_LAYOUT
from ui.filters import sidebar_filters
from ui.views import (
    compute_date_range,
    view_filtros, view_comparar, view_placeholder
)

# [L13-L20] Diagnóstico (puedes borrarlo luego)
print(">>> ROOT =", ROOT)
print(">>> Contenido ROOT:", os.listdir(ROOT))
print(">>> ¿Existe services/transforms.py? ->", os.path.exists(os.path.join(ROOT, "services", "transforms.py")))


st.set_page_config(page_title=PAGE_TITLE, layout=PAGE_LAYOUT)
st.title("🍕 Dashboard de Ventas")

# Sidebar
f = sidebar_filters()

# Fechas reales
fecha_inicio, fecha_fin, m_ini, m_fin = compute_date_range(
    f["anio_inicio"], f["anio_fin"], f["months_dict"], f["mes_inicio"], f["mes_fin"]
)

# Router de vistas
if f["vista"] == "Filtros":
    view_filtros(fecha_inicio, fecha_fin, f["sucs_sel"], f["show_avg"], f["mes_inicio"], f["mes_fin"], f["anio_inicio"], f["anio_fin"])
elif f["vista"] == "Comparar sucursales":
    view_comparar(fecha_inicio, fecha_fin, f["sucs_sel"])
elif f["vista"] == "xxyyy":
    view_placeholder("xxyyy")
else:
    view_placeholder("ydsjvsdu")
