"""Halaman utama: KPI utama dan ringkasan segmen."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st

from utils.data import SEGMENT_EMOJI, gbp, load_profile, load_summary
from utils.ui import render_sidebar, stretch

st.set_page_config(
    page_title="Dashboard RFM — Online Retail II",
    page_icon="🛍️",
    layout="wide",
)
render_sidebar()

st.title("🛍️ Segmentasi Customer — RFM & KMeans")
st.caption(
    "Dataset **Online Retail II** · Des 2009 – Des 2011 · sampel 1.000 customer · "
    "retur, pembatalan, dan customer tanpa ID dikeluarkan dari perhitungan RFM."
)
st.divider()

summary = load_summary().set_index("metric")["value"]
profile = load_profile()

row1 = st.columns(4)
row1[0].metric("Customer (sampel)", f"{int(summary['customers_sampel']):,}")
row1[1].metric("Transaksi", f"{int(summary['baris_sampel']):,}")
row1[2].metric("Invoice unik", f"{int(summary['invoice_sampel']):,}")
row1[3].metric("Total revenue", gbp(float(profile["M_total"].sum()), 0))

row2 = st.columns(4)
row2[0].metric("Jumlah segmen (k)", str(int(summary["k"])))
row2[1].metric("Silhouette score", f"{float(summary['silhouette']):.4f}")
row2[2].metric("Davies-Bouldin", f"{float(summary['davies_bouldin']):.4f}")
row2[3].metric("Stabilitas (ARI)", f"{float(summary['ari_mean']):.4f}")

st.divider()
st.subheader("Ringkasan segmen")

tbl = profile[[
    "Segment", "n_customers", "pct_customers", "R_median", "F_median",
    "M_median", "revenue_share_pct",
]].copy()
tbl["Segment"] = tbl["Segment"].map(SEGMENT_EMOJI)
tbl["pct_customers"] = tbl["pct_customers"].map(lambda v: f"{v:.1f}%")
tbl["M_median"] = tbl["M_median"].map(lambda v: gbp(v))
tbl["revenue_share_pct"] = tbl["revenue_share_pct"].map(lambda v: f"{v:.1f}%")
tbl = tbl.rename(columns={
    "n_customers": "Customer",
    "pct_customers": "% Customer",
    "R_median": "Median R (hari)",
    "F_median": "Median F (invoice)",
    "M_median": "Median M",
    "revenue_share_pct": "Revenue share",
})
st.dataframe(tbl, hide_index=True, **stretch())

st.divider()
st.subheader("Navigasi")
st.markdown(
    """
- **📊 Ringkasan** — proporsi customer, kontribusi revenue, tren belanja bulanan
- **🧩 Segmen** — peta Recency × Monetary, profil RFM, dan distribusi tiap segmen
- **👥 Customer** — telusuri 1.000 customer: filter, cari ID, lihat detail belanja
- **🛒 Transaksi** — tren, produk & negara teratas, aktivitas hari × jam
- **⚙️ Metodologi** — funnel cleaning, pemilihan k, centroid, status sumber data
"""
)
st.caption(
    "Tip: setelah notebook di-re-run, klik tombol **🔄 Muat ulang data** di sidebar "
    "atau cukup biarkan — cache diperbarui otomatis saat file hasil berubah."
)
