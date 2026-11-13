# PSD — Segmentasi Customer Online Retail II (RFM & KMeans) + Dashboard

Proyek analisis segmentasi customer untuk dataset **Online Retail II**
(Des 2009 – Des 2011): audit data, cleaning, sampling 1.000 customer,
perhitungan **RFM**, clustering **KMeans** (k=3), hingga dashboard
interaktif berbasis **Streamlit**.

## 📊 Hasil utama

| Segmen | Customer | % | R median | F median | M median | Revenue share |
|---|---:|---:|---:|---:|---:|---:|
| 🏆 Champions | 305 | 30,5% | 26 hari | 10 invoice | £3.444 | **85,8%** |
| 🌱 Potential | 375 | 37,5% | 60 hari | 3 invoice | £680 | 8,7% |
| 💤 Lost | 320 | 32,0% | 430 hari | 1 invoice | £328 | 5,5% |

Kualitas model: silhouette **0.395**, Davies-Bouldin **0.890**, stabilitas ARI **1.0**.

## 📁 Struktur proyek

```
PSD/
├── rfm_kmeans.ipynb          ← notebook pipeline (audit → cleaning → RFM → KMeans → Excel)
├── run.sh                    ← runner otomatis (notebook + dashboard) — macOS/Linux
├── run.bat                   ← runner otomatis untuk Windows (bisa double-click)
├── README.md
├── data/                     ← hasil cleaning & RFM (dibuat/diperbarui notebook)
│   ├── clean_transactions_sample.csv
│   ├── rfm_sample.csv
│   └── rfm_clusters.csv
├── reports/                  ← laporan CSV + workbook Excel 15 sheet
│   ├── rfm_kmeans_results.xlsx
│   ├── cluster_profile.csv
│   ├── cleaning_funnel.csv
│   ├── final_summary.csv
│   └── rfm_summary.csv
├── figures/                  ← grafik PNG dari notebook
└── dashboard/
    ├── app.py                ← Home (KPI + ringkasan segmen)
    ├── requirements.txt      ← dependensi dashboard
    ├── utils/                ← loader cache mtime + elemen UI bersama
    └── pages/                ← 5 halaman: Ringkasan, Segmen, Customer, Transaksi, Metodologi
```

## ⚙️ Persiapan lingkungan (sekali saja)

1. **Python 3.12+** (proyek ini dibuat dengan Python 3.14).
2. **File mentah** `online_retail_II.xlsx` ada di `~/Downloads/`
   (atau lokasi lain — lihat bagian *Pembaruan data*).
3. **Virtual environment** — runner otomatis mencari `.venv` di folder proyek,
   lalu `~/Downloads/rfm_kmeans_online_retail/.venv`. Jika belum ada, buat:

   **macOS / Linux:**
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -r dashboard/requirements.txt
   .venv/bin/pip install pandas numpy scikit-learn matplotlib \
       seaborn python-calamine openpyxl jupyter nbconvert ipykernel
   ```

   **Windows (cmd):**
   ```bat
   python -m venv .venv
   .venv\Scripts\pip install -r dashboard\requirements.txt
   .venv\Scripts\pip install pandas numpy scikit-learn matplotlib seaborn python-calamine openpyxl jupyter nbconvert ipykernel
   ```

## 🚀 Cara cepat

```bash
./run.sh
```

Perintah ini akan:

1. **Re-run notebook** — audit, cleaning, RFM, KMeans, export Excel
   (±1 menit; data/ dan reports/ diperbarui).
2. **Menjalankan dashboard** di **http://localhost:8501**
   (dashboard lama otomatis dihentikan).

> Opsi: `./run.sh --dashboard-only` → langsung dashboard saja (±5 detik),
> memakai hasil notebook yang sudah ada.

Buka **http://localhost:8501** di browser, hentikan dengan **Ctrl+C**.

> **🪟 Pengguna Windows:** double-click `run.bat`, atau jalankan `run.bat`
> di cmd (opsi dan variabel lingkungan yang sama, lihat *Pembaruan data*).
> `run.sh` hanya untuk macOS/Linux — di Windows gunakan WSL jika ingin
> memakai versi bash (di Git Bash, `pgrep` tidak tersedia).

## 🖥️ Panduan halaman dashboard

| Halaman | Isi | Yang bisa dicoba |
|---|---|---|
| 🏠 **Home** | 8 KPI + ringkasan segmen + navigasi | — |
| 📊 **Ringkasan** | Donut proporsi, revenue share, tren bulanan | Toggle **Total / Per segmen** |
| 🧩 **Segmen** | Scatter Recency × Monetary, heatmap profil, boxplot, distribusi, skor RFM | Hover titik (CustomerID), drag untuk zoom, pilih/hilangkan segmen di sidebar |
| 👥 **Customer** | Tabel 1.000 customer dengan filter | Ketik sebagian ID di pencarian, klik satu baris → detail + top produk + timeline belanja |
| 🛒 **Transaksi** | Tren bulanan, top produk/negara, heatmap hari × jam | Geser rentang tanggal, centang **Kecualikan United Kingdom**, pilih invoice untuk detail |
| ⚙️ **Metodologi** | Funnel cleaning, elbow/silhouette, centroid, parameter, status data | Lihat panel **🗄️ Sumber Data** di bawah |

Tips umum: semua grafik interaktif (hover = tooltip, drag = zoom, ikon kamera = simpan PNG).
Filter berada di **sidebar kiri** dan berbeda per halaman.

## 🔄 Pembaruan data

```
online_retail_II.xlsx          ← file mentah (sumber)
      │  ./run.sh / run.bat  (atau re-run notebook manual)
      ▼
