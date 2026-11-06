import streamlit as st
from utils.auth import current_user, demo_login_screen, logout, allowed_pages
from utils.notify import ensure_schema, unread_count

st.set_page_config(page_title="ALSJ Travel Agency", page_icon="✈️", layout="wide")

PAGES = {
    "home":            st.Page("views/home.py", title="Home", icon="🏠", default=True),
    "my_applications": st.Page("views/my_applications.py", title="My Application", icon="🧳"),
    "applications":    st.Page("views/applications.py", title="Applications", icon="📋"),
    "clients":         st.Page("views/clients.py", title="Clients", icon="👥"),
    "employees":       st.Page("views/employees.py", title="Employees", icon="🧑‍💼"),
    "my_clients":      st.Page("views/my_clients.py", title="My Clients", icon="🤝"),
    "documents":       st.Page("views/documents.py", title="Documents", icon="📄"),
    "payments":        st.Page("views/payments.py", title="Payments", icon="💳"),
    "appointments":    st.Page("views/appointments.py", title="Appointments", icon="📅"),
    "notifications":   st.Page("views/notifications.py", title="Notifications", icon="🔔"),
    "analytics":       st.Page("views/analytics.py", title="Analytics", icon="📊"),
    "system_flow":     st.Page("views/system_flow.py", title="System Flow", icon="🧭"),
    "table_viewer":    st.Page("views/table_viewer.py", title="Table Viewer", icon="🗂️"),
    "data_dictionary": st.Page("views/data_dictionary.py", title="Data Dictionary", icon="📖"),
    "erd":             st.Page("views/erd.py", title="ERD Diagram", icon="🗺️"),
    "audit":           st.Page("views/audit.py", title="Audit Log", icon="🛡️"),
}
SECTIONS = {
    "Overview": ["home"],
    "People": ["clients", "employees", "my_clients"],
    "Operations": ["my_applications", "applications", "documents", "payments",
                   "appointments", "notifications"],
    "Insights": ["analytics", "system_flow"],
    "Data & Admin": ["table_viewer", "data_dictionary", "erd", "audit"],
}

user = current_user()
if not user:
    demo_login_screen()
    st.stop()

ensure_schema()

# the menu entry itself turns into 🔴 Notifications (n) when something is unread
n_unread = unread_count(user["user_id"])
PAGES["notifications"] = st.Page(
    "views/notifications.py",
    title="Notifications" + (f" ({n_unread})" if n_unread else ""),
    icon="🔴" if n_unread else "🔔")

allowed = set(allowed_pages(user["role_name"]))
menu = {s: [PAGES[k] for k in keys if k in allowed] for s, keys in SECTIONS.items()}
menu = {s: pages for s, pages in menu.items() if pages}
nav = st.navigation(menu)

if st.session_state.pop("go_home", False):
    st.switch_page(PAGES["home"])


@st.fragment(run_every=10)
def bell(uid):
    """Sidebar bell: re-checks every 10 s and pops a toast when something new arrives."""
    n = unread_count(uid)
    if n > st.session_state.get("seen_unread", 0):
        st.toast(f"🔔 {n - st.session_state.get('seen_unread', 0)} new notification(s)")
    st.session_state["seen_unread"] = n
    if n:
        st.markdown(f"<span style='background:#E4572E;color:#fff;padding:3px 12px;border-radius:14px;"
                    f"font-weight:700'>🔔 {n} unread</span>", unsafe_allow_html=True)
    else:
        st.caption("🔔 No new notifications")


with st.sidebar:
    st.divider()
    bell(user["user_id"])
    st.markdown(f"**{user['full_name']}**")
    st.caption(f"Role: {user['role_name']}")
    st.button("🔄 Switch role", on_click=logout, width="stretch")

nav.run()