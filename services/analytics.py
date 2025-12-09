# services/analytics.py
import math
import pandas as pd
from scipy import stats 
import calendar


def monthly_means_by_branch(df: pd.DataFrame) -> pd.Series:
    # df esperado: sucursal, anio, mes, total_ventas (0 rellenado si faltan meses)
    return df.groupby("sucursal")["total_ventas"].mean()

def summary_two_branches(df: pd.DataFrame, a: str, b: str) -> dict:
    """
    Calcula promedios mensuales A y B (asume df ya rellenado con 0 en faltantes),
    ganador, base = menor, % a favor del ganador. Devuelve dict para UI.
    """
    mean_a = df.loc[df["sucursal"] == a, "total_ventas"].mean()
    mean_b = df.loc[df["sucursal"] == b, "total_ventas"].mean()

    if math.isnan(mean_a) or math.isnan(mean_b):
        return {"mean_a": mean_a, "mean_b": mean_b, "pct_text": "N/A", "winner": None, "base": None}

    if mean_a >= mean_b:
        winner, base_label = a, b
        base_val = mean_b
        diff_abs = mean_a - mean_b
    else:
        winner, base_label = b, a
        base_val = mean_a
        diff_abs = mean_b - mean_a

    if base_val == 0:
        pct_text = "N/A"
    else:
        pct_text = f"{(diff_abs / base_val) * 100:,.2f}%"

    return {
        "mean_a": mean_a, "mean_b": mean_b,
        "winner": winner, "base": base_label,
        "pct_text": pct_text
    }

def t_test_two_branches(df: pd.DataFrame, a: str, b: str):
    """
    Aplica prueba t de Student (independiente) entre sucursales A y B.
    df debe tener columnas: sucursal, total_ventas, anio, mes.
    Devuelve dict con estadístico t y p-valor.
    """
    sales_a = df.loc[df["sucursal"] == a, "total_ventas"].dropna()
    sales_b = df.loc[df["sucursal"] == b, "total_ventas"].dropna()

    if sales_a.empty or sales_b.empty:
        return {"t_stat": None, "p_value": None}

    t_stat, p_value = stats.ttest_ind(sales_a, sales_b, equal_var=False)  
    # equal_var=False = versión de Welch (más robusta)
    return {"t_stat": t_stat, "p_value": p_value}


# [NUEVO] Intervalo de confianza 95% para la media (t de Student)
def mean_confint(series: pd.Series, alpha: float = 0.05):
    """
    Devuelve (media, li, ls, n) usando t-interval.
    series: una serie de números (dropna aplicado dentro).
    """
    x = series.dropna()
    n = len(x)
    if n < 2:
        m = float(x.mean()) if n == 1 else float("nan")
        return {"mean": m, "li": float("nan"), "ls": float("nan"), "n": n}

    m = float(x.mean())
    s = float(x.std(ddof=1))
    se = s / (n ** 0.5)
    from scipy.stats import t
    tcrit = t.ppf(1 - alpha/2, df=n-1)
    li = m - tcrit * se
    ls = m + tcrit * se
    return {"mean": m, "li": li, "ls": ls, "n": n}



    """
    df: DataFrame con columnas ['sucursal','total_ventas'] filtrado al rango UI.
    Devuelve DataFrame con columnas: sucursal, mean, li, ls, n.
    """
    import pandas as pd
    from .analytics import mean_confint  # si estás en el mismo archivo, puedes llamar mean_confint directo

    rows = []
    for suc, sub in df.groupby("sucursal"):
        ic = mean_confint(sub["total_ventas"], alpha=0.05)
        rows.append({
            "sucursal": suc,
            "mean": ic["mean"],
            "li": ic["li"],
            "ls": ic["ls"],
            "n": ic["n"],
        })
    return pd.DataFrame(rows)


import pandas as pd

def calcular_kpis_generales(df: pd.DataFrame):
    """Calcula KPIs globales básicos."""
    total_ventas = df["net"].sum()
    total_ordenes = df["order_id"].nunique()
    ticket_promedio = total_ventas / total_ordenes if total_ordenes > 0 else 0
    return total_ventas, total_ordenes, ticket_promedio




