import streamlit as st
from utils.auth import guard, current_user, normalize_role
from utils.db import fetch_all, fetch_df, run, tx
from utils.notify import notify
from utils.ui import show_flash, attempt, need

guard("notifications")
show_flash()
user = current_user()
uid, role = user["user_id"], normalize_role(user["role_name"])
manage = role in ("DIRECTOR", "SECRETARY")
st.title("🔔 Notifications")


def mark_read(where, params):
    with tx(uid) as c:
        run(c, f"UPDATE notifications SET read_at = now() WHERE user_id = :u AND read_at IS NULL {where}",
            {"u": uid, **params})


tabs = st.tabs(["📥 My inbox"] + (["📤 Send", "🗂️ All sent"] if manage else []))
with tabs[0]:
    rows = fetch_all("""SELECT notification_id, channel::text AS channel, message, application_id, read_at,
                               created_at AT TIME ZONE 'Africa/Kampala' AS created
                        FROM notifications WHERE user_id = :u
                        ORDER BY created_at DESC, notification_id DESC LIMIT 50""", {"u": uid})
    unread = sum(1 for r in rows if r["read_at"] is None)
    c1, c2 = st.columns([4, 1])
    c1.markdown(f"**{unread} unread** · showing {len(rows)}")
    if unread and c2.button("Mark all read", width="stretch"):
        attempt(lambda: mark_read("", {}), "All marked as read.")
    if not rows:
        st.info("Nothing here yet. Updates about your application will appear here.")
    for r in rows:
        with st.container(border=True):
            a, b = st.columns([5, 1])
            a.markdown(("🔴 " if r["read_at"] is None else "") + r["message"])
            a.caption(f"{r['created']:%d %b %Y, %H:%M} · {r['channel']}")
            nid = r["notification_id"]
            if r["application_id"]:
                if b.button("Open", key=f"open_{nid}", width="stretch"):
                    mark_read("AND notification_id = :i", {"i": nid})
                    st.session_state["open_app"] = str(r["application_id"])
                    st.switch_page("views/my_applications.py" if role == "CLIENT" else "views/applications.py")
            elif r["read_at"] is None and b.button("Mark read", key=f"mr_{nid}", width="stretch"):
                attempt(lambda nid=nid: mark_read("AND notification_id = :i", {"i": nid}), "Marked as read.")

if manage:
    with tabs[1]:
        people = fetch_all("""SELECT u.user_id, u.full_name, u.phone, r.role_name FROM users u
                              JOIN roles r ON r.role_id = u.role_id ORDER BY u.full_name""")
        apps = fetch_all("""SELECT a.application_id, c.full_name || ' → ' || a.destination AS label
                            FROM applications a JOIN users c ON c.user_id = a.client_id ORDER BY c.full_name""")
        with st.form("send_notif", clear_on_submit=True):
            to = st.selectbox("Send to *", people,
                              format_func=lambda x: f"{x['full_name']} · {x['role_name']} · {x['phone']}")
            channel = st.radio("Channel", ["SMS", "EMAIL"], horizontal=True)
            msg = st.text_area("Message * (max 300 characters)", max_chars=300)
            about = st.selectbox("About an application (optional)", [None] + apps,
                                 format_func=lambda x: "(none)" if x is None else x["label"])
            submitted = st.form_submit_button("Send", type="primary")
        if submitted:
            def go():
                need(message=msg)
                with tx(uid) as c:
                    notify(c, to["user_id"], msg.strip(), about["application_id"] if about else None, channel)
            attempt(go, "Notification sent.")
    with tabs[2]:
        st.dataframe(fetch_df("""SELECT n.created_at AT TIME ZONE 'Africa/Kampala' AS "When", u.full_name AS "To",
                n.channel::text AS "Channel", n.message AS "Message",
                CASE WHEN n.read_at IS NULL THEN 'unread' ELSE 'read' END AS "Read"
            FROM notifications n JOIN users u ON u.user_id = n.user_id
            ORDER BY n.created_at DESC, n.notification_id DESC LIMIT 300"""),
            width="stretch", hide_index=True)