data/ + reports/ + figures/    ← hasil jadi (diperbarui otomatis)
      │  cache mtime otomatis
      ▼
dashboard Streamlit            ← langsung membaca data baru
```

- **Sampel baru / seed berbeda** → jalankan `./run.sh`
- **Dataset mentah baru** → letakkan xlsx baru di `~/Downloads/` (nama sama),
  lalu `./run.sh`
- **Lokasi file mentah berbeda** → `SRC=/path/ke/file.xlsx ./run.sh`
  (atau ubah konstanta `SRC` di sel *Setup* notebook)
- **Windows (cmd)** →
  ```bat
  set SRC=C:\path\ke\online_retail_II.xlsx
  set PORT=8502
  run.bat
  ```
  atau di PowerShell: `$env:SRC = "C:\path\ke\file.xlsx"; .\run.bat`
- Dashboard membaca file hasil via cache ber-**key mtime**: begitu notebook
  selesai dan file berubah, cache otomatis invalid. Tombol **🔄 Muat ulang data**
  di sidebar tersedia sebagai jaminan tambahan.
- Port bisa diganti: `PORT=8502 ./run.sh` (Windows: `set PORT=8502` lalu `run.bat`)

## 🧯 Troubleshooting

| Masalah | Solusi |
|---|---|
| `Virtual environment tidak ditemukan` | Buat venv sesuai bagian *Persiapan lingkungan* |
| `File sumber tidak ditemukan` | Unduh `online_retail_II.xlsx` ke `~/Downloads` atau pakai `SRC=...` |
| Port dipakai / dashboard lama mengganggu | Runner otomatis menghentikan dashboard lama; atau `PORT=8502 ./run.sh` |
| Kernel jupyter belum ada | Runner otomatis mendaftarkan kernel `rfm-kmeans` |
| Data dashboard tidak berubah setelah re-run | Klik **🔄 Muat ulang data** di sidebar; cek panel **Sumber Data** di halaman Metodologi |
| Streamlit menanyakan email saat pertama jalan | Sudah diatasi otomatis: runner membuat `~/.streamlit/credentials.toml` (macOS/Linux) atau `%USERPROFILE%\.streamlit\credentials.toml` (Windows) dengan email kosong |
| Jendela `run.bat` tertutup terlalu cepat | Jalankan `run.bat` dari cmd agar pesan terbaca — semua jalur error sudah diakhiri `pause` |
| Notebook gagal: `SRC` tidak ditemukan di Windows | Ubah konstanta `SRC` di sel *Setup* notebook menjadi path Windows, mis. `Path(r"C:\Users\Andi\Downloads\online_retail_II.xlsx")` |

## 📌 Catatan metodologi

- Cleaning: duplikat persis, invoice pembatalan `C`/adjustment `A`,
  `Quantity ≤ 0`, `UnitPrice ≤ 0`, customer tanpa ID, StockCode non-produk
  → 776.579 baris, 5.852 customer.
- Sampling **per customer** (seed 42) agar riwayat belanja utuh → RFM valid.
- Snapshot RFM = tanggal transaksi maksimum + 1 hari.
- Preprocessing: winsorize p99 → `log1p` (F & M) → `StandardScaler`.
- k=3 dipilih agar segmen ringkas & dapat ditindaklanjuti; elbow/silhouette
  k=2..10 tetap dihitung sebagai pembanding (lihat halaman Metodologi).
- Formula Excel asli per customer tersedia di sheet `Perhitungan_RFM`
  workbook `reports/rfm_kmeans_results.xlsx`.
