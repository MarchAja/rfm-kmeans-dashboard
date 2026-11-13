"""Halaman 1 — Ringkasan: proporsi, revenue share, dan tren bulanan."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import plotly.express as px
import streamlit as st

from utils.data import (
    SEGMENT_COLORS,
    SEGMENT_ORDER,
    gbp,
    join_segment,
    load_profile,
    load_rfm,
    load_transactions,
)
from utils.ui import render_sidebar, stretch

st.set_page_config(page_title="Ringkasan", page_icon="📊", layout="wide")
render_sidebar()
px.defaults.template = "plotly_white"

st.title("📊 Ringkasan")
st.caption("Proporsi customer, kontribusi revenue, dan tren belanja bulanan.")

rfm = load_rfm()
profile = load_profile()
tx = join_segment(load_transactions(), rfm)

# --- Proporsi & revenue share -------------------------------------------
col1, col2 = st.columns(2, gap="medium")

with col1:
    st.subheader("Distribusi customer per segmen")
    fig = px.pie(
        profile, names="Segment", values="n_customers", hole=0.55,
        color="Segment", color_discrete_map=SEGMENT_COLORS,
        category_orders={"Segment": SEGMENT_ORDER},
    )
    fig.update_traces(textinfo="label+percent", textfont_size=13)
    fig.update_layout(showlegend=False, height=340, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, **stretch())

with col2:
    st.subheader("Kontribusi revenue")
    p = profile.sort_values("revenue_share_pct")
    fig = px.bar(
        p, x="revenue_share_pct", y="Segment", orientation="h",
        color="Segment", color_discrete_map=SEGMENT_COLORS,
        category_orders={"Segment": p["Segment"].tolist()},
        text=p["revenue_share_pct"].map(lambda v: f"{v:.1f}%"),
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        showlegend=False, height=340,
        xaxis=dict(range=[0, 100], title="% dari total revenue", tickformat=",.0f"),
        yaxis_title="", margin=dict(l=10, r=30, t=10, b=10),
    )
    st.plotly_chart(fig, **stretch())

# --- Revenue bulanan ------------------------------------------------------
st.subheader("Revenue bulanan")
mode = st.radio("Tampilan", ["Total", "Per segmen"], horizontal=True)
if mode == "Total":
    monthly = tx.groupby("Bulan", as_index=False)["Revenue"].sum()
    fig = px.area(monthly, x="Bulan", y="Revenue")
else:
    monthly = tx.groupby(["Bulan", "Segment"], as_index=False)["Revenue"].sum()
    fig = px.area(
        monthly, x="Bulan", y="Revenue", color="Segment",
        color_discrete_map=SEGMENT_COLORS, category_orders={"Segment": SEGMENT_ORDER},
    )
fig.update_layout(
    height=380, legend=dict(orientation="h", yanchor="bottom", y=1.02),
    margin=dict(l=10, r=10, t=10, b=10),
)
fig.update_yaxes(tickprefix="£", tickformat=",.0f")
st.plotly_chart(fig, **stretch())

# --- Median monetary + profil segmen --------------------------------------
col3, col4 = st.columns([2, 3], gap="medium")

with col3:
    st.subheader("Median Monetary per segmen")
    fig = px.bar(
        profile.sort_values("M_median"), x="M_median", y="Segment", orientation="h",
        color="Segment", color_discrete_map=SEGMENT_COLORS,
        text=profile.sort_values("M_median")["M_median"].map(lambda v: gbp(v, 0)),
        category_orders={"Segment": profile.sort_values("M_median")["Segment"].tolist()},
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        showlegend=False, height=300,
        xaxis=dict(tickprefix="£", tickformat=",.0f", title="Median belanja"),
        yaxis_title="", margin=dict(l=10, r=40, t=10, b=10),
    )
    st.plotly_chart(fig, **stretch())

with col4:
    st.subheader("Profil segmen")
    prof = profile[[
        "Segment", "n_customers", "pct_customers", "R_median", "F_median",
        "M_median", "M_mean", "M_total", "revenue_share_pct",
    ]].copy()
    for col, fmt in [("pct_customers", 1), ("revenue_share_pct", 1)]:
        prof[col] = prof[col].map(lambda v, f=fmt: f"{v:.{f}f}%")
    for col in ("M_median", "M_mean", "M_total"):
        prof[col] = prof[col].map(lambda v: gbp(v))
    prof = prof.rename(columns={
        "n_customers": "Customer", "pct_customers": "% Customer",
        "R_median": "R median", "F_median": "F median",
        "M_median": "M median", "M_mean": "M rata-rata",
        "M_total": "M total", "revenue_share_pct": "Revenue share",
    })
    st.dataframe(prof, hide_index=True, **stretch())
