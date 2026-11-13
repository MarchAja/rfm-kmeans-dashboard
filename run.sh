#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Runner otomatis proyek PSD — Segmentasi Customer RFM & KMeans
#
#   ./run.sh                    → re-run notebook (pipeline penuh) + dashboard
#   ./run.sh --dashboard-only   → langsung dashboard saja (tanpa re-run notebook)
#   ./run.sh --skip-notebook    → sama dengan --dashboard-only
#
# Variabel lingkungan (opsional):
#   SRC=/path/online_retail_II.xlsx   lokasi file mentah
#   PORT=8501                         port dashboard
# ---------------------------------------------------------------------------
set -euo pipefail

PSD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PSD_DIR"

SRC="${SRC:-$HOME/Downloads/online_retail_II.xlsx}"
PORT="${PORT:-8501}"

# --- Cari Python environment (venv) ---------------------------------------
PY=""
VENV_BIN=""
for v in "$PSD_DIR/.venv" "$HOME/Downloads/rfm_kmeans_online_retail/.venv"; do
    if [ -x "$v/bin/python" ]; then
        PY="$v/bin/python"
        VENV_BIN="$v/bin"
        break
    fi
done

if [ -z "$PY" ]; then
    echo "❌ Virtual environment tidak ditemukan."
    echo "   Buat dulu lalu install dependensi:"
    echo ""
    echo "     python3 -m venv .venv"
    echo "     .venv/bin/pip install -r dashboard/requirements.txt"
    echo "     .venv/bin/pip install pandas numpy scikit-learn matplotlib \\"
    echo "         seaborn python-calamine openpyxl jupyter nbconvert ipykernel"
    exit 1
fi

echo "🛍️  Runner RFM Dashboard — PSD"
echo "   Python    : $PY"
echo "   Sumber    : $SRC"
echo "   Port      : $PORT"
echo ""

# --- Pastikan file mentah ada ----------------------------------------------
if [ ! -f "$SRC" ]; then
    echo "⚠️  File sumber tidak ditemukan: $SRC"
    echo "   Unduh online_retail_II.xlsx ke \$HOME/Downloads, atau jalankan dengan:"
    echo "   SRC=/path/ke/online_retail_II.xlsx ./run.sh"
    exit 1
fi

# --- Mode -------------------------------------------------------------------
SKIP_NOTEBOOK=false
case "${1:-}" in
    --dashboard-only|--skip-notebook) SKIP_NOTEBOOK=true ;;
esac

# --- [1/2] Notebook: audit → cleaning → RFM → KMeans → export Excel ---------
if [ "$SKIP_NOTEBOOK" = false ]; then
    # Daftarkan kernel bila belum ada (venv baru)
    if ! "$VENV_BIN/jupyter" kernelspec list 2>/dev/null | grep -q "rfm-kmeans"; then
        echo "🔧 Mendaftarkan kernel jupyter 'rfm-kmeans'…"
        "$PY" -m ipykernel install --user --name rfm-kmeans \
            --display-name "Python (rfm-kmeans)" >/dev/null
    fi

    echo "▶️  [1/2] Re-run notebook (audit, cleaning, RFM, KMeans, export Excel)…"
    "$VENV_BIN/jupyter" nbconvert --to notebook --execute --inplace \
        rfm_kmeans.ipynb
    echo "✅ Notebook selesai — data/ dan reports/ diperbarui."
    echo ""
else
    echo "⏭️  [1/2] Melewati re-run notebook (--dashboard-only)."
    echo ""
fi

# --- Hentikan dashboard lama bila ada ---------------------------------------
PIDS="$(pgrep -f "streamlit run dashboard/app.py" || true)"
if [ -n "$PIDS" ]; then
    echo "🛑 Menghentikan dashboard lama (PID: $PIDS)…"
    kill $PIDS 2>/dev/null || true
    sleep 1
fi

# --- [2/2] Dashboard Streamlit ----------------------------------------------
echo "▶️  [2/2] Menjalankan dashboard di http://localhost:$PORT …"
echo "   (Ctrl+C untuk berhenti)"
echo ""
exec "$VENV_BIN/streamlit" run dashboard/app.py \
    --server.headless true --server.port "$PORT"
