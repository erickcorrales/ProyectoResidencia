
# data/connection.py
from sqlalchemy import create_engine
import pandas as pd
from sqlalchemy.sql import text, bindparam
import streamlit as st
from .config import DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME

@st.cache_resource(show_spinner=False)
def get_engine():
    url = (
        f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        "?charset=utf8mb4"
    )
    engine = create_engine(url, pool_pre_ping=True, future=True)
    return engine

@st.cache_data(show_spinner=True)
def read_sql_df(sql, params=None, expanding=None):
    """
    Lee SQL en DataFrame. Si 'expanding' es dict de {nombre_param: iterable},
    aplica bindparam(expanding=True) para cláusulas IN.
    """
    engine = get_engine()
    if expanding:
        # construye text() con bindparam(expanding)
        t = text(sql)
        for pname in expanding.keys():
            t = t.bindparams(bindparam(pname, expanding=True))
        with engine.connect() as con:
            return pd.read_sql(t, con, params=params)
    else:
        with engine.connect() as con:
            return pd.read_sql(text(sql), con, params=params)
