"""Halaman 2 — Segmen: peta R×M, profil RFM, dan distribusi."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.data import SEGMENT_COLORS, SEGMENT_ORDER, load_profile, load_rfm
from utils.ui import render_sidebar, stretch

st.set_page_config(page_title="Segmen", page_icon="🧩", layout="wide")
render_sidebar()
px.defaults.template = "plotly_white"

st.title("🧩 Segmen")
st.caption("Karakteristik tiap segmen: posisi di peta R×M, profil median RFM, dan sebarannya.")

rfm = load_rfm()
profile = load_profile()

pilihan = st.sidebar.multiselect(
    "Segmen", SEGMENT_ORDER, default=SEGMENT_ORDER
)
if not pilihan:
    st.warning("Pilih minimal satu segmen di sidebar.")
    st.stop()

d = rfm[rfm["Segment"].isin(pilihan)].copy()

# --- Scatter Recency vs Monetary -----------------------------------------
st.subheader("Peta Recency × Monetary")
fig = px.scatter(
    d, x="Recency", y="Monetary", color="Segment",
    color_discrete_map=SEGMENT_COLORS, opacity=0.75, log_y=True,
    hover_data={"CustomerID": True, "Frequency": True, "RFM_Score": True},
    category_orders={"Segment": SEGMENT_ORDER},
)
fig.update_layout(
    height=430, legend=dict(orientation="h", yanchor="bottom", y=1.02),
    margin=dict(l=10, r=10, t=10, b=10),
)
fig.update_yaxes(tickprefix="£", tickformat=",.0f")
st.plotly_chart(fig, **stretch())
st.caption(
    "Sumbu Y log-scale · titik kiri-atas = customer bernilai tinggi yang baru "
    "saja belanja · hover untuk detail · drag untuk zoom."
)

# --- Heatmap profil + boxplot --------------------------------------------
col1, col2 = st.columns(2, gap="medium")

with col1:
    st.subheader("Profil median RFM (z-score)")
    med = (
        d.groupby("Segment")[["Recency", "Frequency", "Monetary"]]
        .median()
        .reindex(pilihan)
    )
    if len(med) > 1:
        z = (med - med.mean()) / med.std(ddof=0)
    else:  # satu segmen saja → skala relatif terhadap nilai maksimum
        z = med / med.max()
    fig = go.Figure(go.Heatmap(
        z=z.values, x=list(med.columns), y=list(med.index.astype(str)),
        colorscale="RdYlGn_r", text=med.round(1).values,
        texttemplate="%{text}", hovertemplate="%{y} · %{x}: %{text}<extra></extra>",
    ))
    fig.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, **stretch())

with col2:
    st.subheader("Sebaran Monetary per segmen")
    fig = px.box(
        d, x="Segment", y="Monetary", color="Segment", log_y=True,
        points="outliers", color_discrete_map=SEGMENT_COLORS,
        category_orders={"Segment": SEGMENT_ORDER},
    )
    fig.update_layout(
        showlegend=False, height=320, margin=dict(l=10, r=10, t=10, b=10),
    )
    fig.update_yaxes(tickprefix="£", tickformat=",.0f")
    st.plotly_chart(fig, **stretch())

# --- Distribusi metric + rata-rata skor -----------------------------------
col3, col4 = st.columns(2, gap="medium")

with col3:
    st.subheader("Distribusi metric")
    metric = st.radio(
        "Metric", ["Recency", "Frequency", "Monetary"], horizontal=True
    )
    upper = None if metric == "Recency" else float(rfm[metric].quantile(0.99))
    fig = px.histogram(
        d, x=metric, color="Segment", nbins=40, barmode="overlay", opacity=0.55,
        color_discrete_map=SEGMENT_COLORS, category_orders={"Segment": SEGMENT_ORDER},
    )
    if upper is not None:
        fig.update_xaxes(range=[0, upper], title=f"{metric} (dipotong di p99)")
    fig.update_traces(marker_line_width=0)
    fig.update_layout(
        height=320, legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=10, r=10, t=10, b=10),
    )
    if metric == "Monetary":
        fig.update_xaxes(tickprefix="£", tickformat=",.0f")
    st.plotly_chart(fig, **stretch())

with col4:
    st.subheader("Rata-rata skor RFM")
    skor = (
        d.groupby("Segment")[["R_Score", "F_Score", "M_Score"]]
        .mean()
        .reindex(pilihan)
    )
    melted = skor.reset_index().melt(
        id_vars="Segment", var_name="Skor", value_name="Rata-rata"
    )
    fig = px.bar(
        melted, x="Segment", y="Rata-rata", color="Skor", barmode="group",
        color_discrete_sequence=["#F9A825", "#1565C0", "#8E24AA"],
        category_orders={"Segment": SEGMENT_ORDER, "Skor": ["R_Score", "F_Score", "M_Score"]},
    )
    fig.update_layout(
        height=320, legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig, **stretch())

# --- Tabel profil ----------------------------------------------------------
st.subheader("Tabel profil segmen")
prof = profile[profile["Segment"].isin(pilihan)].copy()
prof_display = prof[[
    "Segment", "n_customers", "R_median", "F_median", "M_median", "M_mean",
    "M_total", "revenue_share_pct", "RFM_score_mean", "top_country",
]].copy()
prof_display["M_median"] = prof_display["M_median"].map(lambda v: f"£{v:,.2f}")
prof_display["M_mean"] = prof_display["M_mean"].map(lambda v: f"£{v:,.2f}")
prof_display["M_total"] = prof_display["M_total"].map(lambda v: f"£{v:,.2f}")
prof_display["revenue_share_pct"] = prof_display["revenue_share_pct"].map(
    lambda v: f"{v:.2f}%"
)
prof_display = prof_display.rename(columns={
    "n_customers": "Customer", "R_median": "R median", "F_median": "F median",
    "M_median": "M median", "M_mean": "M rata-rata", "M_total": "M total",
    "revenue_share_pct": "Revenue share", "RFM_score_mean": "RFM score rata-rata",
    "top_country": "Negara dominan",
})
st.dataframe(prof_display, hide_index=True, **stretch())
