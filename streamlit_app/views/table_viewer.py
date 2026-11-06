import datetime as dt
import pandas as pd
import streamlit as st
from utils.auth import (guard, current_user, normalize_role, can, hash_password,
                        READ_ONLY_TABLES, HIDDEN_TABLES,NO_ADD_TABLES, LOCKED_COLUMNS)
from utils.db import fetch_all, fetch_df, execute
from utils.schema import (q, list_relations, columns_meta, primary_keys,
                          foreign_keys, enum_values, row_count)

guard("table_viewer")
role = current_user()["role_name"]

# which column to show as a human label when a foreign key points at a table
LABEL_COLS = {"users": "full_name", "roles": "role_name",
              "pipeline_stages": "stage_name", "applications": "destination"}
MIN_D, MAX_D = dt.date(1900, 1, 1), dt.date(2100, 12, 31)


# ---------- small helpers ----------
def py(v):
    """DataFrame cell -> plain Python (NaN -> None, numpy scalar -> int/float/bool)."""
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    return v.item() if hasattr(v, "item") else v


def is_auto(c):
    """Column the database fills itself (identity, nextval, uuid default, now())."""
    d = (c["column_default"] or "").lower()
    return c["is_identity"] == "YES" or any(
        k in d for k in ("nextval", "gen_random_uuid", "uuid_generate", "now()",
                         "current_timestamp", "clock_timestamp"))


def parse_default(c):
    """Simple constant default ('PENDING'::enum -> PENDING). Function defaults -> None."""
    d = c["column_default"]
    if not d:
        return None
    first = d.split("::")[0]
    return None if "(" in first else first.strip("'")


def fk_options(dst_table, dst_col):
    label = LABEL_COLS.get(dst_table)
    sel = f"{q(dst_col)} AS v" + (f", {q(label)}::text AS l" if label else "")
    rows = fetch_all(f"SELECT {sel} FROM {q(dst_table)} ORDER BY 1 LIMIT 500")
    return [(r["v"], f"{r['l']} · {str(r['v'])[:8]}" if label else str(r["v"])) for r in rows]


# ---------- one widget per column, chosen by its type ----------
def render_field(c, key, current=None):
    name, dtype, udt = c["column_name"], c["data_type"], c["udt_name"]
    required = c["is_nullable"] == "NO"
    label = f"{name}{' *' if required else ''}"

    if name in fk_map:                                   # foreign key -> dropdown of parents
        opts = fk_options(*fk_map[name])
        values = ([] if required else [None]) + [v for v, _ in opts]
        labels = {v: l for v, l in opts}
        labels[None] = "— none —"
        idx = values.index(current) if current in values else 0
        return st.selectbox(label, values, index=idx,
                            format_func=lambda v: labels.get(v, str(v)), key=key)

    if dtype == "USER-DEFINED" and udt in enum_values():  # enum -> dropdown of labels
        values = ([] if required else [None]) + enum_values()[udt]
        default = current if current is not None else parse_default(c)
        idx = values.index(default) if default in values else 0
        return st.selectbox(label, values, index=idx,
                            format_func=lambda v: "— none —" if v is None else v, key=key)

    if dtype == "boolean":
        start = bool(current) if current is not None else str(parse_default(c)).lower() == "true"
        return st.checkbox(label, value=start, key=key)

    if dtype == "date":
        start = current if current is not None else (None if not required else dt.date.today())
        return st.date_input(label, value=start, min_value=MIN_D, max_value=MAX_D, key=key)

    if "timestamp" in dtype:
        base = current if current is not None else dt.datetime.now().replace(second=0, microsecond=0)
        d = st.date_input(f"{label} (date)", value=base.date(), min_value=MIN_D,
                          max_value=MAX_D, key=key + "_d")
        t = st.time_input(f"{label} (time)", value=base.time(), key=key + "_t")
        return dt.datetime.combine(d, t)

    if dtype in ("smallint", "integer", "bigint"):
        return st.number_input(label, value=int(current) if current is not None else 0,
                               step=1, key=key)

    if dtype in ("numeric", "double precision", "real"):
        return st.number_input(label, value=float(current) if current is not None else 0.0,
                               step=0.01, format="%.2f", key=key)

    text = str(current) if current is not None else (parse_default(c) or "")
    v = st.text_input(label, value=text, max_chars=c["character_maximum_length"], key=key)
    return v if (v != "" or required) else None


def editable_cols(insert):
    out = []
    for c in meta:
        n = c["column_name"]
        if is_auto(c):
            continue
        if not insert and (table, n) in LOCKED_COLUMNS:
            continue
        if not insert and (n in pks or n == "password_hash"):
            continue
        if "timestamp" in c["data_type"] and c["is_nullable"] == "YES":
            continue                                       # set by the workflow, not by hand
        out.append(c)
    return out


def collect(cols, prefix, row=None):
    """Render widgets for cols; return ({column: value}, [validation errors])."""
    values, errors = {}, []
    for c in cols:
        n = c["column_name"]
        if n == "password_hash":
            pw = st.text_input("password *", type="password", key=f"{prefix}_pw")
            values[n] = hash_password(pw) if pw else None
        else:
            cur = py(row.get(n)) if row is not None else None
            values[n] = render_field(c, f"{prefix}_{n}", cur)
        if c["is_nullable"] == "NO" and values[n] in (None, ""):
            errors.append(f"{n} is required")
    return values, errors


