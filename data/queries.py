
# data/queries.py
from .connection import read_sql_df

def get_branches():
    sql = "SELECT DISTINCT sucursal FROM ventas_totales ORDER BY sucursal"
    df = read_sql_df(sql)
    return df["sucursal"].tolist()

def get_monthly_sales(fecha_inicio: str, fecha_fin: str, sucursales: list[str]):
    sql = """
        SELECT 
            sucursal,
            YEAR(fecha_compra) AS anio,
            MONTH(fecha_compra) AS mes,
            SUM(net) AS total_ventas
        FROM ventas_totales
        WHERE fecha_compra BETWEEN :fi AND :ff
          AND sucursal IN :sucs
        GROUP BY sucursal, anio, mes
        ORDER BY anio, mes
    """
    params = {"fi": fecha_inicio, "ff": fecha_fin, "sucs": tuple(sucursales)}
    # expanding=: sucs
    df = read_sql_df(sql, params=params, expanding={"sucs": sucursales})
    return df

def get_monthly_total(fecha_inicio: str, fecha_fin: str, sucursales: list[str]):
    sql = """
        SELECT 
            MONTH(fecha_compra) AS mes,
            SUM(net) AS total_ventas
        FROM ventas_totales
        WHERE fecha_compra BETWEEN :fi AND :ff
          AND sucursal IN :sucs
        GROUP BY mes
        ORDER BY mes
    """
    params = {"fi": fecha_inicio, "ff": fecha_fin, "sucs": tuple(sucursales)}
    df = read_sql_df(sql, params=params, expanding={"sucs": sucursales})
    return df

def get_table_range_diag():
    sql = """
        SELECT 
            MIN(fecha_compra) AS min_fecha, 
            MAX(fecha_compra) AS max_fecha, 
            COUNT(*) AS filas 
        FROM ventas_totales
    """
    return read_sql_df(sql)
