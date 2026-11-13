"""Loader data untuk dashboard RFM.

Semua file dibaca dari folder proyek (PSD). Setiap loader di-cache dengan
`st.cache_data` dan ber-key pada mtime file, sehingga begitu notebook
di-re-run dan file hasil berubah, cache otomatis invalid dan data baru
terbaca pada rerun berikutnya.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# dashboard/utils/data.py -> parents[2] = folder PSD
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"
XLSX_PATH = REPORTS_DIR / "rfm_kmeans_results.xlsx"

# Urutan & warna segmen yang konsisten di semua halaman
SEGMENT_ORDER = ["Champions", "Potential", "Lost"]
SEGMENT_COLORS = {
    "Champions": "#2E7D32",   # hijau
    "Potential": "#F9A825",   # kuning
    "Lost": "#C62828",        # merah
}
SEGMENT_EMOJI = {
    "Champions": "🏆 Champions",
    "Potential": "🌱 Potential",
    "Lost": "💤 Lost",
}


# ---------------------------------------------------------------------------
# Cache primitif
# ---------------------------------------------------------------------------
@st.cache_data
def _read_csv(path: str, mtime: float, **kwargs) -> pd.DataFrame:
    del mtime  # hanya berperan sebagai cache key
    return pd.read_csv(path, **kwargs)


@st.cache_data
def _read_sheet(path: str, mtime: float, sheet_name: str) -> pd.DataFrame:
    del mtime
    return pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl")


def _csv(path: Path, **kwargs) -> pd.DataFrame:
    return _read_csv(str(path), path.stat().st_mtime, **kwargs)


def _sheet(sheet_name: str) -> pd.DataFrame:
    return _read_sheet(str(XLSX_PATH), XLSX_PATH.stat().st_mtime, sheet_name)


# ---------------------------------------------------------------------------
# Loader utama
# ---------------------------------------------------------------------------
def load_rfm() -> pd.DataFrame:
    """RFM 1.000 customer + skor, cluster, dan segmen."""
    df = _csv(DATA_DIR / "rfm_clusters.csv", dtype={"CustomerID": "string"})
    df["CustomerID"] = df["CustomerID"].astype(str)
    return df


def load_transactions() -> pd.DataFrame:
    """126 ribu transaksi sampel + kolom turunan (Bulan, Hari, Jam)."""
    df = _csv(
        DATA_DIR / "clean_transactions_sample.csv",
        dtype={"Invoice": "string", "StockCode": "string", "CustomerID": "string"},
        parse_dates=["InvoiceDate"],
    )
    df["CustomerID"] = df["CustomerID"].astype(str)
    df["Bulan"] = df["InvoiceDate"].dt.to_period("M").dt.to_timestamp()
    hari_urut = [
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
        "Saturday", "Sunday",
    ]
    df["Hari"] = pd.Categorical(
        df["InvoiceDate"].dt.day_name(), categories=hari_urut, ordered=True
    )
    df["Jam"] = df["InvoiceDate"].dt.hour
    return df


def load_profile() -> pd.DataFrame:
    """Profil agregat per segmen."""
    return _csv(REPORTS_DIR / "cluster_profile.csv")


def load_funnel() -> pd.DataFrame:
    """Funnel cleaning 7 langkah."""
    return _csv(REPORTS_DIR / "cleaning_funnel.csv")


def load_summary() -> pd.DataFrame:
    """Ringkasan akhir (metric, value)."""
    return _csv(REPORTS_DIR / "final_summary.csv")


def load_rfm_summary() -> pd.DataFrame:
    """Perbandingan populasi vs sampel."""
    return _csv(REPORTS_DIR / "rfm_summary.csv")


def load_eval() -> pd.DataFrame:
    """Evaluasi k=2..10 (inertia, silhouette, davies-bouldin) dari workbook."""
    return _sheet("Evaluasi_k")


def load_centroids() -> pd.DataFrame:
    """Centroid KMeans dalam skala terstandarisasi."""
    return _sheet("KMeans_Centroids")


def load_parameters() -> pd.DataFrame:
    """Parameter model: snapshot, cap p99, mean/std scaler."""
    return _sheet("Parameter")


def join_segment(transactions: pd.DataFrame, rfm: pd.DataFrame) -> pd.DataFrame:
    """Lampirkan nama segmen ke transaksi via CustomerID."""
    return transactions.merge(
        rfm[["CustomerID", "Segment"]], on="CustomerID", how="inner"
    )


# ---------------------------------------------------------------------------
# Status data (untuk panel "Sumber Data" & sidebar)
# ---------------------------------------------------------------------------
DATA_FILES = [
    ("data/rfm_clusters.csv", DATA_DIR / "rfm_clusters.csv"),
    ("data/rfm_sample.csv", DATA_DIR / "rfm_sample.csv"),
    ("data/clean_transactions_sample.csv", DATA_DIR / "clean_transactions_sample.csv"),
    ("reports/cluster_profile.csv", REPORTS_DIR / "cluster_profile.csv"),
    ("reports/cleaning_funnel.csv", REPORTS_DIR / "cleaning_funnel.csv"),
    ("reports/final_summary.csv", REPORTS_DIR / "final_summary.csv"),
    ("reports/rfm_summary.csv", REPORTS_DIR / "rfm_summary.csv"),
    ("reports/rfm_kmeans_results.xlsx", XLSX_PATH),
]


def data_status() -> pd.DataFrame:
    """Kapan tiap file terakhir ditulis + ukuran — untuk cek kesegaran data."""
    rows = []
    for name, path in DATA_FILES:
        if path.exists():
            stat = path.stat()
            size = stat.st_size
            if size >= 1024 * 1024:
                ukuran = f"{size / 1024 / 1024:.1f} MB"
            else:
                ukuran = f"{size / 1024:.0f} KB"
            rows.append({
                "file": name,
                "terakhir_ditulis": datetime.fromtimestamp(
                    stat.st_mtime
                ).strftime("%Y-%m-%d %H:%M:%S"),
                "ukuran": ukuran,
                "status": "✅ ada",
            })
        else:
            rows.append({
                "file": name,
                "terakhir_ditulis": "—",
                "ukuran": "—",
                "status": "⚠️ tidak ditemukan",
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Formatter
# ---------------------------------------------------------------------------
def gbp(x: float, decimals: int = 2) -> str:
    """Format GBP dengan pemisah ribuan, mis. £3,374.32."""
    return f"£{x:,.{decimals}f}"


def pct(x: float, decimals: int = 1) -> str:
    return f"{x:.{decimals}f}%"
