@echo off
cd /d %~dp0
call venv\Scripts\activate
venv\Scripts\python -m uvicorn main:app --reload --reload-dir=routes --reload-dir=uploads --reload-delay=0.2
