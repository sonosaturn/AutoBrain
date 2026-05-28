@echo off
title Jarvis Web Interface Launcher
cd %~dp0

echo 🚀 Starting Jarvis Backend...
start "Jarvis Backend" ..\venv\Scripts\python.exe main.py

echo 🌐 Starting React Frontend...
cd webapp
npm run dev

pause
