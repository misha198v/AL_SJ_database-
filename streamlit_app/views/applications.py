import streamlit as st
from utils.app_detail import new_application_form, render_application
from utils.auth import guard, current_user, normalize_role
from utils.db import fetch_df
from utils.ui import show_flash,gkey

guard("applications")
show_flash()
user = current_user()
role = normalize_role(user["role_name"])
st.title("📋 Applications")

scope = "WHERE a.assigned_agent_id = :u" if role == "FIELD_AGENT" else ""
df = fetch_df(f"""SELECT o.application_id, o.client_name AS "Client", o.destination AS "Destination",
        o.service_type::text AS "Service", o.stage_order || '. ' || o.stage_name AS "Stage",
        o.status::text AS "Status", o.agent_name AS "Agent", o.preferred_travel_date AS "Travel date"
    FROM v_application_overview o JOIN applications a ON a.application_id = o.application_id
    {scope} ORDER BY o.created_at DESC""", {"u": user["user_id"]} if scope else None)

can_create = role in ("DIRECTOR", "SECRETARY")
tabs = st.tabs(["Applications"] + (["➕ New application"] if can_create else []))

with tabs[0]:
    c1, c2 = st.columns([1, 2])
    stage = c1.selectbox("Stage", ["All"] + sorted(df["Stage"].unique()))
    search = c2.text_input("🔎 Search client, destination or agent")
    view = df if stage == "All" else df[df["Stage"] == stage]
    if search:
        m = view.astype(str).apply(lambda s: s.str.contains(search, case=False, na=False)).any(axis=1)
        view = view[m]

    ev = st.dataframe(view, width="stretch", hide_index=True, key=gkey("apps_grid"),
                      column_config={"application_id": None},
                      on_select="rerun", selection_mode="single-row")
    if ev.selection.rows and ev.selection.rows[0] < len(view):
        st.session_state["open_app"] = str(view.iloc[ev.selection.rows[0]]["application_id"])
    open_id = st.session_state.get("open_app")      # also set by "Open" in Notifications
    if open_id:
        st.divider()
        if st.button("✖ Close application"):
            st.session_state.pop("open_app", None)
            st.session_state["grid_ver"] = st.session_state.get("grid_ver", 0) + 1
            st.rerun()
        render_application(open_id, user)
    else:
        st.info("👆 Tick an application to open it.")

if can_create:
    with tabs[1]:
        new_application_form(user)