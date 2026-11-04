import datetime as dt
import streamlit as st
from utils.auth import guard, current_user
from utils.db import fetch_df
from utils.people import create_client
from utils.ui import show_flash, attempt

guard("clients")
show_flash()
user = current_user()
st.title("👥 Clients")
tab_list, tab_add = st.tabs(["All clients", "➕ Add client"])

with tab_list:
    search = st.text_input("🔎 Search name, phone or national ID")
    df = fetch_df("""SELECT u.full_name AS "Name", u.phone AS "Phone", u.email AS "Email",
            cp.national_id AS "National ID", cp.date_of_birth AS "Date of birth", cp.address AS "Address",
            COUNT(a.application_id) AS "Applications", u.is_active AS "Active"
        FROM users u JOIN client_profiles cp ON cp.user_id = u.user_id
        LEFT JOIN applications a ON a.client_id = u.user_id
        GROUP BY u.user_id, cp.user_id ORDER BY u.full_name""")
    if search:
        m = df.astype(str).apply(lambda s: s.str.contains(search, case=False, na=False)).any(axis=1)
        df = df[m]
    st.caption(f"{len(df)} client(s)")
    st.dataframe(df, width="stretch", hide_index=True)

with tab_add:
    with st.form("add_client"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Full name *")
        phone = c2.text_input("Phone *")
        pw = c1.text_input("Password * (min 8 characters)", type="password")
        nid = c2.text_input("National ID *")
        email = c1.text_input("Email")
        dob = c2.date_input("Date of birth", value=None, min_value=dt.date(1900, 1, 1),
                            max_value=dt.date.today())
        addr = st.text_input("Address")
        if st.form_submit_button("Add client", type="primary"):
            attempt(lambda: create_client(user["user_id"], name, phone, pw, nid, email, dob, addr),
                    "Client added.")