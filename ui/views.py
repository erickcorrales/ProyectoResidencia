
# ui/views.py
import streamlit as st
from calendar import monthrange

import os, sys
THIS_DIR = os.path.dirname(os.path.abspath(__file__))        # ...\ResidenciasStreamlit\ui
ROOT = os.path.dirname(THIS_DIR)                             # ...\ResidenciasStreamlit
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
# (Diagnóstico opcional: borra luego)
print(">>> ROOT (ui/views.py) =", ROOT)
print(">>> ¿Existe services/transforms.py? ->",
      os.path.exists(os.path.join(ROOT, "services", "transforms.py")))
# ------------------------------------------------------
from data.queries import get_monthly_total, get_monthly_sales, get_table_range_diag
from services.transforms import add_month_name, add_period, wide_table_month_branch, fill_missing_months
from services.analytics import summary_two_branches
from charts.sales_charts import chart_monthly_bars, chart_comparison_lines, chart_small_multiples

from services.transforms import (
    add_month_name, add_period, wide_table_month_branch, fill_missing_months,
    month_pairs_between, fill_missing_months_range  # 👈 estas dos son clave
)

from services.analytics import summary_two_branches, t_test_two_branches

def compute_date_range(anio_inicio, anio_fin, months_dict, mes_inicio, mes_fin):
    m_ini = months_dict[mes_inicio]
    m_fin = months_dict[mes_fin]
    if (anio_inicio > anio_fin) or (anio_inicio == anio_fin and m_ini > m_fin):
        st.error(" Rango inválido: el inicio debe ser ≤ al fin (año/mes).")
        st.stop()

    fecha_inicio = f"{anio_inicio}-{m_ini:02d}-01"
    dia_fin = monthrange(anio_fin, m_fin)[1]
    fecha_fin = f"{anio_fin}-{m_fin:02d}-{dia_fin:02d}"
    return fecha_inicio, fecha_fin, m_ini, m_fin

def view_filtros(fecha_inicio, fecha_fin, sucs_sel, show_avg, mes_inicio, mes_fin, anio_inicio, anio_fin):
    if not sucs_sel:
        st.warning("⚠️ Selecciona al menos una sucursal.")
        st.stop()

    df = get_monthly_total(fecha_inicio, fecha_fin, sucs_sel)
    st.caption(f"Rango: **{fecha_inicio}** → **{fecha_fin}** | Sucursales: **{', '.join(sucs_sel)}**")

    if df.empty:
        st.info("No hay ventas para el rango y sucursal(es) seleccionados.")
        diag = get_table_range_diag()
        st.write("📌 Diagnóstico rápido de la tabla:", diag)
        return

    df = add_month_name(df, "mes")
    title = f"Ventas de {mes_inicio} a {mes_fin} ({anio_inicio}–{anio_fin}) — {', '.join(sucs_sel)}"
    st.altair_chart(chart_monthly_bars(df, title=title, show_avg=show_avg), use_container_width=True)

    # Tabla
    st.subheader("🔍 Detalle de Ventas")
    df_out = df[["mes_nombre", "total_ventas"]].rename(columns={"mes_nombre": "Mes", "total_ventas": "Ventas ($)"})
    df_out["Ventas ($)"] = df_out["Ventas ($)"].round(2)
    st.dataframe(df_out, use_container_width=True)

