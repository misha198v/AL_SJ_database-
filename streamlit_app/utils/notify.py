import streamlit as st
from utils.db import fetch_all, run, tx


@st.cache_resource
def ensure_schema():
    """Adds created_at/read_at to notifications once. Skips if present; never hangs."""
    try:
        with tx() as c:
            have = {r[0] for r in run(c, """SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'notifications' AND column_name IN ('created_at', 'read_at')""")}
            if {"created_at", "read_at"} <= have:
                return
            run(c, "SET LOCAL lock_timeout = '3s'")
            run(c, "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now()")
            run(c, "ALTER TABLE notifications ADD COLUMN IF NOT EXISTS read_at timestamptz")
            if "read_at" not in have:
                run(c, "UPDATE notifications SET read_at = now() WHERE read_at IS NULL")
    except Exception as e:
        st.error(f"Could not add notification tracking columns: {e}")
        st.stop()


def unread_count(uid):
    return fetch_all("SELECT COUNT(*) AS n FROM notifications WHERE user_id = :u AND read_at IS NULL",
                     {"u": str(uid)})[0]["n"]


def notify(conn, user_id, message, application_id=None, channel="SMS"):
    """Insert one notification inside the caller's transaction (no real SMS gateway: stored as SENT)."""
    if not user_id:
        return
    run(conn, """INSERT INTO notifications (user_id, application_id, channel, message, status)
                 VALUES (:u, :a, :c, :m, 'SENT')""",
        {"u": str(user_id), "a": str(application_id) if application_id else None,
         "c": channel, "m": message[:300]})


def notify_role(conn, role_name, message, application_id=None):
    ids = [r[0] for r in run(conn, """SELECT u.user_id FROM users u JOIN roles r ON r.role_id = u.role_id
                                      WHERE r.role_name = :r AND u.is_active""", {"r": role_name})]
    for uid in ids:
        notify(conn, uid, message, application_id)