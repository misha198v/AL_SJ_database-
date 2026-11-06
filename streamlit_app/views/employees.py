import streamlit as st
from utils.auth import guard, current_user
from utils.db import audit, fetch_all, fetch_df, run, tx
from utils.people import create_staff
from utils.ui import show_flash, attempt

guard("employees")
show_flash()
user = current_user()
st.title("🧑‍💼 Employees")
tab_list, tab_add = st.tabs(["All employees", "➕ Add employee"])

with tab_list:
    df = fetch_df("""SELECT u.user_id, u.full_name AS "Name", r.role_name AS "Role", sp.employee_no AS "Employee no",
            u.phone AS "Phone", u.email AS "Email", sp.date_hired AS "Hired", u.is_active AS "Active"
        FROM users u JOIN staff_profiles sp ON sp.user_id = u.user_id
        JOIN roles r ON r.role_id = u.role_id ORDER BY r.role_name, u.full_name""")
    ev = st.dataframe(df, width="stretch", hide_index=True, column_config={"user_id": None},
                      on_select="rerun", selection_mode="single-row", key="emp_grid")
    if ev.selection.rows:
        row = df.iloc[ev.selection.rows[0]]
        uid = str(row["user_id"])
        label = "Deactivate" if row["Active"] else "Activate"
        st.markdown(f"**{row['Name']}** · {row['Role']}")

        def toggle():
            with tx(user["user_id"]) as c:
                run(c, "UPDATE users SET is_active = NOT is_active WHERE user_id = :u", {"u": uid})
                audit(c, user["user_id"], f"USER_{label.upper()}D", "users", uid)
        if uid == user["user_id"]:
            st.caption("You can't deactivate your own account.")
        elif st.button(f"{label} account"):
            attempt(toggle, f"Account {label.lower()}d.")

with tab_add:
    roles = fetch_all("SELECT role_id, role_name FROM roles WHERE role_name <> 'Client' ORDER BY role_name")
    with st.form("add_emp"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Full name *")
        phone = c2.text_input("Phone *")
        email = c1.text_input("Email")
        pw = c2.text_input("Password * (min 8 characters)", type="password")
        role = c1.selectbox("Role *", roles, format_func=lambda r: r["role_name"])
        emp_no = c2.text_input("Employee number *")
        hired = st.date_input("Date hired")
        if st.form_submit_button("Add employee", type="primary"):
            attempt(lambda: create_staff(user["user_id"], name, phone, pw, role["role_id"], emp_no, email, hired),
                    "Employee added.")