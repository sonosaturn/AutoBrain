@echo off
echo 🔎 Apertura Dashboard Osservabilita' AI (CodeBurn)...
npx codeburn today
echo.
echo 🐍 Statistiche Python Scripts (Secondo Cervello/Jarvis):
.\venv\Scripts\python.exe -c "import sys; import os; sys.path.append(os.path.join(os.getcwd(), 'autobrain_core')); from usage_logger import get_today_stats; print(get_today_stats())"
pause
