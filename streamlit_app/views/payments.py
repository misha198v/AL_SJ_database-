import streamlit as st
from utils.app_detail import payment_buttons
from utils.auth import guard, current_user, perms
from utils.db import fetch_df
from utils.ui import show_flash,gkey

guard("payments")
show_flash()
user = current_user()
p = perms(user["role_name"])
st.title("💳 Payments")
df = fetch_df("""SELECT p.payment_id, p.application_id, c.full_name AS "Client", a.destination AS "Destination",
        p.amount AS "Amount", p.currency AS "Cur", p.payment_method::text AS "Method",
        p.status::text AS "Status", p.transaction_reference AS "Reference",
        p.initiated_at AS "Started", p.completed_at AS "Completed"
    FROM payments p JOIN applications a ON a.application_id = p.application_id
    JOIN users c ON c.user_id = a.client_id ORDER BY p.initiated_at DESC""")
c1, c2, c3 = st.columns(3)
c1.metric("Completed total", f"{df.loc[df['Status'] == 'COMPLETED', 'Amount'].sum():,.0f}")
c2.metric("Pending", int((df["Status"] == "PENDING").sum()))
status = c3.selectbox("Status", ["All"] + sorted(df["Status"].unique()))
view = df if status == "All" else df[df["Status"] == status]
ev = st.dataframe(view, width="stretch", hide_index=True, key=gkey("pay_grid"),
                  column_config={"payment_id": None, "application_id": None},
                  on_select="rerun", selection_mode="single-row")
if ev.selection.rows and ev.selection.rows[0] < len(view) and p["pay_status"]:
    r = view.iloc[ev.selection.rows[0]]
    payment_buttons({"payment_id": r["payment_id"], "amount": r["Amount"], "currency": r["Cur"],
                     "payment_method": r["Method"], "status": r["Status"]}, str(r["application_id"]), user)
elif not p["pay_status"]:
    st.caption("View only. Director and Data Entry Staff change payment status.")