# data/connection.py
from sqlalchemy import create_engine, text
import pandas as pd
import os

# ============================================
# 🔧 CONFIGURACIÓN DE CONEXIÓN
# ============================================

DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "Zaiperaldama1!")   # cámbialo si es distinto
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "pizzasnew2")

# ============================================
# 🚀 CREAR MOTOR SQLAlchemy
# ============================================

try:
    engine = create_engine(
        f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
        pool_pre_ping=True,
    )
    print("✅ Conexión establecida con la base de datos.")
except Exception as e:
    print("❌ Error al conectar con la base de datos:", e)

# ============================================
# 🧩 FUNCIONES COMPATIBLES
# ============================================

def get_engine():
    """Devuelve el motor global de conexión."""
    return engine


def read_sql_df(query: str, params=None):
    """
    Ejecuta una consulta SQL y devuelve el resultado como DataFrame.
    query: puede ser string o sqlalchemy.text
    params: diccionario opcional con parámetros de la consulta
    """
    with engine.connect() as con:
        df = pd.read_sql(text(query), con, params=params)
    return df
