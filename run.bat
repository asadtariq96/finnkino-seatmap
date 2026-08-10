@echo off
cd /d "%~dp0"
if not exist .venv (uv venv .venv && uv pip install --python .venv\Scripts\python.exe -r requirements.txt)
.venv\Scripts\python.exe app.py
