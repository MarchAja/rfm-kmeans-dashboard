"""Halaman 4 — Transaksi: tren, produk, negara, aktivitas, dan drill-down."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.data import (
    SEGMENT_COLORS,
    SEGMENT_ORDER,
    gbp,
    join_segment,
    load_rfm,
    load_transactions,
)
from utils.ui import render_sidebar, stretch

st.set_page_config(page_title="Transaksi", page_icon="🛒", layout="wide")
render_sidebar()
px.defaults.template = "plotly_white"

st.title("🛒 Transaksi")
st.caption("Eksplorasi 126 ribu transaksi sampel: tren bulanan, produk, negara, dan pola waktu belanja.")

rfm = load_rfm()
tx = join_segment(load_transactions(), rfm)

# --- Filter ----------------------------------------------------------------
pilihan = st.sidebar.multiselect("Segmen", SEGMENT_ORDER, default=SEGMENT_ORDER)
ex_uk = st.sidebar.checkbox("Kecualikan United Kingdom", value=False)

dmin = tx["InvoiceDate"].min().date()
dmax = tx["InvoiceDate"].max().date()
rentang = st.date_input(
    "Rentang tanggal", (dmin, dmax), min_value=dmin, max_value=dmax,
    format="YYYY-MM-DD",
)
d1, d2 = (rentang if isinstance(rentang, tuple) and len(rentang) == 2 else (dmin, dmax))

mask = (
    tx["InvoiceDate"].dt.date.between(d1, d2)
    & tx["Segment"].isin(pilihan)
)
txf = tx[mask]
if ex_uk:
    txf = txf[txf["Country"] != "United Kingdom"]

if not len(txf):
    st.warning("Tidak ada transaksi pada filter ini.")
    st.stop()

st.caption(
    f"**{len(txf):,}** baris · **{txf['Invoice'].nunique():,}** invoice · "
    f"revenue **{gbp(float(txf['Revenue'].sum()), 0)}**"
)

# --- Tren bulanan ----------------------------------------------------------
st.subheader("Tren bulanan")
metrik = st.radio(
    "Metrik", ["Revenue", "Jumlah invoice", "Jumlah baris"], horizontal=True
)
if metrik == "Revenue":
    monthly = txf.groupby("Bulan", as_index=False)["Revenue"].sum()
    kolom_y = "Revenue"
elif metrik == "Jumlah invoice":
    monthly = (
        txf.groupby("Bulan", as_index=False)["Invoice"]
        .nunique()
        .rename(columns={"Invoice": "Jumlah invoice"})
    )
    kolom_y = "Jumlah invoice"
else:
    monthly = txf.groupby("Bulan", as_index=False).size().rename(columns={"size": "Jumlah baris"})
    kolom_y = "Jumlah baris"

fig = px.line(monthly, x="Bulan", y=kolom_y, markers=True)
if kolom_y == "Revenue":
    fig.update_yaxes(tickprefix="£", tickformat=",.0f")
fig.update_layout(height=340, margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig, **stretch())

# --- Produk & negara -------------------------------------------------------
col1, col2 = st.columns(2, gap="medium")

with col1:
    st.subheader("Top 10 produk (revenue)")
    top_produk = (
        txf.groupby("Description", as_index=False)["Revenue"].sum()
        .nlargest(10, "Revenue")
        .sort_values("Revenue")
    )
    fig = px.bar(
        top_produk, x="Revenue", y="Description", orientation="h",
        color_discrete_sequence=["#2E7D32"],
        text=top_produk["Revenue"].map(lambda v: gbp(v, 0)),
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=380, margin=dict(l=10, r=70, t=10, b=10),
        xaxis=dict(tickprefix="£", tickformat=",.0f"), yaxis_title="",
    )
    st.plotly_chart(fig, **stretch())

with col2:
    st.subheader("Top 15 negara (revenue)")
    top_negara = (
        txf.groupby("Country", as_index=False)["Revenue"].sum()
        .nlargest(15, "Revenue")
        .sort_values("Revenue")
    )
    fig = px.bar(
        top_negara, x="Revenue", y="Country", orientation="h",
        color_discrete_sequence=["#1565C0"],
        text=top_negara["Revenue"].map(lambda v: gbp(v, 0)),
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        height=380, margin=dict(l=10, r=70, t=10, b=10),
        xaxis=dict(tickprefix="£", tickformat=",.0f"), yaxis_title="",
    )
    st.plotly_chart(fig, **stretch())

# --- Heatmap hari × jam ----------------------------------------------------
st.subheader("Aktivitas belanja: hari × jam")
pivot = txf.pivot_table(
    index="Jam", columns="Hari", values="Revenue", aggfunc="sum", observed=False
)
pivot = pivot.reindex(index=range(24), columns=[
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
]).fillna(0.0)
pivot = pivot.rename(columns={
    "Monday": "Sen", "Tuesday": "Sel", "Wednesday": "Rab", "Thursday": "Kam",
    "Friday": "Jum", "Saturday": "Sab", "Sunday": "Min",
})
fig = go.Figure(go.Heatmap(
    z=pivot.values, x=list(pivot.columns), y=list(pivot.index),
    colorscale="YlGnBu", hovertemplate="Jam %{y}:00 · %{x} · %{z:,.0f} GBP<extra></extra>",
))
fig.update_yaxes(autorange="reversed", dtick=2, title="Jam")
fig.update_xaxes(title="", side="top")
fig.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10))
st.plotly_chart(fig, **stretch())

# --- Drill-down invoice ----------------------------------------------------
st.subheader("Detail invoice")
top_invoice = (
    txf.groupby("Invoice", as_index=False)["Revenue"].sum()
    .nlargest(500, "Revenue")
    .sort_values("Revenue", ascending=False)
)
st.caption("Pilih dari 500 invoice terbesar sesuai filter aktif.")
pilih_invoice = st.selectbox(
    "Invoice",
    options=top_invoice["Invoice"].tolist(),
    format_func=lambda inv: (
        f"{inv}  ·  {gbp(float(top_invoice.loc[top_invoice['Invoice'] == inv, 'Revenue'].iloc[0]))}"
    ),
)
garis = txf[txf["Invoice"] == pilih_invoice]

g1, g2, g3, g4 = st.columns(4)
g1.metric("Tanggal", f"{garis['InvoiceDate'].iloc[0]:%Y-%m-%d}")
g2.metric("Customer", str(garis["CustomerID"].iloc[0]))
g3.metric("Jumlah baris", f"{len(garis):,}")
g4.metric("Total invoice", gbp(float(garis["Revenue"].sum())))

st.dataframe(
    garis[["StockCode", "Description", "Quantity", "UnitPrice", "Revenue", "Country"]]
    .sort_values("Revenue", ascending=False)
    .rename(columns={
        "StockCode": "Kode", "Description": "Produk", "Quantity": "Qty",
        "UnitPrice": "Harga satuan", "Revenue": "Revenue", "Country": "Negara",
    }),
    hide_index=True, height=300, **stretch(),
)

# --- Tabel transaksi -------------------------------------------------------
st.subheader("Tabel transaksi (terbaru dulu)")
st.dataframe(
    txf[[
        "Invoice", "InvoiceDate", "CustomerID", "StockCode", "Description",
        "Quantity", "UnitPrice", "Revenue", "Country", "Segment",
    ]]
    .sort_values("InvoiceDate", ascending=False)
    .rename(columns={
        "InvoiceDate": "Tanggal", "CustomerID": "ID customer",
        "StockCode": "Kode", "Description": "Produk", "Quantity": "Qty",
        "UnitPrice": "Harga satuan", "Revenue": "Revenue", "Country": "Negara",
        "Segment": "Segmen",
    }),
    hide_index=True, height=400, **stretch(),
)
