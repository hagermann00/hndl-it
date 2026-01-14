@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
start python read-it/main.py --y 200
exit
