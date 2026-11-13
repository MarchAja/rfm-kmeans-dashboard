"""Halaman 3 — Customer: filter, pencarian, dan detail per customer."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.data import SEGMENT_COLORS, SEGMENT_EMOJI, SEGMENT_ORDER, gbp, load_rfm, load_transactions
from utils.ui import render_sidebar, stretch

st.set_page_config(page_title="Customer", page_icon="👥", layout="wide")
render_sidebar()
px.defaults.template = "plotly_white"

st.title("👥 Customer")
st.caption("Telusuri 1.000 customer: filter segmen/negara/skor, lalu pilih satu baris untuk melihat detail belanjanya.")

rfm = load_rfm()
tx = load_transactions()

# --- Filter sidebar --------------------------------------------------------
pilihan = st.sidebar.multiselect("Segmen", SEGMENT_ORDER, default=SEGMENT_ORDER)
negara = st.sidebar.selectbox(
    "Negara", ["Semua"] + sorted(rfm["Country"].dropna().unique().tolist())
)
skor_rentang = st.sidebar.slider("Rentang RFM Score", 3, 15, (3, 15))

mask = (
    rfm["Segment"].isin(pilihan)
    & rfm["RFM_Score"].between(*skor_rentang)
)
if negara != "Semua":
    mask &= rfm["Country"] == negara
cari = st.text_input("🔎 Cari CustomerID (boleh sebagian, mis. 130)")
if cari:
    mask &= rfm["CustomerID"].str.contains(cari, na=False)

d = rfm[mask].sort_values("Monetary", ascending=False).reset_index(drop=True)
st.caption(f"**{len(d):,}** customer cocok dengan filter")

# --- Tabel customer --------------------------------------------------------
tampil = d[[
    "CustomerID", "Segment", "Recency", "Frequency", "Monetary",
    "R_Score", "F_Score", "M_Score", "RFM_Score", "Country",
]].copy()
tampil["Monetary"] = tampil["Monetary"].map(lambda v: gbp(v))

event = st.dataframe(
    tampil,
    column_config={
        "CustomerID": st.column_config.TextColumn("ID"),
        "Segment": st.column_config.TextColumn("Segmen"),
        "Recency": st.column_config.NumberColumn("R (hari)", format="%.0f"),
        "Frequency": st.column_config.NumberColumn("F (invoice)", format="%.0f"),
        "Monetary": st.column_config.TextColumn("Monetary"),
        "R_Score": st.column_config.ProgressColumn(
            "R skor", min_value=1, max_value=5, format="%.0f"
        ),
        "F_Score": st.column_config.ProgressColumn(
            "F skor", min_value=1, max_value=5, format="%.0f"
        ),
        "M_Score": st.column_config.ProgressColumn(
            "M skor", min_value=1, max_value=5, format="%.0f"
        ),
        "RFM_Score": st.column_config.ProgressColumn(
            "RFM", min_value=3, max_value=15, format="%.0f"
        ),
        "Country": st.column_config.TextColumn("Negara"),
    },
    selection_mode="single-row", on_select="rerun", key="tabel_customer",
    hide_index=True, height=400, **stretch(),
)

baris = event.selection.rows
if not baris:
    st.info("⬆️ Pilih satu baris di tabel untuk melihat detail customer.")
    st.stop()

row = d.iloc[baris[0]]
cid = str(row["CustomerID"])
tx_c = tx[tx["CustomerID"] == cid]

# --- Kartu detail ----------------------------------------------------------
st.divider()
chip_warna = SEGMENT_COLORS.get(row["Segment"], "#455A64")
st.markdown(
    f"### 👤 Customer {cid} "
    f"<span style='background:{chip_warna};color:white;padding:2px 10px;"
    f"border-radius:12px;font-size:0.7em;vertical-align:middle'>"
    f"{SEGMENT_EMOJI.get(row['Segment'], row['Segment'])}</span>",
    unsafe_allow_html=True,
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Recency", f"{int(row['Recency'])} hari")
m2.metric("Frequency", f"{int(row['Frequency'])} invoice")
m3.metric("Monetary", gbp(float(row["Monetary"])))
persentil = float((rfm["Monetary"] < row["Monetary"]).mean() * 100)
m4.metric("Persentil Monetary", f"{persentil:.0f}%")

col_a, col_b = st.columns(2, gap="medium")

with col_a:
    st.subheader("Posisi di peta R×M")
    fig = px.scatter(
        rfm, x="Recency", y="Monetary", log_y=True, opacity=0.3,
        color_discrete_sequence=["#B0BEC5"],
    )
    fig.add_trace(go.Scatter(
        x=[row["Recency"]], y=[row["Monetary"]], mode="markers",
        marker=dict(color="#D32F2F", size=15, symbol="star", line=dict(width=1, color="white")),
        name=f"Customer {cid}",
    ))
    fig.update_layout(
        showlegend=True, height=340, legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=10, r=10, t=10, b=10),
    )
    fig.update_yaxes(tickprefix="£", tickformat=",.0f")
    st.plotly_chart(fig, **stretch())

with col_b:
    st.subheader("Top 10 produk yang dibeli")
    if len(tx_c):
        top = (
            tx_c.groupby("Description", as_index=False)["Revenue"].sum()
            .nlargest(10, "Revenue")
            .sort_values("Revenue")
        )
        fig = px.bar(
            top, x="Revenue", y="Description", orientation="h",
            color_discrete_sequence=["#2E7D32"],
            text=top["Revenue"].map(lambda v: gbp(v, 0)),
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            height=340, margin=dict(l=10, r=70, t=10, b=10),
            xaxis=dict(tickprefix="£", tickformat=",.0f"), yaxis_title="",
        )
        st.plotly_chart(fig, **stretch())
    else:
        st.info("Tidak ada transaksi untuk customer ini.")

# --- Timeline belanja ------------------------------------------------------
st.subheader("Pola belanja bulanan")
if len(tx_c):
    colx, coly, colz = st.columns(3)
    colx.metric("Total belanja", gbp(float(tx_c["Revenue"].sum()), 0))
    coly.metric("Invoice unik", f"{tx_c['Invoice'].nunique():,}")
    colz.metric(
        "Periode belanja",
        f"{tx_c['InvoiceDate'].min():%b %Y} – {tx_c['InvoiceDate'].max():%b %Y}",
    )
    monthly = tx_c.groupby("Bulan", as_index=False)["Revenue"].sum()
    fig = px.area(
        monthly, x="Bulan", y="Revenue", color_discrete_sequence=["#1565C0"]
    )
    fig.update_layout(height=300, margin=dict(l=10, r=10, t=10, b=10))
    fig.update_yaxes(tickprefix="£", tickformat=",.0f")
    st.plotly_chart(fig, **stretch())
else:
    st.info("Tidak ada transaksi untuk customer ini.")
