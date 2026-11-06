import streamlit as st
from utils.auth import guard
from utils.db import fetch_df

guard("audit")
st.title("🛡️ Audit & History")
t1, t2 = st.tabs(["Audit trail", "Stage history"])
with t1:
    df = fetch_df("SELECT * FROM v_audit_trail ORDER BY created_at DESC LIMIT 500")
    act = st.selectbox("Action", ["All"] + sorted(df["action"].dropna().unique()))
    st.dataframe(df if act == "All" else df[df["action"] == act],
                 width="stretch", hide_index=True)
with t2:
    st.dataframe(fetch_df("""SELECT h.changed_at AS "When", c.full_name AS "Client", a.destination AS "Destination",
            fs.stage_name AS "From", ts.stage_name AS "To", COALESCE(u.full_name, 'system') AS "By"
        FROM stage_history h JOIN applications a ON a.application_id = h.application_id
        JOIN users c ON c.user_id = a.client_id
        LEFT JOIN pipeline_stages fs ON fs.stage_id = h.from_stage_id
        JOIN pipeline_stages ts ON ts.stage_id = h.to_stage_id
        LEFT JOIN users u ON u.user_id = h.changed_by
        ORDER BY h.changed_at DESC, h.history_id DESC LIMIT 500"""),
        width="stretch", hide_index=True)