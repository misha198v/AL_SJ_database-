import streamlit as st
from utils.auth import guard
from utils.schema import table_names, columns_meta, primary_keys, foreign_keys

guard("erd")
st.title("🗺️ Entity Relationship Diagram")

# colour tables by business domain (unknown tables fall back to grey)
GROUPS = {
    "Identity":  (["users", "roles", "client_profiles", "staff_profiles"], "#0E7C86"),
    "Workflow":  (["applications", "pipeline_stages", "stage_history", "documents"], "#F2A541"),
    "Money":     (["payments"], "#76B041"),
    "Operations": (["schedule_records", "notifications", "audit_logs"], "#7D5BA6"),
}
COLOR = {t: c for ts, c in GROUPS.values() for t in ts}

c1, c2, c3 = st.columns(3)
direction = c1.radio("Layout", ["LR", "TB"], horizontal=True,
                     format_func=lambda x: "Left → Right" if x == "LR" else "Top → Down")
show_cols = c2.checkbox("Show columns", value=True)
focus = c3.selectbox("Focus on", ["All tables"] + table_names(only_tables=True))


def build_dot():
    pks, fks = primary_keys(), foreign_keys()
    fk_cols = {(f["src_table"], f["src_col"]) for f in fks}
    tables = table_names(only_tables=True)

    if focus != "All tables":                       # keep only the table + its neighbours
        near = {focus} | {f["dst_table"] for f in fks if f["src_table"] == focus} \
                       | {f["src_table"] for f in fks if f["dst_table"] == focus}
        tables = [t for t in tables if t in near]
        fks = [f for f in fks if f["src_table"] in tables and f["dst_table"] in tables]

    out = ["digraph ERD {",
           f"rankdir={direction}; bgcolor=\"transparent\";",
           "graph [pad=0.3, nodesep=0.5, ranksep=1.1];",
           "node [shape=plaintext, fontname=\"Courier\"];",
           "edge [color=\"#5B6B7B\", dir=both, arrowtail=crow, arrowhead=tee, "
           "fontname=\"Courier\", fontsize=9];"]
    for t in tables:
        color = COLOR.get(t, "#5B6B7B")
        rows = [f'<TR><TD BGCOLOR="{color}" COLSPAN="2"><FONT COLOR="white"><B>{t}</B></FONT></TD></TR>']
        if show_cols:
            for c in columns_meta(t):
                n = c["column_name"]
                tags = (["PK"] if n in pks.get(t, []) else []) + (["FK"] if (t, n) in fk_cols else [])
                rows.append(f'<TR><TD ALIGN="LEFT">{n}</TD><TD ALIGN="RIGHT"><B>{",".join(tags)}</B></TD></TR>')
        out.append(f'"{t}" [label=<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="4">'
                   f'{"".join(rows)}</TABLE>>];')
    for f in fks:
        out.append(f'"{f["src_table"]}" -> "{f["dst_table"]}" [label="{f["src_col"]}"];')
    out.append("}")
    return "\n".join(out)


dot = build_dot()
st.graphviz_chart(dot, width="stretch")

st.markdown(" ".join(f"<span style='background:{c};color:white;padding:2px 8px;border-radius:4px'>{g}</span>"
                     for g, (_, c) in GROUPS.items()), unsafe_allow_html=True)
st.caption("Crow's foot = many side, bar = one side. Built from the live catalog, not a drawing.")
st.download_button("⬇️ Download DOT source", dot, "erd.dot", "text/plain")