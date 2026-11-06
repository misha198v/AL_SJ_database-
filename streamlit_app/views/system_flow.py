import streamlit as st
from utils.auth import guard
from utils.db import fetch_all, fetch_df

guard("system_flow")
st.title("🧭 System Flow")
tab1, tab2, tab3 = st.tabs(["Live pipeline", "Process & data flow", "Trace one application"])

# ---------------- 1. live 7-stage pipeline ----------------
with tab1:
    stages = fetch_all(
        """SELECT ps.stage_id, ps.stage_order, ps.stage_name, ps.description,
                  COUNT(a.application_id) AS n
           FROM pipeline_stages ps
           LEFT JOIN applications a ON a.current_stage_id = ps.stage_id
           GROUP BY ps.stage_id, ps.stage_order, ps.stage_name, ps.description
           ORDER BY ps.stage_order""")
    nodes = [f'"{s["stage_id"]}" [label="{s["stage_order"]}. {s["stage_name"]}\\n{s["n"]} application(s)", '
             f'fillcolor="{"#0E7C86" if s["n"] else "#B8C4CC"}"];' for s in stages]
    ids = [s["stage_id"] for s in stages]
    edges = [f'"{a}" -> "{b}";' for a, b in zip(ids, ids[1:])]
    dot = ('digraph P { rankdir=LR; bgcolor="transparent"; '
           'node [shape=box, style="rounded,filled", fontname="Courier", fontcolor=white, margin="0.2,0.12"]; '
           'edge [color="#5B6B7B"]; ' + " ".join(nodes + edges) + " }")
    st.graphviz_chart(dot, width="stretch")
    st.caption("Teal stages currently hold applications. Grey stages are empty.")
    st.dataframe([{"Order": s["stage_order"], "Stage": s["stage_name"],
                   "Applications": s["n"], "Description": s["description"]} for s in stages],
                 width="stretch", hide_index=True)

# ---------------- 2. who does what, and which tables are touched ----------------
with tab2:
    FLOW = """
    digraph F {
      rankdir=LR; bgcolor="transparent";
      node [shape=box, style="rounded,filled", fillcolor="white", color="#0E7C86",
            fontname="Courier", fontsize=11];
      edge [color="#5B6B7B", fontname="Courier", fontsize=9];

      subgraph cluster_client { label="CLIENT"; fontname="Courier"; style="filled,rounded"; color="#E6F2F7";
        submit [label="Submit application\\n[applications]"];
        upload [label="Upload documents\\n[documents]"];
        pay    [label="Pay via MoMo / Airtel\\n[payments]"]; }

      subgraph cluster_sec { label="SECRETARY"; fontname="Courier"; style="filled,rounded"; color="#FDF1DC";
        verify [label="Verify / reject documents\\n[documents]"];
        assign [label="Assign agent\\n[applications]"];
        appt   [label="Book appointments\\n[schedule_records]"]; }

      subgraph cluster_agent { label="AGENT"; fontname="Courier"; style="filled,rounded"; color="#E8F3DE";
        advance [label="Advance pipeline stage\\n[applications]"]; }

      subgraph cluster_dir { label="DIRECTOR"; fontname="Courier"; style="filled,rounded"; color="#EDE6F5";
        reports [label="KPIs and revenue\\n[rpt_* views]"]; }

      subgraph cluster_sys { label="SYSTEM"; fontname="Courier"; style="filled,rounded"; color="#EEF1F3";
        provider [label="Provider reply (simulated)\\n[payments.status]"];
        history  [label="Stage history record\\n[stage_history]"];
        notify   [label="Notify client\\n[notifications]"];
        audit    [label="Audit trail\\n[audit_logs]"]; }

      submit -> upload -> verify -> assign -> advance;
      submit -> pay -> provider -> reports;
      advance -> history; advance -> notify; verify -> notify;
      assign -> appt;
      verify -> audit [style=dashed]; advance -> audit [style=dashed]; provider -> audit [style=dashed];
    }"""
    st.graphviz_chart(FLOW, width="stretch")
    st.caption("Solid arrows = business flow. Dashed = audit logging. Brackets = tables written.")

# ---------------- 3. follow a single application end to end ----------------
with tab3:
    apps = fetch_all("""SELECT application_id, client_name, destination, stage_name
                        FROM v_application_overview ORDER BY created_at DESC LIMIT 200""")
    if not apps:
        st.info("No applications yet.")
        st.stop()
    a = st.selectbox("Application", apps,
                     format_func=lambda x: f"{x['client_name']} → {x['destination']}  ({x['stage_name']})")
    aid = str(a["application_id"])

    st.markdown("**Stage history**")
    st.dataframe(fetch_df(
        """SELECT h.changed_at AS "When", fs.stage_name AS "From", ts.stage_name AS "To",
                  u.full_name AS "By"
           FROM stage_history h
           LEFT JOIN pipeline_stages fs ON fs.stage_id = h.from_stage_id
           JOIN pipeline_stages ts ON ts.stage_id = h.to_stage_id
           LEFT JOIN users u ON u.user_id = h.changed_by
           WHERE h.application_id = :a ORDER BY h.changed_at""", {"a": aid}),
        width="stretch", hide_index=True)

    cl, cr = st.columns(2)
    with cl:
        st.markdown("**Documents**")
        st.dataframe(fetch_df(
            """SELECT document_type::text AS "Type", verification_status::text AS "Status",
                      rejection_reason AS "Reason"
               FROM documents WHERE application_id = :a ORDER BY uploaded_at""", {"a": aid}),
            width="stretch", hide_index=True)
    with cr:
        st.markdown("**Payments**")
        st.dataframe(fetch_df(
            """SELECT amount AS "Amount", currency AS "Cur", payment_method::text AS "Method",
                      status::text AS "Status"
               FROM payments WHERE application_id = :a ORDER BY initiated_at""", {"a": aid}),
            width="stretch", hide_index=True)