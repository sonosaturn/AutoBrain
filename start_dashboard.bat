@echo off
echo 🔎 Apertura Dashboard Osservabilita' AI (CodeBurn)...
npx codeburn today
echo.
echo 🐍 Statistiche Python Scripts (Secondo Cervello/Jarvis):
python -c "import sys; sys.path.append('C:/Users/Lorenzo/Desktop/project/secondo_cervello_ai'); from usage_logger import get_today_stats; print(get_today_stats())"
pause
