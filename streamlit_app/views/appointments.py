import datetime as dt
import streamlit as st
from utils.auth import guard, current_user, normalize_role
from utils.db import fetch_all, fetch_df, run, tx
from utils.ui import show_flash, attempt, need,gkey
from utils.notify import notify
guard("appointments")
show_flash()
user = current_user()
manage = normalize_role(user["role_name"]) in ("DIRECTOR", "SECRETARY")
st.title("📅 Appointments")

scope = "" if manage else "WHERE s.client_id = :u OR s.staff_id = :u"
df = fetch_df(f"""SELECT s.schedule_id, c.full_name AS "Client", sf.full_name AS "Staff",
        s.appointment_type AS "Type", s.scheduled_datetime AT TIME ZONE 'Africa/Kampala' AS "When (Kampala)",
        s.status::text AS "Status"
    FROM schedule_records s JOIN users c ON c.user_id = s.client_id JOIN users sf ON sf.user_id = s.staff_id
    {scope} ORDER BY s.scheduled_datetime DESC""", {"u": user["user_id"]} if scope else None)

tabs = st.tabs(["Schedule"] + (["➕ New appointment"] if manage else []))
with tabs[0]:
    show = st.radio("Show", ["Upcoming", "All"], horizontal=True)
    view = df if show == "All" else df[df["Status"] == "UPCOMING"]
    ev = st.dataframe(view, width="stretch", hide_index=True, key=gkey("appt_grid"),
                      column_config={"schedule_id": None},
                      on_select="rerun" if manage else "ignore", selection_mode="single-row")
    if manage and ev.selection.rows and ev.selection.rows[0] < len(view):
        r = view.iloc[ev.selection.rows[0]]
        sid = str(r["schedule_id"])
        if r["Status"] == "UPCOMING":
                def setst(s):
                    with tx(user["user_id"]) as c:
                        row = run(c, """UPDATE schedule_records SET status = :s WHERE schedule_id = :i
                                    RETURNING client_id, staff_id, appointment_type""",
                              {"s": s, "i": sid}).mappings().first()
                    msg = f"📅 Your {row['appointment_type']} appointment was {s.lower()}."
                    notify(c, row["client_id"], msg)
                    notify(c, row["staff_id"], msg)
        else:
            st.caption(f"This appointment is already {r['Status'].lower()}.")

if manage:
    with tabs[1]:
        clients = fetch_all("""SELECT u.user_id, u.full_name FROM users u
                               JOIN client_profiles c ON c.user_id = u.user_id ORDER BY u.full_name""")
        staff = fetch_all("""SELECT u.user_id, u.full_name FROM users u
                             JOIN staff_profiles s ON s.user_id = u.user_id ORDER BY u.full_name""")
        with st.form("new_appt"):
            c1, c2 = st.columns(2)
            client = c1.selectbox("Client *", clients, format_func=lambda x: x["full_name"])
            member = c2.selectbox("Staff member *", staff, format_func=lambda x: x["full_name"])
            kind = c1.text_input("Type *", value="Consultation")
            d = c1.date_input("Date *", min_value=dt.date.today())
            t = c2.time_input("Time (Kampala) *", value=dt.time(9, 0))
            if st.form_submit_button("Book appointment", type="primary"):
                def go():
                    need(type=kind)
                    with tx(user["user_id"]) as c:
                        run(c, """INSERT INTO schedule_records (client_id, staff_id, appointment_type, scheduled_datetime)
                                  VALUES (:c, :s, :t, CAST(:w AS timestamp) AT TIME ZONE 'Africa/Kampala')""",
                            {"c": client["user_id"], "s": member["user_id"], "t": kind.strip(),
                             "w": dt.datetime.combine(d, t)})
                        msg = f"📅 {kind.strip()} booked for {d:%a %d %b %Y} at {t:%H:%M}."
                        notify(c, client["user_id"], msg)
                        notify(c, member["user_id"], msg)
                attempt(go, "Appointment booked.")