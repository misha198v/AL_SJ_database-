import datetime as dt
import os
import uuid

import pandas as pd
import streamlit as st
from sqlalchemy.exc import ProgrammingError

from utils.auth import normalize_role, perms
from utils.db import audit, fetch_all, fetch_df, run, tx
from utils.ui import FormError, attempt, need, stepper

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
AGENTS_SQL = """SELECT u.user_id, u.full_name FROM users u JOIN roles r ON r.role_id = u.role_id
                WHERE r.role_name = 'Field Agent' AND u.is_active ORDER BY u.full_name"""
PAY_SQL = {  # allowed payment transitions (same rules as the Django version)
    "COMPLETED": """UPDATE payments SET status = 'COMPLETED', completed_at = now(),
                    transaction_reference = 'SIM-' || upper(substr(md5(random()::text), 1, 10))
                    WHERE payment_id = :p AND application_id = :a AND status = 'PENDING'""",
    "FAILED": "UPDATE payments SET status = 'FAILED' WHERE payment_id = :p AND application_id = :a AND status = 'PENDING'",
    "REFUNDED": "UPDATE payments SET status = 'REFUNDED' WHERE payment_id = :p AND application_id = :a AND status = 'COMPLETED'",
}


# ---------- access + loading ----------
def can_see(user, app):
    role = normalize_role(user["role_name"])
    if role == "CLIENT":
        return str(app["client_id"]) == user["user_id"]          # only their own
    if role == "FIELD_AGENT":
        return str(app["assigned_agent_id"]) == user["user_id"]  # only assigned ones
    return role in ("DIRECTOR", "SECRETARY", "DATA_ENTRY_STAFF")


def load_app(app_id):
    rows = fetch_all(
        """SELECT a.*, c.full_name AS client_name, c.phone AS client_phone, ag.full_name AS agent_name,
                  ps.stage_name, ps.stage_order
           FROM applications a JOIN users c ON c.user_id = a.client_id
           JOIN pipeline_stages ps ON ps.stage_id = a.current_stage_id
           LEFT JOIN users ag ON ag.user_id = a.assigned_agent_id
           WHERE a.application_id = :a""", {"a": str(app_id)})
    return rows[0] if rows else None


def move_stage(user, app_id, stage_id):
    """Prefer the DB routine change_stage(); fall back to the same steps by hand."""
    args = {"a": str(app_id), "s": int(stage_id), "u": user["user_id"]}
    try:
        with tx(user["user_id"]) as c:
            run(c, "SELECT change_stage(:a, :s, :u)", args)
    except ProgrammingError as e:
        if "change_stage" not in str(e):
            raise
        with tx(user["user_id"]) as c:
            old = run(c, "SELECT current_stage_id FROM applications WHERE application_id = :a FOR UPDATE", args).scalar()
            run(c, "UPDATE applications SET current_stage_id = :s WHERE application_id = :a", args)
            run(c, """INSERT INTO stage_history (application_id, from_stage_id, to_stage_id, changed_by)
                      VALUES (:a, :o, :s, :u)""", {**args, "o": old})


# ---------- live tracker (refreshes itself every 5 s) ----------
@st.fragment(run_every=5)
def live_tracker(app_id):
    app = load_app(app_id)
    stages = fetch_all("SELECT stage_order, stage_name FROM pipeline_stages ORDER BY stage_order")
    stepper(stages, app["stage_order"])
    st.progress(app["stage_order"] / len(stages),
                text=f"Stage {app['stage_order']} of {len(stages)} · {app['stage_name']}")
    hist = fetch_df(
        """SELECT h.changed_at AS "When", fs.stage_name AS "From", ts.stage_name AS "To",
                  COALESCE(u.full_name, 'system') AS "By"
           FROM stage_history h LEFT JOIN pipeline_stages fs ON fs.stage_id = h.from_stage_id
           JOIN pipeline_stages ts ON ts.stage_id = h.to_stage_id
           LEFT JOIN users u ON u.user_id = h.changed_by
           WHERE h.application_id = :a ORDER BY h.changed_at, h.history_id""", {"a": str(app_id)})
    hist["From"] = hist["From"].fillna("(start)")
    st.caption("🔴 Live: refreshes every 5 seconds")
    st.dataframe(hist, width="stretch", hide_index=True)


