"""Halaman 5 — Metodologi: cleaning, pemilihan k, centroid, status data."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import plotly.express as px
import plotly.graph_objects as go
import plotly.subplots as sp
import streamlit as st

from utils.data import (
    data_status,
    load_centroids,
    load_eval,
    load_funnel,
    load_parameters,
    load_rfm,
    load_summary,
    load_transactions,
)
from utils.ui import render_sidebar, stretch

st.set_page_config(page_title="Metodologi", page_icon="⚙️", layout="wide")
render_sidebar()
px.defaults.template = "plotly_white"

st.title("⚙️ Metodologi")
st.caption("Bagaimana data diolah dan model dibangun: funnel cleaning, evaluasi k, centroid, dan parameter.")

summary = load_summary().set_index("metric")["value"]
FINAL_K = int(summary["k"])

# --- Funnel cleaning -------------------------------------------------------
st.subheader(f"Funnel cleaning — dari {int(load_funnel().iloc[0]['before']):,} baris jadi {int(load_funnel().iloc[-1]['remaining']):,} baris")
funnel = load_funnel()
fig = px.bar(
    funnel, x="remaining", y="step", orientation="h",
    color_discrete_sequence=["#5B9BD5"],
    text=funnel["removed"].map(lambda v: f"−{v:,}" if v else "0"),
    category_orders={"step": funnel["step"].tolist()[::-1]},
)
fig.update_traces(textposition="outside")
fig.update_layout(
    showlegend=False, height=360,
    xaxis=dict(title="Baris tersisa", tickformat=",.0f"), yaxis_title="",
    margin=dict(l=10, r=60, t=10, b=10),
)
st.plotly_chart(fig, **stretch())

with st.expander("Tabel funnel lengkap"):
    st.dataframe(funnel, hide_index=True, **stretch())

# --- Evaluasi k ------------------------------------------------------------
st.subheader(f"Pemilihan jumlah cluster — final k={FINAL_K}")
eval_df = load_eval()

col1, col2 = st.columns(2, gap="medium")
with col1:
    fig = px.line(
        eval_df, x="k", y="inertia", markers=True,
        color_discrete_sequence=["#1F4E78"],
    )
    fig.add_vline(
        x=FINAL_K, line_dash="dash", line_color="#C62828",
        annotation_text=f"k={FINAL_K}", annotation_position="top",
    )
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
    st.plotly_chart(fig, **stretch())
    st.caption("Elbow method — inersia (within-cluster SSE).")

with col2:
    fig = sp.make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=eval_df["k"], y=eval_df["silhouette"], name="Silhouette",
            mode="lines+markers", line=dict(color="#F9A825", width=2),
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=eval_df["k"], y=eval_df["davies_bouldin"], name="Davies-Bouldin",
            mode="lines+markers", line=dict(color="#1565C0", width=2, dash="dot"),
        ),
        secondary_y=True,
    )
    fig.add_vline(
        x=FINAL_K, line_dash="dash", line_color="#C62828",
        annotation_text=f"k={FINAL_K}", annotation_position="top",
    )
    fig.update_layout(
        height=340, margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    fig.update_yaxes(title="Silhouette", secondary_y=False)
    fig.update_yaxes(title="Davies-Bouldin", secondary_y=True)
    st.plotly_chart(fig, **stretch())
    st.caption("Silhouette tinggi lebih baik; Davies-Bouldin rendah lebih baik.")

# --- Centroid --------------------------------------------------------------
st.subheader("Centroid KMeans (skala terstandarisasi)")
cent = load_centroids()
kolom_scaled = ["R_scaled", "F_scaled", "M_scaled"]
fig = go.Figure(go.Heatmap(
    z=cent[kolom_scaled].values,
    x=["Recency", "Frequency", "Monetary"],
    y=cent["Cluster"].astype(str).tolist(),
    colorscale="RdBu_r", zmid=0,
    text=cent[kolom_scaled].round(2).values, texttemplate="%{text}",
    hovertemplate="Cluster %{y} · %{x}: %{text}<extra></extra>",
))
fig.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig, **stretch())
st.caption(
    f"Pembacaan: cluster dengan R_scaled negatif = customer baru saja belanja; "
    f"F/M_scaled positif = sering & besar belanja. Nama segmen diurutkan berdasar "
    f"median Monetary (Champions → Lost)."
)

# --- Parameter -------------------------------------------------------------
st.subheader("Parameter")
params = load_parameters().set_index("Parameter")["Nilai"]
c1, c2, c3 = st.columns(3)
c1.metric("Snapshot RFM", f"{params['Snapshot']:%Y-%m-%d}")
c2.metric("Cap Frequency (p99)", f"{float(params['Cap_Frequency_p99']):.0f}")
c3.metric("Cap Monetary (p99)", f"£{float(params['Cap_Monetary_p99']):,.2f}")

with st.expander("Tabel parameter lengkap (mean & std untuk StandardScaler)"):
    st.dataframe(
        load_parameters().rename(columns={
            "Parameter": "Parameter", "Nilai": "Nilai", "Keterangan": "Keterangan"
        }),
        hide_index=True, **stretch(),
    )

# --- Status sumber data ----------------------------------------------------
st.subheader("🗄️ Sumber Data")
st.caption(
    "Dashboard membaca hasil notebook (CSV/Excel) di folder proyek. "
    "Setelah notebook di-re-run, file di bawah berubah dan cache dashboard "
    "otomatis diperbarui — atau klik **🔄 Muat ulang data** di sidebar."
)
st.dataframe(data_status(), hide_index=True, **stretch())
st.caption(
    f"Jumlah baris: rfm_clusters = **{len(load_rfm()):,}** · "
    f"clean_transactions_sample = **{len(load_transactions()):,}**"
)
