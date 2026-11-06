import plotly.express as px
import streamlit as st
from utils.auth import guard
from utils.db import fetch_df

guard("analytics")
st.title("📊 Executive Analytics")

PALETTE = ["#0E7C86", "#F2A541", "#5B6B7B", "#E4572E", "#76B041", "#7D5BA6"]


def style(fig):
    fig.update_layout(font=dict(family="monospace"), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=50, b=10),
                      legend_title_text="")
    return fig


rev = fetch_df("SELECT * FROM rpt_revenue_by_month_and_method ORDER BY month")
rej = fetch_df("SELECT * FROM rpt_document_rejection_rate")
notif = fetch_df("SELECT * FROM rpt_notification_delivery")
stages = fetch_df(
    """SELECT ps.stage_order, ps.stage_name, COUNT(a.application_id) AS n
       FROM pipeline_stages ps LEFT JOIN applications a ON a.current_stage_id = ps.stage_id
       GROUP BY ps.stage_order, ps.stage_name ORDER BY ps.stage_order""")
mix = fetch_df("SELECT service_type::text AS service_type, COUNT(*) AS n FROM applications GROUP BY 1")
dest = fetch_df("SELECT destination, COUNT(*) AS n FROM applications GROUP BY 1 ORDER BY n DESC LIMIT 8")
monthly = fetch_df("""SELECT date_trunc('month', created_at)::date AS month, COUNT(*) AS n
                      FROM applications GROUP BY 1 ORDER BY 1""")
clients = fetch_df("SELECT COUNT(*) AS n FROM client_profiles")["n"][0]

currencies = sorted(rev["currency"].dropna().str.strip().unique()) if not rev.empty else []
cur = st.selectbox("Currency", currencies) if currencies else None
rev_c = rev[rev["currency"].str.strip() == cur] if cur else rev

# ---------- KPI row ----------
k1, k2, k3, k4 = st.columns(4)
k1.metric("Applications", int(stages["n"].sum()))
k2.metric("Clients", int(clients))
k3.metric(f"Net revenue ({cur or '-'})", f"{rev_c['net_revenue'].sum():,.0f}" if cur else "0")
tot = rej["total_documents"].sum()
k4.metric("Document rejection", f"{100 * rej['rejected_documents'].sum() / tot:.1f}%" if tot else "0%")

# ---------- charts ----------
if cur:
    st.plotly_chart(style(px.bar(rev_c, x="month", y="net_revenue", color="payment_method",
                                 barmode="group", title=f"Net revenue by month and method ({cur})",
                                 color_discrete_sequence=PALETTE)), width="stretch")

c1, c2 = st.columns(2)
c1.plotly_chart(style(px.bar(stages, x="n", y="stage_name", orientation="h",
                             title="Applications per pipeline stage",
                             color_discrete_sequence=PALETTE)), width="stretch")
c2.plotly_chart(style(px.pie(mix, names="service_type", values="n", hole=0.45,
                             title="Service mix", color_discrete_sequence=PALETTE)),
                width="stretch")

c3, c4 = st.columns(2)
c3.plotly_chart(style(px.bar(rej, x="document_type", y="rejection_percentage",
                             title="Document rejection rate (%)",
                             color_discrete_sequence=PALETTE)), width="stretch")
long = notif.melt(id_vars="channel", value_vars=["sent_count", "failed_count"],
                  var_name="outcome", value_name="count")
c4.plotly_chart(style(px.bar(long, x="channel", y="count", color="outcome", barmode="stack",
                             title="Notification delivery by channel",
                             color_discrete_sequence=PALETTE)), width="stretch")

c5, c6 = st.columns(2)
c5.plotly_chart(style(px.bar(dest, x="n", y="destination", orientation="h",
                             title="Top destinations", color_discrete_sequence=PALETTE)),
                width="stretch")
c6.plotly_chart(style(px.line(monthly, x="month", y="n", markers=True,
                              title="New applications per month",
                              color_discrete_sequence=PALETTE)), width="stretch")

with st.expander("Raw report views"):
    st.dataframe(rev, width="stretch", hide_index=True)
    st.dataframe(rej, width="stretch", hide_index=True)
    st.dataframe(notif, width="stretch", hide_index=True)