def view_comparar(fecha_inicio, fecha_fin, sucs_sel):
    # Validación de sucursales
    if len(sucs_sel) < 2:
        st.warning("Selecciona **al menos dos** sucursales para comparar.")
        return

    # Leer datos crudos (solo lo que pide el rango UI)
    df = get_monthly_sales(fecha_inicio, fecha_fin, sucs_sel)
    st.caption(f"Rango: **{fecha_inicio}** → **{fecha_fin}** | Sucursales: **{', '.join(sucs_sel)}**")

    if df.empty:
        st.info("No hay ventas para el rango y sucursal(es) seleccionados.")
        return

    # Normalizar grid SOLO para los meses del rango UI (n correcto)
    month_pairs = month_pairs_between(fecha_inicio, fecha_fin)   # lista de (anio, mes)
    df_full = fill_missing_months_range(df, branches=sucs_sel, month_pairs=month_pairs)
    # df_full tiene columnas: sucursal, anio, mes, total_ventas, mes_nombre, periodo

    # === Gráfico 1: líneas (comparación directa) ===
    st.altair_chart(
        chart_comparison_lines(df_full, title="Comparación de Ventas Mensuales por Sucursal (mismo eje)"),
        use_container_width=True
    )

    # === Gráfico 2: small multiples (paneles apilados) ===
    st.altair_chart(
        chart_small_multiples(df_full, title="Ventas por Sucursal (paneles apilados)"),
        use_container_width=True
    )
    
    # prueba grafica error
    
    
    # fin grafica error
    
    

    # === Tabla comparativa (ancha) ===
    tabla = wide_table_month_branch(df_full)

    # === Resumen / Estadística cuando hay exactamente 2 sucursales ===
    if len(sucs_sel) == 2:
        # 1) Define primero las dos sucursales
        a, b = sucs_sel[0], sucs_sel[1]

        # 2) Series de ventas mensuales SOLO del rango elegido
        sA = df_full.loc[df_full["sucursal"] == a, "total_ventas"]
        sB = df_full.loc[df_full["sucursal"] == b, "total_ventas"]
        nA, nB = len(sA), len(sB)

        # 3) Resumen intuitivo (base = menor promedio)
        res = summary_two_branches(df_full, a, b)
        if res["winner"]:
            st.markdown(
                f"**Resumen:** Promedio mensual — **{a}**: ${res['mean_a']:,.2f}, "
                f"**{b}**: ${res['mean_b']:,.2f} → {res['pct_text']} a favor de **{res['winner']}** "
                f"(base **{res['base']}**)."
            )
            st.caption("🔎 Nota: el % usa como base el promedio menor (más intuitivo).")

        # 4) Prueba t de Student (Welch)
        try:
            from services.analytics import t_test_two_branches
            t_res = t_test_two_branches(df_full, a, b)
            if t_res["t_stat"] is not None:
                sig = (t_res["p_value"] < 0.05)
                st.caption(
                    f"📐 Prueba t (Welch): t = {t_res['t_stat']:.3f}, "
                    f"p = {t_res['p_value']:.4f} → "
                    f"{'diferencia estadísticamente significativa' if sig else 'diferencia NO significativa'}."
                )
        except Exception as e:
            st.caption(f"⚠️ No se pudo calcular la prueba t: {e}")

        # 5) IC95% y tamaño de efecto (Cohen's d)
        try:
            from services.analytics import mean_confint, cohens_d_independent
            icA = mean_confint(sA, alpha=0.05)
            icB = mean_confint(sB, alpha=0.05)
            d = cohens_d_independent(sA, sB)

            st.caption(
                f"🧭 IC 95% — {a}: [{icA['li']:,.2f}, {icA['ls']:,.2f}] (n={nA}); "
                f"{b}: [{icB['li']:,.2f}, {icB['ls']:,.2f}] (n={nB})."
            )
            magnitud = (
                "muy pequeño" if abs(d) < 0.2 else
                "pequeño" if abs(d) < 0.5 else
                "mediano" if abs(d) < 0.8 else
                "grande"
            )
            st.caption(f"📏 Tamaño de efecto (Cohen’s d): {d:.2f} ({magnitud}).")
            
        except Exception as e:
            st.caption(f"⚠️ No se pudieron calcular IC/d: {e}")
            
            
            

    # === Formatos bonitos de la tabla y render ===
    for col in tabla.columns:
        if col not in ["anio", "mes", "mes_nombre"]:
            tabla[col] = tabla[col].round(2)

    st.subheader("📋 Tabla comparativa por mes")
    st.dataframe(
        tabla.rename(columns={"anio": "Año", "mes": "Mes", "mes_nombre": "Mes (nombre)"}),
        use_container_width=True
    )


def view_placeholder(title: str):
    st.info(f"🚧 Placeholder para '{title}'. Aquí podrás agregar otra vista personalizada.")
