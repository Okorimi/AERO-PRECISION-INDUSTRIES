@echo off
cd /d "%~dp0"
if not exist .venv (
  py -3 -m venv .venv 2>nul || python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
if errorlevel 1 (
  echo Installation impossible. Verifiez Python 3.10 ou plus et votre connexion Internet.
  pause
  exit /b 1
)
start "" cmd /c "timeout /t 5 >nul & start http://localhost:8501"
python -m streamlit run app.py --server.headless true --server.port 8501
pause