# =============================================
# Comparar sucursales
# =============================================
def get_branch_comparison_data(fecha_inicio, fecha_fin, sucursales):
    from data.queries import query_branch_monthly_sales
    df = query_branch_monthly_sales(fecha_inicio, fecha_fin, sucursales)

    if df.empty:
        return df

    df["mes"] = df["mes"].astype(int)
    df = df.sort_values(["anio", "mes"])
    df["periodo"] = df["anio"].astype(str) + "-" + df["mes"].astype(str).str.zfill(2)

    import calendar
    df["mes_nombre"] = df["mes"].apply(lambda x: calendar.month_name[int(x)])

    return df


def preparar_top5(df):
    df = df.copy()
    df["ventas_totales_fmt"] = df["ventas_totales"].apply(lambda x: f"${x:,.2f}")
    df["ticket_promedio_fmt"] = df["ticket_promedio"].apply(lambda x: f"${x:,.2f}")
    df["total_ordenes_fmt"] = df["total_ordenes"].apply(lambda x: f"{x:,}")
    return df


def preparar_participacion(df):
    df = df.copy()
    df["ventas_totales_fmt"] = df["ventas_totales"].apply(lambda x: f"${x:,.2f}")
    df["ticket_promedio_fmt"] = df["ticket_promedio"].apply(lambda x: f"${x:,.2f}")
    df["total_ordenes_fmt"] = df["total_ordenes"].apply(lambda x: f"{x:,}")
    df["porcentaje_fmt"] = df["porcentaje"].apply(lambda x: f"{x:.2f}%")
    return df



def calcular_crecimiento_anual(df):
    """
    Calcula ventas por año y porcentaje de crecimiento YoY.
    df: DataFrame con columna 'fecha_compra' y 'net'
    """
    df = df.copy()
    df["anio"] = df["fecha_compra"].dt.year

    tabla = (
        df.groupby("anio", as_index=False)["net"]
          .sum()
          .rename(columns={"net": "ventas"})
    )

    tabla["crecimiento"] = tabla["ventas"].pct_change() * 100
    tabla["ventas_formato"] = tabla["ventas"].apply(lambda x: f"${x:,.2f}")
    tabla["crecimiento_formato"] = tabla["crecimiento"].apply(
        lambda x: "---" if pd.isna(x) else f"{x:.2f}%"
    )

    return tabla




def calcular_pareto_productos(df):
    # Ordenar por ventas DESC 
    df = df.sort_values(by="ventas", ascending=False).reset_index(drop=True)

    # Cálculo real de Pareto
    df["ventas_acum"] = df["ventas"].cumsum()
    df["porcentaje_acum"] = df["ventas_acum"] / df["ventas"].sum()

    return df



import pandas as pd

def comparar_dos_sucursales(df_resumen):
    # df_resumen TIENE columnas: "Sucursal" y "Ventas Totales"
    
    a = df_resumen.iloc[0]
    b = df_resumen.iloc[1]

    ventas_a = float(a["Ventas Totales"])
    ventas_b = float(b["Ventas Totales"])
    
    

    diferencia = ventas_a - ventas_b
    porcentaje = (diferencia / ventas_b) * 100 if ventas_b != 0 else None
    mejor = a["Sucursal"] if ventas_a > ventas_b else b["Sucursal"]

    tabla = pd.DataFrame([{
        "Sucursal A": a["Sucursal"],
        "Sucursal B": b["Sucursal"],
        "Ventas A": ventas_a,
        "Ventas B": ventas_b,
        "Diferencia": diferencia,
        "% Diferencia": round(porcentaje, 2),
        "Mejor Sucursal": mejor
    }])
    
    tabla["Ventas A"] = tabla["Ventas A"].apply(lambda x: f"${x:,.2f}")
    tabla["Ventas B"] = tabla["Ventas B"].apply(lambda x: f"${x:,.2f}")
    tabla["Diferencia"] = tabla["Diferencia"].apply(lambda x: f"${x:,.2f}")
    tabla["% Diferencia"] = tabla["% Diferencia"].apply(lambda x: f"{x:.2f}%")

    return tabla