# ---------- documents ----------
def decision_form(d, user):
    key = f"dec_{d['document_id']}"
    decision = st.radio("Decision", ["VERIFIED", "REJECTED"], horizontal=True, key=key + "_d")
    reason = st.text_input("Reason (required if rejecting)", key=key + "_r")

    def go():
        if decision == "REJECTED":
            need(reason=reason)
        with tx(user["user_id"]) as c:
            n = run(c, """UPDATE documents SET verification_status = :s, verified_by = :u,
                                 verified_at = now(), rejection_reason = :r
                          WHERE document_id = :d AND verification_status = 'PENDING'""",
                    {"s": decision, "u": user["user_id"], "d": str(d["document_id"]),
                     "r": reason.strip() if decision == "REJECTED" else None}).rowcount
            if n == 0:
                raise FormError("This document was already decided.")

    if st.button("Save decision", key=key + "_b", type="primary"):
        attempt(go, "Decision saved.")


def document_panel(d, user, p):
    path = os.path.join(UPLOAD_DIR, d["file_path"])
    if os.path.exists(path):
        with open(path, "rb") as f:
            st.download_button("⬇️ Download file", f.read(), os.path.basename(path),
                               key=f"dl_{d['document_id']}")
    else:
        st.caption(f"File on record: {d['file_path']} (not stored on this machine)")
    if isinstance(d["rejection_reason"], str) and d["rejection_reason"]:
        st.warning(f"Rejected: {d['rejection_reason']}")
    if p["decide"] and d["verification_status"] == "PENDING":
        decision_form(d, user)


def documents_section(app, user, p):
    aid = str(app["application_id"])
    docs = fetch_all(
        """SELECT d.*, v.full_name AS verifier FROM documents d
           LEFT JOIN users v ON v.user_id = d.verified_by
           WHERE d.application_id = :a ORDER BY d.uploaded_at""", {"a": aid})
    if not docs:
        st.info("No documents uploaded yet.")
    for d in docs:
        icon = {"VERIFIED": "✅", "REJECTED": "❌"}.get(d["verification_status"], "⏳")
        with st.expander(f"{icon} {d['document_type'].replace('_', ' ').title()} · {d['verification_status']}"
                         + (f" · by {d['verifier']}" if d["verifier"] else "")):
            document_panel(d, user, p)

    if p["is_client"]:
        st.markdown("**Upload a document**")
        n = st.session_state.get(f"upn_{aid}", 0)           # bump to clear the file box after upload
        dtype = st.selectbox("Document type", ["PASSPORT", "NATIONAL_ID", "TRAVEL_DECLARATION"],
                             format_func=lambda x: x.replace("_", " ").title(), key=f"up_t_{aid}")
        f = st.file_uploader("PDF, JPG or PNG, max 5 MB", type=["pdf", "jpg", "jpeg", "png"],
                             key=f"up_f_{aid}_{n}")

        def go():
            data = f.getvalue()
            if not 1 <= len(data) <= 5 * 1024 * 1024:
                raise FormError("The file must be between 1 byte and 5 MB.")
            ext = f.name.rsplit(".", 1)[-1].lower()
            rel = f"documents/{aid}/{dtype}_{uuid.uuid4().hex[:8]}.{ext}"
            full = os.path.join(UPLOAD_DIR, rel)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "wb") as out:
                out.write(data)
            with tx(user["user_id"]) as c:
                run(c, """INSERT INTO documents (application_id, document_type, file_path, file_size_bytes)
                          VALUES (:a, :t, :p, :s)""", {"a": aid, "t": dtype, "p": rel, "s": len(data)})
            st.session_state[f"upn_{aid}"] = n + 1

        if st.button("Upload", disabled=f is None, key=f"up_b_{aid}", type="primary"):
            attempt(go, "Document uploaded.")


