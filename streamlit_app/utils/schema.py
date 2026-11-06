import streamlit as st
from utils.db import fetch_all, fetch_df


def q(name):
    """Quote a table/column name. Identifiers can't be bound parameters,
    so every name we put in SQL comes from the database metadata and goes through this."""
    return '"' + str(name).replace('"', '""') + '"'


@st.cache_data(ttl=300)
def list_relations():
    return fetch_all(
        """SELECT table_name, table_type FROM information_schema.tables
           WHERE table_schema = 'public' ORDER BY table_type, table_name"""
    )


def table_names(only_tables=False):
    return [r["table_name"] for r in list_relations()
            if not only_tables or r["table_type"] == "BASE TABLE"]


@st.cache_data(ttl=300)
def columns_meta(table):
    return fetch_all(
        """SELECT column_name, data_type, udt_name, is_nullable, column_default,
                  is_identity, character_maximum_length
           FROM information_schema.columns
           WHERE table_schema = 'public' AND table_name = :t
           ORDER BY ordinal_position""",
        {"t": table},
    )


@st.cache_data(ttl=300)
def primary_keys():
    """{table: [pk columns]}"""
    rows = fetch_all(
        """SELECT tc.table_name, kcu.column_name
           FROM information_schema.table_constraints tc
           JOIN information_schema.key_column_usage kcu
             ON kcu.constraint_name = tc.constraint_name
            AND kcu.table_schema = tc.table_schema
           WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema = 'public'
           ORDER BY tc.table_name, kcu.ordinal_position"""
    )
    out = {}
    for r in rows:
        out.setdefault(r["table_name"], []).append(r["column_name"])
    return out


@st.cache_data(ttl=300)
def foreign_keys():
    """[{src_table, src_col, dst_table, dst_col}]"""
    return fetch_all(
        """SELECT tc.table_name AS src_table, kcu.column_name AS src_col,
                  ccu.table_name AS dst_table, ccu.column_name AS dst_col
           FROM information_schema.table_constraints tc
           JOIN information_schema.key_column_usage kcu
             ON kcu.constraint_name = tc.constraint_name
            AND kcu.table_schema = tc.table_schema
           JOIN information_schema.constraint_column_usage ccu
             ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
           WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
           ORDER BY tc.table_name"""
    )


@st.cache_data(ttl=300)
def enum_values():
    """{enum type name: [labels in order]}"""
    rows = fetch_all(
        """SELECT t.typname, e.enumlabel
           FROM pg_type t JOIN pg_enum e ON e.enumtypid = t.oid
           ORDER BY t.typname, e.enumsortorder"""
    )
    out = {}
    for r in rows:
        out.setdefault(r["typname"], []).append(r["enumlabel"])
    return out


def row_count(table):
    if table not in table_names():          # whitelist check before building SQL
        raise ValueError(f"Unknown table: {table}")
    return fetch_all(f"SELECT COUNT(*) AS n FROM {q(table)}")[0]["n"]


@st.cache_data(ttl=300)
def dictionary_df(table):
    """One table's data dictionary as a DataFrame (types, keys, defaults, comments)."""
    df = fetch_df(
        """SELECT c.ordinal_position AS "#", c.column_name AS "Column",
                  CASE WHEN c.data_type = 'USER-DEFINED' THEN c.udt_name
                       ELSE c.data_type END AS "Type",
                  c.is_nullable AS "Nullable", c.column_default AS "Default",
                  col_description(
                    (quote_ident(c.table_schema) || '.' || quote_ident(c.table_name))::regclass::oid,
                    c.ordinal_position) AS "Description"
           FROM information_schema.columns c
           WHERE c.table_schema = 'public' AND c.table_name = :t
           ORDER BY c.ordinal_position""",
        {"t": table},
    )
    pks = primary_keys().get(table, [])
    fk_map = {f["src_col"]: f"{f['dst_table']}.{f['dst_col']}"
              for f in foreign_keys() if f["src_table"] == table}

    def key_tag(col):
        tags = (["PK"] if col in pks else []) + ([f"FK → {fk_map[col]}"] if col in fk_map else [])
        return ", ".join(tags)

    df.insert(3, "Key", df["Column"].map(key_tag))
    df["Default"] = df["Default"].fillna("")
    df["Description"] = df["Description"].fillna("")
    return df


@st.cache_data(ttl=300)
def view_definition(view):
    rows = fetch_all(
        "SELECT pg_get_viewdef(quote_ident(:v)::regclass, true) AS d", {"v": view}
    )
    return rows[0]["d"] if rows else ""