def done(message):
    st.session_state["flash"] = message
    st.session_state["grid_ver"] = st.session_state.get("grid_ver", 0) + 1
    st.rerun()


# ---------- page ----------
if msg := st.session_state.pop("flash", None):
    st.success(msg)

st.title("🗂️ Table Viewer")
hidden = HIDDEN_TABLES.get(normalize_role(role), set())
rels = {r["table_name"]: r["table_type"] for r in list_relations()
        if r["table_name"] not in hidden}
table = st.selectbox("Table or view", list(rels),
                     format_func=lambda t: ("📋 " if rels[t] == "BASE TABLE" else "👁️ ") + t)

is_view = rels[table] == "VIEW"
read_only = is_view or table in READ_ONLY_TABLES
meta = columns_meta(table)
pks = primary_keys().get(table, [])
pk = pks[0] if len(pks) == 1 else None
fk_map = {f["src_col"]: (f["dst_table"], f["dst_col"])
          for f in foreign_keys() if f["src_table"] == table}
colnames = [c["column_name"] for c in meta]

st.caption(f"{row_count(table):,} rows · {len(meta)} columns · "
           + ("view (read-only)" if is_view else "audit-protected (read-only)" if read_only else "table"))

c1, c2, c3 = st.columns([1, 2, 1])
limit = c1.number_input("Rows to load", 10, 2000, 200, 10)
search = c2.text_input("🔎 Search all columns")
c3.write("")
c3.button("🔄 Refresh", width="stretch")

order_by = next((f"{q(c)} DESC" for c in ("created_at", "initiated_at", "changed_at",
                 "uploaded_at", "scheduled_datetime") if c in colnames), "1")
df = fetch_df(f"SELECT * FROM {q(table)} ORDER BY {order_by} LIMIT :n", {"n": int(limit)})
df = df.drop(columns=["password_hash"], errors="ignore")      # never display hashes
if search:
    mask = df.astype(str).apply(lambda s: s.str.contains(search, case=False, na=False)).any(axis=1)
    df = df[mask]

manageable = (not read_only) and pk is not None
tab_browse, tab_add = st.tabs(["📄 Browse & manage", "➕ Add record"])

with tab_browse:
    ver = st.session_state.get("grid_ver", 0)
    ev = st.dataframe(df, width="stretch", hide_index=True,
                      on_select="rerun" if manageable else "ignore",
                      selection_mode="single-row", key=f"grid_{table}_{ver}")
    st.download_button("⬇️ Download CSV", df.to_csv(index=False), f"{table}.csv", "text/csv")

    if manageable:
        if not ev.selection.rows:
            st.info("👆 Tick a row's checkbox on the left to edit or delete it.")
        else:
            row = df.iloc[ev.selection.rows[0]]
            pk_val = py(row[pk])
            st.markdown(f"#### Selected record · `{pk} = {pk_val}`")

            if can(role, "update"):
                with st.form(f"edit_{table}_{pk_val}"):
                    new, errs = collect(editable_cols(insert=False), f"e_{table}_{pk_val}", row)
                    if st.form_submit_button("💾 Save changes", type="primary"):
                        if errs:
                            st.error("; ".join(errs))
                        else:
                            sets = [f"{q(c)} = :v{i}" for i, c in enumerate(new)]
                            if "updated_at" in colnames:
                                sets.append('"updated_at" = now()')
                            params = {f"v{i}": v for i, v in enumerate(new.values())}
                            params["pk"] = pk_val
                            try:
                                execute(f"UPDATE {q(table)} SET {', '.join(sets)} WHERE {q(pk)} = :pk", params)
                                done("✅ Record updated.")
                            except Exception as e:
                                st.error(f"Update failed: {getattr(e, 'orig', e)}")
            else:
                st.info("Your role cannot edit records.")

            if can(role, "delete"):
                with st.expander("🗑️ Delete this record"):
                    sure = st.checkbox("I understand this cannot be undone", key=f"ok_{table}_{pk_val}")
                    if st.button("Delete record", disabled=not sure, key=f"del_{table}_{pk_val}"):
                        try:
                            execute(f"DELETE FROM {q(table)} WHERE {q(pk)} = :pk", {"pk": pk_val})
                            done("🗑️ Record deleted.")
                        except Exception as e:
                            st.error(f"Delete failed (other rows may depend on it): {getattr(e, 'orig', e)}")

with tab_add:
    if read_only:
        st.info("This relation is read-only.")
    elif table in NO_ADD_TABLES:
        st.info("Use the Clients / Employees pages: they create the user and profile together.")
    elif not can(role, "create"):
        st.info("Your role cannot add records.")
    else:
        with st.form(f"add_{table}"):
            vals, errs = collect(editable_cols(insert=True), f"add_{table}")
            if st.form_submit_button("➕ Insert record", type="primary"):
                if errs:
                    st.error("; ".join(errs))
                else:
                    cols = list(vals)
                    sql = (f"INSERT INTO {q(table)} ({', '.join(q(c) for c in cols)}) "
                           f"VALUES ({', '.join(f':v{i}' for i in range(len(cols)))})")
                    try:
                        execute(sql, {f"v{i}": vals[c] for i, c in enumerate(cols)})
                        done("✅ Record added.")
                    except Exception as e:
                        st.error(f"Insert failed: {getattr(e, 'orig', e)}")