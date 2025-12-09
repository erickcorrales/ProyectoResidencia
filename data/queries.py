
# data/queries.py

import pandas as pd
from data.connection import get_engine  # si ya tienes esta función definida
from sqlalchemy import text
from .connection import read_sql_df
import streamlit as st
from sqlalchemy import text, bindparam
from .connection import engine


def get_branches():
    """Devuelve un DataFrame con IDs y nombres legibles de sucursales."""
    engine = get_engine()
    query = text("SELECT id_sucursal, nombre, ciudad FROM sucursales ORDER BY ciudad, nombre;")
    df = pd.read_sql(query, engine)
    df["label"] = df["ciudad"] + " - " + df["nombre"]
    return df[["id_sucursal", "label"]]


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


@st.cache_data(ttl=600)
def get_ventas():
    """Obtiene todos los registros de ventas_totales."""
    engine = get_engine()
    query = text("SELECT * FROM ventas_totales;")
    df = pd.read_sql(query, engine)
    return df

@st.cache_data(ttl=600)
def get_sucursales():
    """Obtiene la lista de sucursales."""
    engine = get_engine()
    query = text("SELECT * FROM sucursales;")
    df = pd.read_sql(query, engine)
    return df


from sqlalchemy import text
from .connection import get_engine


def get_top_pizzas(top_n=5, sucursales_ids=None):
    """
    Devuelve las pizzas más vendidas (por cantidad y ventas),
    mostrando el nombre desde la tabla pizzas_info.
    Si se especifican sucursales, filtra por ellas.
    """
    engine = get_engine()

    base_sql = """
        SELECT 
            info.name AS nombre,             -- nombre legible de la pizza
            SUM(v.quantity) AS cantidad, 
            SUM(v.net) AS ventas
        FROM ventas_totales v
        JOIN pizzas p ON v.pizza_id = p.pizza_id
        JOIN pizzas_info info ON p.pizza_type_id = info.pizza_type_id
        {where_clause}
        GROUP BY info.name
        ORDER BY ventas DESC
        LIMIT :top_n;
    """

    params = {"top_n": top_n}
    where_clause = ""

    if sucursales_ids:
        placeholders = ", ".join([f":suc_{i}" for i in range(len(sucursales_ids))])
        where_clause = f"WHERE v.sucursal IN ({placeholders})"
        for i, val in enumerate(sucursales_ids):
            params[f"suc_{i}"] = val

    sql = base_sql.format(where_clause=where_clause)

    with engine.connect() as con:
        result = con.execute(text(sql), params)
        rows = result.fetchall()

    df = pd.DataFrame(rows, columns=["nombre", "cantidad", "ventas"])

    print(f"[DEBUG get_top_pizzas] sucursales_ids={sucursales_ids}, filas={len(df)}")
    return df


def get_top5_sucursales():
    query = text("""
        SELECT 
            s.id_sucursal,
            s.nombre AS sucursal,
            s.ciudad,
            SUM(v.net) AS ventas_totales,
            COUNT(DISTINCT v.order_id) AS total_ordenes,
            SUM(v.net) / COUNT(DISTINCT v.order_id) AS ticket_promedio
        FROM ventas_totales v
        JOIN sucursales s 
            ON v.id_sucursal = s.id_sucursal
        GROUP BY s.id_sucursal, s.nombre, s.ciudad
        ORDER BY ventas_totales DESC
        LIMIT 5;
    """)

    df = pd.read_sql(query, engine)
    return df







# =============================================
# 📊 COMPARAR SUCURSALES: OBTENER VENTAS MENSUALES
# =============================================
def query_branch_monthly_sales(fecha_inicio: str, fecha_fin: str, sucursales: list[str]):
    """
    Retorna ventas mensuales por sucursal, dentro del rango seleccionado.
    Columnas: sucursal, anio, mes, total_ventas
    """
    if not sucursales:
        return pd.DataFrame()

    placeholders = ", ".join([f":s{i}" for i in range(len(sucursales))])

    sql = f"""
        SELECT
            sucursal,
            YEAR(fecha_compra) AS anio,
            MONTH(fecha_compra) AS mes,
            SUM(net) AS total_ventas
        FROM ventas_totales
        WHERE fecha_compra BETWEEN :fi AND :ff
        AND sucursal IN ({placeholders})
        GROUP BY sucursal, anio, mes
        ORDER BY anio, mes;
    """

    params = {"fi": fecha_inicio, "ff": fecha_fin}
    for i, suc in enumerate(sucursales):
        params[f"s{i}"] = suc

    df = read_sql_df(sql, params=params)
    return df




def get_pareto_productos():
    query = """
        SELECT 
            info.name AS producto,
            SUM(v.net) AS ventas
        FROM ventas_totales v
        JOIN pizzas p ON v.pizza_id = p.pizza_id
        JOIN pizzas_info info ON p.pizza_type_id = info.pizza_type_id
        GROUP BY info.name
        ORDER BY ventas DESC;
    """
    return read_sql_df(query)