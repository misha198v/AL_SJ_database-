import streamlit as st
from utils.auth import guard, current_user, normalize_role
from utils.db import fetch_all, fetch_df
from utils.ui import show_flash, stepper

guard("home")
show_flash()
user = current_user()
uid, role = user["user_id"], normalize_role(user["role_name"])
st.title(f"Welcome, {user['full_name']} 👋")
st.caption(f"Signed in as {user['role_name']}")

PEND_DOCS = "SELECT COUNT(*) AS n FROM documents WHERE verification_status = 'PENDING'"
MY_DOCS = ("SELECT COUNT(*) AS n FROM documents d JOIN applications a ON a.application_id = d.application_id "
           "WHERE d.verification_status = 'PENDING' AND a.{col} = :u")
METRICS = {
    "DIRECTOR": [("Applications", "SELECT COUNT(*) AS n FROM applications"),
                 ("Clients", "SELECT COUNT(*) AS n FROM client_profiles"),
                 ("Employees", "SELECT COUNT(*) AS n FROM staff_profiles"), ("Docs awaiting review", PEND_DOCS)],
    "SECRETARY": [("Clients", "SELECT COUNT(*) AS n FROM client_profiles"),
                  ("Active applications", "SELECT COUNT(*) AS n FROM applications WHERE status = 'ACTIVE'"),
                  ("Without an agent", "SELECT COUNT(*) AS n FROM applications WHERE assigned_agent_id IS NULL"),
                  ("Upcoming appointments", "SELECT COUNT(*) AS n FROM schedule_records WHERE status = 'UPCOMING'")],
    "FIELD_AGENT": [("My applications", "SELECT COUNT(*) AS n FROM applications WHERE assigned_agent_id = :u"),
                    ("Docs to review", MY_DOCS.format(col="assigned_agent_id")),
                    ("My upcoming appointments",
                     "SELECT COUNT(*) AS n FROM schedule_records WHERE staff_id = :u AND status = 'UPCOMING'")],
    "DATA_ENTRY_STAFF": [("Docs awaiting review", PEND_DOCS),
                         ("Pending payments", "SELECT COUNT(*) AS n FROM payments WHERE status = 'PENDING'"),
                         ("Applications", "SELECT COUNT(*) AS n FROM applications")],
    "CLIENT": [("My applications", "SELECT COUNT(*) AS n FROM applications WHERE client_id = :u"),
               ("Docs awaiting review", MY_DOCS.format(col="client_id")),
               ("Pending payments", "SELECT COUNT(*) AS n FROM payments p JOIN applications a "
                                    "ON a.application_id = p.application_id WHERE p.status = 'PENDING' AND a.client_id = :u"),
               ("Upcoming appointments",
                "SELECT COUNT(*) AS n FROM schedule_records WHERE client_id = :u AND status = 'UPCOMING'")],
}
items = METRICS.get(role, [])
for col, (label, sql) in zip(st.columns(len(items) or 1), items):
    col.metric(label, fetch_all(sql, {"u": uid} if ":u" in sql else None)[0]["n"])

st.divider()
if role == "CLIENT":
    mine = fetch_all("""SELECT a.destination, ps.stage_order, ps.stage_name FROM applications a
                        JOIN pipeline_stages ps ON ps.stage_id = a.current_stage_id
                        WHERE a.client_id = :u ORDER BY a.created_at DESC LIMIT 1""", {"u": uid})
    if mine:
        st.subheader(f"Your trip to {mine[0]['destination']}")
        stepper(fetch_all("SELECT stage_order, stage_name FROM pipeline_stages ORDER BY stage_order"),
                mine[0]["stage_order"])
    else:
        st.info("Open **My Application** to start your first application.")
elif role == "DIRECTOR":
    st.subheader("Recent activity")
    st.dataframe(fetch_df("SELECT actor_name, actor_role, action, entity_type, created_at "
                          "FROM v_audit_trail ORDER BY created_at DESC LIMIT 8"),
                 width="stretch", hide_index=True)
elif role == "SECRETARY":
    st.subheader("Needs an agent")
    st.dataframe(fetch_df("""SELECT c.full_name AS "Client", a.destination AS "Destination", a.created_at AS "Created"
        FROM applications a JOIN users c ON c.user_id = a.client_id
        WHERE a.assigned_agent_id IS NULL ORDER BY a.created_at"""), width="stretch", hide_index=True)
elif role in ("FIELD_AGENT", "DATA_ENTRY_STAFF"):
    st.subheader("Documents waiting for you")
    scope = "AND a.assigned_agent_id = :u" if role == "FIELD_AGENT" else ""
    st.dataframe(fetch_df(f"""SELECT c.full_name AS "Client", d.document_type::text AS "Type", d.uploaded_at AS "Uploaded"
        FROM documents d JOIN applications a ON a.application_id = d.application_id
        JOIN users c ON c.user_id = a.client_id
        WHERE d.verification_status = 'PENDING' {scope} ORDER BY d.uploaded_at""",
        {"u": uid} if scope else None), width="stretch", hide_index=True)