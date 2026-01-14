@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
start python todo-it/main.py --y 300
exit
