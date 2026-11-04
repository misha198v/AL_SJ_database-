import streamlit as st
from utils.app_detail import document_panel
from utils.auth import guard, current_user, normalize_role, perms
from utils.db import fetch_df
from utils.ui import show_flash,gkey

guard("documents")
show_flash()
user = current_user()
p = perms(user["role_name"])
scope = "WHERE a.assigned_agent_id = :u" if normalize_role(user["role_name"]) == "FIELD_AGENT" else ""
df = fetch_df(f"""SELECT d.document_id, d.file_path, d.rejection_reason, c.full_name AS "Client",
        a.destination AS "Destination", d.document_type::text AS "Type",
        d.verification_status::text AS "Status", d.uploaded_at AS "Uploaded"
    FROM documents d JOIN applications a ON a.application_id = d.application_id
    JOIN users c ON c.user_id = a.client_id {scope}
    ORDER BY (d.verification_status = 'PENDING') DESC, d.uploaded_at""",
    {"u": user["user_id"]} if scope else None)

st.title("📄 Document Review Queue")
c1, c2 = st.columns(2)
c1.metric("Pending", int((df["Status"] == "PENDING").sum()))
c2.metric("Total", len(df))
show = st.radio("Show", ["Pending", "All"], horizontal=True)
view = df if show == "All" else df[df["Status"] == "PENDING"]
ev = st.dataframe(view, width="stretch", hide_index=True, key=gkey("doc_grid"),
                  column_config={"document_id": None, "file_path": None, "rejection_reason": None},
                  on_select="rerun", selection_mode="single-row")
if ev.selection.rows and ev.selection.rows[0] < len(view):
    row = view.iloc[ev.selection.rows[0]]
    d = {"document_id": row["document_id"], "file_path": row["file_path"],
         "rejection_reason": row["rejection_reason"], "verification_status": row["Status"]}
    st.markdown(f"**{row['Client']}** · {row['Type']} · {row['Status']}")
    document_panel(d, user, p)
    if not p["decide"]:
        st.caption("Only Field Agents and Data Entry Staff can verify documents (database rule).")
else:
    st.info("👆 Tick a document to open it.")