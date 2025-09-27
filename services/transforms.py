
# services/transforms.py
import calendar
import pandas as pd

MONTH_NAME = list(calendar.month_name)[1:]
MONTH_MAP = {i: calendar.month_name[i] for i in range(1, 13)}

def add_month_name(df: pd.DataFrame, month_col="mes"):
    df = df.copy()
    df["mes_nombre"] = df[month_col].astype(int).map(MONTH_MAP)
    return df

def add_period(df: pd.DataFrame, year_col="anio", month_col="mes"):
    df = df.copy()
    df["periodo"] = df[year_col].astype(str) + "-" + df[month_col].astype(int).astype(str).str.zfill(2)
    return df

def wide_table_month_branch(df: pd.DataFrame):
    tabla = df.pivot_table(
        index=["anio", "mes", "mes_nombre"],
        columns="sucursal",
        values="total_ventas",
        aggfunc="sum",
    ).sort_index().reset_index()
    return tabla

def fill_missing_months(df: pd.DataFrame, branches: list[str], years: list[int]):
    """
    Garantiza mismo grid año-mes por sucursal. Rellena faltantes con 0.
    """
    idx = pd.MultiIndex.from_product([branches, years, range(1,13)],
                                     names=["sucursal","anio","mes"])
    base = df.set_index(["sucursal","anio","mes"]).reindex(idx).reset_index()
    base["total_ventas"] = base["total_ventas"].fillna(0)
    base["mes_nombre"] = base["mes"].map(MONTH_MAP)
    base["periodo"] = base["anio"].astype(str) + "-" + base["mes"].astype(str).str.zfill(2)
    return base


# [NUEVO] Genera la lista de (anio, mes) incluidos en el rango [fecha_inicio, fecha_fin]
def month_pairs_between(fecha_inicio: str, fecha_fin: str):
    """
    fecha_inicio y fecha_fin en formato 'YYYY-MM-DD'.
    Devuelve lista de tuplas (anio:int, mes:int) inclusiva.
    """
    import datetime as dt
    y1, m1 = int(fecha_inicio[:4]), int(fecha_inicio[5:7])
    y2, m2 = int(fecha_fin[:4]), int(fecha_fin[5:7])

    pairs = []
    y, m = y1, m1
    while (y < y2) or (y == y2 and m <= m2):
        pairs.append((y, m))
        # avanzar un mes
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1
    return pairs

# [NUEVO] Igual que fill_missing_months pero RESPECTA los meses exactos de la UI
def fill_missing_months_range(df, branches: list[str], month_pairs: list[tuple[int, int]]):
    """
    Rellena con 0 exactamente para los (anio,mes) dados en month_pairs.
    Espera columnas: sucursal, anio, mes, total_ventas.
    """
    import pandas as pd
    import calendar

    MONTH_MAP = {i: calendar.month_name[i] for i in range(1, 13)}

    idx = pd.MultiIndex.from_product(
        [branches, [p[0] for p in month_pairs], [p[1] for p in month_pairs]],
        names=["sucursal", "anio", "mes"]
    )
    # El product de arriba no sirve tal cual porque repite pares; construimos MultiIndex correcto:
    idx = pd.MultiIndex.from_tuples(
        [(s, y, m) for s in branches for (y, m) in month_pairs],
        names=["sucursal", "anio", "mes"]
    )

    base = df.set_index(["sucursal", "anio", "mes"]).reindex(idx).reset_index()
    base["total_ventas"] = base["total_ventas"].fillna(0)
    base["mes_nombre"] = base["mes"].map(MONTH_MAP)
    base["periodo"] = (
        base["anio"].astype(str) + "-" +
        base["mes"].astype(int).astype(str).str.zfill(2)
    )
    return base