# ---------- payments ----------
def payment_buttons(x, aid, user):
    pid = str(x["payment_id"])
    opts = {"PENDING": [("COMPLETED", "✅ Complete"), ("FAILED", "❌ Fail")],
            "COMPLETED": [("REFUNDED", "↩️ Refund")]}.get(x["status"], [])
    if not opts:
        st.caption("No further actions for this payment.")
        return

    def go(new):
        with tx(user["user_id"]) as c:
            if run(c, PAY_SQL[new], {"p": pid, "a": aid}).rowcount == 0:
                raise FormError("That payment is not in a state that allows this action.")

    cols = st.columns(len(opts) + 1)
    cols[0].write(f"{float(x['amount']):,.0f} {x['currency']} · {x['payment_method']} · {x['status']}")
    for i, (new, label) in enumerate(opts, start=1):
        if cols[i].button(label, key=f"pay_{pid}_{new}"):
            attempt(lambda new=new: go(new), f"Payment marked {new.lower()}.")


def payments_section(app, user, p):
    aid = str(app["application_id"])
    pays = fetch_all("SELECT * FROM payments WHERE application_id = :a ORDER BY initiated_at", {"a": aid})
    if pays:
        paid = sum(float(x["amount"]) for x in pays if x["status"] == "COMPLETED")
        st.metric("Paid so far (completed)", f"{paid:,.0f} {pays[0]['currency']}")
        df = pd.DataFrame(pays)[["initiated_at", "amount", "currency", "payment_method",
                                 "status", "transaction_reference", "completed_at"]]
        st.dataframe(df, width="stretch", hide_index=True)
    else:
        st.info("No payments yet.")
    if p["pay_status"]:
        for x in pays:
            payment_buttons(x, aid, user)
    if p["is_client"]:
        st.markdown("**Make a payment** (the provider's reply is simulated by staff)")
        with st.form(f"pay_{aid}"):
            amount = st.number_input("Amount (UGX)", min_value=1.0, step=1000.0)
            method = st.selectbox("Mobile money", ["MTN_MOMO", "AIRTEL_MONEY"],
                                  format_func=lambda m: m.replace("_", " ").title())
            phone = st.text_input("Payer phone")
            if st.form_submit_button("Pay", type="primary"):
                def go():
                    need(payer_phone=phone)
                    with tx(user["user_id"]) as c:
                        run(c, """INSERT INTO payments (application_id, amount, payment_method, payer_phone)
                                  VALUES (:a, :m, :t, :p)""",
                            {"a": aid, "m": amount, "t": method, "p": phone.strip()})
                attempt(go, "Payment started. Waiting for the provider.")


# ---------- staff actions ----------
def manage_panel(app, user, p):
    if not (p["assign"] or p["stage"]):
        return
    aid = str(app["application_id"])
    with st.expander("⚙️ Manage this application"):
        if p["assign"]:
            agents = fetch_all(AGENTS_SQL)
            ids = [None] + [a["user_id"] for a in agents]
            names = {a["user_id"]: a["full_name"] for a in agents}
            cur = app["assigned_agent_id"]
            pick = st.selectbox("Field Agent", ids, index=ids.index(cur) if cur in ids else 0,
                                format_func=lambda i: names.get(i, "(none)"), key=f"ag_{aid}")

            def assign():
                with tx(user["user_id"]) as c:
                    run(c, "UPDATE applications SET assigned_agent_id = :g WHERE application_id = :a",
                        {"g": pick, "a": aid})
                    audit(c, user["user_id"], "APPLICATION_ASSIGNED", "applications", aid)
            if st.button("Assign agent", key=f"ag_b_{aid}"):
                attempt(assign, "Agent assigned.")
        if p["stage"]:
            stages = fetch_all("SELECT stage_id, stage_order, stage_name FROM pipeline_stages ORDER BY stage_order")
            sid = st.selectbox("Move to stage", [s["stage_id"] for s in stages],
                               index=app["stage_order"] - 1,
                               format_func=lambda i: next(f"{s['stage_order']}. {s['stage_name']}"
                                                          for s in stages if s["stage_id"] == i),
                               key=f"st_{aid}")
            if st.button("Move stage", key=f"st_b_{aid}"):
                attempt(lambda: move_stage(user, aid, sid), "Stage updated.")


