# services/analytics.py
import math
import pandas as pd
from scipy import stats 

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

# [NUEVO] Tamaño de efecto (Cohen's d) para muestras independientes (pooled SD)
def cohens_d_independent(s1: pd.Series, s2: pd.Series):
    """
    Cohen's d clásico con SD combinada (pooled).
    """
    x1 = s1.dropna()
    x2 = s2.dropna()
    n1, n2 = len(x1), len(x2)
    if n1 < 2 or n2 < 2:
        return float("nan")
    m1, m2 = float(x1.mean()), float(x2.mean())
    s1_ = float(x1.std(ddof=1))
    s2_ = float(x2.std(ddof=1))
    # SD combinada
    import math
    s_pooled = math.sqrt(((n1 - 1) * s1_**2 + (n2 - 1) * s2_**2) / (n1 + n2 - 2))
    if s_pooled == 0:
        return float("nan")
    d = (m2 - m1) / s_pooled  # nota: orden m2 - m1 (puedes elegir el que prefieras)
    return d


# [NUEVO] Estadísticos por sucursal: media e IC95% (para barras de error)
def branch_means_ci(df):
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

