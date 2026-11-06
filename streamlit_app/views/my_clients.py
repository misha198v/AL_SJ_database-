import streamlit as st
from utils.auth import guard, current_user
from utils.db import fetch_df

guard("my_clients")
user = current_user()
st.title("🤝 My Clients")
st.caption("Clients whose applications are assigned to you.")
st.dataframe(fetch_df("""SELECT c.full_name AS "Client", c.phone AS "Phone", a.destination AS "Destination",
        ps.stage_order || '. ' || ps.stage_name AS "Stage", a.status::text AS "Status",
        a.preferred_travel_date AS "Travel date"
    FROM applications a JOIN users c ON c.user_id = a.client_id
    JOIN pipeline_stages ps ON ps.stage_id = a.current_stage_id
    WHERE a.assigned_agent_id = :u ORDER BY a.preferred_travel_date""", {"u": user["user_id"]}),
    width="stretch", hide_index=True)