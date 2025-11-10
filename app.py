

# app.py
import os, sys
import streamlit as st

# ============================================
# 🔧 RUTAS Y CONFIGURACIÓN
# ============================================
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

print(">>> ROOT =", ROOT)
print(">>> Contenido ROOT:", os.listdir(ROOT))

# ============================================
# 🧩 IMPORTS INTERNOS
# ============================================
from data.config import PAGE_TITLE, PAGE_LAYOUT
from ui.filters import sidebar_filters
from ui.views import (
    compute_date_range,
    kpis_view,
    ranking_pizzas_view,
    view_placeholder  # la puedes usar para futuras secciones
)

# ============================================
# 🎨 CONFIG STREAMLIT
# ============================================
st.set_page_config(page_title=PAGE_TITLE, layout=PAGE_LAYOUT)
st.title("🍕 Dashboard de Ventas")

# ============================================
# 🧭 SIDEBAR Y FILTROS
# ============================================
f = sidebar_filters()

# Rango de fechas real
fecha_inicio, fecha_fin, m_ini, m_fin = compute_date_range(
    f["anio_inicio"], f["anio_fin"], f["months_dict"],
    f["mes_inicio"], f["mes_fin"]
)

# ============================================
# 📂 MENÚ PRINCIPAL
# ============================================
st.sidebar.title("Menú de Navegación")
opcion = st.sidebar.selectbox(
    "Selecciona una sección:",
    [
        "📊 KPIs",
        "🏙️ Comparar Sucursales",
        "🍕 Ranking de Productos (Pizzas)"
    ]
)

st.sidebar.caption(f"Debug: sección seleccionada ⇒ {opcion}")

# ============================================
# 🧠 VISTAS
# ============================================
if "kpi" in opcion.lower():
    kpis_view()

elif "sucursal" in opcion.lower():
    view_placeholder("Comparar Sucursales")

elif "pizza" in opcion.lower():
    ranking_pizzas_view()
    
print("🧩 DEBUG opción seleccionada:", opcion)
