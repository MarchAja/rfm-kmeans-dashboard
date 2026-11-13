"""Elemen UI bersama: sidebar, kompatibilitas lebar, dan helper Plotly."""
from __future__ import annotations

import streamlit as st

from utils.data import data_status

# Streamlit >= 1.46 mengganti use_container_width dengan width="stretch"
_version = tuple(int(p) for p in st.__version__.split(".")[:2])
_WIDE_API = _version >= (1, 46)


def stretch() -> dict:
    """Kwarg agar elemen memenuhi lebar container, sesuai versi Streamlit."""
    if _WIDE_API:
        return {"width": "stretch"}
    return {"use_container_width": True}


def render_sidebar() -> None:
    st.sidebar.markdown("## 🛍️ Dashboard RFM")
    st.sidebar.caption("Segmentasi customer Online Retail II — RFM + KMeans")
    st.sidebar.divider()
    if st.sidebar.button("🔄 Muat ulang data"):
        st.cache_data.clear()
        st.rerun()
    st.sidebar.caption("Cache otomatis: data diperbarui begitu file hasil berubah.")
    status = data_status()
    terbaru = status["terakhir_ditulis"].max()
    if terbaru not in ("—", None):
        st.sidebar.caption(f"Data terakhir ditulis: **{terbaru}**")
