@echo off
setlocal
title RFM Dashboard - PSD

REM ============================================================
REM  Runner otomatis proyek PSD (Windows)
REM    run.bat                     -> re-run notebook + dashboard
REM    run.bat --dashboard-only    -> dashboard saja (tanpa re-run notebook)
REM    run.bat --skip-notebook     -> sama dengan --dashboard-only
REM
REM  Variabel lingkungan (opsional), dijalankan sebelum run.bat:
REM    set SRC=C:\path\ke\online_retail_II.xlsx
REM    set PORT=8502
REM ============================================================

set "PSD=%~dp0"
if "%PSD:~-1%"=="\" set "PSD=%PSD:~0,-1%"
pushd "%PSD%"

if not defined SRC set "SRC=%USERPROFILE%\Downloads\online_retail_II.xlsx"
if not defined PORT set "PORT=8501"

echo RFM Dashboard Runner - PSD
echo   Sumber : %SRC%
echo   Port   : %PORT%
echo.

REM --- cari virtual environment (venv) ---
set "VENV=%PSD%\.venv\Scripts"
if not exist "%VENV%\python.exe" set "VENV=%USERPROFILE%\Downloads\rfm_kmeans_online_retail\.venv\Scripts"
if not exist "%VENV%\python.exe" goto NOVENV

REM --- cek file mentah ---
if not exist "%SRC%" goto NOSRC

REM --- bootstrap credentials streamlit (anti prompt email) ---
if not exist "%USERPROFILE%\.streamlit\credentials.toml" (
    mkdir "%USERPROFILE%\.streamlit" 2>nul
    echo [general]>"%USERPROFILE%\.streamlit\credentials.toml"
    >>"%USERPROFILE%\.streamlit\credentials.toml" echo email = ""
)

REM --- mode ---
set SKIP=0
if /i "%~1"=="--dashboard-only" set SKIP=1
if /i "%~1"=="--skip-notebook" set SKIP=1

if "%SKIP%"=="1" goto DASHBOARD

echo [1/2] Re-run notebook (audit, cleaning, RFM, KMeans, export Excel)...
"%VENV%\jupyter.exe" kernelspec list 2>nul | findstr /c:"rfm-kmeans" >nul
if errorlevel 1 (
    echo       Mendaftarkan kernel jupyter "rfm-kmeans"...
    "%VENV%\python.exe" -m ipykernel install --user --name rfm-kmeans --display-name "Python (rfm-kmeans)" >nul
)
"%VENV%\python.exe" -m jupyter nbconvert --to notebook --execute --inplace rfm_kmeans.ipynb
if errorlevel 1 goto NBFAIL
echo       Notebook selesai - data/ dan reports/ diperbarui.
echo.

:DASHBOARD
if "%SKIP%"=="1" echo [1/2] Melewati re-run notebook (--dashboard-only).

REM --- hentikan dashboard lama yang memakai port yang sama ---
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /c:":%PORT%" ^| findstr /c:"LISTENING"') do (
    echo Menghentikan dashboard lama di port %PORT% (PID %%P)...
    taskkill /F /PID %%P >nul 2>&1
)

echo [2/2] Menjalankan dashboard di http://localhost:%PORT% ...
echo       (Ctrl+C untuk berhenti, tutup jendela ini untuk keluar)
"%VENV%\python.exe" -m streamlit run dashboard\app.py --server.headless true --server.port %PORT%
pause
exit /b 0

:NOVENV
echo [X] Virtual environment tidak ditemukan.
echo     Buat dulu di folder proyek (dijalankan satu kali):
echo       python -m venv .venv
echo       .venv\Scripts\pip install -r dashboard\requirements.txt
echo       .venv\Scripts\pip install pandas numpy scikit-learn matplotlib seaborn python-calamine openpyxl jupyter nbconvert ipykernel
pause
exit /b 1

:NOSRC
echo [X] File sumber tidak ditemukan: %SRC%
echo     Unduh online_retail_II.xlsx ke folder Downloads, atau jalankan:
echo       set SRC=C:\path\ke\online_retail_II.xlsx
echo       run.bat
pause
exit /b 1

:NBFAIL
echo [X] Notebook gagal dijalankan. Periksa pesan error di atas.
pause
exit /b 1
