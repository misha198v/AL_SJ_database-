import streamlit as st
from utils.app_detail import new_application_form, render_application
from utils.auth import guard, current_user
from utils.db import fetch_all
from utils.ui import show_flash

guard("my_applications")
show_flash()
user = current_user()
st.title("🧳 My Application")

apps = fetch_all("""SELECT a.application_id, a.destination, a.status::text AS status, ps.stage_name
                    FROM applications a JOIN pipeline_stages ps ON ps.stage_id = a.current_stage_id
                    WHERE a.client_id = :u ORDER BY a.created_at DESC""", {"u": user["user_id"]})
tab_cur, tab_new = st.tabs(["Current application", "➕ New application"])
with tab_cur:
    if not apps:
        st.info("You have no applications yet. Start one in the next tab.")
    else:
        target = st.session_state.pop("open_app", None)       # set by a notification's "Open"
        ids = [str(a["application_id"]) for a in apps]
        if target in ids:
            st.session_state["my_app_pick"] = ids.index(target)
        if len(apps) == 1:
            chosen = apps[0]
        else:
            i = st.selectbox("Application", range(len(apps)), key="my_app_pick",
                             format_func=lambda i: f"{apps[i]['destination']} · {apps[i]['stage_name']}")
            chosen = apps[i]
        render_application(chosen["application_id"], user)
with tab_new:
    new_application_form(user)