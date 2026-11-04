import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from contextlib import contextmanager


@st.cache_resource  # build the engine ONCE and reuse it on every rerun
def get_engine():
    c = st.secrets["db"]
    url = URL.create(
        drivername="postgresql+psycopg2",
        username=c["user"],
        password=c["password"],  # special characters like @ are escaped safely
        host=c["host"],
        port=int(c["port"]),
        database=c["name"],
    )
    return create_engine(url, pool_pre_ping=True)


def fetch_all(sql, params=None):
    """Run a SELECT and return a list of dicts (same contract as the Django version)."""
    with get_engine().connect() as conn:
        result = conn.execute(text(sql), params or {})
        return [dict(row._mapping) for row in result]


def fetch_df(sql, params=None):
    """Run a SELECT and return a pandas DataFrame (handy for st.dataframe and charts)."""
    with get_engine().connect() as conn:
        return pd.read_sql(text(sql), conn, params=params or {})


def execute(sql, params=None):
    """Run an INSERT/UPDATE/DELETE inside a transaction (commits automatically)."""
    with get_engine().begin() as conn:
        conn.execute(text(sql), params or {})
        

def run(conn, sql, params=None):
    """Execute one statement inside an open transaction (see tx())."""
    return conn.execute(text(sql), params or {})


@contextmanager
def tx(actor_id=None):
    """One atomic transaction. Also tells the DB who is acting (app.current_user_id)."""
    with get_engine().begin() as conn:
        if actor_id:
            conn.execute(text("SELECT set_config('app.current_user_id', :u, true)"), {"u": str(actor_id)})
        yield conn


def audit(conn, user_id, action, entity_type, entity_id):
    run(conn, """INSERT INTO audit_logs (user_id, action, entity_type, entity_id)
                 VALUES (:u, :a, :t, :e)""",
        {"u": str(user_id), "a": action, "t": entity_type, "e": str(entity_id)})


def db_message(e):
    """First line of the database's own error, in plain words."""
    msg = str(getattr(e, "orig", e)).strip()
    return msg.splitlines()[0] if msg else "unknown error"