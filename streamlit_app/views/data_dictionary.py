import streamlit as st
from utils.auth import guard
from utils.schema import (list_relations, dictionary_df, foreign_keys, enum_values,
                          columns_meta, row_count, view_definition, table_names)

guard("data_dictionary")
st.title("📖 Data Dictionary")
st.caption("Generated live from the PostgreSQL catalog. It can't go out of date.")

rels = {r["table_name"]: r["table_type"] for r in list_relations()}
tab1, tab2 = st.tabs(["By table", "Full dictionary"])

with tab1:
    t = st.selectbox("Table or view", list(rels),
                     format_func=lambda x: ("📋 " if rels[x] == "BASE TABLE" else "👁️ ") + x)
    meta = columns_meta(t)
    m1, m2, m3 = st.columns(3)
    m1.metric("Type", "Table" if rels[t] == "BASE TABLE" else "View")
    m2.metric("Columns", len(meta))
    m3.metric("Rows", f"{row_count(t):,}")

    st.dataframe(dictionary_df(t), width="stretch", hide_index=True)

    used = {c["udt_name"] for c in meta if c["data_type"] == "USER-DEFINED"}
    if used:
        with st.expander("🎛️ Allowed values (enum types)"):
            for name in sorted(used):
                st.markdown(f"**{name}**: " + " · ".join(f"`{v}`" for v in enum_values().get(name, [])))

    fks = foreign_keys()
    out = [f for f in fks if f["src_table"] == t]
    inc = [f for f in fks if f["dst_table"] == t]
    cl, cr = st.columns(2)
    with cl:
        st.markdown("**References (this table points to)**")
        for f in out:
            st.write(f"`{f['src_col']}` → `{f['dst_table']}.{f['dst_col']}`")
        if not out:
            st.caption("none")
    with cr:
        st.markdown("**Referenced by (other tables point here)**")
        for f in inc:
            st.write(f"`{f['src_table']}.{f['src_col']}` → `{f['dst_col']}`")
        if not inc:
            st.caption("none")

    if rels[t] == "VIEW":
        st.markdown("**View definition**")
        st.code(view_definition(t), language="sql")

with tab2:
    names = table_names()
    md = ["# Data Dictionary\n"]
    for n in names:
        d = dictionary_df(n)
        md.append(f"## {n}\n")
        md.append("| " + " | ".join(d.columns) + " |")
        md.append("|" + "---|" * len(d.columns))
        for _, r in d.iterrows():
            md.append("| " + " | ".join(str(x) for x in r) + " |")
        md.append("")
        with st.expander(f"{n}  ·  {len(d)} columns"):
            st.dataframe(d, width="stretch", hide_index=True)
    st.download_button("⬇️ Download as Markdown", "\n".join(md),
                       "data_dictionary.md", "text/markdown")