# ---------- create ----------
def new_application_form(user):
    staff = not perms(user["role_name"])["is_client"]
    with st.form("new_app"):
        client_id, agent = user["user_id"], None
        if staff:
            clients = fetch_all("""SELECT u.user_id, u.full_name, u.phone FROM users u
                                   JOIN client_profiles cp ON cp.user_id = u.user_id ORDER BY u.full_name""")
            client = st.selectbox("Client *", clients, format_func=lambda c: f"{c['full_name']} ({c['phone']})")
            client_id = client["user_id"] if client else None
        service = st.selectbox("Service *", ["LABOUR_MIGRATION", "DOMESTIC_TOURISM"],
                               format_func=lambda s: s.replace("_", " ").title())
        destination = st.text_input("Destination *")
        purpose = st.text_input("Purpose")
        travel = st.date_input("Preferred travel date *", value=dt.date.today() + dt.timedelta(days=30),
                               min_value=dt.date.today())
        if staff:
            agents = fetch_all(AGENTS_SQL)
            agent = st.selectbox("Assign a Field Agent (optional)", [None] + agents,
                                 format_func=lambda a: "(none yet)" if a is None else a["full_name"])
        if st.form_submit_button("Create application", type="primary"):
            def go():
                need(destination=destination, client=client_id)
                with tx(user["user_id"]) as c:
                    aid = run(c, """INSERT INTO applications (client_id, assigned_agent_id, current_stage_id,
                                        service_type, destination, travel_purpose, preferred_travel_date, status)
                                    VALUES (:c, :g, (SELECT stage_id FROM pipeline_stages WHERE stage_order = 1),
                                            :s, :d, :t, :dt, 'ACTIVE') RETURNING application_id""",
                              {"c": client_id, "g": agent["user_id"] if agent else None, "s": service,
                               "d": destination.strip(), "t": purpose.strip() or None, "dt": travel}).scalar()
                    # first history row, unless the DB trigger already wrote it
                    run(c, """INSERT INTO stage_history (application_id, from_stage_id, to_stage_id, changed_by)
                              SELECT :a, NULL, (SELECT stage_id FROM pipeline_stages WHERE stage_order = 1), NULL
                              WHERE NOT EXISTS (SELECT 1 FROM stage_history WHERE application_id = :a)""",
                        {"a": aid})
                    audit(c, user["user_id"], "APPLICATION_REGISTERED", "applications", aid)
            attempt(go, "Application created.")


# ---------- the whole workspace ----------
def render_application(app_id, user):
    app = load_app(app_id)
    if not app:
        st.error("Application not found.")
        return
    if not can_see(user, app):
        st.error("🚫 You are not allowed to view this application.")
        return
    p = perms(user["role_name"])
    st.subheader(f"{app['destination']} · {app['service_type'].replace('_', ' ').title()}")
    c = st.columns(4)
    c[0].metric("Status", app["status"])
    c[1].metric("Field Agent", app["agent_name"] or "Not assigned yet")
    c[2].metric("Travel date", str(app["preferred_travel_date"]))
    if not p["is_client"]:
        c[3].metric("Client", app["client_name"])
        st.caption(f"Client phone: {app['client_phone']}")
    live_tracker(str(app_id))
    manage_panel(app, user, p)
    t1, t2 = st.tabs(["📄 Documents", "💳 Payments"])
    with t1:
        documents_section(app, user, p)
    with t2:
        payments_section(app, user, p)