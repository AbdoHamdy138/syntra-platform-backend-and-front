@echo off
title SYNTRA FastAPI Backend
echo ========================================================
echo   Starting SYNTRA FastAPI Backend on http://localhost:4000
echo ========================================================
cd /d "%~dp0backend"
call .venv\Scripts\activate.bat
python run.py
pause

